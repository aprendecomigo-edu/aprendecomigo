#!/usr/bin/env python3
"""
Test script for Django Waffle feature switches.
Usage: python test_feature_switches.py [switch_name] [on|off]

Examples:
- python test_feature_switches.py                    # Show current status
- python test_feature_switches.py schedule_feature off  # Turn off schedule feature
- python test_feature_switches.py chat_feature on       # Turn on chat feature
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings')
django.setup()

from waffle.models import Switch
from waffle.utils import get_setting


def show_current_status():
    """Display current status of all feature switches."""
    print("🚀 Django Waffle Feature Switches Status")
    print("=" * 50)
    
    # Show environment defaults
    default_value = get_setting('WAFFLE_SWITCH_DEFAULT')
    print(f"Default switch value: {default_value}")
    print()
    
    # Show specific switches
    switches = ['schedule_feature', 'chat_feature']
    
    for switch_name in switches:
        try:
            switch = Switch.objects.get(name=switch_name)
            status = "🟢 ON" if switch.active else "🔴 OFF"
            print(f"{switch_name}: {status}")
        except Switch.DoesNotExist:
            # Check default behavior
            from waffle import switch_is_active
            status = "🟢 ON (default)" if switch_is_active(switch_name) else "🔴 OFF (default)"
            print(f"{switch_name}: {status} (using default)")
    
    print()
    print("💡 Features controlled by switches:")
    print("   - schedule_feature: Calendar, Scheduling, Teacher Availability")
    print("   - chat_feature: Chat, Messaging, Real-time Communication")


def toggle_switch(switch_name, state):
    """Toggle a feature switch on or off."""
    if switch_name not in ['schedule_feature', 'chat_feature']:
        print(f"❌ Invalid switch name: {switch_name}")
        print("Valid switches: schedule_feature, chat_feature")
        return False
    
    if state not in ['on', 'off']:
        print(f"❌ Invalid state: {state}")
        print("Valid states: on, off")
        return False
    
    active = (state == 'on')
    
    try:
        switch, created = Switch.objects.get_or_create(
            name=switch_name,
            defaults={'active': active}
        )
        
        if not created:
            switch.active = active
            switch.save()
        
        status = "🟢 ON" if active else "🔴 OFF"
        action = "Created" if created else "Updated"
        print(f"✅ {action} {switch_name}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating switch: {e}")
        return False


def main():
    if len(sys.argv) == 1:
        # No arguments - show status
        show_current_status()
    elif len(sys.argv) == 3:
        # Switch name and state provided
        switch_name = sys.argv[1]
        state = sys.argv[2]
        
        if toggle_switch(switch_name, state):
            print()
            show_current_status()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()