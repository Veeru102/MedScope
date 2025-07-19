#!/usr/bin/env python3
"""
Health check script for the MedPub backend
This script can be used to verify the server is running properly
"""

import requests
import sys
import json
import time

def check_endpoint(url, endpoint_name, timeout=10):
    """Check if an endpoint is responding"""
    try:
        print(f"Checking {endpoint_name} at {url}...")
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            print(f"✅ {endpoint_name} is working (Status: {response.status_code})")
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response (text): {response.text[:200]}...")
            return True
        else:
            print(f"❌ {endpoint_name} returned status {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint_name} failed: {e}")
        return False

def main():
    """Main health check function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"=== Health Check for {base_url} ===")
    print()
    
    # Check various endpoints
    endpoints = [
        ("/", "Root endpoint"),
        ("/healthz", "Health check"),
        ("/test-upload", "Upload test endpoint"),
    ]
    
    all_good = True
    
    for path, name in endpoints:
        url = f"{base_url}{path}"
        if not check_endpoint(url, name):
            all_good = False
        print()
        time.sleep(1)  # Small delay between checks
    
    if all_good:
        print("🎉 All health checks passed!")
        return True
    else:
        print("⚠️  Some health checks failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 