#!/usr/bin/env python3
"""
Configuration checker for BlindBot
This script verifies that all required environment variables and dependencies are set up correctly
"""

import os
import sys

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version: {sys.version.split()[0]}")
        return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    
    required_packages = [
        'discord',
        'openai',
        'aiohttp',
        'PIL',
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
                print(f"✅ {package} (Pillow)")
            elif package == 'dotenv':
                import dotenv
                print(f"✅ {package}")
            else:
                __import__(package)
                print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - not installed")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def check_environment():
    """Check if environment variables are set"""
    print("\nChecking environment variables...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("❌ python-dotenv not installed")
            return False
        
        # Check Discord token
        discord_token = os.getenv('DISCORD_TOKEN')
        if discord_token and discord_token != 'your_discord_bot_token_here':
            print("✅ DISCORD_TOKEN is set")
        else:
            print("❌ DISCORD_TOKEN is not set or still has default value")
            return False
        
        # Check OpenAI API key
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key != 'your_openai_api_key_here':
            print("✅ OPENAI_API_KEY is set")
        else:
            print("❌ OPENAI_API_KEY is not set or still has default value")
            return False
        
    else:
        print("❌ .env file not found")
        print("   Copy config.env.example to .env and fill in your tokens")
        return False
    
    return True

def check_file_permissions():
    """Check if required files are accessible"""
    print("\nChecking file permissions...")
    
    required_files = ['bot.py', 'requirements.txt']
    
    for file in required_files:
        if os.path.exists(file):
            if os.access(file, os.R_OK):
                print(f"✅ {file} is readable")
            else:
                print(f"❌ {file} is not readable")
                return False
        else:
            print(f"❌ {file} not found")
            return False
    
    return True

def main():
    """Main configuration check"""
    print("🔍 BlindBot Configuration Checker")
    print("=" * 40)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_environment(),
        check_file_permissions()
    ]
    
    print("\n" + "=" * 40)
    
    if all(checks):
        print("🎉 All checks passed! Your bot is ready to run.")
        print("\nTo start the bot:")
        print("   python bot.py")
        print("   or")
        print("   ./run.sh (Linux/Mac)")
        print("   run.bat (Windows)")
    else:
        print("❌ Some checks failed. Please fix the issues above before running the bot.")
        sys.exit(1)

if __name__ == "__main__":
    main()
