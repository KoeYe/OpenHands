from dataclasses import dataclass, field
from typing import Any
import json
import base64
import os
from pathlib import Path

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation
from openhands.core.logger import openhands_logger as logger


@dataclass
class MCPObservation(Observation):
    """This data class represents the result of a MCP Server operation."""

    observation: str = ObservationType.MCP
    name: str = ''  # The name of the MCP tool that was called
    arguments: dict[str, Any] = field(
        default_factory=dict
    )  # The arguments passed to the MCP tool
    image_paths: list[str] = field(
        default_factory=list
    )  # List of image file paths returned by MCP tool

    def __post_init__(self):
        if hasattr(super(), '__post_init__'):
            super().__post_init__()
        
        # Try to extract image paths from content
        try:
            if isinstance(self.content, str):
                parsed_content = json.loads(self.content)
                
                # Handle MCP protocol wrapper format
                # MCP responses are often: {"content": [{"type": "text", "text": "actual_json"}]}
                if (isinstance(parsed_content, dict) and 
                    'content' in parsed_content and 
                    isinstance(parsed_content['content'], list) and
                    len(parsed_content['content']) > 0):
                    
                    first_content = parsed_content['content'][0]
                    if (isinstance(first_content, dict) and 
                        'type' in first_content and 
                        first_content['type'] == 'text' and
                        'text' in first_content):
                        # Parse the nested JSON in the text field
                        try:
                            inner_json = json.loads(first_content['text'])
                            if isinstance(inner_json, dict):
                                parsed_content = inner_json
                        except json.JSONDecodeError:
                            pass  # Keep original parsed_content
                
                # Look for image paths in different possible formats
                image_paths = []
                
                # Format 1: Direct image_paths field
                if isinstance(parsed_content, dict) and 'image_paths' in parsed_content:
                    paths = parsed_content['image_paths']
                    if isinstance(paths, list):
                        image_paths.extend(paths)
                    elif isinstance(paths, str):
                        image_paths.append(paths)
                
                # Format 2: Images in content array (if not MCP wrapper)
                if isinstance(parsed_content, dict) and 'content' in parsed_content and not image_paths:
                    content_items = parsed_content.get('content', [])
                    if isinstance(content_items, list):
                        for item in content_items:
                            if isinstance(item, dict):
                                # Look for image path fields
                                for key in ['path', 'file_path', 'image_path', 'filepath']:
                                    if key in item and isinstance(item[key], str):
                                        image_paths.append(item[key])
                                        break
                
                # Format 3: Top-level paths fields
                for key in ['paths', 'files', 'images', 'screenshots']:
                    if isinstance(parsed_content, dict) and key in parsed_content:
                        paths = parsed_content[key]
                        if isinstance(paths, list):
                            image_paths.extend([p for p in paths if isinstance(p, str)])
                        elif isinstance(paths, str):
                            image_paths.append(paths)
                
                # Validate and filter image paths
                valid_paths = []
                image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
                
                for path in image_paths:
                    if isinstance(path, str) and path.strip():
                        path = path.strip()
                        # Check if it's a valid image file
                        if (Path(path).suffix.lower() in image_extensions or
                            any(ext in path.lower() for ext in image_extensions)):
                            # Check if file exists
                            if os.path.isfile(path):
                                valid_paths.append(path)
                            else:
                                logger.warning(f"Image file not found: {path}")
                
                self.image_paths = valid_paths
                
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            logger.debug(f"Could not parse MCP content for image paths: {e}")
            # Keep image_paths as empty list if parsing fails

    def has_images(self) -> bool:
        """Check if this observation contains any image paths."""
        return bool(self.image_paths)

    def get_image_base64_data(self) -> list[dict[str, str]]:
        """Convert image paths to base64 data for LLM consumption.
        
        Returns:
            List of dictionaries with 'data' (base64) and 'path' (original path)
        """
        image_data = []
        
        for path in self.image_paths:
            try:
                if os.path.isfile(path):
                    with open(path, 'rb') as f:
                        image_bytes = f.read()
                        base64_data = base64.b64encode(image_bytes).decode('utf-8')
                        
                        # Determine MIME type based on extension
                        ext = Path(path).suffix.lower()
                        mime_map = {
                            '.png': 'image/png',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.gif': 'image/gif',
                            '.bmp': 'image/bmp',
                            '.webp': 'image/webp',
                            '.svg': 'image/svg+xml',
                            '.tiff': 'image/tiff',
                        }
                        mime_type = mime_map.get(ext, 'image/png')
                        
                        image_data.append({
                            'data': f'data:{mime_type};base64,{base64_data}',
                            'path': path,
                            'mime_type': mime_type
                        })
                        
            except Exception as e:
                logger.error(f"Failed to read image file {path}: {e}")
                
        return image_data

    @property
    def message(self) -> str:
        return self.content
