#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO工具打包脚本
使用PyInstaller打包为exe
支持直接使用JPG/PNG图片作为图标
"""

import os
import sys
import subprocess


def convert_image_to_icon(image_path, output_path='app.ico'):
    """将图片转换为ICO格式"""
    try:
        from PIL import Image
        
        # 打开图片
        img = Image.open(image_path)
        
        # 转换为RGBA模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 如果图片不是正方形，裁剪为正方形
        width, height = img.size
        if width != height:
            min_size = min(width, height)
            left = (width - min_size) // 2
            top = (height - min_size) // 2
            right = left + min_size
            bottom = top + min_size
            img = img.crop((left, top, right, bottom))
        
        # 生成多种尺寸的图标
        sizes = [16, 32, 48, 64, 128, 256]
        icons = []
        
        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            icons.append(resized)
        
        # 保存ICO文件
        icons[0].save(
            output_path,
            format='ICO',
            sizes=[(s, s) for s in sizes],
            append_images=icons[1:]
        )
        
        print(f"✓ 图片已转换为ICO: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"✗ 转换图标失败: {e}")
        return None


def get_icon_path(icon_path=None):
    """获取图标路径，支持自动转换图片格式
    
    Args:
        icon_path: 指定的图标路径
        
    Returns:
        ICO格式的图标路径，或None
    """
    if icon_path and os.path.exists(icon_path):
        ext = os.path.splitext(icon_path)[1].lower()
        
        # 如果已经是ICO格式，直接使用
        if ext == '.ico':
            return icon_path
        
        # 如果是图片格式，转换为ICO
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
            print(f"检测到图片格式 {ext}，正在转换为ICO...")
            temp_ico = 'temp_icon.ico'
            return convert_image_to_icon(icon_path, temp_ico)
        
        print(f"✗ 不支持的图标格式: {ext}")
        return None
    
    # 检查默认图标
    default_icons = ['app.ico', 'icon.ico', 'logo.ico']
    for icon in default_icons:
        if os.path.exists(icon):
            return icon
    
    return None


def build_exe(icon_path=None):
    """打包exe
    
    Args:
        icon_path: 图标文件路径（支持.ico, .jpg, .jpeg, .png, .bmp等格式）
    """
    
    # 处理图标
    ico_path = get_icon_path(icon_path)
    
    # 打包配置
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=YOLO数据处理工具',
        '--windowed',  # GUI应用，不显示控制台
        '--onefile',   # 打包成单个exe文件
        '--clean',     # 清理临时文件
        '--noconfirm', # 不确认覆盖
        
        # 添加数据文件
        '--add-data', 'yolo_tool.py;.',
        
        # 隐藏导入
        '--hidden-import', 'PyQt5.sip',
        '--hidden-import', 'PyQt5.QtCore',
        '--hidden-import', 'PyQt5.QtGui',
        '--hidden-import', 'PyQt5.QtWidgets',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.Image',
        
        # 主程序
        'yolo_tool.py'
    ]
    
    # 添加图标
    if ico_path:
        cmd.extend(['--icon', ico_path])
        print(f"使用图标: {ico_path}")
    
    print("开始打包...")
    print(f"命令: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd, capture_output=False)
    
    # 清理临时图标文件
    if icon_path and os.path.exists('temp_icon.ico'):
        os.remove('temp_icon.ico')
        print("已清理临时图标文件")
    
    if result.returncode == 0:
        print("-" * 50)
        print("✓ 打包成功!")
        print(f"exe文件位置: {os.path.abspath('dist/YOLO数据处理工具.exe')}")
    else:
        print("-" * 50)
        print("✗ 打包失败!")
        sys.exit(1)


def build_exe_folder(icon_path=None):
    """打包为文件夹形式（启动更快，文件更小）
    
    Args:
        icon_path: 图标文件路径（支持.ico, .jpg, .jpeg, .png, .bmp等格式）
    """
    
    # 处理图标
    ico_path = get_icon_path(icon_path)
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=YOLO数据处理工具',
        '--windowed',
        '--onedir',    # 打包为文件夹
        '--clean',
        '--noconfirm',
        
        '--hidden-import', 'PyQt5.sip',
        '--hidden-import', 'PyQt5.QtCore',
        '--hidden-import', 'PyQt5.QtGui',
        '--hidden-import', 'PyQt5.QtWidgets',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.Image',
        
        'yolo_tool.py'
    ]
    
    # 添加图标
    if ico_path:
        cmd.extend(['--icon', ico_path])
        print(f"使用图标: {ico_path}")
    
    print("开始打包（文件夹模式）...")
    print(f"命令: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd, capture_output=False)
    
    # 清理临时图标文件
    if icon_path and os.path.exists('temp_icon.ico'):
        os.remove('temp_icon.ico')
        print("已清理临时图标文件")
    
    if result.returncode == 0:
        print("-" * 50)
        print("✓ 打包成功!")
        print(f"程序文件夹: {os.path.abspath('dist/YOLO数据处理工具')}")
        print(f"启动文件: {os.path.abspath('dist/YOLO数据处理工具/YOLO数据处理工具.exe')}")
    else:
        print("-" * 50)
        print("✗ 打包失败!")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='打包YOLO工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用默认图标打包
  python build_exe.py --folder
  
  # 使用ICO图标打包
  python build_exe.py --folder --icon myicon.ico
  
  # 使用JPG/PNG图片打包（自动转换）
  python build_exe.py --folder --icon mylogo.png
  python build_exe.py --folder --icon photo.jpg
        """
    )
    
    parser.add_argument('--folder', action='store_true', 
                        help='打包为文件夹模式（推荐，启动更快）')
    parser.add_argument('--icon', type=str, 
                        help='指定图标文件路径（支持.ico, .jpg, .jpeg, .png, .bmp等格式）')
    args = parser.parse_args()
    
    if args.folder:
        build_exe_folder(args.icon)
    else:
        build_exe(args.icon)
