#!/usr/bin/env python3
"""
Simple test script to call the API directly
"""

import requests
import json

def test_api():
    """Test the API directly"""
    # First, get a token by logging in
    login_data = {
        "email": "Admin@gmail.com",
        "password": "Admin"
    }
    
    response = requests.post("http://localhost:8000/auth/signin", json=login_data)
    if response.status_code == 200:
        token = response.json().get("token")
        print(f"Got token: {token[:20]}...")
        
        # Now call the docker images endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:8000/docker/images", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API returned {len(data.get('images', []))} images")
            
            for i, image in enumerate(data.get('images', [])):
                print(f"Image {i+1}: ID={image.get('id')}, Name={image.get('image_name')}, User={image.get('user_email')}")
        else:
            print(f"Failed to get images: {response.status_code}")
    else:
        print(f"Failed to login: {response.status_code}")

if __name__ == "__main__":
    test_api()
