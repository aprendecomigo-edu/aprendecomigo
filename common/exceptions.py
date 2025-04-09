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
    if response is not None:
        response.data["status_code"] = response.status_code

        # Add more custom error handling logic here
        if response.status_code == 404:
            response.data["message"] = "Resource not found"
        elif response.status_code == 403:
            response.data["message"] = (
                "You don't have permission to perform this action"
            )
        elif response.status_code == 401:
            response.data["message"] = (
                "Authentication credentials were not provided or are invalid"
            )

    return response
