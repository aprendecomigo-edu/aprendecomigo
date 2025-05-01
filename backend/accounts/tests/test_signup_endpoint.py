import json

from django.test import TestCase


class SignupEndpointTest(TestCase):
    """Test specifically for the signup endpoint with the exact payload that's failing."""

    def test_signup_with_specific_payload(self):
        """Test the signup endpoint with the exact payload that's failing."""
        payload = {
            "name": "Ana Paula Martins de Carvalho",
            "email": "anamartinsdecarvalho@protonmail.com",
            "phone_number": "960095846",
            "primary_contact": "email",
            "school": {"name": "ANa", "address": "Rua Estrada Nacional, nr 938"},
        }

        response = self.client.post(
            "/api/accounts/users/signup/", data=json.dumps(payload), content_type="application/json"
        )

        # Print response details for debugging
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content.decode()}")

        # This should pass, but it's failing with the error
        self.assertEqual(response.status_code, 201)
