#!/usr/bin/env python3
"""
Simple test script to verify the search functionality works correctly
without needing to run the full Flask server.
"""

import json
from main import app

def test_search_functionality():
    """Test the search functionality directly"""
    with app.test_client() as client:
        print("Testing ECL Search Functionality")
        print("=" * 50)
        
        # Test 1: Empty query
        print("\n1. Testing empty query:")
        response = client.get('/search_ecl?q=')
        print(f"   Status: {response.status_code}")
        data = json.loads(response.data)
        print(f"   Results: {len(data)} items")
        
        # Test 2: Short query
        print("\n2. Testing short query (single character):")
        response = client.get('/search_ecl?q=a')
        print(f"   Status: {response.status_code}")
        data = json.loads(response.data)
        print(f"   Results: {len(data)} items")
        
        # Test 3: Search for "injection"
        print("\n3. Testing search for 'injection':")
        response = client.get('/search_ecl?q=injection')
        print(f"   Status: {response.status_code}")
        data = json.loads(response.data)
        print(f"   Results: {len(data)} items")
        if data:
            print("   Sample result:")
            result = data[0]
            print(f"     Filename: {result['filename']}")
            print(f"     Description: {result['description'][:60]}...")
            print(f"     Category: {result['category']}")
            print(f"     Match Score: {result['match_score']}")
        
        # Test 4: Search for "disorder"
        print("\n4. Testing search for 'disorder':")
        response = client.get('/search_ecl?q=disorder')
        print(f"   Status: {response.status_code}")
        data = json.loads(response.data)
        print(f"   Results: {len(data)} items")
        if data:
            print("   Top 3 results:")
            for i, result in enumerate(data[:3], 1):
                print(f"     {i}. {result['filename']} (score: {result['match_score']})")
        
        # Test 5: Case insensitive search
        print("\n5. Testing case insensitive search ('DISORDER' vs 'disorder'):")
        response1 = client.get('/search_ecl?q=disorder')
        response2 = client.get('/search_ecl?q=DISORDER')
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        print(f"   'disorder': {len(data1)} results")
        print(f"   'DISORDER': {len(data2)} results")
        print(f"   Same results: {len(data1) == len(data2)}")
        
        # Test 6: Search for something that might not exist
        print("\n6. Testing search for unlikely term 'xyzzyzx':")
        response = client.get('/search_ecl?q=xyzzyzx')
        print(f"   Status: {response.status_code}")
        data = json.loads(response.data)
        print(f"   Results: {len(data)} items")
        
        print("\n" + "=" * 50)
        print("Search functionality testing complete!")

if __name__ == "__main__":
    test_search_functionality()
