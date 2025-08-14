"""
Receipt Generation Service for the finances app.

Handles HTML receipt generation with professional templates.
Provides comprehensive receipt creation, validation, and file management.
"""

import logging
import os
from decimal import Decimal
from typing import Dict, Any, Optional

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction as db_transaction

from finances.models import Receipt, PurchaseTransaction, TransactionPaymentStatus


logger = logging.getLogger(__name__)


class ReceiptGenerationService:
    """
    Service for generating HTML receipts for student purchases.
    
    Features:
    - Professional HTML templates
    - Automatic receipt numbering
    - File storage and cleanup
    - Comprehensive error handling
    - Audit trail maintenance
    """
    
    @classmethod
    def generate_receipt(cls, transaction_id: int, force_regenerate: bool = False) -> Dict[str, Any]:
        """
        Generate an HTML receipt for a completed transaction.
        
        Args:
            transaction_id: ID of the transaction to generate receipt for
            force_regenerate: Whether to regenerate if receipt already exists
            
        Returns:
            Dict containing success status, receipt data, or error information
        """
        # Type validation for transaction_id - strict validation to match test expectations
        if transaction_id is None:
            raise ValueError("transaction_id cannot be None")
        if isinstance(transaction_id, bool) or not isinstance(transaction_id, int):
            raise TypeError(f"transaction_id must be an integer, got {type(transaction_id).__name__}")
                
        try:
            # Get and validate transaction
            try:
                transaction = PurchaseTransaction.objects.select_related('student').get(
                    id=transaction_id
                )
            except PurchaseTransaction.DoesNotExist:
                return {
                    'success': False,
                    'error_type': 'not_found',
                    'message': 'Transaction not found'
                }
            
            # Validate transaction status
            if transaction.payment_status != TransactionPaymentStatus.COMPLETED:
                return {
                    'success': False,
                    'error_type': 'invalid_status',
                    'message': 'Can only generate receipts for completed transactions'
                }
            
            # Check if receipt already exists
            existing_receipt = Receipt.objects.filter(transaction=transaction).first()
            if existing_receipt and not force_regenerate:
                logger.info(f"Receipt already exists for transaction {transaction_id}")
                return {
                    'success': True,
                    'receipt_id': existing_receipt.id,
                    'receipt_number': existing_receipt.receipt_number,
                    'already_existed': True,
                    'message': 'Receipt already exists'
                }
            
            # Generate receipt with atomic transaction
            with db_transaction.atomic():
                if existing_receipt and force_regenerate:
                    # Delete existing receipt file and record
                    cls._cleanup_receipt_file(existing_receipt)
                    existing_receipt.delete()
                
                receipt = cls._create_receipt_record(transaction)
                html_content = cls._generate_html_content(receipt)
                cls._save_html_file(receipt, html_content)
            
            logger.info(f"Successfully generated receipt {receipt.receipt_number} for transaction {transaction_id}")
            
            return {
                'success': True,
                'receipt_id': receipt.id,
                'receipt_number': receipt.receipt_number,
                'html_file_url': receipt.pdf_file.url if receipt.pdf_file else None,
                'amount': float(receipt.amount),
                'generated_at': receipt.generated_at.isoformat(),
                'message': 'Receipt generated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error generating receipt for transaction {transaction_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error_type': 'generation_error',
                'message': f'Failed to generate receipt: {str(e)}'
            }
    
    @classmethod
    def get_receipt_download_url(cls, receipt_id: int, student_user) -> Dict[str, Any]:
        """
        Get secure download URL for a receipt.
        
        Args:
            receipt_id: ID of the receipt
            student_user: User requesting the download (for security validation)
            
        Returns:
            Dict containing download URL or error information
        """
        # Type validation for receipt_id - strict validation to match test expectations
        if receipt_id is None:
            raise ValueError("receipt_id cannot be None")
        if isinstance(receipt_id, bool) or not isinstance(receipt_id, int):
            raise TypeError(f"receipt_id must be an integer, got {type(receipt_id).__name__}")
                
        try:
            receipt = Receipt.objects.select_related('student', 'transaction').get(
                id=receipt_id
            )
            
            # Validate ownership
            if receipt.student != student_user:
                return {
                    'success': False,
                    'error_type': 'permission_denied',
                    'message': 'You can only download your own receipts'
                }
            
            # Validate receipt is valid
            if not receipt.is_valid:
                return {
                    'success': False,
                    'error_type': 'invalid_receipt',
                    'message': 'This receipt is no longer valid'
                }
            
            # Check if HTML file exists
            if not receipt.pdf_file:
                # Try to regenerate if missing
                logger.warning(f"HTML file missing for receipt {receipt.id}, attempting regeneration")
                generation_result = cls.generate_receipt(receipt.transaction.id, force_regenerate=True)
                
                if not generation_result['success']:
                    return {
                        'success': False,
                        'error_type': 'file_missing',
                        'message': 'Receipt HTML file is missing and could not be regenerated'
                    }
                
                # Refresh receipt from database
                receipt.refresh_from_db()
            
            return {
                'success': True,
                'download_url': receipt.pdf_file.url,
                'receipt_number': receipt.receipt_number,
                'filename': f"receipt_{receipt.receipt_number}.html"
            }
            
        except Receipt.DoesNotExist:
            return {
                'success': False,
                'error_type': 'not_found',
                'message': 'Receipt not found'
            }
        except Exception as e:
            logger.error(f"Error getting download URL for receipt {receipt_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error_type': 'download_error',
                'message': f'Failed to get download URL: {str(e)}'
            }
    
    @classmethod
    def list_student_receipts(cls, student_user, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List all receipts for a student with optional filtering.
        
        Args:
            student_user: Student user to get receipts for
            filters: Optional filtering parameters
            
        Returns:
            Dict containing receipt list or error information
        """
        try:
            queryset = Receipt.objects.filter(
                student=student_user
            ).select_related('transaction').order_by('-generated_at')
            
            # Apply filters if provided
            if filters:
                if 'is_valid' in filters:
                    queryset = queryset.filter(is_valid=filters['is_valid'])
                
                if 'start_date' in filters:
                    queryset = queryset.filter(generated_at__gte=filters['start_date'])
                
                if 'end_date' in filters:
                    queryset = queryset.filter(generated_at__lte=filters['end_date'])
            
            receipts = []
            for receipt in queryset:
                receipts.append({
                    'id': receipt.id,
                    'receipt_number': receipt.receipt_number,
                    'amount': float(receipt.amount),
                    'generated_at': receipt.generated_at.isoformat(),
                    'is_valid': receipt.is_valid,
                    'transaction_id': receipt.transaction.id,
                    'transaction_type': receipt.transaction.get_transaction_type_display(),
                    'plan_name': receipt.transaction.metadata.get('plan_name', 'Unknown Plan') if receipt.transaction.metadata else 'Unknown Plan',
                    'has_html': bool(receipt.pdf_file),
                    'download_url': receipt.pdf_file.url if receipt.pdf_file else None
                })
            
            return {
                'success': True,
                'receipts': receipts,
                'count': len(receipts)
            }
            
        except Exception as e:
            logger.error(f"Error listing receipts for student {student_user.id}: {e}", exc_info=True)
            return {
                'success': False,
                'error_type': 'list_error',
                'message': f'Failed to list receipts: {str(e)}'
            }
    
    @classmethod
    def _create_receipt_record(cls, transaction: PurchaseTransaction) -> Receipt:
        """Create receipt database record."""
        receipt = Receipt.objects.create(
            student=transaction.student,
            transaction=transaction,
            amount=transaction.amount,
            metadata={
                'transaction_type': transaction.transaction_type,
                'plan_name': transaction.metadata.get('plan_name') if transaction.metadata else None,
                'generation_timestamp': timezone.now().isoformat(),
            }
        )
        
        logger.info(f"Created receipt record {receipt.receipt_number} for transaction {transaction.id}")
        return receipt
    
    @classmethod
    def _generate_html_content(cls, receipt: Receipt) -> str:
        """Generate HTML content with embedded styles."""
        # Prepare template context
        context = cls._prepare_template_context(receipt)
        
        # Render HTML template
        html_content = render_to_string('emails/receipt_template.html', context)
        
        # Add embedded CSS styles
        css_styles = cls._get_receipt_css()
        html_with_styles = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Receipt {receipt.receipt_number}</title>
    <style>
{css_styles}
    </style>
</head>
<body>
{html_content[html_content.find('<body>') + 6:html_content.find('</body>')]}
</body>
</html>"""
        
        logger.info(f"Generated HTML content for receipt {receipt.receipt_number} ({len(html_with_styles.encode('utf-8'))} bytes)")
        return html_with_styles
    
    @classmethod
    def _prepare_template_context(cls, receipt: Receipt) -> Dict[str, Any]:
        """Prepare context data for PDF template."""
        transaction = receipt.transaction
        student = receipt.student
        
        # Get plan details from metadata
        plan_details = {}
        if transaction.metadata:
            plan_details = {
                'name': transaction.metadata.get('plan_name', 'Unknown Plan'),
                'type': transaction.metadata.get('plan_type', 'package'),
                'hours_included': transaction.metadata.get('hours_included'),
                'validity_days': transaction.metadata.get('validity_days'),
            }
        
        context = {
            'receipt': receipt,
            'transaction': transaction,
            'student': student,
            'plan_details': plan_details,
            'company_info': {
                'name': 'Aprende Comigo',
                'address': 'Your Company Address',
                'email': 'support@aprendecomigo.com',
                'website': 'https://aprendecomigo.com',
            },
            'generated_date': timezone.now().strftime('%d/%m/%Y'),
            'generated_time': timezone.now().strftime('%H:%M:%S'),
        }
        
        return context
    
    @classmethod
    def _get_receipt_css(cls) -> str:
        """Get CSS styles for HTML receipt."""
        return """
        @media print {
            @page {
                size: A4;
                margin: 2cm;
            }
        }
        
        body {
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
        }
        
        .company-name {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 10px;
        }
        
        .receipt-title {
            font-size: 18px;
            font-weight: bold;
            margin: 20px 0;
        }
        
        .receipt-number {
            font-size: 16px;
            color: #666;
            margin-bottom: 20px;
        }
        
        .info-section {
            margin: 20px 0;
        }
        
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        
        .info-table th,
        .info-table td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .info-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        .amount-section {
            margin: 30px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        
        .total-amount {
            font-size: 20px;
            font-weight: bold;
            color: #007bff;
            text-align: right;
        }
        
        .footer {
            margin-top: 40px;
            text-align: center;
            font-size: 10px;
            color: #666;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }
        """
    
    @classmethod
    def _save_html_file(cls, receipt: Receipt, html_content: str) -> None:
        """Save HTML content to file field."""
        filename = f"receipt_{receipt.receipt_number}.html"
        receipt.pdf_file.save(
            filename,
            ContentFile(html_content.encode('utf-8')),
            save=True
        )
        
        logger.info(f"Saved HTML file for receipt {receipt.receipt_number}")
    
    @classmethod
    def _cleanup_receipt_file(cls, receipt: Receipt) -> None:
        """Clean up HTML file for a receipt."""
        if receipt.pdf_file:
            try:
                receipt.pdf_file.delete()
                logger.info(f"Cleaned up HTML file for receipt {receipt.receipt_number}")
            except Exception as e:
                logger.warning(f"Failed to cleanup HTML file for receipt {receipt.receipt_number}: {e}")


class ReceiptValidationError(Exception):
    """Exception raised for receipt validation errors."""
    pass