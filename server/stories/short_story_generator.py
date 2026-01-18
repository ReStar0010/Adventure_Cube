#!/usr/bin/env python3
"""
簡單故事生成器 - 使用 prompt_to_follow.md 模板
Simple story generator using prompt_to_follow.md template
"""
import csv
import json
import random
import sys
import os
import google.generativeai as genai

# ========== 設定區 ==========
GEMINI_API_KEY = "AIzaSyCqadx5k7aFDRF6IcHsii_TUXMfxk9ieeE"  # 請填入你的 API Key

# 自動找到正確的資料夾路徑 (相對於這個腳本的位置)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(SCRIPT_DIR, "prompt_0105")
# ============================

def load_json(filename):
    """載入 JSON 檔案"""
    filepath = os.path.join(DATA_FOLDER, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_template_file():
    """載入 prompt_to_follow.md 模板"""
    template_path = os.path.join(DATA_FOLDER, "prompt_to_follow.md")
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_phase_instruction(story_type, phase_name):
    """從短篇故事模板.json 提取特定 Phase 的指令
    
    Args:
        story_type: 故事類型
        phase_name: Phase 名稱（如 "Setup", "Twist", "Climax", "Ending"）
    """
    templates = load_json("短篇故事模板.json")
    for row in templates:
        story_type_match = row.get('story_type', '').strip() == story_type.strip()
        phase_name_value = row.get('phase_name', '').strip()
        # Phase_Name 可能包含換行和額外信息，使用 startswith 匹配
        phase_match = phase_name_value.startswith(phase_name.strip())
        
        if story_type_match and phase_match:
            # prompt_instruction 是一個數組，需要合併成字串
            instructions = row.get('prompt_instruction', [])
            if isinstance(instructions, list):
                return '\n'.join(instructions)
            return str(instructions) if instructions else ''
    return ''

def get_all_story_types():
    """獲取所有可用的故事類型
    
    Returns:
        list: 所有故事類型的列表
    """
    templates = load_json("短篇故事模板.json")
    story_types = set()
    
    for row in templates:
        story_type = row.get('story_type', '').strip()
        if story_type:
            story_types.add(story_type)
    
    return sorted(list(story_types))

def get_total_word_limit(story_type):
    """計算指定故事類型所有 Phase 的總字數限制（中文字）
    
    Args:
        story_type: 故事類型
    
    Returns:
        int: 所有 Phase 的總字數限制（中文字）
    """
    templates = load_json("短篇故事模板.json")
    total = 0
    
    # 遍歷所有模板，找出屬於該故事類型的所有 phase
    for row in templates:
        if row.get('story_type', '').strip() == story_type.strip():
            word_limit = row.get('word_limit', 0)
            total += int(word_limit) if word_limit else 0
    
    return total

def get_character_by_id(character_id, persona_id):
    """根據 character_id 和 persona_id 嚴格匹配角色
    
    Args:
        character_id: 角色 ID (如 "C01")
        persona_id: 人格 ID (如 "T01")
    
    Returns:
        dict: 匹配的角色資料，如果找不到則返回 None
    """
    characters = load_json("Character_Personas.json")
    for char in characters:
        if char.get('character_id', '') == character_id and char.get('persona_id', '') == persona_id:
            return char
    return None

def get_location_by_id(world_id, location_id):
    """根據 world_id 和 location_id 嚴格匹配地點
    
    Args:
        world_id: 世界 ID (如 "W01")
        location_id: 地點 ID (如 "A01")
    
    Returns:
        dict: 匹配的地點資料，如果找不到則返回 None
    """
    locations = load_json("Location.json")
    for loc in locations:
        if loc.get('world_id', '') == world_id and loc.get('location_id', '') == location_id:
            return loc
    return None

def get_prop_by_id(prop_id):
    """根據 prop_id 嚴格匹配道具
    
    Args:
        prop_id: 道具 ID (如 "K01")
    
    Returns:
        dict: 匹配的道具資料，如果找不到則返回 None
    """
    props = load_json("Props.json")
    for prop in props:
        if prop.get('prop_id', '') == prop_id:
            return prop
    return None

def get_elements_by_id(char_a_id, char_a_trait, char_b_id, char_b_trait, world_id, location_id, prop_id):
    """根據 ID 嚴格匹配角色、道具、背景
    
    Args:
        char_a_id: 角色 A 的 character_id (如 "C01")
        char_a_trait: 角色 A 的 persona_id (如 "T01")
        char_b_id: 角色 B 的 character_id (如 "C02")
        char_b_trait: 角色 B 的 persona_id (如 "T01")
        world_id: 世界 ID (如 "W01")
        location_id: 地點 ID (如 "A01")
        prop_id: 道具 ID (如 "K01")
    
    Returns:
        dict: 包含所有元素的字典，如果找不到任何元素則返回 None
    """
    # 載入資料
    char_a = get_character_by_id(char_a_id, char_a_trait)
    char_b = get_character_by_id(char_b_id, char_b_trait)
    prop = get_prop_by_id(prop_id)
    background = get_location_by_id(world_id, location_id)
    funny_incidents = load_json("Funny_incidents.json")
    
    # 檢查是否所有元素都找到
    if not char_a or not char_b or not prop or not background:
        missing = []
        if not char_a:
            missing.append(f"角色 A ({char_a_id}{char_a_trait})")
        if not char_b:
            missing.append(f"角色 B ({char_b_id}{char_b_trait})")
        if not prop:
            missing.append(f"道具 ({prop_id})")
        if not background:
            missing.append(f"地點 ({world_id}{location_id})")
        print(f"⚠️  警告: 找不到以下元素: {', '.join(missing)}")
        return None
    
    # 隨機選擇一個喜劇手法（因為沒有 ID 系統）
    comedy = random.choice(funny_incidents)
    
    # 提取地點和環境特徵
    location_full = background.get('location', '神奇的地方')
    # 地點名稱通常是括號前的部分
    location_name = location_full.split('(')[0].strip() if '(' in location_full else location_full
    sensory_detail = background.get('details', location_full)  # 使用 details 欄位作為環境特徵
    
    return {
        'Hero_Info': f"{char_a.get('name', '小英雄')} ({char_a.get('persona', '')})",
        'Sidekick_Info': f"{char_b.get('name', '小夥伴')} ({char_b.get('persona', '')})",
        'Prop_Info': f"{prop.get('prop_name', '神奇道具')} (邏輯：{prop.get('prop_logic', '')})",
        'Location': location_name,
        'Sensory_Detail': sensory_detail,
        'Comedy': f"{comedy.get('trope', '')} ({comedy.get('description', '')})",
        'char_a_id': char_a_id,
        'char_a_trait': char_a_trait,
        'char_b_id': char_b_id,
        'char_b_trait': char_b_trait,
        'world_id': world_id,
        'location_id': location_id,
        'prop_id': prop_id,
    }


def get_phase_summary(phase_instruction):
    """從 Phase 指令中提取簡要描述，用於 Writing Task 部分"""
    if not phase_instruction:
        return ""
    
    # 提取指令中的關鍵點
    lines = phase_instruction.split('\n')
    summary_parts = []
    
    for line in lines:
        line = line.strip()
        # 跳過格式標記、空行和變數
        if (line and 
            not line.startswith('[') and 
            not line.startswith('{') and
            not line.startswith('Format') and
            not line.startswith('不要')):
            
            # 提取數字開頭的項目（如 "1. 感官開場"）
            if line and line[0].isdigit():
                # 移除數字和點號，提取描述
                clean_line = line.split('.', 1)[-1].strip()
                # 移除冒號後的內容（如果有）
                if '：' in clean_line:
                    clean_line = clean_line.split('：')[0].strip()
                elif ':' in clean_line:
                    clean_line = clean_line.split(':')[0].strip()
                # 移除變數引用
                clean_line = clean_line.replace('{Location}', '').replace('{Character_A}', '主角').replace('{Character_B}', '夥伴').replace('{Prop}', '道具').replace('{prop_logic}', '').replace('{Prop_Logic}', '').replace('{Trait}', '').replace('{Theme}', '').strip()
                if clean_line and len(clean_line) < 30:
                    summary_parts.append(clean_line)
    
    # 如果沒有找到，嘗試提取關鍵動詞
    if not summary_parts:
        for line in lines:
            line = line.strip()
            if line and ('開場' in line or '轉折' in line or '高潮' in line or '結局' in line or 
                        '失控' in line or '糾纏' in line or '觸發' in line or '落地' in line):
                # 提取關鍵短語
                if '：' in line:
                    key_part = line.split('：')[-1].strip()
                    if len(key_part) < 30:
                        summary_parts.append(key_part)
    
    return '，'.join(summary_parts[:2]) if summary_parts else "按照階段指令完成"


def fill_template(template, story_type, elements):
    """填充模板變數"""
    # 載入 META prompt
    # 讀取 META prompt 的 markdown 文件
    meta_prompt_path = os.path.join(DATA_FOLDER, "META_prompt.md")
    with open(meta_prompt_path, encoding="utf-8") as f:
        meta_prompt = f.read()
    
    theme = story_type
    
    # 獲取各階段指令
    task_phase_1 = get_phase_instruction(story_type, 'Setup')
    task_phase_2 = get_phase_instruction(story_type, 'Twist')
    task_phase_3 = get_phase_instruction(story_type, 'Climax')
    task_phase_4 = get_phase_instruction(story_type, 'Ending')
    
    # 從 Prop_Info 中提取道具名稱（移除邏輯部分）
    prop_info = elements['Prop_Info']
    prop_name = prop_info.split('(邏輯：')[0].strip() if '(邏輯：' in prop_info else prop_info.split('(')[0].strip()
    
    # 替換所有變數
    replacements = {
        '{{META prompt.csv / Prompt_Instruction}}': meta_prompt,
        '{{Theme}}': theme,
        '{{Location}}': elements['Location'],
        '{{Sensory_Detail}}': elements['Sensory_Detail'],
        '{{Character_A}}': elements['Hero_Info'],
        '{{Character_B}}': elements['Sidekick_Info'],
        '{{Prop}}': prop_name,
        '{{Comedy}}': elements['Comedy'],
        '{{Task_Phase_1}}': task_phase_1,
        '{{Task_Phase_2}}': task_phase_2,
        '{{Task_Phase_3}}': task_phase_3,
        '{{Task_Phase_4}}': task_phase_4,
    }
    
    filled_template = template
    for key, value in replacements.items():
        filled_template = filled_template.replace(key, value)
    
    return filled_template


def format_output_file(story_type, elements, story, theme):
    """格式化輸出文件，與 prompt_to_follow_example.txt 格式一致"""
    # 提取道具名稱和邏輯
    prop_info = elements['Prop_Info']
    prop_name = prop_info.split('(')[0].strip()
    prop_logic = prop_info.split('邏輯：')[-1].strip() if '邏輯：' in prop_info else ''
    
    # 提取喜劇手法
    comedy_info = elements['Comedy']
    comedy_name = comedy_info.split('(')[0].strip() if '(' in comedy_info else comedy_info
    
    # 構建 [Current Story Context] 部分
    context_section = f"""[Current Story Context]
核心概念：{theme}
地點：{elements['Location']} (環境特徵：{elements['Sensory_Detail']})
角色：
主角 A：{elements['Hero_Info']}
夥伴 B：{elements['Sidekick_Info']}
關鍵道具：{prop_name} (邏輯：{prop_logic})
指定喜劇手法：{comedy_name}"""
    
    # 構建 [Writing Task] 部分
    phase_1_summary = get_phase_summary(get_phase_instruction(story_type, 'Setup'))
    phase_2_summary = get_phase_summary(get_phase_instruction(story_type, 'Twist'))
    phase_3_summary = get_phase_summary(get_phase_instruction(story_type, 'Climax'))
    phase_4_summary = get_phase_summary(get_phase_instruction(story_type, 'Ending'))
    
    writing_task = f"""[Writing Task: Full Story Arc] 【Phase 1】 {phase_1_summary}。 【Phase 2】 {phase_2_summary}。 【Phase 3】 {phase_3_summary}。 【Phase 4】 {phase_4_summary}。"""
    
    # 組合完整輸出
    full_output = f"""{context_section}
{writing_task}
Output Story (AI 生成結果)
{story}"""
    
    return full_output


def generate_with_gemini(user_prompt, max_words=0):
    """使用 Gemini 生成故事（繁體中文）
    
    Args:
        user_prompt: 用戶提示詞（已包含 META prompt）
        max_words: 目標字數（中文字），0 表示不限制
    """
    genai.configure(api_key=GEMINI_API_KEY)
    
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    
    # 如果不設置 system_instruction，因為 META prompt 已經包含在 user_prompt 中
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        safety_settings=safety_settings
    )
    
    # 如果有字數限制，在 prompt 末尾添加字數要求
    final_prompt = user_prompt
    if max_words > 0:
        word_limit_note = f"\n\n[重要] 請確保完整故事的總字數約為 {max_words} 字（中文字）。請嚴格控制字數，不要超過此限制。"
        final_prompt = final_prompt + word_limit_note
    
    response = model.generate_content(
        final_prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.7)
    )
    
    return response.candidates[0].content.parts[0].text.strip()

