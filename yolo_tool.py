#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO数据处理工具
功能：
1. YOLO标签批量替换
2. JSON转TXT（支持COCO、LabelMe格式）
3. 分割数据集转检测数据集
"""

import sys
import os
import json
import shutil
import re
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QFileDialog, QMessageBox,
    QTabWidget, QGroupBox, QGridLayout, QSpinBox, QComboBox, QProgressBar,
    QCheckBox, QListWidget, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon


class WorkerThread(QThread):
    """工作线程，用于执行耗时操作"""
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished_signal.emit(True, result)
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class YOLOLabelReplacer(QWidget):
    """YOLO标签批量替换工具"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 文件夹选择
        folder_group = QGroupBox("选择标签文件夹")
        folder_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("请选择包含YOLO标签文件的文件夹")
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(browse_btn)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # 替换规则
        rule_group = QGroupBox("替换规则")
        rule_layout = QGridLayout()

        rule_layout.addWidget(QLabel("旧标签ID:"), 0, 0)
        self.old_id = QSpinBox()
        self.old_id.setRange(0, 999)
        rule_layout.addWidget(self.old_id, 0, 1)

        rule_layout.addWidget(QLabel("新标签ID:"), 0, 2)
        self.new_id = QSpinBox()
        self.new_id.setRange(0, 999)
        rule_layout.addWidget(self.new_id, 0, 3)

        # 批量替换表格
        rule_layout.addWidget(QLabel("批量替换规则 (旧ID->新ID, 每行一个):"), 1, 0, 1, 4)
        self.batch_rules = QTextEdit()
        self.batch_rules.setPlaceholderText("例如:\n0->1\n1->2\n2->0")
        self.batch_rules.setMaximumHeight(100)
        rule_layout.addWidget(self.batch_rules, 2, 0, 1, 4)

        rule_group.setLayout(rule_layout)
        layout.addWidget(rule_group)

        # 选项
        options_group = QGroupBox("选项")
        options_layout = QVBoxLayout()
        self.backup_check = QCheckBox("替换前备份原文件")
        self.backup_check.setChecked(True)
        options_layout.addWidget(self.backup_check)
        self.preview_check = QCheckBox("仅预览，不实际替换")
        options_layout.addWidget(self.preview_check)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        preview_btn = QPushButton("预览替换")
        preview_btn.clicked.connect(self.preview_replace)
        replace_btn = QPushButton("执行替换")
        replace_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        replace_btn.clicked.connect(self.execute_replace)
        btn_layout.addWidget(preview_btn)
        btn_layout.addWidget(replace_btn)
        layout.addLayout(btn_layout)

        # 日志输出
        layout.addWidget(QLabel("操作日志:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        layout.addStretch()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择标签文件夹")
        if folder:
            self.folder_path.setText(folder)

    def log(self, message):
        self.log_output.append(message)

    def get_replace_rules(self):
        """获取替换规则字典"""
        rules = {}

        # 添加单行规则
        old = self.old_id.value()
        new = self.new_id.value()
        if old != new:
            rules[old] = new

        # 解析批量规则
        batch_text = self.batch_rules.toPlainText().strip()
        if batch_text:
            for line in batch_text.split('\n'):
                line = line.strip()
                if '->' in line:
                    parts = line.split('->')
                    if len(parts) == 2:
                        try:
                            old_val = int(parts[0].strip())
                            new_val = int(parts[1].strip())
                            rules[old_val] = new_val
                        except ValueError:
                            continue
        return rules

    def preview_replace(self):
        folder = self.folder_path.text()
        if not folder or not os.path.exists(folder):
            QMessageBox.warning(self, "警告", "请选择有效的文件夹")
            return

        rules = self.get_replace_rules()
        if not rules:
            QMessageBox.warning(self, "警告", "请设置替换规则")
            return

        self.log("=" * 50)
        self.log("预览替换结果:")
        self.log(f"替换规则: {rules}")

        txt_files = list(Path(folder).glob("*.txt"))
        total_files = len(txt_files)
        affected_files = 0
        total_changes = 0

        for txt_file in txt_files:
            changes_in_file = 0
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line in lines:
                    parts = line.strip().split()
                    if parts:
                        try:
                            class_id = int(parts[0])
                            if class_id in rules:
                                changes_in_file += 1
                                total_changes += 1
                        except ValueError:
                            continue

                if changes_in_file > 0:
                    affected_files += 1
                    self.log(f"  {txt_file.name}: {changes_in_file} 处需要替换")

            except Exception as e:
                self.log(f"  {txt_file.name}: 读取失败 - {e}")

        self.log(f"\n总计: {total_files} 个文件, {affected_files} 个文件需要修改, {total_changes} 处替换")

    def execute_replace(self):
        folder = self.folder_path.text()
        if not folder or not os.path.exists(folder):
            QMessageBox.warning(self, "警告", "请选择有效的文件夹")
            return

        rules = self.get_replace_rules()
        if not rules:
            QMessageBox.warning(self, "警告", "请设置替换规则")
            return

        if self.preview_check.isChecked():
            self.preview_replace()
            return

        reply = QMessageBox.question(
            self, "确认",
            f"确定要执行替换吗？\n规则: {rules}\n文件夹: {folder}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.log("=" * 50)
        self.log("开始执行替换...")

        backup_folder = None
        if self.backup_check.isChecked():
            backup_folder = os.path.join(folder, "backup_" + str(int(os.path.getctime(folder))))
            os.makedirs(backup_folder, exist_ok=True)
            self.log(f"备份文件夹: {backup_folder}")

        txt_files = list(Path(folder).glob("*.txt"))
        total_files = len(txt_files)
        processed_files = 0
        modified_files = 0
        total_changes = 0

        for txt_file in txt_files:
            try:
                # 备份
                if backup_folder:
                    shutil.copy2(txt_file, backup_folder)

                with open(txt_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                new_lines = []
                changes_in_file = 0

                for line in lines:
                    parts = line.strip().split()
                    if parts:
                        try:
                            class_id = int(parts[0])
                            if class_id in rules:
                                parts[0] = str(rules[class_id])
                                changes_in_file += 1
                                total_changes += 1
                            new_lines.append(' '.join(parts))
                        except ValueError:
                            new_lines.append(line.strip())
                    else:
                        new_lines.append(line.strip())

                if changes_in_file > 0:
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines) + '\n')
                    modified_files += 1
                    self.log(f"  已修改: {txt_file.name} ({changes_in_file} 处)")

                processed_files += 1

            except Exception as e:
                self.log(f"  错误: {txt_file.name} - {e}")

        self.log(f"\n完成! 处理了 {processed_files} 个文件, 修改了 {modified_files} 个文件, 共 {total_changes} 处替换")
        QMessageBox.information(self, "完成", f"替换完成!\n处理了 {processed_files} 个文件\n修改了 {modified_files} 个文件\n共 {total_changes} 处替换")


class JSONToTXTConverter(QWidget):
    """JSON转TXT转换器"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 输入文件夹
        input_group = QGroupBox("输入设置")
        input_layout = QGridLayout()

        input_layout.addWidget(QLabel("JSON文件夹:"), 0, 0)
        self.json_folder = QLineEdit()
        self.json_folder.setPlaceholderText("包含JSON文件的文件夹")
        json_browse = QPushButton("浏览...")
        json_browse.clicked.connect(self.browse_json_folder)
        input_layout.addWidget(self.json_folder, 0, 1)
        input_layout.addWidget(json_browse, 0, 2)

        input_layout.addWidget(QLabel("图片文件夹:"), 1, 0)
        self.img_folder = QLineEdit()
        self.img_folder.setPlaceholderText("对应的图片文件夹（用于获取尺寸）")
        img_browse = QPushButton("浏览...")
        img_browse.clicked.connect(self.browse_img_folder)
        input_layout.addWidget(self.img_folder, 1, 1)
        input_layout.addWidget(img_browse, 1, 2)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QGridLayout()

        output_layout.addWidget(QLabel("输出文件夹:"), 0, 0)
        self.output_folder = QLineEdit()
        self.output_folder.setPlaceholderText("YOLO格式TXT输出文件夹")
        output_browse = QPushButton("浏览...")
        output_browse.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(self.output_folder, 0, 1)
        output_layout.addWidget(output_browse, 0, 2)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # 格式选择
        format_group = QGroupBox("JSON格式")
        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["LabelMe", "COCO", "自定义"])
        format_layout.addWidget(self.format_combo)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # 类别映射
        class_group = QGroupBox("类别映射 (可选)")
        class_layout = QVBoxLayout()
        self.class_map = QTextEdit()
        self.class_map.setPlaceholderText("格式: 类别名->ID\n例如:\ncar->0\nperson->1\ndog->2")
        self.class_map.setMaximumHeight(100)
        class_layout.addWidget(self.class_map)
        class_group.setLayout(class_layout)
        layout.addWidget(class_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        convert_btn = QPushButton("开始转换")
        convert_btn.setStyleSheet("background-color: #2196F3; color: white;")
        convert_btn.clicked.connect(self.start_convert)
        btn_layout.addStretch()
        btn_layout.addWidget(convert_btn)
        layout.addLayout(btn_layout)

        # 日志
        layout.addWidget(QLabel("转换日志:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        layout.addStretch()

    def browse_json_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择JSON文件夹")
        if folder:
            self.json_folder.setText(folder)

    def browse_img_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            self.img_folder.setText(folder)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder.setText(folder)

    def log(self, message):
        self.log_output.append(message)

    def get_class_map(self):
        """解析类别映射"""
        class_map = {}
        text = self.class_map.toPlainText().strip()
        if text:
            for line in text.split('\n'):
                line = line.strip()
                if '->' in line:
                    parts = line.split('->')
                    if len(parts) == 2:
                        class_name = parts[0].strip()
                        try:
                            class_id = int(parts[1].strip())
                            class_map[class_name] = class_id
                        except ValueError:
                            continue
        return class_map

    def convert_labelme(self, json_file, img_folder, class_map):
        """转换LabelMe格式"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 获取图片尺寸
        img_name = data.get('imagePath', '')
        img_width = data.get('imageWidth', 0)
        img_height = data.get('imageHeight', 0)

        if img_width == 0 or img_height == 0:
            # 尝试从图片文件获取
            from PIL import Image
            img_path = os.path.join(img_folder, img_name)
            if os.path.exists(img_path):
                with Image.open(img_path) as img:
                    img_width, img_height = img.size

        if img_width == 0 or img_height == 0:
            raise ValueError(f"无法获取图片尺寸: {img_name}")

        yolo_lines = []
        shapes = data.get('shapes', [])

        for shape in shapes:
            label = shape.get('label', '')
            points = shape.get('points', [])
            shape_type = shape.get('shape_type', 'polygon')

            # 获取类别ID
            if label in class_map:
                class_id = class_map[label]
            else:
                # 自动分配ID
                if label not in class_map:
                    class_map[label] = len(class_map)
                class_id = class_map[label]

            if shape_type == 'rectangle' and len(points) == 2:
                # 矩形框
                x1, y1 = points[0]
                x2, y2 = points[1]
                x_center = (x1 + x2) / 2 / img_width
                y_center = (y1 + y2) / 2 / img_height
                width = abs(x2 - x1) / img_width
                height = abs(y2 - y1) / img_height

            elif shape_type in ['polygon', 'linestrip'] and len(points) >= 3:
                # 多边形转bbox
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                x1, x2 = min(xs), max(xs)
                y1, y2 = min(ys), max(ys)
                x_center = (x1 + x2) / 2 / img_width
                y_center = (y1 + y2) / 2 / img_height
                width = (x2 - x1) / img_width
                height = (y2 - y1) / img_height
            else:
                continue

            # 限制在0-1范围内
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))
            width = max(0, min(1, width))
            height = max(0, min(1, height))

            yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

        return yolo_lines, class_map

    def convert_coco(self, json_file, class_map):
        """转换COCO格式"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # COCO通常是单个文件包含所有标注
        images = {img['id']: img for img in data.get('images', [])}
        categories = {cat['id']: cat['name'] for cat in data.get('categories', [])}
        annotations = data.get('annotations', [])

        # 按图片分组
        img_annotations = {}
        for ann in annotations:
            img_id = ann['image_id']
            if img_id not in img_annotations:
                img_annotations[img_id] = []
            img_annotations[img_id].append(ann)

        results = {}

        for img_id, img_info in images.items():
            img_name = img_info['file_name']
            img_width = img_info['width']
            img_height = img_info['height']

            yolo_lines = []
            anns = img_annotations.get(img_id, [])

            for ann in anns:
                cat_id = ann['category_id']
                cat_name = categories.get(cat_id, str(cat_id))

                # 获取类别ID
                if cat_name in class_map:
                    class_id = class_map[cat_name]
                else:
                    if cat_name not in class_map:
                        class_map[cat_name] = len(class_map)
                    class_id = class_map[cat_name]

                bbox = ann['bbox']  # [x, y, width, height]
                x, y, w, h = bbox

                x_center = (x + w / 2) / img_width
                y_center = (y + h / 2) / img_height
                width = w / img_width
                height = h / img_height

                # 限制在0-1范围内
                x_center = max(0, min(1, x_center))
                y_center = max(0, min(1, y_center))
                width = max(0, min(1, width))
                height = max(0, min(1, height))

                yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

            base_name = os.path.splitext(img_name)[0]
            results[base_name] = yolo_lines

        return results, class_map

    def start_convert(self):
        json_folder = self.json_folder.text()
        img_folder = self.img_folder.text()
        output_folder = self.output_folder.text()
        format_type = self.format_combo.currentText()

        if not json_folder or not os.path.exists(json_folder):
            QMessageBox.warning(self, "警告", "请选择有效的JSON文件夹")
            return

        if not output_folder:
            QMessageBox.warning(self, "警告", "请选择输出文件夹")
            return

        os.makedirs(output_folder, exist_ok=True)

        class_map = self.get_class_map()
        self.log("=" * 50)
        self.log(f"开始转换 - 格式: {format_type}")
        self.log(f"JSON文件夹: {json_folder}")
        self.log(f"输出文件夹: {output_folder}")

        try:
            if format_type == "COCO":
                # COCO通常是单个文件
                json_files = list(Path(json_folder).glob("*.json"))
                if not json_files:
                    QMessageBox.warning(self, "警告", "未找到JSON文件")
                    return

                # 使用第一个找到的JSON文件
                json_file = json_files[0]
                self.log(f"处理COCO文件: {json_file}")

                results, class_map = self.convert_coco(str(json_file), class_map)

                for base_name, lines in results.items():
                    output_file = os.path.join(output_folder, f"{base_name}.txt")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    self.log(f"  已生成: {base_name}.txt ({len(lines)} 个目标)")

            else:  # LabelMe或其他
                json_files = list(Path(json_folder).glob("*.json"))
                total = len(json_files)
                processed = 0

                for json_file in json_files:
                    try:
                        yolo_lines, class_map = self.convert_labelme(
                            str(json_file), img_folder, class_map
                        )

                        base_name = json_file.stem
                        output_file = os.path.join(output_folder, f"{base_name}.txt")

                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(yolo_lines))

                        processed += 1
                        self.log(f"  已转换: {json_file.name} -> {base_name}.txt ({len(yolo_lines)} 个目标)")

                    except Exception as e:
                        self.log(f"  错误: {json_file.name} - {e}")

                self.log(f"\n完成! 成功转换 {processed}/{total} 个文件")

            # 保存类别映射
            if class_map:
                class_file = os.path.join(output_folder, "classes.txt")
                with open(class_file, 'w', encoding='utf-8') as f:
                    for name, idx in sorted(class_map.items(), key=lambda x: x[1]):
                        f.write(f"{idx}: {name}\n")
                self.log(f"类别映射已保存到: {class_file}")

            QMessageBox.information(self, "完成", "转换完成!")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"转换失败: {e}")
            self.log(f"错误: {e}")


class SegToDetConverter(QWidget):
    """分割数据集转检测数据集"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 输入设置
        input_group = QGroupBox("输入设置")
        input_layout = QGridLayout()

        input_layout.addWidget(QLabel("分割标签文件夹:"), 0, 0)
        self.seg_folder = QLineEdit()
        self.seg_folder.setPlaceholderText("包含分割标签的文件夹")
        seg_browse = QPushButton("浏览...")
        seg_browse.clicked.connect(self.browse_seg_folder)
        input_layout.addWidget(self.seg_folder, 0, 1)
        input_layout.addWidget(seg_browse, 0, 2)

        input_layout.addWidget(QLabel("图片文件夹:"), 1, 0)
        self.img_folder = QLineEdit()
        self.img_folder.setPlaceholderText("对应的图片文件夹")
        img_browse = QPushButton("浏览...")
        img_browse.clicked.connect(self.browse_img_folder)
        input_layout.addWidget(self.img_folder, 1, 1)
        input_layout.addWidget(img_browse, 1, 2)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QGridLayout()

        output_layout.addWidget(QLabel("输出文件夹:"), 0, 0)
        self.output_folder = QLineEdit()
        self.output_folder.setPlaceholderText("检测格式标签输出文件夹")
        output_browse = QPushButton("浏览...")
        output_browse.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(self.output_folder, 0, 1)
        output_layout.addWidget(output_browse, 0, 2)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # 分割格式选择
        format_group = QGroupBox("分割标签格式")
        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["YOLO分割格式", "COCO分割格式", "Mask图像"])
        format_layout.addWidget(self.format_combo)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # 选项
        options_group = QGroupBox("转换选项")
        options_layout = QVBoxLayout()
        self.normalize_check = QCheckBox("归一化坐标 (0-1)")
        self.normalize_check.setChecked(True)
        options_layout.addWidget(self.normalize_check)
        self.bbox_format = QComboBox()
        self.bbox_format.addItems(["xywh (中心点+宽高)", "xyxy (左上角+右下角)"])
        options_layout.addWidget(QLabel("边界框格式:"))
        options_layout.addWidget(self.bbox_format)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        convert_btn = QPushButton("开始转换")
        convert_btn.setStyleSheet("background-color: #FF9800; color: white;")
        convert_btn.clicked.connect(self.start_convert)
        btn_layout.addStretch()
        btn_layout.addWidget(convert_btn)
        layout.addLayout(btn_layout)

        # 日志
        layout.addWidget(QLabel("转换日志:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        layout.addStretch()

    def browse_seg_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择分割标签文件夹")
        if folder:
            self.seg_folder.setText(folder)

    def browse_img_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            self.img_folder.setText(folder)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder.setText(folder)

    def log(self, message):
        self.log_output.append(message)

    def polygon_to_bbox(self, points):
        """从多边形点计算边界框"""
        if not points:
            return None

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        return x_min, y_min, x_max, y_max

    def convert_yolo_seg(self, seg_file, img_width, img_height):
        """转换YOLO分割格式到检测格式"""
        yolo_lines = []

        with open(seg_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 5:
                continue

            try:
                class_id = int(parts[0])
                # 分割格式: class_id x1 y1 x2 y2 x3 y3 ...
                coords = [float(p) for p in parts[1:]]

                # 还原为像素坐标
                points = []
                for i in range(0, len(coords), 2):
                    x = coords[i] * img_width
                    y = coords[i + 1] * img_height
                    points.append((x, y))

                # 计算边界框
                bbox = self.polygon_to_bbox(points)
                if bbox:
                    x_min, y_min, x_max, y_max = bbox

                    if self.normalize_check.isChecked():
                        x_center = (x_min + x_max) / 2 / img_width
                        y_center = (y_min + y_max) / 2 / img_height
                        width = (x_max - x_min) / img_width
                        height = (y_max - y_min) / img_height
                    else:
                        x_center = (x_min + x_max) / 2
                        y_center = (y_min + y_max) / 2
                        width = x_max - x_min
                        height = y_max - y_min

                    yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

            except (ValueError, IndexError):
                continue

        return yolo_lines

    def start_convert(self):
        seg_folder = self.seg_folder.text()
        img_folder = self.img_folder.text()
        output_folder = self.output_folder.text()
        format_type = self.format_combo.currentText()

        if not seg_folder or not os.path.exists(seg_folder):
            QMessageBox.warning(self, "警告", "请选择有效的分割标签文件夹")
            return

        if not output_folder:
            QMessageBox.warning(self, "警告", "请选择输出文件夹")
            return

        os.makedirs(output_folder, exist_ok=True)

        self.log("=" * 50)
        self.log(f"开始转换 - 格式: {format_type}")
        self.log(f"分割标签文件夹: {seg_folder}")
        self.log(f"输出文件夹: {output_folder}")

        try:
            from PIL import Image

            seg_files = list(Path(seg_folder).glob("*.txt"))
            total = len(seg_files)
            processed = 0

            for seg_file in seg_files:
                try:
                    # 获取对应的图片尺寸
                    base_name = seg_file.stem
                    img_file = None

                    # 尝试常见图片格式
                    for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                        temp_img = os.path.join(img_folder, base_name + ext)
                        if os.path.exists(temp_img):
                            img_file = temp_img
                            break

                    if not img_file:
                        self.log(f"  跳过: {seg_file.name} - 未找到对应图片")
                        continue

                    with Image.open(img_file) as img:
                        img_width, img_height = img.size

                    if format_type == "YOLO分割格式":
                        yolo_lines = self.convert_yolo_seg(str(seg_file), img_width, img_height)
                    else:
                        self.log(f"  跳过: {seg_file.name} - 暂不支持的格式")
                        continue

                    # 保存检测格式标签
                    output_file = os.path.join(output_folder, f"{base_name}.txt")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(yolo_lines))

                    processed += 1
                    self.log(f"  已转换: {seg_file.name} -> {base_name}.txt ({len(yolo_lines)} 个目标)")

                except Exception as e:
                    self.log(f"  错误: {seg_file.name} - {e}")

            self.log(f"\n完成! 成功转换 {processed}/{total} 个文件")
            QMessageBox.information(self, "完成", f"转换完成!\n成功转换 {processed}/{total} 个文件")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"转换失败: {e}")
            self.log(f"错误: {e}")


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO数据处理工具 v1.0")
        self.setGeometry(100, 100, 900, 700)

        # 设置窗口图标
        self.set_window_icon()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("YOLO数据处理工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 创建标签页
        self.tabs = QTabWidget()

        # 标签替换页
        self.replacer = YOLOLabelReplacer()
        self.tabs.addTab(self.replacer, "标签批量替换")

        # JSON转TXT页
        self.converter = JSONToTXTConverter()
        self.tabs.addTab(self.converter, "JSON转TXT")

        # 分割转检测页
        self.seg_to_det = SegToDetConverter()
        self.tabs.addTab(self.seg_to_det, "分割转检测")

        layout.addWidget(self.tabs)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def set_window_icon(self):
        """设置窗口图标"""
        # 尝试多种方式设置图标
        icon_paths = [
            'app.ico',
            'icon.ico',
            'logo.ico',
            os.path.join(os.path.dirname(sys.executable), 'app.ico'),
            os.path.join(os.path.dirname(__file__), 'app.ico'),
        ]

        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置应用程序样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QPushButton {
            padding: 5px 15px;
            border: 1px solid #999;
            border-radius: 3px;
            background-color: #e0e0e0;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QTextEdit {
            border: 1px solid #ccc;
            border-radius: 3px;
        }
        QLineEdit {
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
