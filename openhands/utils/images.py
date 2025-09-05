import os
from pathlib import Path
from typing import List, Tuple

# 在文件顶部添加图像相关常量
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
DEFAULT_IMAGE_FOLDER = 'images'  # 默认图像文件夹名称

def get_workspace_images(workspace_path: str, image_folder: str = DEFAULT_IMAGE_FOLDER) -> List[str]:
    """获取工作区指定文件夹中的所有图像文件。
    
    Args:
        workspace_path: 工作区路径
        image_folder: 图像文件夹名称
        
    Returns:
        图像文件路径列表
    """
    image_folder_path = Path(workspace_path) / image_folder
    image_files = []
    
    if image_folder_path.exists() and image_folder_path.is_dir():
        for file_path in image_folder_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                image_files.append(str(file_path))
    
    return sorted(image_files)

def create_image_analysis_prompt(image_files: List[str]) -> str:
    """为图像文件创建分析提示。
    
    Args:
        image_files: 图像文件路径列表
        
    Returns:
        包含图像分析指令的提示文本
    """
    if not image_files:
        return ""
    
    prompt_parts = [
        "Please analyze the following images before proceeding:",
        ""
    ]
    
    for i, image_path in enumerate(image_files, 1):
        filename = Path(image_path).name
        prompt_parts.append(f"{i}. {filename} (path: {image_path})")
        prompt_parts.append(f"   Analysis: parse_image('{image_path}', 'Describe this image in detail and identify any relevant information for the current task.')")
        prompt_parts.append("")
    
    return "\n".join(prompt_parts)