def generate_single_story(story_type, char_a_id, char_a_trait, char_b_id, char_b_trait, 
                         world_id, location_id, prop_id, template, output_dir=None):
    """生成單一故事
    
    Args:
        story_type: 故事類型
        char_a_id, char_a_trait: 角色 A 的 ID 和特質
        char_b_id, char_b_trait: 角色 B 的 ID 和特質
        world_id, location_id: 世界和地點 ID
        prop_id: 道具 ID
        template: 已載入的模板
        output_dir: 輸出目錄（可選）
    
    Returns:
        bool: 是否成功生成
    """
    # 1. 根據 ID 獲取元素
    elements = get_elements_by_id(char_a_id, char_a_trait, char_b_id, char_b_trait,
                                  world_id, location_id, prop_id)
    if not elements:
        return False
    
    # 2. 填充模板
    filled_prompt = fill_template(template, story_type, elements)
    
    # 3. 獲取字數限制
    total_word_limit = get_total_word_limit(story_type)
    
    # 4. 生成故事
    try:
        story = generate_with_gemini(filled_prompt, max_words=total_word_limit)
    except Exception as e:
        print(f"   ❌ 生成失敗: {e}")
        return False
    
    # 5. 格式化輸出
    theme = story_type
    formatted_output = format_output_file(story_type, elements, story, theme)
    
    # 6. 生成檔名（類似語音檔名格式）
    # 格式: {主題}_{角色組合}_{背景}_{道具}_TW_V1.txt
    char_combo = f"{char_a_id}{char_a_trait}_{char_b_id}{char_b_trait}"
    location_combo = f"{world_id}{location_id}"
    
    # 根據故事類型生成主題代碼
    story_type_lower = story_type.lower().replace(" ", "")
    if "adventure" in story_type_lower or "comedy" in story_type_lower or "comdey" in story_type_lower:
        theme_code = "ADV"
    elif "sharing" in story_type_lower:
        theme_code = "SOC"
    elif "nature" in story_type_lower:
        theme_code = "NAT"
    else:
        # 預設使用前三個大寫字母
        theme_code = story_type.upper().replace(" ", "")[:3]
    
    filename = f"{theme_code}_{char_combo}_{location_combo}_{prop_id}_TW_V1.txt"
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
    else:
        filepath = filename
    
    # 7. 儲存檔案
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(formatted_output)
    
    # 8. 顯示進度（計算中文字數）
    word_count = len(story) if story else 0
    print(f"   ✓ [{char_combo}][{location_combo}][{prop_id}] 完成 - {word_count} 字")
    
    return True

