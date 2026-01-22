#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story Filter Script
Filters and cleans story files in the specified directories.
"""

import os
import re
from pathlib import Path
import sys


def extract_story_content(content):
    """
    抽取「故事正文」並清理標記。
    
    1. 刪除 [Story Start] 和 [Story End] 標記
    2. 移除 setup/logic 區塊（如 [Story Setup]、[Story Logic Setup]、條列 * / 引用 >）
    3. 保留字數註記（不刪除 "(約..字)"）
    
    Args:
        content: Original file content
        
    Returns:
        Cleaned story content
    """
    if not content:
        return ""
    
    # Normalize newlines for consistent regex behavior
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    
    # 刪除 [Story Start] 和 [Story End] 標記（整行）
    text = re.sub(r'(?mi)^\s*\[Story Start\]\s*$', '', text)
    text = re.sub(r'(?mi)^\s*\[Story End\]\s*$', '', text)
    
    story_content = text.strip()
    if not story_content:
        return ""
    
    def _is_metadata_line(line: str) -> bool:
        s = (line or "").strip()
        if not s:
            return True
        
        # Markdown-ish setup headers frequently used before the actual narrative
        # Examples:
        # **[Story Logic Setup]**
        # [Story Setup]
        if re.match(r'^\*{0,2}\[[^\]]+\]\*{0,2}$', s):
            return True
        
        # Blockquote/list/bullets that usually describe logic/setup, not narrative
        # Examples:
        # * **Co-op Mode**: ...
        # > * **Prop Backfire**: ...
        if s.startswith(">"):
            return True
        if re.match(r'^[-*]\s+', s):
            return True
        
        # Common setup headings (even without brackets)
        lower = s.lower()
        if "story logic setup" in lower or "story setup" in lower:
            return True
        
        return False
    
    # Drop leading metadata/setup lines until we hit the first narrative line.
    lines = story_content.split("\n")
    i = 0
    while i < len(lines) and _is_metadata_line(lines[i]):
        i += 1
    story_content = "\n".join(lines[i:]).strip()
    
    # 不再刪除字數註記，保留 "(約..字)" 等格式
    
    return story_content.strip()


def count_chinese_characters(text):
    """
    Count Chinese characters (CJK Unified Ideographs) in the text.
    
    Args:
        text: Text to count
        
    Returns:
        Number of Chinese characters
    """
    # CJK Unified Ideographs range: U+4E00-U+9FFF
    # CJK Extension A: U+3400-U+4DBF
    # CJK Extension B: U+20000-U+2A6DF (requires surrogate pairs in Python)
    count = 0
    for char in text:
        code_point = ord(char)
        # Basic CJK range
        if 0x4E00 <= code_point <= 0x9FFF:
            count += 1
        # Extension A
        elif 0x3400 <= code_point <= 0x4DBF:
            count += 1
        # CJK Compatibility Ideographs
        elif 0xF900 <= code_point <= 0xFAFF:
            count += 1
    
    return count


def has_non_chinese_characters(text):
    """
    Check if text contains non-Chinese characters (excluding punctuation).
    Rejects: Russian (Cyrillic), Simplified Chinese, and other non-Chinese scripts.
    Accepts: Traditional Chinese characters and punctuation marks.
    
    Args:
        text: Text to check
        
    Returns:
        True if non-Chinese characters are found, False otherwise
    """
    # Try to use zhconv for Simplified Chinese detection
    try:
        import zhconv
        # Convert to traditional - if text changes, it contains simplified
        traditional = zhconv.convert(text, 'zh-tw')
        if traditional != text:
            return True
    except ImportError:
        # zhconv not available, use fallback method
        pass
    
    # Common punctuation marks to allow (Chinese and general)
    allowed_punctuation = set(
        '，。！？、；：""''（）【】《》〈〉「」『』〔〕〖〗·…—–～・'
        + '.,!?;:\'"()[]{}/\\-_+=*&^%$#@~`|<>'  # Common ASCII punctuation
        + '\n\r\t '  # Whitespace
        + '0123456789'  # Numbers (often used in stories)
    )
    
    # Common Simplified Chinese characters that differ from Traditional
    # These are simplified-only characters (not used in Traditional Chinese)
    simplified_only_chars = set([
        '这', '个', '说', '过', '还', '来', '时', '为', '会', '们',
        '现', '发', '当', '没', '对', '样', '应', '该', '实', '现',
        '从', '经', '动', '样', '处', '种', '长', '开', '点', '样',
        # Add more as needed - this is a basic set
    ])
    
    for char in text:
        code_point = ord(char)
        
        # Skip allowed punctuation and whitespace
        if char in allowed_punctuation:
            continue
        
        # Check for simplified-only characters
        if char in simplified_only_chars:
            return True
        
        # Check for Cyrillic (Russian) characters: U+0400-U+04FF
        if 0x0400 <= code_point <= 0x04FF:
            return True
        
        # Check for Latin letters (reject standalone Latin letters)
        if ('A' <= char <= 'Z') or ('a' <= char <= 'z'):
            return True
        
        # Check for other non-CJK scripts
        # Allow CJK Unified Ideographs and extensions
        is_cjk = (
            0x4E00 <= code_point <= 0x9FFF or  # CJK Unified Ideographs
            0x3400 <= code_point <= 0x4DBF or  # Extension A
            0xF900 <= code_point <= 0xFAFF     # Compatibility Ideographs
        )
        
        if not is_cjk:
            # Check if it's a common Chinese punctuation we might have missed
            # Additional CJK punctuation ranges
            if not (
                0x3000 <= code_point <= 0x303F or  # CJK Symbols and Punctuation
                0xFF00 <= code_point <= 0xFFEF     # Halfwidth and Fullwidth Forms
            ):
                return True
    
    return False


def _params_to_key(p):
    """將故事參數轉成可比較的 tuple，用於集合運算。"""
    return (
        p["char_a_id"], p["char_a_trait"], p["char_b_id"], p["char_b_trait"],
        p["world_id"], p["location_id"], p["prop_id"],
    )


def _story_type_to_dir_base(story_type):
    """故事類型 -> 目錄名前綴（不含 _2）。"""
    return "stories_" + story_type.replace(" ", "_")


def get_existing_combination_keys(base_dir, story_type):
    """
    掃描該故事類型對應的目錄（含 _2），回傳已存在檔案的組合 key 集合。
    """
    base = Path(base_dir)
    dir_base = _story_type_to_dir_base(story_type)
    keys = set()
    for suffix in ("", "_2"):
        d = base / (dir_base + suffix)
        if not d.is_dir():
            continue
        for f in d.glob("*.txt"):
            params = parse_filename(f.name, d.name)
            if params:
                keys.add(_params_to_key(params))
    return keys


def run_fill_missing():
    """
    補齊缺失組合：每種故事類型應有完整組合，缺失者重新生成並輸出到 _2 目錄。
    """
    base_dir = Path(__file__).parent
    story_types = ["Nature", "adventure comedy", "Sharing"]

    try:
        from short_story_generator import (
            get_full_expected_params_for_type,
            regenerate_stories,
        )
    except Exception as e:
        print(f"無法載入 short_story_generator: {e}")
        return

    all_missing = []
    for st in story_types:
        full = get_full_expected_params_for_type(st)
        existing = get_existing_combination_keys(base_dir, st)
        missing_params = [p for p in full if _params_to_key(p) not in existing]
        n_missing = len(missing_params)
        n_full = len(full)
        print(f"  {st}: 應有 {n_full} 組，已有 {n_full - n_missing} 組，缺失 {n_missing} 組")
        all_missing.extend(missing_params)

    if not all_missing:
        print("\n所有故事類型皆已補齊，無需重新生成。")
        return

    print(f"\n共需重新生成 {len(all_missing)} 個故事，輸出至各類型 _2 目錄。")
    confirm = input("是否繼續？(yes/no): ")
    if confirm.lower() not in ("yes", "y"):
        print("已取消。")
        return

    regenerate_stories(all_missing, output_dir_suffix="_2")


def parse_filename(filename, directory_name):
    """
    從文件名解析故事參數
    
    文件名格式: {theme_code}_{char_combo}_{location_combo}_{prop_id}_TW_V1.txt
    例如: ADV_C01T02_C04T01_W02A02_K02_TW_V1.txt
    
    Args:
        filename: 文件名（不含路徑）
        directory_name: 目錄名稱（用於推斷故事類型）
    
    Returns:
        dict: 包含故事參數的字典，如果解析失敗則返回 None
        {
            'story_type': str,
            'char_a_id': str,
            'char_a_trait': str,
            'char_b_id': str,
            'char_b_trait': str,
            'world_id': str,
            'location_id': str,
            'prop_id': str
        }
    """
    # 移除 .txt 擴展名
    name_without_ext = filename.replace('.txt', '')
    
    # 解析文件名各部分
    # 格式: {theme_code}_{char_a_id}{char_a_trait}_{char_b_id}{char_b_trait}_{location_combo}_{prop_id}_TW_V1
    # 例如: SOC_C03T01_C04T02_W02A02_K01_TW_V1
    parts = name_without_ext.split('_')
    
    if len(parts) < 5:
        return None
    
    theme_code = parts[0]  # 例如: SOC, ADV, NAT
    char_a_str = parts[1]  # 例如: C03T01
    char_b_str = parts[2]  # 例如: C04T02
    location_combo = parts[3]  # 例如: W02A02
    prop_id = parts[4]  # 例如: K01
    
    # 解析第一個角色: C03T01 -> C03, T01
    char_a_match = re.match(r'^([A-Z]\d+)([A-Z]\d+)$', char_a_str)
    if not char_a_match:
        return None
    char_a_id = char_a_match.group(1)
    char_a_trait = char_a_match.group(2)
    
    # 解析第二個角色: C04T02 -> C04, T02
    char_b_match = re.match(r'^([A-Z]\d+)([A-Z]\d+)$', char_b_str)
    if not char_b_match:
        return None
    char_b_id = char_b_match.group(1)
    char_b_trait = char_b_match.group(2)
    
    # 解析地點組合: W02A02 -> W02, A02
    location_match = re.match(r'^([A-Z]\d+)([A-Z]\d+)$', location_combo)
    if not location_match:
        return None
    world_id = location_match.group(1)
    location_id = location_match.group(2)
    
    # 從目錄名稱推斷故事類型
    # 目錄名稱格式: stories_Nature, stories_adventure_comedy, stories_Sharing
    # 實際故事類型: "Nature", "adventure comedy", "Sharing"
    story_type = None
    dir_lower = directory_name.lower()
    if 'nature' in dir_lower:
        story_type = 'Nature'
    elif 'adventure' in dir_lower or 'comedy' in dir_lower:
        story_type = 'adventure comedy'  # 注意：實際 JSON 中使用小寫
    elif 'sharing' in dir_lower:
        story_type = 'Sharing'
    
    if not story_type:
        return None
    
    return {
        'story_type': story_type,
        'char_a_id': char_a_id,
        'char_a_trait': char_a_trait,
        'char_b_id': char_b_id,
        'char_b_trait': char_b_trait,
        'world_id': world_id,
        'location_id': location_id,
        'prop_id': prop_id
    }


def process_file(file_path):
    """
    Process a single story file: clean it and check if it meets criteria.
    
    Args:
        file_path: Path to the story file
        
    Returns:
        tuple: (should_keep, cleaned_content, reason_for_deletion)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return (False, None, f"Error reading file: {e}")
    
    # Extract and clean story content
    cleaned_content = extract_story_content(content)
    
    if not cleaned_content:
        return (False, None, "No story content found")
    
    # Count Chinese characters
    char_count = count_chinese_characters(cleaned_content)
    
    # Check word count range (900-1400)
    if char_count < 700 or char_count > 1250:
        return (False, None, f"Word count out of range: {char_count} ")
    
    # Check for non-Chinese characters
    if has_non_chinese_characters(cleaned_content):
        return (False, None, "Contains non-Chinese characters (excluding punctuation)")
    
    return (True, cleaned_content, None)


