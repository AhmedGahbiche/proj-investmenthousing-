"""
Text validation and sanitization service.
Ensures extracted text is clean, valid, and free from corruption.
"""
import logging
import re
import unicodedata
from typing import Tuple, Optional
import sys

logger = logging.getLogger(__name__)


class TextValidator:
    """Validates and sanitizes extracted text content."""
    
    # Configuration thresholds
    MAX_TEXT_SIZE = 10 * 1024 * 1024  # 10 MB
    MIN_VALID_LENGTH = 1  # Minimum characters for valid extraction
    SUSPICIOUS_NULL_BYTE_THRESHOLD = 0.01  # More than 1% null bytes = corrupted
    SUSPICIOUS_CONTROL_CHAR_THRESHOLD = 0.05  # More than 5% control chars = suspicious
    
    # Regex patterns for anomalies
    EXCESSIVE_WHITESPACE = re.compile(r'\s{3,}')  # 3+ consecutive whitespace
    EXCESSIVE_NEWLINES = re.compile(r'\n{3,}')  # 3+ consecutive newlines
    MIXED_ENCODINGS = re.compile(r'[\x80-\xFF][\x00-\x7F]|[\x00-\x7F][\x80-\xFF]{2,}')
    
    def validate_and_sanitize(self, text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate and sanitize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Tuple of (is_valid, sanitized_text, warning_message)
            warning_message is None if validation passes perfectly
        """
        if not isinstance(text, str):
            return False, "", "Text is not a string"
        
        # Check for empty text
        if not text or not text.strip():
            return False, "", "Text is empty or contains only whitespace"
        
        # Check for excessive size
        if len(text) > self.MAX_TEXT_SIZE:
            return False, "", f"Text exceeds maximum size ({len(text)} bytes > {self.MAX_TEXT_SIZE})"
        
        # Check for null bytes (indicates binary/corrupted content)
        null_byte_ratio = text.count('\x00') / len(text) if text else 0
        if null_byte_ratio > self.SUSPICIOUS_NULL_BYTE_THRESHOLD:
            return False, "", f"Text contains excessive null bytes ({null_byte_ratio:.2%}) - likely corrupted"
        
        # Check for control characters
        control_char_count = sum(1 for c in text if unicodedata.category(c).startswith('C'))
        control_char_ratio = control_char_count / len(text) if text else 0
        warning = None
        
        if control_char_ratio > self.SUSPICIOUS_CONTROL_CHAR_THRESHOLD:
            warning = f"Text contains high percentage of control characters ({control_char_ratio:.2%})"
        
        # Sanitize: remove problematic characters
        sanitized = self._sanitize_text(text)
        
        # Verify sanitized text isn't empty
        if not sanitized or not sanitized.strip():
            return False, "", "Text became empty after sanitization"
        
        return True, sanitized, warning
    
    def _sanitize_text(self, text: str) -> str:
        """
        Remove or normalize problematic characters.
        
        Args:
            text: Raw text
            
        Returns:
            Sanitized text
        """
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove form feed, vertical tab, and other problematic control chars
        # Keep only common whitespace (space, tab, newline, carriage return)
        allowed_control_chars = {'\t', '\n', '\r'}
        text = ''.join(c if unicodedata.category(c) != 'Cc' or c in allowed_control_chars 
                      else ' ' for c in text)
        
        # Normalize Unicode (NFC normalization)
        text = unicodedata.normalize('NFC', text)
        
        # Replace excessive whitespace patterns
        text = self.EXCESSIVE_WHITESPACE.sub('  ', text)  # Collapse 3+ spaces to 2
        text = self.EXCESSIVE_NEWLINES.sub('\n\n', text)  # Collapse 3+ newlines to 2
        
        # Clean up line endings (normalize to \n)
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove trailing whitespace from lines and overall
        text = '\n'.join(line.rstrip() for line in text.split('\n')).strip()
        
        return text
    
    def get_text_health_score(self, text: str) -> dict:
        """
        Generate a health assessment for extracted text.
        
        Args:
            text: Extracted text
            
        Returns:
            Dictionary with health metrics
        """
        if not text:
            return {
                'score': 0.0,
                'is_valid': False,
                'length': 0,
                'word_count': 0,
                'line_count': 0,
                'unique_chars': 0,
                'null_bytes': 0,
                'control_chars': 0,
                'encoding_issues': 0,
                'warnings': ['Empty text']
            }
        
        warnings = []
        
        # Character statistics
        length = len(text)
        null_bytes = text.count('\x00')
        control_chars = sum(1 for c in text if unicodedata.category(c).startswith('C'))
        unique_chars = len(set(text))
        
        # Text statistics
        lines = text.split('\n')
        line_count = len(lines)
        words = text.split()
        word_count = len(words)
        
        # Check for encoding issues
        encoding_issues = 0
        try:
            text.encode('utf-8')
        except UnicodeEncodeError as e:
            encoding_issues = len(e.reason) if hasattr(e, 'reason') else 1
            warnings.append(f"UTF-8 encoding issues detected: {encoding_issues} characters")
        
        # Calculate health score (0-100)
        score = 100.0
        
        if null_bytes > 0:
            score -= min(50, null_bytes * 5)
            warnings.append(f"Contains {null_bytes} null bytes")
        
        if control_chars > length * 0.05:
            score -= 10
            warnings.append(f"High control character ratio: {control_chars / length:.2%}")
        
        if word_count == 0:
            score -= 50
            warnings.append("No recognizable words detected")
        
        elif word_count < 3:
            score -= 20
            warnings.append(f"Very short text: only {word_count} words")
        
        # Average word length health (typical: 4-7 chars)
        if word_count > 0:
            avg_word_length = length / word_count
            if avg_word_length < 2 or avg_word_length > 20:
                score -= 5
        
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 2),
            'is_valid': score >= 50,
            'length': length,
            'word_count': word_count,
            'line_count': line_count,
            'unique_chars': unique_chars,
            'null_bytes': null_bytes,
            'control_chars': control_chars,
            'encoding_issues': encoding_issues,
            'warnings': warnings
        }


# Global text validator instance
text_validator = TextValidator()
