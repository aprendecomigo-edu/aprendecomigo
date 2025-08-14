from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that adds additional information to the response.
    - Adds status_code to the response
    - Adds descriptive messages for common error codes
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response
    if response is not None and isinstance(response.data, dict):
            response.data["status_code"] = response.status_code

            # Add more custom error handling logic here
            if response.status_code == status.HTTP_404_NOT_FOUND:
                response.data["message"] = "Resource not found"
            elif response.status_code == status.HTTP_403_FORBIDDEN:
                response.data["message"] = "You don't have permission to perform this action"
            elif response.status_code == status.HTTP_401_UNAUTHORIZED:
                response.data["message"] = "Authentication credentials were not provided or are invalid"
            elif response.status_code == status.HTTP_400_BAD_REQUEST:
                response.data["message"] = "Bad request"

    return response
