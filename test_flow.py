#!/usr/bin/env python3
"""
Test script to verify the complete upload and conversion flow
"""

import asyncio
import aiohttp
import os
import time

async def test_complete_flow():
    """Test the complete upload and conversion flow"""
    
    base_url = "http://localhost:8000"
    test_video_path = "test_video.mp4"
    
    if not os.path.exists(test_video_path):
        print(f"❌ Test video file {test_video_path} not found")
        return False
    
    async with aiohttp.ClientSession() as session:
        print("🚀 Starting complete flow test...")
        
        # Test 1: Upload with HLS format
        print("\n1. Testing HLS upload...")
        with open(test_video_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename='test_video.mp4', content_type='video/mp4')
            data.add_field('media_format', 'm3u8')
            data.add_field('streaming_protocol', 'hls')
            
            async with session.post(f"{base_url}/api/v1/upload/", data=data) as response:
                if response.status != 200:
                    print(f"❌ Upload failed with status {response.status}")
                    return False
                
                result = await response.json()
                task_id = result['task_id']
                print(f"✅ Upload started, task ID: {task_id}")
        
        # Wait for conversion to complete
        print("\n2. Waiting for conversion...")
        for i in range(10):  # Wait up to 20 seconds
            async with session.get(f"{base_url}/api/v1/tasks/{task_id}") as response:
                task_data = await response.json()
                if task_data['status'] == 'completed':
                    print("✅ Conversion completed!")
                    break
                elif task_data['status'] == 'failed':
                    print(f"❌ Conversion failed: {task_data.get('error', 'Unknown error')}")
                    return False
                await asyncio.sleep(2)
        else:
            print("❌ Conversion timed out")
            return False
        
        # Test stream endpoint
        print("\n3. Testing stream endpoint...")
        async with session.get(f"{base_url}/api/v1/stream/{task_id}") as response:
            if response.status != 200:
                print(f"❌ Stream endpoint failed with status {response.status}")
                return False
            
            stream_data = await response.json()
            print(f"✅ Stream data: {stream_data}")
            
            if not stream_data.get('hls_url'):
                print("❌ No HLS URL in stream data")
                return False
        
        # Test HLS playlist access
        print("\n4. Testing HLS playlist access...")
        hls_url = f"{base_url}{stream_data['hls_url']}"
        async with session.get(hls_url) as response:
            if response.status != 200:
                print(f"❌ HLS playlist failed with status {response.status}")
                return False
            
            playlist_content = await response.text()
            if not playlist_content.startswith('#EXTM3U'):
                print("❌ Invalid HLS playlist content")
                return False
            
            print(f"✅ HLS playlist accessible ({len(playlist_content)} bytes)")
        
        print("\n🎉 Complete flow test PASSED!")
        return True

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