def main():
    """
    Main function to filter and process story files.
    支援 --fill-missing：補齊每種故事類型的缺失組合，重新生成到 _2 目錄。
    """
    if "--fill-missing" in sys.argv:
        print("Fill-missing 模式：補齊缺失組合並重新生成至 _2 目錄")
        print("=" * 60)
        run_fill_missing()
        return

    # Base directory
    base_dir = Path(__file__).parent
    
    # Target directories (包含原始目錄和 _2 目錄)
    target_dirs = [
        base_dir / "stories_Nature",
        base_dir / "stories_Nature_2",
        base_dir / "stories_adventure_comedy",
        base_dir / "stories_adventure_comedy_2",
        base_dir / "stories_Sharing",
        base_dir / "stories_Sharing_2"
    ]
    
    stats = {
        'processed': 0,
        'kept': 0,
        'deleted': 0,
        'errors': 0
    }
    
    files_to_delete = []
    files_to_update = []
    stories_to_regenerate = []  # 需要重新生成的故事參數列表
    
    print("Starting story file filtering...")
    print("=" * 60)
    
    # First pass: clean all files and check criteria
    print("\nStep 1: Processing all files...")
    for target_dir in target_dirs:
        if not target_dir.exists():
            print(f"Warning: Directory not found: {target_dir}")
            continue
        
        print(f"\nProcessing directory: {target_dir.name}")
        
        for file_path in target_dir.glob("*.txt"):
            stats['processed'] += 1
            
            try:
                # Process file: clean and check criteria
                should_keep, cleaned_content, reason = process_file(file_path)
                
                if should_keep:
                    stats['kept'] += 1
                    # Check if file needs updating (content changed)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                    if current_content != cleaned_content:
                        files_to_update.append((file_path, cleaned_content))
                else:
                    # Mark for deletion and parse story parameters for regeneration
                    files_to_delete.append((file_path, reason))
                    print(f"  ❌ {file_path.name}: {reason}")
                    
                    # 解析文件名以獲取故事參數
                    story_params = parse_filename(file_path.name, target_dir.name)
                    if story_params:
                        stories_to_regenerate.append(story_params)
                    else:
                        print(f"  ⚠️  無法解析文件名參數: {file_path.name}")
                    
            except Exception as e:
                print(f"  ✗ Error processing {file_path.name}: {e}")
                stats['errors'] += 1
    
    stats['deleted'] = len(files_to_delete)
    
    print("\n" + "=" * 60)
    print(f"\nSummary:")
    print(f"  Processed: {stats['processed']} files")
    print(f"  To keep: {stats['kept']} files")
    print(f"  To delete: {stats['deleted']} files")
    print(f"  To update: {len(files_to_update)} files")
    print(f"  To regenerate: {len(stories_to_regenerate)} stories")
    
    if files_to_delete or files_to_update:
        response = input("\nProceed with updates and deletions? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Operation cancelled.")
            return
        
        # Update files that need cleaning
        if files_to_update:
            print("\nUpdating files with cleaned content...")
            for file_path, cleaned_content in files_to_update:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    print(f"  ✓ Updated: {file_path.name}")
                except Exception as e:
                    print(f"  ✗ Error updating {file_path.name}: {e}")
                    stats['errors'] += 1
        
        # Delete files that don't meet criteria
        if files_to_delete:
            print("\nDeleting files...")
            for file_path, reason in files_to_delete:
                try:
                    file_path.unlink()
                    print(f"  ✓ Deleted: {file_path.name} ({reason})")
                except Exception as e:
                    print(f"  ✗ Error deleting {file_path.name}: {e}")
                    stats['errors'] += 1
        
        # Regenerate stories that were filtered out
        if stories_to_regenerate:
            print("\n" + "=" * 60)
            print(f"\n準備重新生成 {len(stories_to_regenerate)} 個被過濾掉的故事...")
            response = input("是否繼續重新生成？(yes/no): ")
            if response.lower() in ['yes', 'y']:
                try:
                    # 導入生成器模組
                    sys.path.insert(0, str(base_dir))
                    from short_story_generator import regenerate_stories
                    
                    # 一律重新生成到 _2 目錄（含從 _2 被 filter 掉的 → 同目錄補回）
                    regenerate_stories(stories_to_regenerate, output_dir_suffix="_2")
                except Exception as e:
                    print(f"  ✗ 重新生成故事時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    stats['errors'] += 1
            else:
                print("跳過重新生成步驟。")
        
        print("\n" + "=" * 60)
        print(f"Operation completed!")
        if stats['errors'] > 0:
            print(f"  Errors encountered: {stats['errors']}")
    else:
        print("\nNo files need to be updated or deleted.")


if __name__ == "__main__":
    main()
