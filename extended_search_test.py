#!/usr/bin/env python3
"""
Extended search testing to show different search scenarios
"""

import json
from main import app

def extended_search_test():
    """Test various search terms to demonstrate functionality"""
    with app.test_client() as client:
        print("Extended ECL Search Testing")
        print("=" * 60)
        
        search_terms = [
            "injection",
            "dose",
            "form",
            "AMT", 
            "clinical",
            "findings",
            "all",
            "administration"
        ]
        
        for term in search_terms:
            print(f"\nSearching for '{term}':")
            response = client.get(f'/search_ecl?q={term}')
            data = json.loads(response.data)
            print(f"  Found {len(data)} results")
            
            if data:
                # Show top 3 results with details
                for i, result in enumerate(data[:3], 1):
                    print(f"    {i}. {result['filename']}")
                    print(f"       Category: {result['category']}")
                    print(f"       Score: {result['match_score']}")
                    print(f"       Description: {result['description'][:80]}...")
                    print()

if __name__ == "__main__":
    extended_search_test()