def get_all_character_combinations():
    """自動生成所有可能的角色組合
    
    從所有角色中選擇 2 個，每個角色有 2 個特質選擇
    例如：C01-C02, C01-C03, C01-C04, C02-C03, C02-C04, C03-C04
    
    Returns:
        list: 所有角色組合的列表，每個元素為 (char_a_id, char_a_trait, char_b_id, char_b_trait)
    """
    characters = load_json("Character_Personas.json")
    
    # 獲取所有唯一的角色 ID
    character_ids = sorted(set(char.get('character_id') for char in characters))
    traits = ["T01", "T02"]  # 每個角色有兩個特質
    
    combinations = []
    
    # 生成所有角色對（不重複，順序不重要，但保持一致的順序）
    for i, char_a_id in enumerate(character_ids):
        for char_b_id in character_ids[i+1:]:  # 只與後面的角色配對，避免重複
            # 為每對角色生成所有特質組合
            for char_a_trait in traits:
                for char_b_trait in traits:
                    combinations.append((char_a_id, char_a_trait, char_b_id, char_b_trait))
    
    return combinations

def generate_stories_for_type(story_type, template):
    """為指定故事類型生成所有組合的故事
    
    Args:
        story_type: 故事類型
        template: 已載入的模板
    
    Returns:
        tuple: (成功數量, 失敗數量, 輸出目錄)
    """
    print(f"\n{'='*80}")
    print(f"📖 生成故事類型: {story_type}")
    print(f"{'='*80}\n")
    
    # 1. 自動生成所有角色組合
    character_combinations = get_all_character_combinations()
    
    # 背景：W01A01, W01A02, W02A01, W02A02
    location_combinations = [
        ("W01", "A01"),
        ("W01", "A02"),
        ("W02", "A01"),
        ("W02", "A02"),
    ]
    
    # 道具：K01, K02（不包括 K00，因為它不存在）
    prop_ids = ["K01", "K02"]
    
    # 2. 計算總數
    total_combinations = len(character_combinations) * len(location_combinations) * len(prop_ids)
    print(f"📊 將生成 {total_combinations} 個故事組合")
    print(f"   - 角色組合: {len(character_combinations)} 種")
    print(f"   - 背景: {len(location_combinations)} 種")
    print(f"   - 道具: {len(prop_ids)} 種")
    
    # 3. 獲取字數限制（中文字）
    total_word_limit = get_total_word_limit(story_type)
    if total_word_limit > 0:
        print(f"   📏 每個故事目標字數: {total_word_limit} 字")
    
    # 4. 創建輸出目錄
    output_dir = f"stories_{story_type.replace(' ', '_')}"
    print(f"💾 輸出目錄: {output_dir}")
    
    # 5. 迭代生成所有組合
    print(f"\n{'='*80}")
    print("開始生成故事...")
    print(f"{'='*80}\n")
    
    success_count = 0
    fail_count = 0
    current = 0
    
    for char_a_id, char_a_trait, char_b_id, char_b_trait in character_combinations:
        for world_id, location_id in location_combinations:
            for prop_id in prop_ids:
                current += 1
                char_combo = f"{char_a_id}{char_a_trait}_{char_b_id}{char_b_trait}"
                location_combo = f"{world_id}{location_id}"
                print(f"[{current}/{total_combinations}] 生成: {char_combo} + {location_combo} + {prop_id}...")
                
                success = generate_single_story(
                    story_type, char_a_id, char_a_trait, char_b_id, char_b_trait,
                    world_id, location_id, prop_id, template, output_dir
                )
                
                if success:
                    success_count += 1
                else:
                    fail_count += 1
    
    # 6. 顯示總結
    print(f"\n{'='*80}")
    print(f"✨ {story_type} 完成!")
    print(f"   ✓ 成功: {success_count} 個")
    if fail_count > 0:
        print(f"   ❌ 失敗: {fail_count} 個")
    print(f"   📁 輸出目錄: {output_dir}")
    print(f"{'='*80}")
    
    return success_count, fail_count, output_dir

