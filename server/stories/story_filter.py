#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story Filter Script
Filters and cleans story files in the specified directories.
"""

import os
import re
from pathlib import Path


def extract_story_content(content):
    """
    Extract content after 'Output Story (AI 生成結果)' and remove word count comments.
    If marker is not found, assume the file is already cleaned and just remove word counts.
    
    Args:
        content: Original file content
        
    Returns:
        Cleaned story content
    """
    # Find the line with "Output Story (AI 生成結果)"
    marker = "Output Story (AI 生成結果)"
    
    if marker not in content:
        # If marker not found, assume file is already cleaned
        # Just remove word count comments
        story_content = content
    else:
        # Split by marker and take everything after it
        parts = content.split(marker, 1)
        if len(parts) < 2:
            return ""
        story_content = parts[1].strip()
    
    # Remove word count comments like "(200字)", "(約200字)", "(约200字)", etc.
    # Pattern matches: (optional 約/约) + digits + 字
    word_count_pattern = r'\([約约]?\d+字\)'
    story_content = re.sub(word_count_pattern, '', story_content)
    
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
    
    # Extract story content after marker
    cleaned_content = extract_story_content(content)
    
    if not cleaned_content:
        return (False, None, "No story content found after marker")
    
    # Count Chinese characters
    char_count = count_chinese_characters(cleaned_content)
    
    # Check word count range (900-1400)
    if char_count < 900 or char_count > 1400:
        return (False, None, f"Word count out of range: {char_count} (required: 900-1400)")
    
    # Check for non-Chinese characters
    if has_non_chinese_characters(cleaned_content):
        return (False, None, "Contains non-Chinese characters (excluding punctuation)")
    
    return (True, cleaned_content, None)


def main():
    """
    Main function to filter and process story files.
    """
    # Base directory
    base_dir = Path(__file__).parent
    
    # Target directories
    target_dirs = [
        base_dir / "stories_Nature",
        base_dir / "stories_adventure_comedy",
        base_dir / "stories_Sharing"
    ]
    
    stats = {
        'processed': 0,
        'kept': 0,
        'deleted': 0,
        'errors': 0
    }
    
    files_to_delete = []
    files_to_update = []
    
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
                    # Mark for deletion
                    files_to_delete.append((file_path, reason))
                    print(f"  ❌ {file_path.name}: {reason}")
                    
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
        
        print("\n" + "=" * 60)
        print(f"Operation completed!")
        if stats['errors'] > 0:
            print(f"  Errors encountered: {stats['errors']}")
    else:
        print("\nNo files need to be updated or deleted.")


if __name__ == "__main__":
    main()
