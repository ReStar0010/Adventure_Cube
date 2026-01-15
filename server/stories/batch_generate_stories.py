#!/usr/bin/env python3
"""
批次生成故事腳本 - 為四個主題各生成 2 個故事
Batch story generator - generates 2 stories for each of 4 themes
"""
import os
import shutil
from short_story_generator import main as generate_story

# 四個主題
THEMES = [
    "adventure comdey",
    "Sharing",
    "Bed Time",
    "Nature"
]

# 每個主題生成的故事數量
STORIES_PER_THEME = 2

# 輸出文件夾
OUTPUT_FOLDER = "generated_stories"


def batch_generate():
    """批次生成所有故事"""
    # 創建輸出文件夾
    if os.path.exists(OUTPUT_FOLDER):
        shutil.rmtree(OUTPUT_FOLDER)
    os.makedirs(OUTPUT_FOLDER)
    
    print(f"\n{'='*80}")
    print(f"🚀 開始批次生成故事")
    print(f"   主題數量: {len(THEMES)}")
    print(f"   每個主題: {STORIES_PER_THEME} 個故事")
    print(f"   總計: {len(THEMES) * STORIES_PER_THEME} 個故事")
    print(f"{'='*80}\n")
    
    # 為每個主題生成故事
    for theme in THEMES:
        print(f"\n📚 處理主題: {theme}")
        print("-" * 80)
        
        for i in range(1, STORIES_PER_THEME + 1):
            print(f"\n  生成第 {i}/{STORIES_PER_THEME} 個故事...")
            
            # 生成故事（會保存到當前目錄）
            generate_story(theme)
            
            # 移動並重命名文件
            old_filename = f"story_{theme.replace(' ', '_')}.txt"
            new_filename = f"{theme.replace(' ', '_')}_{i:02d}.txt"
            old_path = old_filename
            new_path = os.path.join(OUTPUT_FOLDER, new_filename)
            
            if os.path.exists(old_path):
                shutil.move(old_path, new_path)
                print(f"  ✓ 已保存: {new_path}")
            else:
                print(f"  ⚠️  警告: 找不到生成的文件 {old_path}")
    
    print(f"\n{'='*80}")
    print(f"✨ 完成! 所有故事已保存至: {OUTPUT_FOLDER}/")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    batch_generate()


