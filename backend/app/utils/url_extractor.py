"""
URL extraction utility for automatic document ingestion.
Detects and validates URLs from chat messages.
"""

import re
from typing import List, Dict
from urllib.parse import urlparse


class URLExtractor:
    """Extract and validate URLs from text messages."""

    # Regex pattern for URLs (matches http/https URLs)
    URL_PATTERN = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )

    # Blocklist for security (localhost, private IPs, etc.)
    BLOCKED_DOMAINS = {
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '::1'
    }

    @classmethod
    def extract_urls(cls, text: str) -> List[Dict[str, str]]:
        """
        Extract all URLs from text.

        Args:
            text: The text to search for URLs

        Returns:
            List of dicts with 'url', 'domain', 'scheme', 'is_valid'
        """
        if not text:
            return []

        urls = cls.URL_PATTERN.findall(text)
        results = []

        for url in urls:
            parsed = urlparse(url)
            is_valid = cls.is_valid_url(url, parsed)

            results.append({
                'url': url,
                'domain': parsed.netloc,
                'scheme': parsed.scheme,
                'is_valid': is_valid,
                'is_blocked': parsed.netloc.lower() in cls.BLOCKED_DOMAINS
            })

        return results

    @classmethod
    def is_valid_url(cls, url: str, parsed=None) -> bool:
        """
        Validate URL is safe and reachable.

        Args:
            url: The URL to validate
            parsed: Optional pre-parsed URL object

        Returns:
            True if URL is valid and safe
        """
        try:
            if parsed is None:
                parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False

            # Check domain exists
            if not parsed.netloc:
                return False

            # Check not blocked
            if parsed.netloc.lower() in cls.BLOCKED_DOMAINS:
                return False

            # Check reasonable length
            if len(url) > 2000:
                return False

            # Check for private IP ranges (basic check)
            if cls._is_private_ip(parsed.netloc):
                return False

            return True

        except Exception:
            return False

    @classmethod
    def _is_private_ip(cls, domain: str) -> bool:
        """Check if domain is a private IP address."""
        # Simple check for common private IP patterns
        private_patterns = [
            r'^10\.',
            r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',
            r'^192\.168\.',
        ]

        for pattern in private_patterns:
            if re.match(pattern, domain):
                return True

        return False

    @classmethod
    def clean_message(cls, text: str, replacement: str = "[URL]") -> str:
        """
        Remove URLs from message text, replace with placeholder.

        Args:
            text: The text to clean
            replacement: What to replace URLs with

        Returns:
            Text with URLs replaced
        """
        return cls.URL_PATTERN.sub(replacement, text)

    @classmethod
    def count_urls(cls, text: str) -> int:
        """Count number of URLs in text."""
        return len(cls.URL_PATTERN.findall(text))
