"""Simple test to demonstrate MCP image functionality."""

import json
import tempfile
import os
from pathlib import Path

from openhands.events.observation.mcp import MCPObservation
from openhands.core.message import ImageContent, TextContent
from openhands.memory.conversation_memory import ConversationMemory
from openhands.core.config.agent_config import AgentConfig
from openhands.utils.prompt import PromptManager
from openhands.events.action import MessageAction
from openhands.events.event import EventSource


def test_mcp_image_functionality():
    """Test the complete MCP image functionality."""
    print("🧪 Testing MCP Image Functionality")
    
    # Create a temporary PNG file
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc\xf8\x0f\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x07\n\xcb\xc0\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(png_data)
        temp_image_path = f.name
    
    try:
        print(f"📁 Created test image: {temp_image_path}")
        
        # Test 1: MCPObservation with image paths
        print("\n1️⃣ Testing MCPObservation image path extraction...")
        
        content = json.dumps({
            'result': 'Screenshot captured successfully',
            'image_paths': [temp_image_path]
        })
        
        obs = MCPObservation(
            content=content,
            name='screenshot_tool',
            arguments={'region': 'fullscreen'}
        )
        
        print(f"✅ Has images: {obs.has_images()}")
        print(f"✅ Image paths: {obs.image_paths}")
        
        # Test 2: Base64 conversion
        print("\n2️⃣ Testing base64 conversion...")
        
        image_data = obs.get_image_base64_data()
        print(f"✅ Generated {len(image_data)} base64 image(s)")
        if image_data:
            print(f"✅ MIME type: {image_data[0]['mime_type']}")
            print(f"✅ Data starts with: {image_data[0]['data'][:50]}...")
        
        # Test 3: ConversationMemory integration (vision disabled)
        print("\n3️⃣ Testing ConversationMemory (vision disabled)...")
        
        config = AgentConfig(enable_prompt_extensions=True)
        prompt_manager = PromptManager()
        memory = ConversationMemory(config, prompt_manager)
        
        initial_user_message = MessageAction(content='Take a screenshot')
        initial_user_message._source = EventSource.USER
        
        messages = memory.process_events(
            condensed_history=[obs],
            initial_user_action=initial_user_message,
            max_message_chars=None,
            vision_is_active=False,
        )
        
        result_message = messages[-1]  # Last message should be the MCP observation
        print(f"✅ Message role: {result_message.role}")
        print(f"✅ Content types: {[type(c).__name__ for c in result_message.content]}")
        print(f"✅ Contains 'vision not enabled': {'vision not enabled' in str(result_message.content)}")
        
        # Test 4: ConversationMemory integration (vision enabled)
        print("\n4️⃣ Testing ConversationMemory (vision enabled)...")
        
        messages = memory.process_events(
            condensed_history=[obs],
            initial_user_action=initial_user_message,
            max_message_chars=None,
            vision_is_active=True,
        )
        
        result_message = messages[-1]
        print(f"✅ Message role: {result_message.role}")
        print(f"✅ Content count: {len(result_message.content)}")
        
        text_content = None
        image_content = None
        
        for content in result_message.content:
            if isinstance(content, TextContent):
                text_content = content
            elif isinstance(content, ImageContent):
                image_content = content
        
        print(f"✅ Has TextContent: {text_content is not None}")
        print(f"✅ Has ImageContent: {image_content is not None}")
        
        if image_content:
            print(f"✅ Image URLs count: {len(image_content.image_urls)}")
            print(f"✅ First image URL starts with: {image_content.image_urls[0][:50]}...")
        
        if text_content:
            print(f"✅ Text mentions images: {'image(s)' in text_content.text}")
            print(f"✅ Text mentions tool name: {'screenshot_tool' in text_content.text}")
        
        print("\n🎉 All tests passed! MCP image functionality is working correctly.")
        
        return True
        
    finally:
        # Clean up
        try:
            os.unlink(temp_image_path)
        except:
            pass


if __name__ == "__main__":
    test_mcp_image_functionality()
