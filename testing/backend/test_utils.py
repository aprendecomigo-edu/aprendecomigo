import json
import os
import tempfile
from functools import wraps

from django.test import override_settings
from django.urls import reverse
from PIL import Image


def create_test_image():
    """Create a temporary test image for testing file uploads."""
    image = Image.new("RGB", (100, 100), color="red")
    tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
    image.save(tmp_file)
    tmp_file.seek(0)
    return tmp_file


def get_response_json(response):
    """Parse and return the JSON from a response."""
    return json.loads(response.content.decode("utf-8"))


def assert_status_code(response, expected_status_code):
    """Assert that the response has the expected status code."""
    try:
        assert response.status_code == expected_status_code
    except AssertionError:
        content = get_response_json(response)
        raise AssertionError(
            f"Expected status code {expected_status_code}, got {response.status_code}. "
            f"Response content: {content}"
        )


def assert_contains_keys(data, keys):
    """Assert that the data contains all the specified keys."""
    for key in keys:
        assert key in data, f"Expected key '{key}' not found in {data}"


def permission_test_factory(
    client_fixture, url_name, url_kwargs=None, method="get", expected_status=200
):
    """
    Factory function to create permission tests.

    Args:
        client_fixture: The name of the client fixture to use
        url_name: The name of the URL to test
        url_kwargs: Any URL kwargs to pass to reverse
        method: The HTTP method to use
        expected_status: The expected status code

    Returns:
        A test function that will test permissions for the given URL
    """

    def decorator(test_func):
        @wraps(test_func)
        def wrapper(request, *args, **kwargs):
            url_kwargs_to_use = url_kwargs or {}
            url = reverse(url_name, kwargs=url_kwargs_to_use)
            client = request.getfixturevalue(client_fixture)

            # Call the HTTP method on the client
            client_method = getattr(client, method.lower())
            response = client_method(url)

            # Assert the expected status code
            assert_status_code(response, expected_status)

            # Call the original test function
            return test_func(request, response, *args, **kwargs)

        return wrapper

    return decorator


def with_temp_media_root(test_func):
    """
    Decorator to run a test with a temporary MEDIA_ROOT.
    This is useful for tests that involve file uploads.
    """

    @wraps(test_func)
    def wrapped(*args, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(MEDIA_ROOT=os.path.join(temp_dir, "media")):
                return test_func(*args, **kwargs)

    return wrapped
