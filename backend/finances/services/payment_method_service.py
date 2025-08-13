"""
Payment Method Management Service for the finances app.

Handles secure payment method storage using Stripe tokenization.
Maintains PCI compliance by storing only Stripe tokens, not card data.
"""

import logging
from typing import Dict, Any, Optional, List

from django.db import transaction
from django.apps import apps
from finances.models import StoredPaymentMethod
from finances.services.stripe_base import StripeService

logger = logging.getLogger(__name__)


class PaymentMethodService:
    """
    Service for managing stored payment methods with Stripe tokenization.
    
    Features:
    - Secure payment method storage using Stripe tokens
    - PCI compliance (no sensitive card data stored)
    - Default payment method management
    - Payment method validation and cleanup
    - Comprehensive error handling
    """
    
    def __init__(self):
        """Initialize the service with Stripe integration."""
        self.stripe_service = StripeService()
    
    def add_payment_method(self, student_user, stripe_payment_method_id: str, 
                          is_default: bool = False, auto_create_customer: bool = True) -> Dict[str, Any]:
        """
        Add a new payment method for a student using Stripe tokenization with Customer support.
        
        Args:
            student_user: Student user to add payment method for
            stripe_payment_method_id: Stripe PaymentMethod ID from frontend
            is_default: Whether to set as default payment method
            auto_create_customer: Whether to auto-create Stripe Customer if needed
            
        Returns:
            Dict containing success status, payment method data, or error information
        """
        try:
            # Validate Stripe payment method
            payment_method_data = self._validate_stripe_payment_method(stripe_payment_method_id)
            if not payment_method_data['success']:
                return payment_method_data
            
            stripe_pm_data = payment_method_data['payment_method']
            
            # Check if payment method already exists
            if StoredPaymentMethod.objects.filter(
                stripe_payment_method_id=stripe_payment_method_id
            ).exists():
                return {
                    'success': False,
                    'error_type': 'already_exists',
                    'message': 'This payment method is already stored'
                }
            
            # Get or create Stripe Customer
            customer_result = self._get_or_create_stripe_customer(student_user, auto_create_customer)
            if not customer_result['success']:
                return customer_result
            
            stripe_customer_id = customer_result['customer_id']
            
            # Attach payment method to customer
            attach_result = self.stripe_service.attach_payment_method_to_customer(
                stripe_payment_method_id, 
                stripe_customer_id
            )
            if not attach_result['success']:
                return attach_result
            
            # Create payment method record with atomic transaction
            with transaction.atomic():
                # If setting as default, unset other defaults
                if is_default:
                    StoredPaymentMethod.objects.filter(
                        student=student_user,
                        is_default=True
                    ).update(is_default=False)
                
                # Create new payment method record
                stored_payment_method = StoredPaymentMethod.objects.create(
                    student=student_user,
                    stripe_payment_method_id=stripe_payment_method_id,
                    stripe_customer_id=stripe_customer_id,
                    card_brand=stripe_pm_data.get('brand', ''),
                    card_last4=stripe_pm_data.get('last4', ''),
                    card_exp_month=stripe_pm_data.get('exp_month'),
                    card_exp_year=stripe_pm_data.get('exp_year'),
                    is_default=is_default,
                    is_active=True
                )
            
            logger.info(
                f"Added payment method {stored_payment_method.id} "
                f"for student {student_user.id} (Stripe PM: {stripe_payment_method_id}, Customer: {stripe_customer_id})"
            )
            
            return {
                'success': True,
                'payment_method_id': stored_payment_method.id,
                'card_display': stored_payment_method.card_display,
                'is_default': stored_payment_method.is_default,
                'stripe_customer_id': stripe_customer_id,
                'message': 'Payment method added successfully'
            }
            
        except Exception as e:
            logger.error(
                f"Error adding payment method for student {student_user.id}: {e}", 
                exc_info=True
            )
            return {
                'success': False,
                'error_type': 'creation_error',
                'message': f'Failed to add payment method: {str(e)}'
            }
    
    def remove_payment_method(self, student_user, payment_method_id: int) -> Dict[str, Any]:
        """
        Remove a stored payment method and detach from Stripe.
        
        Args:
            student_user: Student user removing the payment method
            payment_method_id: ID of the stored payment method to remove
            
        Returns:
            Dict containing success status or error information
        """
        try:
            # Get and validate payment method
            try:
                stored_payment_method = StoredPaymentMethod.objects.get(
                    id=payment_method_id,
                    student=student_user
                )
            except StoredPaymentMethod.DoesNotExist:
                return {
                    'success': False,
                    'error_type': 'not_found',
                    'message': 'Payment method not found'
                }
            
            stripe_payment_method_id = stored_payment_method.stripe_payment_method_id
            was_default = stored_payment_method.is_default
            
            # Detach from Stripe and remove from database
            with transaction.atomic():
                # Detach from Stripe (best effort - don't fail if Stripe call fails)
                try:
                    self.stripe_service.detach_payment_method(stripe_payment_method_id)
                    logger.info(f"Detached payment method {stripe_payment_method_id} from Stripe")
                except Exception as e:
                    logger.warning(
                        f"Failed to detach payment method {stripe_payment_method_id} from Stripe: {e}"
                    )
                
                # Remove from database
                stored_payment_method.delete()
                
                # If this was the default, set another one as default
                if was_default:
                    next_payment_method = StoredPaymentMethod.objects.filter(
                        student=student_user,
                        is_active=True
                    ).first()
                    
                    if next_payment_method:
                        next_payment_method.is_default = True
                        next_payment_method.save()
                        logger.info(f"Set payment method {next_payment_method.id} as new default")
            
            logger.info(f"Removed payment method {payment_method_id} for student {student_user.id}")
            
            return {
                'success': True,
                'message': 'Payment method removed successfully',
                'was_default': was_default
            }
            
        except Exception as e:
            logger.error(
                f"Error removing payment method {payment_method_id} for student {student_user.id}: {e}", 
                exc_info=True
            )
            return {
                'success': False,
                'error_type': 'removal_error',
                'message': f'Failed to remove payment method: {str(e)}'
            }
    
    def list_payment_methods(self, student_user, include_expired: bool = False) -> Dict[str, Any]:
        """
        List all stored payment methods for a student.
        
        Args:
            student_user: Student user to list payment methods for
            include_expired: Whether to include expired payment methods
            
        Returns:
            Dict containing payment methods list or error information
        """
        try:
            queryset = StoredPaymentMethod.objects.filter(
                student=student_user,
                is_active=True
            ).order_by('-is_default', '-created_at')
            
            payment_methods = []
            for pm in queryset:
                # Skip expired unless explicitly requested
                if pm.is_expired and not include_expired:
                    continue
                
                # Use PCI-compliant response format
                payment_methods.append({
                    'id': pm.id,
                    'card_brand': pm.card_brand,
                    'card_exp_month': pm.card_exp_month,
                    'card_exp_year': pm.card_exp_year,
                    'card_display': pm.card_display,  # PCI-compliant display only
                    'is_default': pm.is_default,
                    'is_expired': pm.is_expired,
                    'stripe_customer_id': pm.stripe_customer_id,
                    'created_at': pm.created_at.isoformat(),
                })
            
            return {
                'success': True,
                'payment_methods': payment_methods,
                'count': len(payment_methods)
            }
            
        except Exception as e:
            logger.error(f"Error listing payment methods for student {student_user.id}: {e}", exc_info=True)
            return {
                'success': False,
                'error_type': 'list_error',
                'message': f'Failed to list payment methods: {str(e)}'
            }
    
    def set_default_payment_method(self, student_user, payment_method_id: int) -> Dict[str, Any]:
        """
        Set a payment method as the default for a student.
        
        Args:
            student_user: Student user setting the default
            payment_method_id: ID of the payment method to set as default
            
        Returns:
            Dict containing success status or error information
        """
        try:
            with transaction.atomic():
                # Validate payment method exists and belongs to user
                try:
                    new_default = StoredPaymentMethod.objects.get(
                        id=payment_method_id,
                        student=student_user,
                        is_active=True
                    )
                except StoredPaymentMethod.DoesNotExist:
                    return {
                        'success': False,
                        'error_type': 'not_found',
                        'message': 'Payment method not found'
                    }
                
                # Check if expired
                if new_default.is_expired:
                    return {
                        'success': False,
                        'error_type': 'expired',
                        'message': 'Cannot set expired payment method as default'
                    }
                
                # Unset current default
                StoredPaymentMethod.objects.filter(
                    student=student_user,
                    is_default=True
                ).update(is_default=False)
                
                # Set new default
                new_default.is_default = True
                new_default.save()
            
            logger.info(f"Set payment method {payment_method_id} as default for student {student_user.id}")
            
            return {
                'success': True,
                'message': 'Default payment method updated successfully'
            }
            
        except Exception as e:
            logger.error(
                f"Error setting default payment method {payment_method_id} for student {student_user.id}: {e}", 
                exc_info=True
            )
            return {
                'success': False,
                'error_type': 'update_error',
                'message': f'Failed to update default payment method: {str(e)}'
            }
    
    def get_default_payment_method(self, student_user) -> Optional[StoredPaymentMethod]:
        """
        Get the default payment method for a student.
        
        Args:
            student_user: Student user to get default payment method for
            
        Returns:
            StoredPaymentMethod instance or None if no default found
        """
        try:
            return StoredPaymentMethod.objects.filter(
                student=student_user,
                is_default=True,
                is_active=True
            ).first()
        except Exception as e:
            logger.error(f"Error getting default payment method for student {student_user.id}: {e}")
            return None
    
    def cleanup_expired_payment_methods(self, student_user=None) -> Dict[str, Any]:
        """
        Clean up expired payment methods (mark as inactive).
        
        Args:
            student_user: Optional specific student to clean up (None for all students)
            
        Returns:
            Dict containing cleanup results
        """
        try:
            queryset = StoredPaymentMethod.objects.filter(is_active=True)
            
            if student_user:
                queryset = queryset.filter(student=student_user)
            
            expired_count = 0
            for pm in queryset:
                if pm.is_expired:
                    pm.is_active = False
                    if pm.is_default:
                        pm.is_default = False
                    pm.save()
                    expired_count += 1
                    
                    logger.info(f"Marked expired payment method {pm.id} as inactive")
            
            return {
                'success': True,
                'expired_count': expired_count,
                'message': f'Cleaned up {expired_count} expired payment methods'
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up expired payment methods: {e}", exc_info=True)
            return {
                'success': False,
                'error_type': 'cleanup_error',
                'message': f'Failed to cleanup expired payment methods: {str(e)}'
            }
    
    def _validate_stripe_payment_method(self, stripe_payment_method_id: str) -> Dict[str, Any]:
        """
        Validate a Stripe payment method and retrieve its details.
        
        Args:
            stripe_payment_method_id: Stripe PaymentMethod ID to validate
            
        Returns:
            Dict containing validation result and payment method data
        """
        try:
            # Retrieve payment method from Stripe
            result = self.stripe_service.retrieve_payment_method(stripe_payment_method_id)
            
            if not result['success']:
                return {
                    'success': False,
                    'error_type': 'stripe_error',
                    'message': f'Invalid payment method: {result.get("message", "Unknown error")}'
                }
            
            stripe_pm = result['payment_method']
            
            # Extract card details
            card_data = {}
            if stripe_pm.get('type') == 'card' and 'card' in stripe_pm:
                card_info = stripe_pm['card']
                card_data = {
                    'brand': card_info.get('brand', ''),
                    'last4': card_info.get('last4', ''),
                    'exp_month': card_info.get('exp_month'),
                    'exp_year': card_info.get('exp_year'),
                }
            
            return {
                'success': True,
                'payment_method': card_data,
                'stripe_data': stripe_pm
            }
            
        except Exception as e:
            logger.error(f"Error validating Stripe payment method {stripe_payment_method_id}: {e}")
            return {
                'success': False,
                'error_type': 'validation_error',
                'message': f'Failed to validate payment method: {str(e)}'
            }
    
    def _get_or_create_stripe_customer(self, student_user, auto_create: bool = True) -> Dict[str, Any]:
        """
        Get or create a Stripe Customer for the student user.
        
        Args:
            student_user: Student user to get/create customer for
            auto_create: Whether to auto-create customer if not found
            
        Returns:
            Dict containing success status and customer_id or error information
        """
        # Check if student already has a stored payment method with customer_id
        existing_payment_method = StoredPaymentMethod.objects.filter(
            student=student_user,
            stripe_customer_id__isnull=False,
            is_active=True
        ).first()
        
        if existing_payment_method and existing_payment_method.stripe_customer_id:
            # Verify customer exists in Stripe
            customer_check = self.stripe_service.retrieve_customer(existing_payment_method.stripe_customer_id)
            if customer_check['success']:
                return {
                    'success': True,
                    'customer_id': existing_payment_method.stripe_customer_id,
                    'existing': True
                }
            else:
                logger.warning(
                    f"Stripe customer {existing_payment_method.stripe_customer_id} "
                    f"for student {student_user.id} not found in Stripe. Will create new one."
                )
        
        # Check existing transactions for customer_id using proper cross-app access
        try:
            PurchaseTransaction = apps.get_model('finances', 'PurchaseTransaction')
            existing_transaction = PurchaseTransaction.objects.filter(
                student=student_user,
                stripe_customer_id__isnull=False
            ).first()
        except LookupError:
            # Model not available, skip transaction check
            existing_transaction = None
        
        if existing_transaction and existing_transaction.stripe_customer_id:
            # Verify customer exists in Stripe
            customer_check = self.stripe_service.retrieve_customer(existing_transaction.stripe_customer_id)
            if customer_check['success']:
                return {
                    'success': True,
                    'customer_id': existing_transaction.stripe_customer_id,
                    'existing': True
                }
            else:
                logger.warning(
                    f"Stripe customer {existing_transaction.stripe_customer_id} "
                    f"for student {student_user.id} not found in Stripe. Will create new one."
                )
        
        # Create new customer if auto_create is enabled
        if auto_create:
            customer_metadata = {
                'student_id': str(student_user.id),
                'platform': 'aprende_comigo',
                'created_via': 'payment_method_service'
            }
            
            customer_result = self.stripe_service.create_customer(
                email=student_user.email,
                name=student_user.name,
                metadata=customer_metadata
            )
            
            if customer_result['success']:
                logger.info(
                    f"Created new Stripe customer {customer_result['customer_id']} "
                    f"for student {student_user.id}"
                )
                return {
                    'success': True,
                    'customer_id': customer_result['customer_id'],
                    'existing': False
                }
            else:
                return customer_result
        else:
            return {
                'success': False,
                'error_type': 'no_customer',
                'message': 'No Stripe customer found and auto-creation is disabled'
            }


class PaymentMethodValidationError(Exception):
    """Exception raised for payment method validation errors."""
    pass