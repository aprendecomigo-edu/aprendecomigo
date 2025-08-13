"""
API Response standardization utilities for consistent error handling and response formatting.

This module provides standardized response formats that ensure:
- Consistent JSON content-type for all API responses
- Uniform error message structure across all endpoints
- Proper HTTP status codes for different scenarios
- Clear error details and debugging information
"""

from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse


class StandardizedAPIResponse:
    """Utility class for creating consistent API responses."""
    
    @staticmethod
    def success(data=None, message="Success", status_code=status.HTTP_200_OK):
        """
        Create a standardized success response.
        
        Args:
            data: Response data (dict, list, or serializable object)
            message: Success message
            status_code: HTTP status code (default: 200)
            
        Returns:
            Response: DRF Response with standardized format
        """
        response_data = {
            'success': True,
            'message': message,
            'data': data
        }
        return Response(response_data, status=status_code, content_type='application/json')
    
    @staticmethod
    def error(message, error_type=None, details=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Create a standardized error response.
        
        Args:
            message: Error message (string)
            error_type: Type of error (validation, permission, not_found, etc.)
            details: Additional error details (dict)
            status_code: HTTP status code (default: 400)
            
        Returns:
            Response: DRF Response with standardized error format
        """
        response_data = {
            'success': False,
            'message': message,
            'error_type': error_type,
            'details': details
        }
        return Response(response_data, status=status_code, content_type='application/json')
    
    @staticmethod
    def validation_error(validation_errors, message="Validation failed"):
        """
        Create a standardized validation error response.
        
        Args:
            validation_errors: Validation errors (dict or list)
            message: General validation error message
            
        Returns:
            Response: DRF Response with standardized validation error format
        """
        response_data = {
            'success': False,
            'message': message,
            'error_type': 'validation_error',
            'details': {
                'validation_errors': validation_errors
            }
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST, content_type='application/json')
    
    @staticmethod
    def permission_denied(message="Permission denied", details=None):
        """
        Create a standardized permission denied response.
        
        Args:
            message: Permission error message
            details: Additional permission details
            
        Returns:
            Response: DRF Response with standardized permission error format
        """
        response_data = {
            'success': False,
            'message': message,
            'error_type': 'permission_denied',
            'details': details
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN, content_type='application/json')
    
    @staticmethod
    def not_found(message="Resource not found", resource_type=None, resource_id=None):
        """
        Create a standardized not found response.
        
        Args:
            message: Not found error message
            resource_type: Type of resource that was not found
            resource_id: ID of the resource that was not found
            
        Returns:
            Response: DRF Response with standardized not found error format
        """
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
            
        response_data = {
            'success': False,
            'message': message,
            'error_type': 'not_found',
            'details': details if details else None
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND, content_type='application/json')
    
    @staticmethod
    def method_not_allowed(message="Method not allowed", allowed_methods=None):
        """
        Create a standardized method not allowed response.
        
        Args:
            message: Method not allowed error message
            allowed_methods: List of allowed HTTP methods
            
        Returns:
            Response: DRF Response with standardized method not allowed error format
        """
        details = {}
        if allowed_methods:
            details['allowed_methods'] = allowed_methods
            
        response_data = {
            'success': False,
            'message': message,
            'error_type': 'method_not_allowed',
            'details': details if details else None
        }
        return Response(response_data, status=status.HTTP_405_METHOD_NOT_ALLOWED, content_type='application/json')
    
    @staticmethod
    def stripe_error(message, stripe_error_code=None, stripe_error_type=None):
        """
        Create a standardized Stripe integration error response.
        
        Args:
            message: Stripe error message
            stripe_error_code: Stripe's error code
            stripe_error_type: Stripe's error type
            
        Returns:
            Response: DRF Response with standardized Stripe error format
        """
        details = {}
        if stripe_error_code:
            details['stripe_error_code'] = stripe_error_code
        if stripe_error_type:
            details['stripe_error_type'] = stripe_error_type
            
        response_data = {
            'success': False,
            'message': message,
            'error_type': 'stripe_error',
            'details': details if details else None
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST, content_type='application/json')


class StandardizedErrorHandler:
    """Exception handler for converting exceptions to standardized responses."""
    
    @staticmethod
    def handle_stripe_error(stripe_error):
        """
        Handle Stripe errors and return standardized response.
        
        Args:
            stripe_error: Stripe exception object
            
        Returns:
            Response: Standardized error response
        """
        return StandardizedAPIResponse.stripe_error(
            message=str(stripe_error),
            stripe_error_code=getattr(stripe_error, 'code', None),
            stripe_error_type=getattr(stripe_error, 'type', None)
        )
    
    @staticmethod
    def handle_validation_error(validation_error):
        """
        Handle Django ValidationError and return standardized response.
        
        Args:
            validation_error: Django ValidationError object
            
        Returns:
            Response: Standardized validation error response
        """
        if hasattr(validation_error, 'error_dict'):
            # Field-specific validation errors
            return StandardizedAPIResponse.validation_error(validation_error.error_dict)
        elif hasattr(validation_error, 'error_list'):
            # General validation errors
            return StandardizedAPIResponse.validation_error(validation_error.error_list)
        else:
            # Single validation error
            return StandardizedAPIResponse.validation_error(str(validation_error))
    
    @staticmethod
    def handle_permission_error(permission_error):
        """
        Handle permission errors and return standardized response.
        
        Args:
            permission_error: Permission error object or string
            
        Returns:
            Response: Standardized permission error response
        """
        return StandardizedAPIResponse.permission_denied(
            message=str(permission_error)
        )


# Legacy function aliases for backward compatibility
def format_success_response(data=None, message="Success"):
    """Legacy alias for StandardizedAPIResponse.success"""
    return StandardizedAPIResponse.success(data=data, message=message)


def format_error_response(message, error_type=None, details=None):
    """Legacy alias for StandardizedAPIResponse.error"""
    return StandardizedAPIResponse.error(message=message, error_type=error_type, details=details)