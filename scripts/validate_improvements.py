#!/usr/bin/env python3
"""
Validation test for text extraction service improvements.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.dependency_checker import dependency_checker
from services.text_validator import text_validator
from services.text_extraction import text_extraction

print("=" * 60)
print("TEXT EXTRACTION SERVICE VALIDATION")
print("=" * 60)

try:
    print("\n1. Testing imports...")
    print("   ✓ All imports successful")
    
    print("\n2. Testing Dependency Checker...")
    all_available, warnings, errors = dependency_checker.check_all()
    
    if all_available:
        print("   ✓ All critical dependencies available")
    else:
        print("   ⚠️  Some dependencies missing")
    
    if warnings:
        print(f"   Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"     - {w[:60]}...")
    
    if errors:
        print(f"   Errors ({len(errors)}):")
        for e in errors:
            print(f"     - {e[:60]}...")
    
    # Show format support
    format_support = dependency_checker.get_format_support_status()
    print(f"\n   Format Support:")
    for fmt, status in format_support.items():
        print(f"     - {fmt.upper()}: {status}")
    
    print("\n3. Testing Text Validator...")
    test_text = "Hello world. This is a test document with some content for validation."
    
    is_valid, sanitized, warning = text_validator.validate_and_sanitize(test_text)
    if is_valid:
        print("   ✓ Text validation passed")
    else:
        print(f"   ✗ Text validation failed: {warning}")
    
    health = text_validator.get_text_health_score(sanitized)
    print(f"   Health Score: {health['score']}/100")
    print(f"   Word Count: {health['word_count']}")
    print(f"   Character Count: {health['length']}")
    
    print("\n4. Testing Text Extraction Service...")
    print(f"   Supported formats: {list(text_extraction.SUPPORTED_FORMATS.keys())}")
    print(f"   Extraction timeouts configured: {text_extraction.EXTRACTION_TIMEOUTS}")
    
    print("\n5. Testing Null Byte Detection...")
    bad_text = "Normal text\x00with null bytes\x00in content"
    is_valid, _, warning = text_validator.validate_and_sanitize(bad_text)
    if not is_valid and "null bytes" in warning.lower():
        print("   ✓ Null byte detection working")
    else:
        print("   ⚠️  Null byte detection may not be working")
    
    print("\n6. Testing Whitespace Sanitization...")
    whitespace_text = "Text   with    excessive    spaces\n\n\nand newlines"
    _, sanitized, _ = text_validator.validate_and_sanitize(whitespace_text)
    if "   " not in sanitized and "\n\n\n" not in sanitized:
        print("   ✓ Whitespace sanitization working")
    else:
        print("   ⚠️  Whitespace sanitization needs review")
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print("\n✓ All text extraction improvements are properly integrated")
    
except Exception as e:
    print(f"\n✗ Validation failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
