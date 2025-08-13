#!/usr/bin/env python
"""
Debug script to test card display format conversion.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.testing')
django.setup()

from django.contrib.auth import get_user_model
from finances.models import StoredPaymentMethod
from finances.serializers import StoredPaymentMethodSerializer
from common.pci_utils import get_secure_card_display

User = get_user_model()

def test_card_display():
    print("=== Testing Card Display Format Conversion ===")
    
    # Create user
    user, created = User.objects.get_or_create(
        email="debug@test.com",
        defaults={"name": "Debug User"}
    )
    
    # Test legacy format directly with PCI utils
    print("\n1. Testing PCI utils function directly:")
    legacy_result = get_secure_card_display("visa", "X242")
    print(f"   get_secure_card_display('visa', 'X242') = '{legacy_result}'")
    
    raw_result = get_secure_card_display("visa", "4242")
    print(f"   get_secure_card_display('visa', '4242') = '{raw_result}'")
    
    # Test with StoredPaymentMethod model
    print("\n2. Testing StoredPaymentMethod model:")
    
    # Clean up any existing payment methods for this test
    StoredPaymentMethod.objects.filter(student=user).delete()
    
    # Create payment method with legacy format
    pm_legacy = StoredPaymentMethod.objects.create(
        student=user,
        stripe_payment_method_id="pm_debug_legacy",
        stripe_customer_id="cus_debug",
        card_brand="visa",
        card_last4="X242",
        card_exp_month=12,
        card_exp_year=2025,
        is_default=True,
        is_active=True
    )
    
    print(f"   Model card_display property: '{pm_legacy.card_display}'")
    print(f"   Model __str__: '{str(pm_legacy)}'")
    
    # Test with serializer
    print("\n3. Testing StoredPaymentMethodSerializer:")
    serializer = StoredPaymentMethodSerializer(pm_legacy)
    data = serializer.data
    print(f"   Serialized card_display: '{data['card_display']}'")
    
    # Test raw format
    print("\n4. Testing raw format (should work correctly):")
    pm_raw = StoredPaymentMethod.objects.create(
        student=user,
        stripe_payment_method_id="pm_debug_raw",
        stripe_customer_id="cus_debug",
        card_brand="visa", 
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2025,
        is_default=False,
        is_active=True
    )
    
    print(f"   Raw format card_display: '{pm_raw.card_display}'")
    
    serializer_raw = StoredPaymentMethodSerializer(pm_raw)
    data_raw = serializer_raw.data
    print(f"   Raw serialized card_display: '{data_raw['card_display']}'")
    
    # Cleanup
    StoredPaymentMethod.objects.filter(student=user).delete()
    user.delete()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_card_display()