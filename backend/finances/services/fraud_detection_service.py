"""
Fraud Detection Service for identifying suspicious payment patterns.

This service analyzes payment transactions, user behavior, and other indicators
to detect potentially fraudulent activities and generate appropriate alerts.
"""

from datetime import timedelta
from decimal import Decimal
import logging
from typing import Any

# Cross-app models will be loaded at runtime using apps.get_model()
from django.utils import timezone

from finances.models import (
    AdminAction,
    AdminActionType,
    FraudAlert,
    FraudAlertSeverity,
    FraudAlertStatus,
    PurchaseTransaction,
    StoredPaymentMethod,
    TransactionPaymentStatus,
)

logger = logging.getLogger(__name__)


class FraudDetectionService:
    """
    Service class for detecting fraudulent payment patterns and generating alerts.

    This service provides comprehensive fraud detection functionality including
    pattern analysis, risk scoring, and alert generation with configurable thresholds.
    """

    # Fraud detection thresholds - these could be moved to Django settings
    THRESHOLDS = {
        "multiple_cards_24h": {
            "count": 5,
            "severity": FraudAlertSeverity.HIGH,
            "alert_type": "multiple_payment_methods",
        },
        "high_value_transactions_24h": {
            "amount": Decimal("500.00"),
            "count": 3,
            "severity": FraudAlertSeverity.MEDIUM,
            "alert_type": "high_value_transactions",
        },
        "rapid_transactions": {
            "count": 10,
            "time_window_minutes": 30,
            "severity": FraudAlertSeverity.HIGH,
            "alert_type": "rapid_fire_transactions",
        },
        "failed_attempts_threshold": {
            "count": 8,
            "time_window_hours": 6,
            "severity": FraudAlertSeverity.MEDIUM,
            "alert_type": "multiple_failed_attempts",
        },
        "unusual_amount_patterns": {
            "deviation_threshold": 5.0,  # Standard deviations
            "severity": FraudAlertSeverity.LOW,
            "alert_type": "unusual_spending_pattern",
        },
        "new_user_high_value": {
            "days_old": 1,
            "amount_threshold": Decimal("200.00"),
            "severity": FraudAlertSeverity.MEDIUM,
            "alert_type": "new_user_high_value",
        },
    }

    def __init__(self):
        """Initialize FraudDetectionService."""
        logger.info("FraudDetectionService initialized successfully")

    def analyze_transaction(
        self,
        transaction: PurchaseTransaction,
        admin_user=None,  # CustomUser instance
    ) -> dict[str, Any]:
        """
        Analyze a single transaction for fraud indicators.

        Args:
            transaction: Transaction to analyze
            admin_user: Administrator performing the analysis

        Returns:
            Dict containing analysis results and any alerts generated
        """
        logger.info(f"Analyzing transaction {transaction.id} for fraud indicators")

        try:
            alerts_generated = []
            risk_factors = []
            total_risk_score = Decimal("0.00")

            # Run all fraud detection checks
            checks = [
                self._check_multiple_payment_methods,
                self._check_high_value_transactions,
                self._check_rapid_transactions,
                self._check_failed_attempts,
                self._check_new_user_high_value,
                self._check_unusual_amount_patterns,
            ]

            for check in checks:
                try:
                    result = check(transaction)
                    if result["risk_score"] > 0:
                        risk_factors.append(result)
                        total_risk_score += result["risk_score"]

                        # Generate alert if threshold exceeded
                        if result.get("generate_alert", False):
                            alert = self._generate_fraud_alert(
                                transaction=transaction, risk_data=result, admin_user=admin_user
                            )
                            if alert:
                                alerts_generated.append(alert)

                except Exception as e:
                    logger.error(f"Error in fraud check {check.__name__}: {e}")
                    continue

            logger.info(
                f"Transaction {transaction.id} analysis complete. "
                f"Risk score: {total_risk_score}, Alerts: {len(alerts_generated)}"
            )

            return {
                "success": True,
                "transaction_id": transaction.id,
                "risk_score": min(total_risk_score, Decimal("100.00")),  # Cap at 100
                "risk_factors": risk_factors,
                "alerts_generated": alerts_generated,
                "alert_count": len(alerts_generated),
            }

        except Exception as e:
            logger.error(f"Error analyzing transaction {transaction.id}: {e}")
            return {
                "success": False,
                "error_type": "analysis_error",
                "message": "An error occurred during fraud analysis",
            }

    def analyze_user_activity(
        self,
        user,  # CustomUser instance
        days_back: int = 30,
        admin_user=None,  # CustomUser instance
    ) -> dict[str, Any]:
        """
        Analyze a user's activity for fraud patterns.

        Args:
            user: User to analyze
            days_back: Number of days to look back
            admin_user: Administrator performing the analysis

        Returns:
            Dict containing user analysis results
        """
        logger.info(f"Analyzing user {user.id} activity for fraud patterns")

        try:
            cutoff_date = timezone.now() - timedelta(days=days_back)

            # Get user's recent transactions
            transactions = PurchaseTransaction.objects.filter(student=user, created_at__gte=cutoff_date).order_by(
                "-created_at"
            )

            alerts_generated = []
            risk_score = Decimal("0.00")

            # Analyze user patterns
            user_analysis = self._analyze_user_patterns(user, transactions)
            risk_score += user_analysis["risk_score"]

            # Check for high-risk patterns that warrant alerts
            if user_analysis["risk_score"] >= Decimal("70.00"):
                alert = self._generate_fraud_alert(user=user, risk_data=user_analysis, admin_user=admin_user)
                if alert:
                    alerts_generated.append(alert)

            return {
                "success": True,
                "user_id": user.id,
                "transactions_analyzed": len(transactions),
                "risk_score": min(risk_score, Decimal("100.00")),
                "user_patterns": user_analysis,
                "alerts_generated": alerts_generated,
                "alert_count": len(alerts_generated),
            }

        except Exception as e:
            logger.error(f"Error analyzing user {user.id} activity: {e}")
            return {
                "success": False,
                "error_type": "analysis_error",
                "message": "An error occurred during user activity analysis",
            }

    def run_batch_analysis(
        self,
        hours_back: int = 24,
        admin_user=None,  # CustomUser instance
    ) -> dict[str, Any]:
        """
        Run batch fraud analysis on recent transactions.

        Args:
            hours_back: Number of hours to look back
            admin_user: Administrator running the analysis

        Returns:
            Dict containing batch analysis results
        """
        logger.info(f"Running batch fraud analysis for last {hours_back} hours")

        try:
            cutoff_time = timezone.now() - timedelta(hours=hours_back)

            # Get recent completed transactions
            recent_transactions = PurchaseTransaction.objects.filter(
                created_at__gte=cutoff_time, payment_status=TransactionPaymentStatus.COMPLETED
            ).select_related("student")

            analyzed_count = 0
            alerts_generated = []
            high_risk_transactions = []

            for transaction in recent_transactions:
                try:
                    analysis = self.analyze_transaction(transaction, admin_user)
                    if analysis["success"]:
                        analyzed_count += 1

                        if analysis["risk_score"] >= Decimal("60.00"):
                            high_risk_transactions.append(
                                {
                                    "transaction_id": transaction.id,
                                    "risk_score": analysis["risk_score"],
                                    "user_email": transaction.student.email,
                                }
                            )

                        alerts_generated.extend(analysis["alerts_generated"])

                except Exception as e:
                    logger.error(f"Error analyzing transaction {transaction.id} in batch: {e}")
                    continue

            # Log batch analysis admin action
            if admin_user:
                self._log_admin_action(
                    admin_user=admin_user,
                    action_type=AdminActionType.FRAUD_ALERT,
                    success=True,
                    result_message=f"Batch analysis complete: {analyzed_count} transactions, {len(alerts_generated)} alerts",
                    action_data={
                        "analyzed_count": analyzed_count,
                        "alerts_generated": len(alerts_generated),
                        "high_risk_count": len(high_risk_transactions),
                    },
                )

            logger.info(
                f"Batch analysis complete: {analyzed_count} transactions analyzed, "
                f"{len(alerts_generated)} alerts generated"
            )

            return {
                "success": True,
                "analyzed_count": analyzed_count,
                "alerts_generated": len(alerts_generated),
                "high_risk_transactions": high_risk_transactions,
                "time_period_hours": hours_back,
            }

        except Exception as e:
            logger.error(f"Error in batch fraud analysis: {e}")
            return {
                "success": False,
                "error_type": "batch_analysis_error",
                "message": "An error occurred during batch fraud analysis",
            }

    def get_active_alerts(self, severity: str | None = None, limit: int = 50) -> dict[str, Any]:
        """
        Get active fraud alerts with optional filtering.

        Args:
            severity: Filter by alert severity
            limit: Maximum number of alerts to return

        Returns:
            Dict containing active alerts
        """
        logger.info(f"Retrieving active fraud alerts with severity={severity}")

        try:
            alerts_query = (
                FraudAlert.objects.filter(status=FraudAlertStatus.ACTIVE)
                .select_related("target_user", "assigned_to")
                .order_by("-created_at")
            )

            if severity:
                alerts_query = alerts_query.filter(severity=severity)

            alerts = alerts_query[:limit]

            alert_data = []
            for alert in alerts:
                alert_data.append(
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity,
                        "alert_type": alert.alert_type,
                        "description": alert.description,
                        "risk_score": alert.risk_score,
                        "target_user_email": alert.target_user.email if alert.target_user else None,
                        "assigned_to": alert.assigned_to.email if alert.assigned_to else None,
                        "created_at": alert.created_at,
                        "days_since_created": alert.days_since_created,
                        "is_high_priority": alert.is_high_priority,
                    }
                )

            return {
                "success": True,
                "alerts": alert_data,
                "count": len(alert_data),
                "total_active": FraudAlert.objects.filter(status=FraudAlertStatus.ACTIVE).count(),
            }

        except Exception as e:
            logger.error(f"Error retrieving active alerts: {e}")
            return {
                "success": False,
                "error_type": "retrieval_error",
                "message": "An error occurred while retrieving fraud alerts",
            }

    def _check_multiple_payment_methods(self, transaction: PurchaseTransaction) -> dict[str, Any]:
        """Check for multiple payment methods used in short time period."""
        user = transaction.student
        last_24h = timezone.now() - timedelta(hours=24)

        # Count unique payment methods used in last 24 hours
        payment_methods_count = StoredPaymentMethod.objects.filter(student=user, created_at__gte=last_24h).count()

        threshold = self.THRESHOLDS["multiple_cards_24h"]
        risk_score = Decimal("0.00")
        generate_alert = False

        if payment_methods_count >= threshold["count"]:
            risk_score = Decimal("40.00")
            generate_alert = True
        elif payment_methods_count >= threshold["count"] - 2:
            risk_score = Decimal("20.00")

        return {
            "check_type": "multiple_payment_methods",
            "risk_score": risk_score,
            "generate_alert": generate_alert,
            "details": {"payment_methods_count": payment_methods_count, "threshold": threshold["count"]},
            "severity": threshold["severity"] if generate_alert else FraudAlertSeverity.LOW,
            "alert_type": threshold["alert_type"],
        }

    def _check_high_value_transactions(self, transaction: PurchaseTransaction) -> dict[str, Any]:
        """Check for multiple high-value transactions in short period."""
        user = transaction.student
        last_24h = timezone.now() - timedelta(hours=24)
        threshold = self.THRESHOLDS["high_value_transactions_24h"]

        high_value_count = PurchaseTransaction.objects.filter(
            student=user,
            created_at__gte=last_24h,
            amount__gte=threshold["amount"],
            payment_status=TransactionPaymentStatus.COMPLETED,
        ).count()

        risk_score = Decimal("0.00")
        generate_alert = False

        if high_value_count >= threshold["count"]:
            risk_score = Decimal("35.00")
            generate_alert = True
        elif high_value_count >= threshold["count"] - 1:
            risk_score = Decimal("15.00")

        return {
            "check_type": "high_value_transactions",
            "risk_score": risk_score,
            "generate_alert": generate_alert,
            "details": {
                "high_value_count": high_value_count,
                "threshold_amount": threshold["amount"],
                "threshold_count": threshold["count"],
            },
            "severity": threshold["severity"] if generate_alert else FraudAlertSeverity.LOW,
            "alert_type": threshold["alert_type"],
        }

    def _check_rapid_transactions(self, transaction: PurchaseTransaction) -> dict[str, Any]:
        """Check for rapid-fire transaction attempts."""
        user = transaction.student
        threshold = self.THRESHOLDS["rapid_transactions"]
        time_window = timezone.now() - timedelta(minutes=threshold["time_window_minutes"])

        rapid_count = PurchaseTransaction.objects.filter(student=user, created_at__gte=time_window).count()

        risk_score = Decimal("0.00")
        generate_alert = False

        if rapid_count >= threshold["count"]:
            risk_score = Decimal("50.00")
            generate_alert = True
        elif rapid_count >= threshold["count"] - 3:
            risk_score = Decimal("25.00")

        return {
            "check_type": "rapid_transactions",
            "risk_score": risk_score,
            "generate_alert": generate_alert,
            "details": {
                "transaction_count": rapid_count,
                "time_window_minutes": threshold["time_window_minutes"],
                "threshold": threshold["count"],
            },
            "severity": threshold["severity"] if generate_alert else FraudAlertSeverity.LOW,
            "alert_type": threshold["alert_type"],
        }

    def _check_failed_attempts(self, transaction: PurchaseTransaction) -> dict[str, Any]:
        """Check for multiple failed payment attempts."""
        user = transaction.student
        threshold = self.THRESHOLDS["failed_attempts_threshold"]
        time_window = timezone.now() - timedelta(hours=threshold["time_window_hours"])

        failed_count = PurchaseTransaction.objects.filter(
            student=user, created_at__gte=time_window, payment_status=TransactionPaymentStatus.FAILED
        ).count()

        risk_score = Decimal("0.00")
        generate_alert = False

        if failed_count >= threshold["count"]:
            risk_score = Decimal("30.00")
            generate_alert = True
        elif failed_count >= threshold["count"] - 3:
            risk_score = Decimal("15.00")

        return {
            "check_type": "failed_attempts",
            "risk_score": risk_score,
            "generate_alert": generate_alert,
            "details": {
                "failed_count": failed_count,
                "time_window_hours": threshold["time_window_hours"],
                "threshold": threshold["count"],
            },
            "severity": threshold["severity"] if generate_alert else FraudAlertSeverity.LOW,
            "alert_type": threshold["alert_type"],
        }

    def _check_new_user_high_value(self, transaction: PurchaseTransaction) -> dict[str, Any]:
        """Check for high-value transactions from new users."""
        user = transaction.student
        threshold = self.THRESHOLDS["new_user_high_value"]

        user_age = timezone.now() - user.date_joined
        is_new_user = user_age.days <= threshold["days_old"]
        is_high_value = transaction.amount >= threshold["amount_threshold"]

        risk_score = Decimal("0.00")
        generate_alert = False

        if is_new_user and is_high_value:
            risk_score = Decimal("45.00")
            generate_alert = True
        elif is_new_user and transaction.amount >= threshold["amount_threshold"] / 2:
            risk_score = Decimal("20.00")

        return {
            "check_type": "new_user_high_value",
            "risk_score": risk_score,
            "generate_alert": generate_alert,
            "details": {
                "user_age_days": user_age.days,
                "transaction_amount": transaction.amount,
                "threshold_days": threshold["days_old"],
                "threshold_amount": threshold["amount_threshold"],
            },
            "severity": threshold["severity"] if generate_alert else FraudAlertSeverity.LOW,
            "alert_type": threshold["alert_type"],
        }

    def _check_unusual_amount_patterns(self, transaction: PurchaseTransaction) -> dict[str, Any]:
        """Check for unusual spending patterns based on user history."""
        user = transaction.student

        # Get user's transaction history (last 90 days, excluding current transaction)
        last_90_days = timezone.now() - timedelta(days=90)
        historical_transactions = PurchaseTransaction.objects.filter(
            student=user, created_at__gte=last_90_days, payment_status=TransactionPaymentStatus.COMPLETED
        ).exclude(id=transaction.id)

        if historical_transactions.count() < 3:
            # Not enough history to determine patterns
            return {
                "check_type": "unusual_amount_patterns",
                "risk_score": Decimal("0.00"),
                "generate_alert": False,
                "details": {"insufficient_history": True},
            }

        # Calculate mean and standard deviation
        amounts = [t.amount for t in historical_transactions]
        mean_amount = sum(amounts) / len(amounts)

        variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
        std_dev = variance ** Decimal("0.5")

        deviation = Decimal("0.00") if std_dev == 0 else abs(transaction.amount - mean_amount) / std_dev

        threshold = self.THRESHOLDS["unusual_amount_patterns"]
        risk_score = Decimal("0.00")
        generate_alert = False

        if deviation >= threshold["deviation_threshold"]:
            risk_score = Decimal("25.00")
            generate_alert = True
        elif deviation >= threshold["deviation_threshold"] - 1:
            risk_score = Decimal("10.00")

        return {
            "check_type": "unusual_amount_patterns",
            "risk_score": risk_score,
            "generate_alert": generate_alert,
            "details": {
                "transaction_amount": transaction.amount,
                "historical_mean": mean_amount,
                "standard_deviation": std_dev,
                "deviation_score": deviation,
                "threshold": threshold["deviation_threshold"],
            },
            "severity": threshold["severity"] if generate_alert else FraudAlertSeverity.LOW,
            "alert_type": threshold["alert_type"],
        }

    def _analyze_user_patterns(
        self,
        user,  # CustomUser instance
        transactions: list[PurchaseTransaction],
    ) -> dict[str, Any]:
        """Analyze overall user patterns for fraud indicators."""
        risk_score = Decimal("0.00")
        patterns = {}

        if not transactions:
            return {"risk_score": risk_score, "patterns": patterns}

        # Calculate transaction frequency
        if len(transactions) > 1:
            time_span = transactions[0].created_at - transactions[-1].created_at
            if time_span.total_seconds() > 0:
                daily_frequency = len(transactions) / (time_span.days + 1)
                patterns["daily_frequency"] = daily_frequency

                if daily_frequency > 5:  # More than 5 transactions per day on average
                    risk_score += Decimal("20.00")

        # Calculate amount volatility
        amounts = [t.amount for t in transactions]
        if len(amounts) > 2:
            mean_amount = sum(amounts) / len(amounts)
            amount_variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
            coefficient_of_variation = (amount_variance ** Decimal("0.5")) / mean_amount if mean_amount > 0 else 0

            patterns["amount_volatility"] = float(coefficient_of_variation)

            if coefficient_of_variation > 2:  # High volatility
                risk_score += Decimal("15.00")

        # Check for geographic patterns (if we had IP/location data)
        # This would be implemented with IP geolocation

        patterns["total_transactions"] = len(transactions)
        patterns["total_amount"] = sum(amounts)

        return {"risk_score": risk_score, "patterns": patterns, "alert_type": "user_behavior_analysis"}

    def _generate_fraud_alert(
        self,
        risk_data: dict[str, Any],
        transaction: PurchaseTransaction | None = None,
        user=None,  # CustomUser instance
        admin_user=None,  # CustomUser instance
    ) -> dict[str, Any] | None:
        """Generate a fraud alert based on risk data."""
        try:
            target_user = user or (transaction.student if transaction else None)
            if not target_user:
                return None

            # Check if similar alert already exists and is active
            existing_alert = FraudAlert.objects.filter(
                target_user=target_user,
                alert_type=risk_data.get("alert_type", "unknown"),
                status=FraudAlertStatus.ACTIVE,
                created_at__gte=timezone.now() - timedelta(hours=24),
            ).first()

            if existing_alert:
                logger.info(f"Similar alert already exists for user {target_user.id}")
                return None

            # Create fraud alert
            alert = FraudAlert.objects.create(
                severity=risk_data.get("severity", FraudAlertSeverity.MEDIUM),
                alert_type=risk_data.get("alert_type", "unknown_pattern"),
                description=self._format_alert_description(risk_data),
                target_user=target_user,
                detection_data=risk_data,
                risk_score=risk_data.get("risk_score", Decimal("0.00")),
            )

            # Associate transaction if provided
            if transaction:
                alert.related_transactions.add(transaction)

            # Log admin action
            if admin_user:
                self._log_admin_action(
                    admin_user=admin_user,
                    action_type=AdminActionType.FRAUD_ALERT,
                    target_user=target_user,
                    success=True,
                    result_message=f"Fraud alert generated: {alert.alert_id}",
                    action_data={"alert_id": alert.alert_id, "risk_score": float(alert.risk_score)},
                )

            logger.info(f"Fraud alert {alert.alert_id} generated for user {target_user.id}")

            return {
                "alert_id": alert.alert_id,
                "severity": alert.severity,
                "alert_type": alert.alert_type,
                "risk_score": alert.risk_score,
            }

        except Exception as e:
            logger.error(f"Error generating fraud alert: {e}")
            return None

    def _format_alert_description(self, risk_data: dict[str, Any]) -> str:
        """Format a user-friendly alert description."""
        alert_type = risk_data.get("alert_type", "unknown")
        details = risk_data.get("details", {})

        descriptions = {
            "multiple_payment_methods": f"User added {details.get('payment_methods_count', 0)} payment methods in 24 hours",
            "high_value_transactions": f"User made {details.get('high_value_count', 0)} high-value transactions in 24 hours",
            "rapid_fire_transactions": f"User made {details.get('transaction_count', 0)} transactions in {details.get('time_window_minutes', 0)} minutes",
            "multiple_failed_attempts": f"User had {details.get('failed_count', 0)} failed payment attempts in {details.get('time_window_hours', 0)} hours",
            "new_user_high_value": f"New user (account age: {details.get('user_age_days', 0)} days) made high-value transaction",
            "unusual_spending_pattern": f"Transaction amount deviates {details.get('deviation_score', 0):.1f} standard deviations from user's normal pattern",
            "user_behavior_analysis": "Suspicious user behavior pattern detected across multiple transactions",
        }

        return descriptions.get(alert_type, f"Suspicious activity detected: {alert_type}")

    def _log_admin_action(
        self,
        admin_user,  # CustomUser instance
        action_type: AdminActionType,
        target_user=None,  # CustomUser instance
        success: bool = True,
        result_message: str = "",
        action_data: dict[str, Any] | None = None,
    ) -> None:
        """Log administrative action for audit trail."""
        try:
            AdminAction.objects.create(
                action_type=action_type,
                action_description=f"Fraud detection analysis for user {target_user.id if target_user else 'system'}",
                admin_user=admin_user,
                target_user=target_user,
                success=success,
                result_message=result_message,
                action_data=action_data or {},
            )

            logger.info(f"Admin action logged: {action_type} by {admin_user.email}")

        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
