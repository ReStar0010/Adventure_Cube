"""
Quick test script for the Adventure Cube backend APIs.
Run this after starting the server to verify everything works.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

# Global token storage
AUTH_TOKEN = None

def get_auth_headers():
    """Get authorization headers if token exists"""
    if AUTH_TOKEN:
        return {"Authorization": f"Token {AUTH_TOKEN}"}
    return {}

def test_register():
    """Test user registration"""
    print("\n=== Testing POST /api/auth/register/ ===")
    import random
    username = f"testuser_{random.randint(1000, 9999)}"
    data = {
        "username": username,
        "password": "testpass123",
        "password2": "testpass123",
        "email": f"{username}@example.com"
    }
    response = requests.post(f"{BASE_URL}/auth/register/", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"User: {result['user']['username']}")
        print(f"Token: {result['token'][:20]}...")
        return True, result['token']
    else:
        print(f"Error: {response.json()}")
        return False, None

def test_login(username="testuser", password="testpass123"):
    """Test user login"""
    global AUTH_TOKEN
    print("\n=== Testing POST /api/auth/login/ ===")
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/auth/login/", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"User: {result['user']['username']}")
        print(f"Token: {result['token'][:20]}...")
        AUTH_TOKEN = result['token']
        return True
    else:
        print(f"Error: {response.json()}")
        return False

def test_themes():
    """Test getting available themes (public endpoint)"""
    print("\n=== Testing GET /api/themes/ (Public) ===")
    response = requests.get(f"{BASE_URL}/themes/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_story_generation():
    """Test story generation (requires auth)"""
    print("\n=== Testing POST /api/stories/generate/ (Authenticated) ===")
    data = {
        "theme": "friendship",
        "child_name": "Alex",
        "child_age": 6
    }
    response = requests.post(f"{BASE_URL}/stories/generate/", json=data, headers=get_auth_headers())
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"Story ID: {result.get('id')}")
        print(f"Title: {result.get('title')}")
        print(f"Model Source: {result.get('model_source')}")
        print(f"Body (first 100 chars): {result.get('body', '')[:100]}...")
        return True, result.get('id')
    else:
        print(f"Error: {response.json()}")
        return False, None

def test_list_stories():
    """Test listing all stories (requires auth)"""
    print("\n=== Testing GET /api/stories/ (Authenticated) ===")
    response = requests.get(f"{BASE_URL}/stories/", headers=get_auth_headers())
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        stories = response.json()
        print(f"Total stories: {len(stories)}")
        return True
    else:
        print(f"Error: {response.json()}")
        return False

def test_tts(story_id):
    """Test TTS generation (requires auth)"""
    print(f"\n=== Testing POST /api/tts/generate/ (Authenticated) ===")
    data = {
        "story_id": story_id,
        "language": "en"
    }
    response = requests.post(f"{BASE_URL}/tts/generate/", json=data, headers=get_auth_headers())
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"Audio ID: {result.get('id')}")
        print(f"Audio URL: {result.get('audio_url')}")
        print(f"Duration: {result.get('duration_seconds')} seconds")
        return True
    else:
        print(f"Error: {response.json()}")
        return False

def test_images():
    """Test image listing (public endpoint)"""
    print("\n=== Testing GET /api/images/ (Public) ===")
    response = requests.get(f"{BASE_URL}/images/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        for category, images in result.items():
            print(f"  {category}: {len(images)} images")
        return True
    else:
        print(f"Error: {response.json()}")
        return False

def test_logout():
    """Test logout"""
    global AUTH_TOKEN
    print("\n=== Testing POST /api/auth/logout/ (Authenticated) ===")
    response = requests.post(f"{BASE_URL}/auth/logout/", headers=get_auth_headers())
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Message: {result.get('message')}")
        AUTH_TOKEN = None
        return True
    else:
        print(f"Error: {response.json()}")
        return False

def main():
    global AUTH_TOKEN
    print("=" * 60)
    print("Adventure Cube Backend API Test (With Authentication)")
    print("=" * 60)
    print("\nMake sure the server is running: python manage.py runserver")
    print()
    
    try:
        # Test 1: Public endpoints (Themes)
        if not test_themes():
            print("❌ Themes test failed")
            return
        print("✅ Themes test passed")
        
        # Test 2: Images (public)
        if not test_images():
            print("⚠️  Images test failed (may need frontend assets)")
        else:
            print("✅ Images test passed")
        
        # Test 3: Register a new user
        print("\n--- Authentication Tests ---")
        success, token = test_register()
        if not success:
            print("❌ Registration test failed")
            return
        print("✅ Registration test passed")
        AUTH_TOKEN = token
        
        # Test 4: Story generation (requires auth)
        success, story_id = test_story_generation()
        if not success:
            print("❌ Story generation test failed")
            return
        print("✅ Story generation test passed")
        
        # Test 5: List stories (requires auth)
        if not test_list_stories():
            print("❌ List stories test failed")
            return
        print("✅ List stories test passed")
        
        # Test 6: TTS (may be slow, requires auth)
        print("\n⏳ TTS test may take 10-30 seconds...")
        if not test_tts(story_id):
            print("⚠️  TTS test failed (may need gTTS installed)")
        else:
            print("✅ TTS test passed")
        
        # Test 7: Logout
        if not test_logout():
            print("⚠️  Logout test failed")
        else:
            print("✅ Logout test passed")
        
        print("\n" + "=" * 60)
        print("✅ All critical tests passed!")
        print("=" * 60)
        print("\nNote: Old stories without user association are hidden.")
        print("Only authenticated users can create and view their own stories.")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        print("   Start with: python manage.py runserver")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
