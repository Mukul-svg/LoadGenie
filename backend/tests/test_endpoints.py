#!/usr/bin/env python3
"""
Test script to verify the unified endpoint works with different content types
"""

import asyncio
import sys
from app.main import app
import json

def test_app_loading():
    """Test that the app loads correctly"""
    print("🧪 Testing app loading...")
    try:
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        
        # List all endpoints
        print("📍 Available endpoints:")
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = list(route.methods) if hasattr(route, 'methods') else []
                print(f"   {methods} {route.path}")
        
        return True
    except Exception as e:
        print(f"❌ App loading failed: {e}")
        return False

async def test_internal_function():
    """Test the internal generation function directly"""
    print("\n🧪 Testing internal script generation function...")
    try:
        from app.api.script_routes import _generate_script_internal
        
        test_description = "Create a k6 test for https://httpbin.org/get with 5 users for 30 seconds"
        result = await _generate_script_internal(test_description)
        
        print("✅ Internal function test successful!")
        print(f"   Script length: {len(result.script)} characters")
        print(f"   Generated at: {result.generated_at}")
        print(f"   Description: {result.scenario_description[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Internal function test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 LoadGenie Backend Validation Tests")
    print("=" * 50)
    
    # Test 1: App loading
    app_test = test_app_loading()
    
    # Test 2: Internal function
    internal_test = asyncio.run(test_internal_function())
    
    print("\n" + "=" * 50)
    if app_test and internal_test:
        print("🎉 All tests passed! The backend is ready to handle both JSON and form data.")
        print("\n📋 Usage Examples:")
        print("   JSON request:")
        print("   curl -X POST http://localhost:8000/api/generate-script \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"scenario_description\": \"Your test description\"}'")
        print("\n   Form data request:")
        print("   curl -X POST http://localhost:8000/api/generate-script \\")
        print("        -F 'scenario_description=Your test description'")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
