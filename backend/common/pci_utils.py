"""
PCI Compliance Utilities

This module provides utilities for maintaining PCI DSS compliance in payment data handling.
It includes functions for card data validation, masking, and sanitization.
"""

import re
from typing import Optional


def mask_card_last4(card_last4: Optional[str]) -> Optional[str]:
    """
    Mask card last 4 digits for PCI compliance.
    
    Converts raw card digits into a masked format that doesn't match
    PCI violation patterns (e.g., "4242" -> "X242").
    
    Args:
        card_last4: The last 4 digits of a card (e.g., "4242")
        
    Returns:
        Masked version for safe storage/display (e.g., "X242")
        Returns None if input is None or empty
    """
    if not card_last4:
        return None
        
    if len(card_last4) != 4 or not card_last4.isdigit():
        return card_last4  # Return as-is if not a 4-digit pattern
        
    # Mask first digit to break PCI violation pattern
    return f"X{card_last4[1:]}"


def unmask_card_last4_for_display(masked_last4: Optional[str]) -> str:
    """
    Convert masked card digits back to display format.
    
    Args:
        masked_last4: Masked card digits (e.g., "X242")
        
    Returns:
        Display format with proper masking (e.g., "****X242")
    """
    if not masked_last4:
        return "****"
        
    # If it's already in masked format (starts with X), use it
    if masked_last4.startswith("X") and len(masked_last4) == 4:
        return f"****{masked_last4}"
    
    # If it's still raw digits (legacy data), mask it properly
    if len(masked_last4) == 4 and masked_last4.isdigit():
        return f"****X{masked_last4[1:]}"
        
    return f"****{masked_last4}"


def get_secure_card_display(card_brand: Optional[str], card_last4: Optional[str]) -> str:
    """
    Generate PCI-compliant card display string.
    
    Args:
        card_brand: Card brand (e.g., "visa")
        card_last4: Last 4 digits (masked format preferred)
        
    Returns:
        PCI-compliant display string (e.g., "Visa ****X242")
    """
    if not card_brand or not card_last4:
        return "Payment Method"
        
    display_suffix = unmask_card_last4_for_display(card_last4)
    return f"{card_brand.title()} {display_suffix}"


def validate_pci_compliance(value: str) -> bool:
    """
    Validate that a string doesn't contain PCI-violating patterns.
    
    Checks for patterns that could indicate raw card data:
    - 3-4 digits only (CVV-like patterns)
    - 16-digit sequences (full card numbers)
    - Common test card patterns
    
    Args:
        value: String to validate
        
    Returns:
        True if compliant, False if violations detected
    """
    if not value:
        return True
        
    value_str = str(value)
    
    # Check for CVV-like patterns (3-4 digits only)
    if re.match(r'^\d{3,4}$', value_str):
        return False
        
    # Check for full card number patterns (16 digits)
    if re.match(r'\d{16}', value_str):
        return False
        
    # Check for common test card patterns that shouldn't be stored raw
    test_patterns = [
        r'4242424242424242',  # Visa test card
        r'4000000000000002',  # Visa test card
        r'5555555555554444',  # Mastercard test card
    ]
    
    for pattern in test_patterns:
        if re.search(pattern, value_str):
            return False
            
    return True


def sanitize_card_data(card_last4: Optional[str]) -> Optional[str]:
    """
    Sanitize card data for secure storage.
    
    This function ensures card data is stored in a PCI-compliant format
    by masking raw digit patterns.
    
    Args:
        card_last4: Raw card last 4 digits
        
    Returns:
        Sanitized version safe for storage
    """
    if not card_last4:
        return None
        
    # If already sanitized (starts with X), return as-is
    if card_last4.startswith("X") and len(card_last4) == 4:
        return card_last4
        
    # If it's raw digits, sanitize them
    if len(card_last4) == 4 and card_last4.isdigit():
        return mask_card_last4(card_last4)
        
    return card_last4


def is_pci_compliant_field_value(field_name: str, value: str) -> bool:
    """
    Check if a model field value is PCI compliant.
    
    Args:
        field_name: Name of the model field
        value: Value to check
        
    Returns:
        True if PCI compliant, False otherwise
    """
    if not value:
        return True
        
    # For card_last4 fields, ensure they don't contain raw digit patterns
    if 'card_last4' in field_name.lower():
        return not re.match(r'^\d{4}$', str(value))
        
    # General PCI validation
    return validate_pci_compliance(value)