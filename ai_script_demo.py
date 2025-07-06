#!/usr/bin/env python3
"""
Demo script showing LoadGenie's AI-powered K6 script generation
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def demo_script_generation():
    """Demonstrate AI script generation capabilities"""
    
    print("🤖 LoadGenie AI Script Generation Demo")
    print("=" * 50)
    
    # Example scenarios to test
    scenarios = [
        "Test a REST API with 10 users for 30 seconds, checking login endpoint",
        "Load test an e-commerce site with users browsing products and adding items to cart",
        "Test a GraphQL API with complex queries and 15 concurrent users",
        "Stress test a file upload endpoint with 5 users uploading different file sizes"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🎯 Scenario {i}: {scenario}")
        print("-" * 60)
        
        try:
            # Generate script
            response = requests.post(f"{BASE_URL}/generate-script", json={
                "scenario_description": scenario
            })
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Script generated successfully!")
                print(f"📝 Generated at: {result['generated_at']}")
                print(f"\n📋 K6 Script Preview (first 500 chars):")
                print("┌" + "─" * 58 + "┐")
                
                # Show first 500 characters of the script
                script_preview = result['script'][:500]
                lines = script_preview.split('\n')
                for line in lines:
                    if len(line) > 56:
                        line = line[:53] + "..."
                    print(f"│ {line:<56} │")
                
                if len(result['script']) > 500:
                    print(f"│ ... (script continues for {len(result['script']) - 500} more chars) │")
                
                print("└" + "─" * 58 + "┘")
                
                # Optional: Ask if user wants to run this script
                print(f"\n💡 You can now use this script with the /api/v1/test/run endpoint")
                
            else:
                print(f"❌ Failed to generate script: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        if i < len(scenarios):
            input("\nPress Enter to continue to the next scenario...")

def demo_full_workflow():
    """Demonstrate the complete workflow: generate + run test"""
    
    print(f"\n🚀 Complete Workflow Demo")
    print("=" * 50)
    
    scenario = "Test a simple API with 3 users for 10 seconds"
    print(f"📋 Scenario: {scenario}")
    
    try:
        # Step 1: Generate script
        print(f"\n⚡ Step 1: Generating K6 script...")
        response = requests.post(f"{BASE_URL}/generate-script", json={
            "scenario_description": scenario
        })
        
        if response.status_code == 200:
            script_result = response.json()
            print(f"✅ Script generated successfully!")
            
            # Step 2: Run the test
            print(f"\n⚡ Step 2: Running the generated test...")
            
            test_response = requests.post(f"{BASE_URL}/api/v1/test/run", json={
                "script": script_result['script'],
                "options": {
                    "vus": 3,
                    "duration": "10s"
                }
            })
            
            if test_response.status_code == 200:
                test_result = test_response.json()
                
                print(f"✅ Test completed successfully!")
                print(f"📊 Results:")
                print(f"   Test ID: {test_result['test_id']}")
                print(f"   Virtual Users: {test_result['metrics']['virtual_users']}")
                print(f"   Total Requests: {test_result['metrics']['total_requests']}")
                print(f"   Avg Response Time: {test_result['metrics']['response_time_avg']:.1f}ms")
                print(f"   Error Rate: {test_result['metrics']['error_rate']:.1f}%")
                print(f"   Throughput: {test_result['metrics']['requests_per_second']:.1f} RPS")
                
                # Show anomaly analysis
                anomaly = test_result['anomaly_analysis']
                print(f"\n🔍 Anomaly Analysis:")
                print(f"   Severity: {anomaly['severity']}")
                print(f"   Issues: {len(anomaly['issues'])} found")
                for rec in anomaly['recommendations']:
                    print(f"   💡 {rec}")
                    
            else:
                print(f"❌ Test execution failed: {test_response.status_code}")
                
        else:
            print(f"❌ Script generation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Workflow error: {e}")

def main():
    """Main demo function"""
    
    # Check if service is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ LoadGenie service is not running on port 8001")
            print("   Please start it with: uvicorn app.main:app --host 0.0.0.0 --port 8001")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to LoadGenie service on port 8001")
        print("   Please start it with: uvicorn app.main:app --host 0.0.0.0 --port 8001")
        return
    
    print("🎉 Welcome to LoadGenie AI Script Generation Demo!")
    print("This demo shows how to generate K6 load test scripts using natural language.")
    print(f"\n🌐 Web interface available at: {BASE_URL}/docs")
    
    choice = input(f"\nChoose demo:\n1. Script Generation Examples\n2. Complete Workflow (Generate + Run)\n\nEnter choice (1 or 2): ")
    
    if choice == "1":
        demo_script_generation()
    elif choice == "2":
        demo_full_workflow()
    else:
        print("Invalid choice. Running script generation demo...")
        demo_script_generation()
    
    print(f"\n🎯 Try it yourself at: {BASE_URL}/docs")
    print("📚 Full documentation in: USAGE_GUIDE.md")

if __name__ == "__main__":
    main()
