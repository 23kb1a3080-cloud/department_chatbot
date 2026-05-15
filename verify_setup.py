"""
Verification script to check project setup.
Tests configuration loading and basic structure.
"""

import os
import sys
from pathlib import Path


def check_directory_structure():
    """Verify all required directories exist."""
    required_dirs = [
        "auth_service",
        "chat_service",
        "rag_service",
        "document_service",
        "notification_service",
        "admin_service",
        "analytics_service",
    ]
    
    print("Checking directory structure...")
    missing_dirs = []
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            missing_dirs.append(dir_name)
        else:
            print(f"  ✓ {dir_name}")
    
    if missing_dirs:
        print(f"\n  ✗ Missing directories: {', '.join(missing_dirs)}")
        return False
    return True


def check_required_files():
    """Verify all required configuration files exist."""
    required_files = [
        "config.py",
        "requirements.txt",
        "docker-compose.yml",
        ".env.example",
        ".gitignore",
        "README.md",
    ]
    
    print("\nChecking required files...")
    missing_files = []
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
        else:
            print(f"  ✓ {file_name}")
    
    if missing_files:
        print(f"\n  ✗ Missing files: {', '.join(missing_files)}")
        return False
    return True


def check_service_files():
    """Verify each service has required files."""
    services = [
        "auth_service",
        "chat_service",
        "rag_service",
        "document_service",
        "notification_service",
        "admin_service",
        "analytics_service",
    ]
    
    print("\nChecking service files...")
    all_good = True
    for service in services:
        service_path = Path(service)
        required_files = ["__init__.py", "main.py", "Dockerfile"]
        
        for file_name in required_files:
            file_path = service_path / file_name
            if not file_path.exists():
                print(f"  ✗ {service}/{file_name} missing")
                all_good = False
        
        if all_good:
            print(f"  ✓ {service} (all files present)")
    
    return all_good


def test_config_loading():
    """Test configuration loading."""
    print("\nTesting configuration loading...")
    try:
        from config import get_settings
        settings = get_settings()
        print(f"  ✓ Configuration loaded successfully")
        print(f"    - App Name: {settings.app_name}")
        print(f"    - Environment: {settings.environment}")
        print(f"    - Debug: {settings.debug}")
        return True
    except Exception as e:
        print(f"  ✗ Configuration loading failed: {e}")
        return False


def check_git_repository():
    """Verify Git repository is initialized."""
    print("\nChecking Git repository...")
    if Path(".git").exists():
        print("  ✓ Git repository initialized")
        return True
    else:
        print("  ✗ Git repository not initialized")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("College AI Chatbot System - Setup Verification")
    print("=" * 60)
    
    checks = [
        check_directory_structure(),
        check_required_files(),
        check_service_files(),
        test_config_loading(),
        check_git_repository(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✓ All checks passed! Project setup is complete.")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your settings")
        print("2. Run 'docker-compose up --build' to start all services")
        print("3. Access services at http://localhost:8000-8006")
        return 0
    else:
        print("✗ Some checks failed. Please review the output above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
