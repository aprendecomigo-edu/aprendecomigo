"""
PWA Detection Utility for Session Management

This module provides comprehensive PWA (Progressive Web App) detection capabilities
with multiple fallback strategies to determine if a request is coming from a PWA
installation versus a regular web browser.

Business Requirements:
- Web browser sessions = 24 hours (86400 seconds)
- PWA installation sessions = 7 days (604800 seconds)

Detection Strategies (in priority order):
1. Custom PWA Headers (highest priority) - X-PWA-Mode, X-Standalone-Mode
2. Cookie-based Detection - pwa_mode cookie set by client-side JS
3. User-Agent Analysis - WebView indicators, mobile Safari patterns
4. Request Characteristics - Missing referer on GET requests
"""

import logging
import re

from django.http import HttpRequest

logger = logging.getLogger(__name__)


class PWADetector:
    """
    Comprehensive PWA detection service with multiple fallback strategies.

    This class provides robust detection of PWA requests to enable differentiated
    session management between web browsers (24h) and PWA installations (7d).
    """

    # Session duration constants (in seconds)
    WEB_SESSION_DURATION = 24 * 60 * 60  # 24 hours = 86400 seconds
    PWA_SESSION_DURATION = 7 * 24 * 60 * 60  # 7 days = 604800 seconds

    # User-Agent patterns that indicate PWA/WebView usage
    PWA_USER_AGENT_PATTERNS = [
        r".*wv\).*",  # WebView indicators (Android)
        r".*Version/.*Mobile.*Safari.*",  # iOS PWA in Safari
        r".*Chrome.*Mobile.*",  # Android PWA in Chrome
        r".*Samsung.*wv.*",  # Samsung Internet PWA
        r".*CriOS.*",  # Chrome iOS (may indicate PWA)
    ]

    @classmethod
    def is_pwa_request(cls, request: HttpRequest) -> bool:
        """
        Determine if the incoming request is from a PWA installation.

        Uses multiple detection strategies with fallback priority:
        1. Custom PWA Headers (most reliable)
        2. Cookie-based detection (client-side JS set)
        3. User-Agent analysis (pattern matching)
        4. Request characteristics (referer analysis)

        Args:
            request: Django HttpRequest object

        Returns:
            bool: True if request is from PWA, False for web browser
        """
        # Strategy 1: Check custom PWA headers (highest priority)
        if cls._check_pwa_headers(request):
            logger.debug("PWA detected via custom headers")
            return True

        # Strategy 2: Check PWA mode cookie (client-side JS detection)
        if cls._check_pwa_cookie(request):
            logger.debug("PWA detected via cookie")
            return True

        # Strategy 3: Analyze User-Agent for PWA/WebView patterns
        if cls._check_user_agent(request):
            logger.debug("PWA detected via User-Agent analysis")
            return True

        # Strategy 4: Check request characteristics (missing referer patterns)
        if cls._check_request_characteristics(request):
            logger.debug("PWA detected via request characteristics")
            return True

        # Default: treat as web browser request
        logger.debug("Request classified as web browser")
        return False

    @classmethod
    def get_session_duration(cls, request: HttpRequest) -> int:
        """
        Get the appropriate session duration based on PWA detection.

        Args:
            request: Django HttpRequest object

        Returns:
            int: Session duration in seconds (86400 for web, 604800 for PWA)
        """
        if cls.is_pwa_request(request):
            logger.info("Setting PWA session duration: 7 days")
            return cls.PWA_SESSION_DURATION
        else:
            logger.info("Setting web browser session duration: 24 hours")
            return cls.WEB_SESSION_DURATION

    @classmethod
    def _check_pwa_headers(cls, request: HttpRequest) -> bool:
        """
        Check for custom PWA headers set by client-side JavaScript.

        Headers checked:
        - X-PWA-Mode: 'standalone' indicates PWA
        - X-Standalone-Mode: '1' or 'true' indicates PWA

        Args:
            request: Django HttpRequest object

        Returns:
            bool: True if PWA headers detected
        """
        # Check X-PWA-Mode header
        pwa_mode = request.headers.get("x-pwa-mode", "").lower()
        if pwa_mode == "standalone":
            return True

        # Check X-Standalone-Mode header
        standalone_mode = request.headers.get("x-standalone-mode", "").lower()
        if standalone_mode in ["1", "true"]:
            return True

        return False

    @classmethod
    def _check_pwa_cookie(cls, request: HttpRequest) -> bool:
        """
        Check for PWA mode cookie set by client-side JavaScript.

        Cookie checked:
        - pwa_mode: 'standalone' indicates PWA installation

        Args:
            request: Django HttpRequest object

        Returns:
            bool: True if PWA cookie detected
        """
        pwa_mode = request.COOKIES.get("pwa_mode", "").lower()
        return pwa_mode == "standalone"

    @classmethod
    def _check_user_agent(cls, request: HttpRequest) -> bool:
        """
        Analyze User-Agent for PWA/WebView indicators.

        Patterns checked:
        - WebView indicators (wv)
        - Mobile Safari patterns
        - Chrome mobile patterns
        - Samsung Internet patterns

        Args:
            request: Django HttpRequest object

        Returns:
            bool: True if User-Agent suggests PWA/WebView
        """
        user_agent = request.headers.get("user-agent", "")
        if not user_agent:
            return False

        # Check against known PWA/WebView patterns
        for pattern in cls.PWA_USER_AGENT_PATTERNS:
            if re.match(pattern, user_agent, re.IGNORECASE):
                logger.debug(f"User-Agent PWA pattern matched: {pattern}")
                return True

        return False

    @classmethod
    def _check_request_characteristics(cls, request: HttpRequest) -> bool:
        """
        Check request characteristics that may indicate PWA usage.

        Characteristics checked:
        - Missing HTTP_REFERER on GET requests (PWA navigation pattern)
        - Specific Accept headers that indicate app context

        Args:
            request: Django HttpRequest object

        Returns:
            bool: True if request characteristics suggest PWA
        """
        # Check for missing referer on GET requests
        # PWA navigation often lacks referer due to app context
        if request.method == "GET":
            referer = request.headers.get("referer")
            accept = request.headers.get("accept", "")

            # If no referer and requesting HTML content, might be PWA
            if not referer and "text/html" in accept:
                logger.debug("Potential PWA detected: GET request with no referer")
                # This is a weak signal, so we're conservative
                # Only consider PWA if other indicators are also present
                user_agent = request.headers.get("user-agent", "")
                return "Mobile" in user_agent or "Android" in user_agent

        return False

    @classmethod
    def get_detection_info(cls, request: HttpRequest) -> dict:
        """
        Get detailed information about PWA detection for debugging/logging.

        Args:
            request: Django HttpRequest object

        Returns:
            dict: Detailed detection information
        """
        return {
            "is_pwa": cls.is_pwa_request(request),
            "session_duration": cls.get_session_duration(request),
            "detection_methods": {
                "pwa_headers": cls._check_pwa_headers(request),
                "pwa_cookie": cls._check_pwa_cookie(request),
                "user_agent": cls._check_user_agent(request),
                "request_characteristics": cls._check_request_characteristics(request),
            },
            "request_info": {
                "user_agent": request.headers.get("user-agent", ""),
                "x_pwa_mode": request.headers.get("x-pwa-mode", ""),
                "x_standalone_mode": request.headers.get("x-standalone-mode", ""),
                "pwa_mode_cookie": request.COOKIES.get("pwa_mode", ""),
                "referer": request.headers.get("referer", ""),
                "method": request.method,
            },
        }
