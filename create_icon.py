#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建应用程序图标
支持：
1. 自动生成图标（简单文字/YOLO风格）
2. 将本地JPG/PNG图片转换为ICO图标
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys


def image_to_icon(image_path, output_path='app.ico', sizes=None):
    """将图片转换为ICO图标
    
    Args:
        image_path: 输入图片路径（支持JPG、PNG、BMP等）
        output_path: 输出ICO路径
        sizes: 图标尺寸列表，默认 [16, 32, 48, 64, 128, 256]
    """
    if sizes is None:
        sizes = [16, 32, 48, 64, 128, 256]
    
    # 打开图片
    img = Image.open(image_path)
    
    # 转换为RGBA模式（支持透明）
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 如果图片不是正方形，裁剪为正方形（从中心）
    width, height = img.size
    if width != height:
        min_size = min(width, height)
        left = (width - min_size) // 2
        top = (height - min_size) // 2
        right = left + min_size
        bottom = top + min_size
        img = img.crop((left, top, right, bottom))
    
    # 生成多种尺寸的图标
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
    
    print(f"✓ 图标已转换: {os.path.abspath(output_path)}")
    print(f"  源文件: {image_path}")
    print(f"  尺寸: {sizes}")
    return output_path


def create_simple_icon(output_path='app.ico', size=256):
    """创建一个简单的图标"""
    
    # 创建图像
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制背景圆角矩形
    margin = size // 16
    bg_color = (76, 175, 80)  # 绿色
    
    # 绘制圆角矩形背景
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 8,
        fill=bg_color
    )
    
    # 绘制边框
    border_color = (56, 142, 60)  # 深绿色
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 8,
        outline=border_color,
        width=size // 32
    )
    
    # 绘制文字 "Y"
    try:
        # 尝试使用系统字体
        font_size = size // 2
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("msyh.ttc", font_size)
            except:
                font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    text = "Y"
    
    # 获取文字尺寸
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 计算居中位置
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - size // 16
    
    # 绘制文字阴影
    shadow_offset = size // 64
    draw.text((x + shadow_offset, y + shadow_offset), text, 
              font=font, fill=(0, 0, 0, 100))
    
    # 绘制主文字
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # 保存为多种尺寸的ICO
    icon_sizes = [16, 32, 48, 64, 128, 256]
    icons = []
    
    for icon_size in icon_sizes:
        resized = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        icons.append(resized)
    
    # 保存ICO文件
    icons[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in icon_sizes],
        append_images=icons[1:]
    )
    
    print(f"✓ 图标已创建: {os.path.abspath(output_path)}")
    return output_path


def create_yolo_icon(output_path='app.ico', size=256):
    """创建YOLO风格的图标 - 检测框样式"""
    
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 背景
    margin = size // 16
    bg_color = (33, 150, 243)  # 蓝色
    
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 8,
        fill=bg_color
    )
    
    # 绘制检测框
    box_margin = size // 4
    box_color = (255, 255, 255, 200)
    line_width = max(2, size // 32)
    
    # 外框
    draw.rectangle(
        [box_margin, box_margin, size - box_margin, size - box_margin],
        outline=box_color,
        width=line_width
    )
    
    # 角标（YOLO风格）
    corner_len = size // 8
    corner_color = (255, 193, 7)  # 黄色
    
    corners = [
        # 左上角
        [(box_margin, box_margin), (box_margin + corner_len, box_margin)],
        [(box_margin, box_margin), (box_margin, box_margin + corner_len)],
        # 右上角
        [(size - box_margin - corner_len, box_margin), (size - box_margin, box_margin)],
        [(size - box_margin, box_margin), (size - box_margin, box_margin + corner_len)],
        # 左下角
        [(box_margin, size - box_margin), (box_margin + corner_len, size - box_margin)],
        [(box_margin, size - box_margin - corner_len), (box_margin, size - box_margin)],
        # 右下角
        [(size - box_margin - corner_len, size - box_margin), (size - box_margin, size - box_margin)],
        [(size - box_margin, size - box_margin - corner_len), (size - box_margin, size - box_margin)],
    ]
    
    for line in corners:
        draw.line(line, fill=corner_color, width=line_width)
    
    # 保存为ICO
    icon_sizes = [16, 32, 48, 64, 128, 256]
    icons = []
    
    for icon_size in icon_sizes:
        resized = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        icons.append(resized)
    
    icons[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in icon_sizes],
        append_images=icons[1:]
    )
    
    print(f"✓ YOLO风格图标已创建: {os.path.abspath(output_path)}")
    return output_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='创建应用程序图标',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 从本地图片生成图标
  python create_icon.py --image mylogo.png
  python create_icon.py --image photo.jpg --output icon.ico
  
  # 自动生成图标
  python create_icon.py --style yolo
  python create_icon.py --style simple --output myicon.ico
        """
    )
    
    parser.add_argument('--image', type=str, 
                        help='使用本地图片作为图标（支持JPG、PNG、BMP等格式）')
    parser.add_argument('--style', choices=['simple', 'yolo'], default='yolo',
                        help='自动生成图标样式: simple=简单文字, yolo=检测框风格（默认）')
    parser.add_argument('--output', default='app.ico', help='输出文件名（默认: app.ico）')
    
    args = parser.parse_args()
    
    if args.image:
        # 使用本地图片
        if not os.path.exists(args.image):
            print(f"✗ 错误: 找不到图片文件 '{args.image}'")
            sys.exit(1)
        
        # 检查文件格式
        ext = os.path.splitext(args.image)[1].lower()
        supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
        
        if ext not in supported_formats:
            print(f"✗ 错误: 不支持的图片格式 '{ext}'")
            print(f"  支持的格式: {', '.join(supported_formats)}")
            sys.exit(1)
        
        print(f"正在转换图片: {args.image}")
        image_to_icon(args.image, args.output)
        
    else:
        # 自动生成图标
        if args.style == 'simple':
            create_simple_icon(args.output)
        else:
            create_yolo_icon(args.output)
    
    print("\n使用方法:")
    print(f"  1. 直接打包: python build_exe.py --folder")
    print(f"  2. 指定图标: python build_exe.py --folder --icon {args.output}")


if __name__ == "__main__":
    main()
