#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腳本：將故事文件中的中國用語替換為台灣用語
讀取 server/stories/generated_stories/ 目錄下的所有 .txt 文件並進行替換
"""

import os
import sys
from pathlib import Path

# 確保輸出編碼正確（Windows 環境）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 中國用語 -> 台灣用語對照表
REPLACEMENT_MAP = {
    # 自然/植物相關 (針對 3-5 歲兒童優化)
    '花骨朵': '花苞',
    '花蕾': '花苞',
    '土豆': '馬鈴薯',
    '西蘭花': '花椰菜',
    '獼猴桃': '奇異果',
    '菠蘿': '鳳梨',
    '燕麥片': '麥片',
    '黃瓜': '小黃瓜',
    '蟬': '知了', # 台灣童書兩者皆有，但「知了」更具狀聲效果

    # 科技/數位相關 (避免學術冷冰冰，轉為台灣生活用語)
    '視頻': '影片', 
    '屏幕': '螢幕', 
    '信息': '訊息', 
    '短信': '簡訊',
    '軟件': '軟體', 
    '硬件': '硬體', 
    '打印': '列印', 
    '複印': '影印',
    '硬盤': '硬碟',
    '內存': '記憶體',
    '光盤': '光碟',
    'U盤': '隨身碟',
    '網絡': '網路',
    '鼠標': '滑鼠',
    '激活': '啟動', 
    '程序': '程式',
    '數據': '資料',
    '人工智能': '人工智慧',
    '充電寶': '行動電源',
    '數據線': '傳輸線',

    # 日常生活/交通/稱呼
    '質量': '品質', 
    '水平': '水準',
    '立馬': '立刻', 
    '早上好': '早安',
    '晚上好': '晚安',
    '合同': '合約',
    '公交車': '公車',
    '出租車': '計程車',
    '地鐵': '捷運',
    '盒飯': '便當',
    '方便麵': '泡麵',
    '愛人': '先生/太太',
    '姥姥': '外婆',
    '姥爺': '外公',
    '幼兒園': '幼兒園', # 台灣目前統一使用幼兒園，早期為幼稚園
    '小學': '國小',
    '中學': '國中',

    # 幽默/情緒/形容詞 (提升反差喜劇效果)
    '給力': '厲害',
    '牛逼': '超強', # 童書禁止，但對照表需列出以防誤用
    '靠譜': '可靠',
    '忽悠': '唬弄',
    '貓膩': '鬼胎',
    '特質': '個性', # 針對 3-5 歲更白話
    '奇思妙想': '天馬行空',
}

def replace_terms_in_text(text: str) -> str:
    """
    在文本中替換中國用語為台灣用語
    
    Args:
        text: 原始文本
        
    Returns:
        替換後的文本
    """
    result = text
    for cn_term, tw_term in REPLACEMENT_MAP.items():
        result = result.replace(cn_term, tw_term)
    return result

def process_story_files(directory: str):
    """
    處理目錄下的所有 .txt 文件
    
    Args:
        directory: 故事文件目錄路徑
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"錯誤：目錄不存在 - {directory}")
        return
    
    # 獲取所有 .txt 文件
    txt_files = list(dir_path.glob("*.txt"))
    
    if not txt_files:
        print(f"在 {directory} 中沒有找到 .txt 文件")
        return
    
    print(f"找到 {len(txt_files)} 個故事文件")
    print("-" * 50)
    
    total_replacements = 0
    
    for txt_file in txt_files:
        try:
            # 讀取文件內容
            with open(txt_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 執行替換
            new_content = replace_terms_in_text(original_content)
            
            # 計算替換次數
            replacements = 0
            for cn_term, tw_term in REPLACEMENT_MAP.items():
                count = original_content.count(cn_term)
                if count > 0:
                    replacements += count
                    print(f"  {txt_file.name}: 替換 '{cn_term}' -> '{tw_term}' ({count} 次)")
            
            # 如果有替換，寫回文件
            if new_content != original_content:
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                total_replacements += replacements
                print(f"  [OK] {txt_file.name} 已更新")
            else:
                print(f"  [-] {txt_file.name} 無需更新")
                
        except Exception as e:
            print(f"  [ERROR] 處理 {txt_file.name} 時發生錯誤: {e}")
        
        print()
    
    print("-" * 50)
    print(f"完成！總共進行了 {total_replacements} 次替換")

if __name__ == "__main__":
    # 獲取腳本所在目錄
    script_dir = Path(__file__).parent
    stories_dir = script_dir / "generated_stories"
    
    print("開始處理故事文件...")
    print(f"目標目錄: {stories_dir}")
    print()
    
    process_story_files(str(stories_dir))

