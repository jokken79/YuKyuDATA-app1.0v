# config/secrets_validation.py
"""
Secrets Validation Module for Production Security

This module validates that required secrets are properly configured
and not using insecure default values before the application starts.

Usage:
    from config.secrets_validation import validate_secrets

    # Call at application startup
    validate_secrets()  # Will exit with code 1 if validation fails in production
"""

import os
import sys
from typing import Dict, List, Tuple

# Insecure default values that should never be used in production
INSECURE_DEFAULTS = {
    'change_me',
    'change-me',
    'changeme',
    'secret',
    'default',
    'password',
    'admin',
    '123456',
    'development',
    'dev-secret',
    'change-me-in-production',
    '0' * 64,  # Default encryption key
    '0' * 32,
}


def get_required_secrets() -> Dict[str, str]:
    """
    Returns a dictionary of required secrets with their descriptions.

    Returns:
        Dict mapping secret name to description
    """
    return {
        'JWT_SECRET_KEY': 'Must be set for JWT token signing (min 32 chars)',
        'CSRF_SECRET': 'Must be set for CSRF protection',
    }


def get_recommended_secrets() -> Dict[str, str]:
    """
    Returns a dictionary of recommended (but not required) secrets.

    Returns:
        Dict mapping secret name to description
    """
    return {
        'ENCRYPTION_KEY': 'Should be set for data encryption (64 hex chars)',
        'API_KEY': 'Should be set for API authentication',
        'DATABASE_ENCRYPTION_KEY': 'Should be set for PII encryption in database',
    }


def validate_secret_value(name: str, value: str) -> List[str]:
    """
    Validate a single secret value for security issues.

    Args:
        name: The secret name
        value: The secret value

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    if not value:
        return errors  # Missing secrets handled separately

    # Check for insecure defaults
    if value.lower() in INSECURE_DEFAULTS or value in INSECURE_DEFAULTS:
        errors.append(f"Insecure default value for {name}")

    # Specific validations per secret type
    if name == 'JWT_SECRET_KEY':
        if len(value) < 32:
            errors.append(f"{name} should be at least 32 characters (current: {len(value)})")
        if value.isalnum() and value.islower():
            errors.append(f"{name} should include mixed case and special characters")

    elif name == 'ENCRYPTION_KEY':
        if len(value) != 64:
            errors.append(f"{name} should be exactly 64 hex characters (current: {len(value)})")
        try:
            bytes.fromhex(value)
        except ValueError:
            errors.append(f"{name} must be a valid hex string")

    elif name == 'CSRF_SECRET':
        if len(value) < 16:
            errors.append(f"{name} should be at least 16 characters (current: {len(value)})")

    return errors


def validate_secrets(exit_on_failure: bool = True) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that required secrets are set and not using default values.

    This function checks environment variables for security-critical secrets
    and ensures they are properly configured for production use.

    Args:
        exit_on_failure: If True, exits the application with code 1 when
                        validation fails in production environment

    Returns:
        Tuple of (is_valid, errors, warnings)
        - is_valid: True if all required secrets pass validation
        - errors: List of critical error messages
        - warnings: List of warning messages (non-critical)

    Environment Variables:
        ENVIRONMENT: Set to 'production' to enforce strict validation
        APP_ENV: Alternative to ENVIRONMENT
        DEBUG: If 'true', treats as development environment
    """
    errors = []
    warnings = []

    # Determine if we're in production
    environment = os.getenv('ENVIRONMENT', os.getenv('APP_ENV', 'development'))
    is_production = environment.lower() == 'production'
    is_debug = os.getenv('DEBUG', 'false').lower() == 'true'
    is_testing = os.getenv('TESTING', 'false').lower() == 'true'

    # In debug or testing mode, only show warnings
    strict_mode = is_production and not is_debug and not is_testing

    # Validate required secrets
    required_secrets = get_required_secrets()
    for secret_name, description in required_secrets.items():
        value = os.getenv(secret_name)

        if not value:
            msg = f"Missing {secret_name}: {description}"
            if strict_mode:
                errors.append(msg)
            else:
                warnings.append(msg)
        else:
            validation_errors = validate_secret_value(secret_name, value)
            for err in validation_errors:
                if strict_mode:
                    errors.append(err)
                else:
                    warnings.append(err)

    # Validate recommended secrets (warnings only)
    recommended_secrets = get_recommended_secrets()
    for secret_name, description in recommended_secrets.items():
        value = os.getenv(secret_name)

        if not value:
            warnings.append(f"Recommended: Set {secret_name} - {description}")
        else:
            validation_errors = validate_secret_value(secret_name, value)
            for err in validation_errors:
                warnings.append(err)

    is_valid = len(errors) == 0

    # Exit if validation fails in production
    if not is_valid and exit_on_failure and strict_mode:
        print("=" * 60)
        print("FATAL: Security validation failed!")
        print("=" * 60)
        print("\nThe application cannot start due to security issues:\n")
        for error in errors:
            print(f"  [ERROR] {error}")
        if warnings:
            print("\nAdditional warnings:")
            for warning in warnings:
                print(f"  [WARN]  {warning}")
        print("\n" + "=" * 60)
        print("Please configure the required secrets in your environment.")
        print("See documentation for secure configuration guidelines.")
        print("=" * 60)
        sys.exit(1)

    return is_valid, errors, warnings


def validate_secrets_healthcheck() -> bool:
    """
    Simplified validation for Docker healthcheck.

    Returns True if secrets are valid, False otherwise.
    Does not exit the process, just returns the result.

    Usage in Docker:
        healthcheck:
          test: ["CMD", "python", "-c",
                 "from config.secrets_validation import validate_secrets_healthcheck; exit(0 if validate_secrets_healthcheck() else 1)"]
    """
    is_valid, _, _ = validate_secrets(exit_on_failure=False)
    return is_valid


def print_secrets_status():
    """
    Print the current secrets configuration status.
    Useful for debugging and logging at startup.
    """
    is_valid, errors, warnings = validate_secrets(exit_on_failure=False)

    environment = os.getenv('ENVIRONMENT', os.getenv('APP_ENV', 'development'))
    is_debug = os.getenv('DEBUG', 'false').lower() == 'true'

    print("\n" + "=" * 50)
    print("SECRETS VALIDATION STATUS")
    print("=" * 50)
    print(f"Environment: {environment}")
    print(f"Debug Mode:  {is_debug}")
    print(f"Status:      {'VALID' if is_valid else 'INVALID'}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")

    print("=" * 50 + "\n")

    return is_valid


# CLI support for Docker healthcheck
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Validate application secrets')
    parser.add_argument('--healthcheck', action='store_true',
                        help='Run in healthcheck mode (exit code only)')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed status')

    args = parser.parse_args()

    if args.healthcheck:
        # Simple healthcheck mode for Docker
        is_valid = validate_secrets_healthcheck()
        sys.exit(0 if is_valid else 1)
    elif args.verbose:
        print_secrets_status()
    else:
        validate_secrets()
