# YOLO数据处理工具

一个基于PyQt5开发的YOLO数据集处理工具，提供图形化界面，支持标签批量替换、JSON格式转换、分割数据集转检测数据集等功能。

## 功能特性

### 1. 标签批量替换
- 支持批量替换YOLO标签文件中的类别ID
- 支持单条规则和批量规则
- 替换前自动备份原文件
- 支持预览模式，查看替换效果

### 2. JSON转TXT
- 支持LabelMe格式转换为YOLO格式
- 支持COCO格式转换为YOLO格式
- 自动获取图片尺寸信息
- 支持自定义类别映射
- 自动生成类别文件

### 3. 分割转检测
- 将YOLO分割格式（多边形）转换为检测格式（边界框）
- 自动计算多边形外接矩形
- 支持归一化坐标输出

## 快速开始

### 环境要求
- Python 3.8+
- PyQt5
- Pillow

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python yolo_tool.py
```

## 打包为EXE

### 方式一：使用默认图标打包

```bash
python build_exe.py --folder
```

### 方式二：使用自定义图标打包

支持直接使用JPG、PNG等图片作为图标：

```bash
# 使用JPG图片
python build_exe.py --folder --icon mylogo.jpg

# 使用PNG图片
python build_exe.py --folder --icon mylogo.png

# 使用ICO图标
python build_exe.py --folder --icon myicon.ico
```

### 方式三：生成图标后打包

```bash
# 从图片生成ICO图标
python create_icon.py --image mylogo.png --output app.ico

# 打包（自动使用app.ico）
python build_exe.py --folder
```

打包完成后，可执行文件位于 `dist/YOLO数据处理工具/` 目录下。

## 使用说明

### 标签批量替换

1. 选择包含YOLO标签文件（.txt）的文件夹
2. 设置替换规则：
   - **单条规则**：在"旧标签ID"和"新标签ID"中输入对应值
   - **批量规则**：在文本框中每行输入一个规则，格式为 `旧ID->新ID`
3. 选择是否备份原文件
4. 点击"预览替换"查看效果
5. 点击"执行替换"完成操作

**示例规则：**
```
0->1
1->2
2->0
```

### JSON转TXT

1. 选择JSON文件所在文件夹
2. 选择对应的图片文件夹（用于获取尺寸）
3. 选择输出文件夹
4. 选择JSON格式（LabelMe或COCO）
5. （可选）设置类别映射
6. 点击"开始转换"

**类别映射格式：**
```
car->0
person->1
dog->2
```

### 分割转检测

1. 选择分割标签文件夹
2. 选择对应的图片文件夹
3. 选择输出文件夹
4. 选择分割标签格式
5. 设置转换选项
6. 点击"开始转换"

## 项目结构

```
all_yolo_tool/
├── yolo_tool.py          # 主程序源代码
├── build_exe.py          # 打包脚本
├── create_icon.py        # 图标生成工具
├── requirements.txt      # 依赖文件
├── README.md             # 本文件
└── dist/                 # 打包输出目录
    └── YOLO数据处理工具/
        └── YOLO数据处理工具.exe
```

## 详细功能说明

### YOLO标签格式

工具处理的标准YOLO标签格式：
```
<class_id> <x_center> <y_center> <width> <height>
```

所有数值均为0-1之间的归一化值。

### 支持的JSON格式

#### LabelMe格式
```json
{
  "imagePath": "image.jpg",
  "imageWidth": 1920,
  "imageHeight": 1080,
  "shapes": [
    {
      "label": "person",
      "shape_type": "rectangle",
      "points": [[x1, y1], [x2, y2]]
    }
  ]
}
```

#### COCO格式
```json
{
  "images": [...],
  "annotations": [...],
  "categories": [...]
}
```

## 常见问题

### Q: 打包后的程序无法运行？
A: 请确保：
1. 使用正确的Python环境
2. 已安装所有依赖
3. 使用 `--folder` 模式打包更稳定

### Q: 如何更换程序图标？
A: 有三种方式：
1. 打包时使用 `--icon` 参数指定图片
2. 使用 `create_icon.py` 生成ICO后打包
3. 将图片命名为 `app.ico` 放在项目根目录

### Q: 支持哪些图片格式作为图标？
A: 支持 JPG、JPEG、PNG、BMP、GIF、TIFF、WebP 等常见格式。

### Q: 转换后的标签文件在哪里？
A: 在输出文件夹中，与原文件同名，扩展名为 `.txt`。

## 更新日志

### v1.0.0
- 初始版本发布
- 实现标签批量替换功能
- 实现JSON转TXT功能
- 实现分割转检测功能
- 支持打包为EXE
- 支持自定义图标

## 许可证

MIT License

## 作者

YOLO数据处理工具开发团队

---

如有问题或建议，欢迎提交Issue或Pull Request。
