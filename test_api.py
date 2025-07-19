#!/usr/bin/env python3
"""
Test script for the bacteria detection API
"""
import requests
import os
import json
from pathlib import Path
import time

# API endpoint
API_URL = "http://localhost:8000/detect/"
TEST_IMAGES_DIR = "test images"

def test_api_endpoint():
    """Test if the API is responding"""
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✅ API is running: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ API is not responding: {e}")
        return False

def test_single_image(image_path):
    """Test bacteria detection on a single image"""
    print(f"\n🔍 Testing: {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/png')}
            response = requests.post(API_URL, files=files)
        
        if response.status_code == 200:
            result = response.json()
            bacteria_count = result.get('bacteria_count', 0)
            detections = result.get('detections', [])
            
            print(f"🦠 Bacteria Count: {bacteria_count}")
            if detections:
                confidences = [d['confidence'] for d in detections]
                avg_confidence = sum(confidences) / len(confidences)
                print(f"📊 Average Confidence: {avg_confidence:.3f}")
                print(f"🎯 Confidence Range: {min(confidences):.3f} - {max(confidences):.3f}")
            
            return result
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing {image_path}: {e}")
        return None

def test_all_images():
    """Test all images in the test images directory"""
    if not test_api_endpoint():
        return
    
    test_dir = Path(TEST_IMAGES_DIR)
    if not test_dir.exists():
        print(f"❌ Test images directory not found: {test_dir}")
        return
    
    # Get all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    image_files = [f for f in test_dir.iterdir() 
                   if f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"❌ No image files found in {test_dir}")
        return
    
    print(f"📁 Found {len(image_files)} test images")
    print("=" * 60)
    
    results = []
    total_bacteria = 0
    
    for i, image_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}]", end=" ")
        result = test_single_image(image_path)
        
        if result:
            results.append({
                'image': image_path.name,
                'bacteria_count': result['bacteria_count'],
                'detections': len(result.get('detections', []))
            })
            total_bacteria += result['bacteria_count']
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"   Images tested: {len(results)}")
    print(f"   Total bacteria detected: {total_bacteria}")
    if results:
        print(f"   Average bacteria per image: {total_bacteria/len(results):.1f}")
        
        # Show top results
        sorted_results = sorted(results, key=lambda x: x['bacteria_count'], reverse=True)
        print(f"\n🏆 TOP DETECTIONS:")
        for result in sorted_results[:3]:
            print(f"   {result['image']}: {result['bacteria_count']} bacteria")
    
    print("=" * 60)

if __name__ == "__main__":
    print("🧪 BACTERIA DETECTION API TEST")
    print("=" * 60)
    test_all_images()
