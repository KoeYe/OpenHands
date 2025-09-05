#!/usr/bin/env python3
"""
Test MCPObservation image processing functionality.
"""

import json
import os
import sys

# Add the current directory to the Python path so we can import openhands modules
sys.path.insert(0, '/home/koe/OpenHands')

from openhands.events.observation.mcp import MCPObservation
from openhands.memory.conversation_memory import ConversationMemory
from openhands.core.config import LLMConfig

def test_mcp_image_processing():
    """Test MCP image processing with a real camera capture response."""
    
    # Simulate the response from get_camera_0_view MCP tool
    mcp_response = {
        "success": True,
        "message": "Camera view captured successfully",
        "image_paths": [
            "/data/koe/coding-agent-ue/Saved/images/currentimage.png"
        ],
        "original_response": {
            "status": "success",
            "result": {
                "success": True,
                "python_logs": [
                    "[2025.09.05-01.04.25:469][ 95]LogPython: Camera view saved: /data/koe/coding-agent-ue/Saved/images/currentimage.png"
                ]
            }
        }
    }
    
    # Create MCPObservation
    content = json.dumps(mcp_response)
    obs = MCPObservation(
        content=content,
        name="get_camera_0_view",
        arguments={}
    )
    
    print("=== MCPObservation Test ===")
    print(f"Has images: {obs.has_images()}")
    print(f"Image paths: {obs.image_paths}")
    
    if obs.has_images():
        print("\n=== Image Base64 Conversion Test ===")
        image_data = obs.get_image_base64_data()
        for idx, img in enumerate(image_data):
            print(f"Image {idx+1}:")
            print(f"  Path: {img['path']}")
            print(f"  MIME type: {img['mime_type']}")
            print(f"  Base64 data length: {len(img['data'])} chars")
            print(f"  Data preview: {img['data'][:50]}...")
    
    # Test ConversationMemory integration
    print("\n=== ConversationMemory Integration Test ===")
    
    # Create a minimal config for testing
    llm_config = LLMConfig()
    memory = ConversationMemory()
    
    # Test processing with vision enabled
    try:
        result = memory._process_observation(obs, vision_is_active=True)
        print(f"Vision processing result type: {type(result)}")
        if hasattr(result, 'content'):
            content_preview = str(result.content)[:200] + "..." if len(str(result.content)) > 200 else str(result.content)
            print(f"Content preview: {content_preview}")
    except Exception as e:
        print(f"Vision processing error: {e}")
    
    # Test processing without vision
    try:
        result = memory._process_observation(obs, vision_is_active=False)
        print(f"Non-vision processing result type: {type(result)}")
        if hasattr(result, 'content'):
            content_preview = str(result.content)[:200] + "..." if len(str(result.content)) > 200 else str(result.content)
            print(f"Content preview: {content_preview}")
    except Exception as e:
        print(f"Non-vision processing error: {e}")

if __name__ == "__main__":
    test_mcp_image_processing()