def main():
    """主程式 - 自動生成所有故事類型的所有組合"""
    print(f"\n{'='*80}")
    print("🚀 短篇故事生成器 - 自動生成所有組合")
    print(f"{'='*80}\n")
    
    # 1. 載入模板
    print("⏳ 載入 prompt_to_follow.md 模板...")
    template = load_template_file()
    print(f"   ✓ 已載入模板 ({len(template)} 字)\n")
    
    # 2. 獲取所有故事類型
    story_types = get_all_story_types()
    print(f"📚 找到 {len(story_types)} 種故事類型:")
    for st in story_types:
        print(f"   - {st}")
    
    # 3. 為每個故事類型生成所有組合
    total_success = 0
    total_fail = 0
    output_dirs = []
    
    for story_type in story_types:
        success, fail, output_dir = generate_stories_for_type(story_type, template)
        total_success += success
        total_fail += fail
        output_dirs.append(output_dir)
    
    # 4. 顯示最終總結
    print(f"\n{'='*80}")
    print("🎉 所有故事生成完成!")
    print(f"{'='*80}")
    print(f"   ✓ 總成功: {total_success} 個")
    if total_fail > 0:
        print(f"   ❌ 總失敗: {total_fail} 個")
    print(f"\n   📁 輸出目錄:")
    for output_dir in output_dirs:
        print(f"      - {output_dir}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ 錯誤: 請先在腳本中設定 GEMINI_API_KEY")
        sys.exit(1)
    
    # 自動生成所有故事類型的所有組合，不需要參數
    main()
