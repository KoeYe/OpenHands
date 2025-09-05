"""Tests for MCPObservation with image support."""

import json
import os
import tempfile
import base64
from pathlib import Path
from unittest.mock import patch

import pytest

from openhands.events.observation.mcp import MCPObservation


class TestMCPObservationImages:
    """Test image handling in MCPObservation."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary image file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.temp_dir, 'test_image.png')
        
        # Create a simple PNG image (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc\xf8\x0f\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x07\n\xcb\xc0\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(self.test_image_path, 'wb') as f:
            f.write(png_data)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mcp_observation_no_images(self):
        """Test MCPObservation without any images."""
        obs = MCPObservation(
            content='{"result": "success"}',
            name='test_tool',
            arguments={'arg1': 'value1'}
        )
        
        assert not obs.has_images()
        assert obs.image_paths == []
        assert obs.get_image_base64_data() == []

    def test_mcp_observation_with_image_paths_field(self):
        """Test MCPObservation with image_paths field in content."""
        content = {
            'result': 'success',
            'image_paths': [self.test_image_path]
        }
        
        obs = MCPObservation(
            content=json.dumps(content),
            name='test_tool',
            arguments={'arg1': 'value1'}
        )
        
        assert obs.has_images()
        assert self.test_image_path in obs.image_paths
        
        # Test base64 conversion
        image_data = obs.get_image_base64_data()
        assert len(image_data) == 1
        assert image_data[0]['path'] == self.test_image_path
        assert image_data[0]['mime_type'] == 'image/png'
        assert image_data[0]['data'].startswith('data:image/png;base64,')

    def test_mcp_observation_with_content_array(self):
        """Test MCPObservation with images in content array."""
        content = {
            'result': 'success',
            'content': [
                {'type': 'text', 'text': 'Operation completed'},
                {'type': 'image', 'path': self.test_image_path}
            ]
        }
        
        obs = MCPObservation(
            content=json.dumps(content),
            name='test_tool',
            arguments={'arg1': 'value1'}
        )
        
        assert obs.has_images()
        assert self.test_image_path in obs.image_paths

    def test_mcp_observation_with_multiple_images(self):
        """Test MCPObservation with multiple image paths."""
        # Create another test image
        test_image_2 = os.path.join(self.temp_dir, 'test_image_2.jpg')
        with open(test_image_2, 'wb') as f:
            f.write(b'fake_jpg_data')  # Just for testing path extraction
        
        content = {
            'result': 'success',
            'images': [self.test_image_path, test_image_2]
        }
        
        obs = MCPObservation(
            content=json.dumps(content),
            name='test_tool',
            arguments={'arg1': 'value1'}
        )
        
        assert obs.has_images()
        # Only the PNG should be valid since the fake JPG doesn't have valid header
        assert self.test_image_path in obs.image_paths
        # test_image_2 might not be included if it fails validation

    def test_mcp_observation_nonexistent_image(self):
        """Test MCPObservation with path to nonexistent image file."""
        nonexistent_path = '/nonexistent/path/image.png'
        content = {
            'result': 'success',
            'image_paths': [nonexistent_path]
        }
        
        obs = MCPObservation(
            content=json.dumps(content),
            name='test_tool',
            arguments={'arg1': 'value1'}
        )
        
        # Nonexistent files should be filtered out
        assert not obs.has_images()
        assert obs.image_paths == []

    def test_mcp_observation_invalid_json(self):
        """Test MCPObservation with invalid JSON content."""
        obs = MCPObservation(
            content='invalid json content',
            name='test_tool',
            arguments={'arg1': 'value1'}
        )
        
        assert not obs.has_images()
        assert obs.image_paths == []

    def test_mcp_observation_various_path_fields(self):
        """Test MCPObservation with different field names for paths."""
        content = {
            'result': 'success',
            'screenshots': [self.test_image_path],
            'files': ['some_text_file.txt', self.test_image_path]
        }
        
        obs = MCPObservation(
            content=json.dumps(content),
            name='test_tool',
            arguments={'arg1': 'value1'}
        )
        
        assert obs.has_images()
        assert self.test_image_path in obs.image_paths

    @patch('openhands.events.observation.mcp.logger')
    def test_mcp_observation_file_read_error(self, mock_logger):
        """Test error handling when reading image file fails."""
        obs = MCPObservation(
            content=json.dumps({'image_paths': [self.test_image_path]}),
            name='test_tool',
            arguments={'arg1': 'value1'}
        )
        
        # Mock file read to raise an exception
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            image_data = obs.get_image_base64_data()
            
            # Should return empty list on error
            assert image_data == []
            # Should log the error
            mock_logger.error.assert_called_once()

    def test_mcp_observation_nested_json_format(self):
        """Test MCPObservation with nested MCP protocol format."""
        # This mimics the actual format returned from MCP tools
        nested_content = json.dumps({
            "meta": None,
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "message": "Camera view captured successfully",
                        "image_paths": [
                            "/data/koe/coding-agent-ue/Saved/images/currentimage.png"
                        ]
                    })
                }
            ],
            "isError": False
        })
        
        obs = MCPObservation(
            content=nested_content,
            name='get_camera_0_view',
            arguments={}
        )
        
        assert obs.has_images() is True
        assert len(obs.image_paths) == 1
        assert obs.image_paths[0] == "/data/koe/coding-agent-ue/Saved/images/currentimage.png"
        
        # Test the message property
        assert "Camera view captured successfully" in obs.message

    def test_message_property(self):
        """Test that message property still works correctly."""
        content = '{"result": "success"}'
        obs = MCPObservation(
            content=content,
            name='test_tool',
            arguments={'arg1': 'value1'}
        )
        
        assert obs.message == content
