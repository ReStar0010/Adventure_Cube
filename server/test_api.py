"""
Quick test script for the Adventure Cube backend APIs.
Run this after starting the server to verify everything works.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_themes():
    """Test getting available themes"""
    print("\n=== Testing GET /api/themes/ ===")
    response = requests.get(f"{BASE_URL}/themes/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_story_generation():
    """Test story generation"""
    print("\n=== Testing POST /api/stories/generate/ ===")
    data = {
        "theme": "friendship",
        "child_name": "Alex",
        "child_age": 6
    }
    response = requests.post(f"{BASE_URL}/stories/generate/", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Story ID: {result.get('id')}")
    print(f"Title: {result.get('title')}")
    print(f"Model Source: {result.get('model_source')}")
    print(f"Body (first 100 chars): {result.get('body', '')[:100]}...")
    return response.status_code == 201, result.get('id')

def test_list_stories():
    """Test listing all stories"""
    print("\n=== Testing GET /api/stories/ ===")
    response = requests.get(f"{BASE_URL}/stories/")
    print(f"Status: {response.status_code}")
    stories = response.json()
    print(f"Total stories: {len(stories)}")
    return response.status_code == 200

def test_tts(story_id):
    """Test TTS generation"""
    print(f"\n=== Testing POST /api/tts/generate/ ===")
    data = {
        "story_id": story_id,
        "language": "en"
    }
    response = requests.post(f"{BASE_URL}/tts/generate/", json=data)
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
    """Test image listing"""
    print("\n=== Testing GET /api/images/ ===")
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

def main():
    print("=" * 60)
    print("Adventure Cube Backend API Test")
    print("=" * 60)
    print("\nMake sure the server is running: python manage.py runserver")
    print()
    
    try:
        # Test 1: Themes
        if not test_themes():
            print("❌ Themes test failed")
            return
        print("✅ Themes test passed")
        
        # Test 2: Story generation
        success, story_id = test_story_generation()
        if not success:
            print("❌ Story generation test failed")
            return
        print("✅ Story generation test passed")
        
        # Test 3: List stories
        if not test_list_stories():
            print("❌ List stories test failed")
            return
        print("✅ List stories test passed")
        
        # Test 4: TTS (may be slow)
        print("\n⏳ TTS test may take 10-30 seconds...")
        if not test_tts(story_id):
            print("⚠️  TTS test failed (may need gTTS installed)")
        else:
            print("✅ TTS test passed")
        
        # Test 5: Images
        if not test_images():
            print("⚠️  Images test failed (may need frontend assets)")
        else:
            print("✅ Images test passed")
        
        print("\n" + "=" * 60)
        print("✅ All critical tests passed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        print("   Start with: python manage.py runserver")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
