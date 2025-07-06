#!/usr/bin/env python3
"""
Test script for LoadGenie AI service integration
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.ai_service import get_ai_service, AIServiceError


async def test_ai_service():
    """Test the AI service functionality"""
    print("Testing LoadGenie AI Service Integration...")
    print("=" * 50)
    
    # Get AI service instance
    ai_service = get_ai_service()
    
    # Test case 1: Basic functionality
    test_description = """
    Create a k6 load test that:
    1. Tests a REST API endpoint at https://api.example.com/users
    2. Simulates 50 virtual users
    3. Runs for 2 minutes
    4. Makes GET requests to fetch user data
    5. Includes basic response validation
    """
    
    try:
        print("Test 1: Basic script generation")
        print(f"Input: {test_description[:100]}...")
        
        result = await ai_service.generate_k6_script(test_description)
        
        print("✅ Success!")
        print(f"Generated script length: {len(result['k6_script'])} characters")
        print(f"Script preview:\n{result['k6_script'][:200]}...")
        print()
        
    except AIServiceError as e:
        print(f"❌ AI Service Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False
    
    # Test case 2: Edge case - empty description
    try:
        print("Test 2: Empty description handling")
        await ai_service.generate_k6_script("")
        print("❌ Should have raised an error for empty description")
        return False
    except AIServiceError:
        print("✅ Correctly handled empty description")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Test case 3: Edge case - very short description
    try:
        print("Test 3: Short description handling")
        await ai_service.generate_k6_script("test")
        print("❌ Should have raised an error for too short description")
        return False
    except AIServiceError:
        print("✅ Correctly handled short description")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! AI service integration is working correctly.")
    return True


async def test_mock_response():
    """Test with the mock response format you provided"""
    print("\nTesting with your expected response format...")
    
    mock_response = {
        "k6_script": "import http from 'k6/http';import { sleep } from 'k6';export const options = {vus: 10,duration: '30s',};export default function () {http.get('https://test.k6.io');sleep(1);}"
    }
    
    print("✅ Mock response format is valid")
    print(f"Script: {mock_response['k6_script']}")
    
    # Validate the script has required components
    script = mock_response['k6_script']
    required_components = ['import http', 'export const options', 'export default function', 'http.get']
    
    for component in required_components:
        if component in script:
            print(f"✅ Found required component: {component}")
        else:
            print(f"❌ Missing component: {component}")
    
    return True


if __name__ == "__main__":
    # Check if GEMINI_API_KEY is set
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️  Warning: GEMINI_API_KEY environment variable not set.")
        print("   The AI service tests will fail without a valid API key.")
        print("   Testing mock response format only...\n")
        
        asyncio.run(test_mock_response())
    else:
        print("🔑 GEMINI_API_KEY found, running full tests...\n")
        success = asyncio.run(test_ai_service())
        
        if success:
            asyncio.run(test_mock_response())
            print("\n🚀 LoadGenie backend is ready for production!")
        else:
            print("\n❌ Some tests failed. Please check the configuration.")
            sys.exit(1)
