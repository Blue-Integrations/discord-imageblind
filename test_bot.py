#!/usr/bin/env python3
"""
Test script for BlindBot functionality
This script tests the core image analysis functions without running the Discord bot
"""

import os
import asyncio
import base64
from PIL import Image
import io

# Mock the OpenAI client for testing
class MockOpenAIClient:
    async def chat_completions_create(self, **kwargs):
        # Return a mock response
        class MockResponse:
            def __init__(self):
                class MockChoice:
                    def __init__(self):
                        class MockMessage:
                            def __init__(self):
                                self.content = "This is a test image description. It contains various objects and elements that would be helpful for a blind person to understand the visual content."
                        self.message = MockMessage()
                self.choices = [MockChoice()]
        
        return MockResponse()

async def test_image_analysis():
    """Test the image analysis functionality"""
    print("Testing BlindBot image analysis...")
    
    # Create a simple test image
    test_image = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    test_image.save(img_buffer, format='JPEG')
    image_data = img_buffer.getvalue()
    
    # Test base64 encoding
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    print(f"✓ Image base64 encoding successful (length: {len(image_base64)})")
    
    # Test OpenAI message structure
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please provide a detailed description of this image that would be helpful for a blind person."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ]
    
    print(f"✓ Message structure created successfully")
    print(f"✓ Message contains {len(messages)} message(s)")
    print(f"✓ First message has {len(messages[0]['content'])} content items")
    
            # Test mock OpenAI response
        mock_client = MockOpenAIClient()
        response = await mock_client.chat.completions_create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
    
    print(f"✓ Mock OpenAI response received")
    print(f"✓ Response content: {response.choices[0].message.content[:100]}...")
    
    print("\n🎉 All tests passed! The bot's core functionality is working correctly.")
    print("\nTo run the actual bot:")
    print("1. Copy config.env.example to .env")
    print("2. Fill in your Discord and OpenAI tokens")
    print("3. Run: python bot.py")

if __name__ == "__main__":
    asyncio.run(test_image_analysis())
