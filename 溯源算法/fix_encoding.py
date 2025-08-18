#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复编码问题的脚本
移除或替换可能导致编码问题的emoji字符
"""

import os
import re
from pathlib import Path

def fix_emoji_in_file(file_path):
    """修复文件中的emoji字符"""
    
    # emoji替换映射
    emoji_replacements = {
        '🌪️': '风暴',
        '🎯': '目标',
        '🔬': '分析',
        '📊': '图表',
        '🚀': '启动',
        '📈': '上升',
        '📉': '下降',
        '⭐': '星',
        '🎨': '图像',
        '🔧': '工具',
        '📋': '列表',
        '🎭': '面具',
        '🎪': '帐篷',
        '💡': '灯泡',
        '⚡': '闪电',
        '🌐': '网络',
        '🔍': '搜索',
        '💾': '保存',
        '🔄': '刷新',
        '📁': '文件夹',
        '📄': '文档',
        '🏆': '奖杯',
        '✅': '[完成]',
        '❌': '[错误]',
        '⚠️': '[警告]',
        '⏳': '[等待]',
        '🌀': '旋涡'
    }
    
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换emoji
        modified = False
        for emoji, replacement in emoji_replacements.items():
            if emoji in content:
                content = content.replace(emoji, replacement)
                modified = True
                print(f"  替换 {emoji} -> {replacement}")
        
        # 如果有修改，写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 已修复: {file_path}")
            return True
        else:
            print(f"- 无需修复: {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ 修复失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    
    print("开始修复编码问题...")
    print("=" * 50)
    
    # 需要检查的文件
    files_to_check = [
        "web_interface.py",
        "enhanced_pollution_tracing.py",
        "start_web.py",
        "start_demo.py",
        "enhanced_demo.py"
    ]
    
    current_dir = Path(__file__).parent
    fixed_count = 0
    
    for file_name in files_to_check:
        file_path = current_dir / file_name
        
        if file_path.exists():
            print(f"\n检查文件: {file_name}")
            if fix_emoji_in_file(file_path):
                fixed_count += 1
        else:
            print(f"文件不存在: {file_name}")
    
    print("\n" + "=" * 50)
    print(f"修复完成！共修复 {fixed_count} 个文件")
    print("现在可以尝试重新运行Web界面")

if __name__ == "__main__":
    main()
