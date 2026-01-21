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
    template_path = os.path.join(DATA_FOLDER, "prompt_to_follow.md")
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_all_story_types():
    templates = load_json("短篇故事模板.json")
    story_types = set()
    
    for row in templates:
        story_type = row.get('story_type', '').strip()
        if story_type:
            story_types.add(story_type)
    
    return sorted(list(story_types))

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
            # prompt_instruction 可能是字串或 list
            instructions = row.get('prompt_instruction', [])
            if isinstance(instructions, list):
                return '\n'.join(instructions)
            return str(instructions) if instructions else ''
    return ''

def get_logic_setup_instruction(story_type):
    """取得指定 story_type 的 Logic Setup 指令（對應 prompt_to_follow.md 的 {{Logic_setup}}）
    
    規則：
    1) 優先找 phase_name 含有 'logic'（不分大小寫）的列
    2) 若找不到，針對 Nature 類型（或未命名 logic phase）再找 phase_id 含 'setting' 的列
    3) 都找不到則回傳空字串
    """
    templates = load_json("短篇故事模板.json")
    st = story_type.strip()
    
    # 1) phase_name contains "logic"
    for row in templates:
        if row.get('story_type', '').strip() != st:
            continue
        phase_name_value = (row.get('phase_name') or '').strip()
        if 'logic' in phase_name_value.lower():
            instructions = row.get('prompt_instruction', '')
            if isinstance(instructions, list):
                return '\n'.join(instructions)
            return str(instructions).strip()
    
    # 2) fallback: phase_id contains "setting" (e.g. Nat_setting)
    for row in templates:
        if row.get('story_type', '').strip() != st:
            continue
        phase_id_value = (row.get('phase_id') or '').strip()
        if 'setting' in phase_id_value.lower():
            instructions = row.get('prompt_instruction', '')
            if isinstance(instructions, list):
                return '\n'.join(instructions)
            return str(instructions).strip()
    
    return ''

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
    logic_setup = get_logic_setup_instruction(story_type)
    task_phase_1 = get_phase_instruction(story_type, 'Setup')
    task_phase_2 = get_phase_instruction(story_type, 'Twist')
    task_phase_3 = get_phase_instruction(story_type, 'Climax')
    task_phase_4 = get_phase_instruction(story_type, 'Ending')
    
    # 從 Prop_Info 中提取道具名稱（移除邏輯部分）
    prop_info = elements['Prop_Info']
    prop_name = prop_info.split('(邏輯：')[0].strip() if '(邏輯：' in prop_info else prop_info.split('(')[0].strip()
    
    # 替換所有變數
    # 注意：repo 內同時存在兩種 placeholder 風格
    # - prompt_to_follow.md 使用 {{LikeThis}}
    # - 短篇故事模板.json 的 phase 指令大量使用 {LikeThis}
    # 由於 phase 指令會被塞進 {{Task_Phase_*}} 後才進入最終 prompt，
    # 若不額外處理，{Location} 這類 token 會保留在 filled_template 中。

    # Add a function to get word_limit of each phase for story_type
    get_phase_word_limit = lambda st, pname: next((str(row.get('word_limit', '')) for row in load_json("短篇故事模板.json") if row.get('story_type', '').strip() == st.strip() and row.get('phase_name', '').strip().startswith(pname)), '')
    replacements = {
        '{{META prompt.csv / Prompt_Instruction}}': meta_prompt,
        '{{Theme}}': theme,
        '{{Location}}': elements['Location'],
        '{{Sensory_Detail}}': elements['Sensory_Detail'],
        '{{Character_A}}': elements['Hero_Info'],
        '{{Character_B}}': elements['Sidekick_Info'],
        '{{Prop}}': prop_name,
        '{{Comedy}}': elements['Comedy'],
        '{{Logic_setup}}': logic_setup,
        '{{Task_Phase_1}}': f"{task_phase_1}\n(字數上限：{get_phase_word_limit(story_type, 'Setup')})",
        '{{Task_Phase_2}}': f"{task_phase_2}\n(字數上限：{get_phase_word_limit(story_type, 'Twist')})",
        '{{Task_Phase_3}}': f"{task_phase_3}\n(字數上限：{get_phase_word_limit(story_type, 'Climax')})",
        '{{Task_Phase_4}}': f"{task_phase_4}\n(字數上限：{get_phase_word_limit(story_type, 'Ending')})",
    }

    # 同步替換單大括號版本（來自短篇故事模板.json）
    replacements.update({
        '{Theme}': theme,
        '{Location}': elements['Location'],
        '{Sensory_Detail}': elements['Sensory_Detail'],
        '{Character_A}': elements['Hero_Info'],
        '{Character_B}': elements['Sidekick_Info'],
        '{Prop}': prop_name,
        '{Comedy}': elements['Comedy'],
    })
    
    filled_template = template
    for key, value in replacements.items():
        filled_template = filled_template.replace(key, value)
    
    return filled_template

def format_output_file(story_type, elements, story, theme):
    """格式化輸出文件，只輸出故事內容本身"""
    # 移除 [Story Setup] 部分和所有以 > 開頭的元數據行
    lines = story.split('\n')
    result_lines = []
    skip_mode = False
    
    for line in lines:
        # 檢測 [Story Setup] 標記（可能有多種格式）
        if '[Story Setup]' in line:
            skip_mode = True
            continue
        
        # 如果處於跳過模式，跳過所有以 > 開頭的行和空行
        if skip_mode:
            # 跳過以 > 開頭的行（包括 "Selected Scene", "Selected NPC", "NPC's Goal" 等）
            if line.strip().startswith('>'):
                continue
            # 跳過空行
            if not line.strip():
                continue
            # 遇到第一個非 > 開頭的非空行，結束跳過模式並開始收集內容
            skip_mode = False
            result_lines.append(line)
        else:
            # 如果不在跳過模式，但遇到以 > 開頭的行，也跳過（以防萬一）
            if line.strip().startswith('>'):
                continue
            result_lines.append(line)
    
    # 返回清理後的故事內容
    return '\n'.join(result_lines).strip()


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

def regenerate_stories(story_params_list):
    """
    重新生成指定的故事列表
    
    Args:
        story_params_list: 故事參數列表，每個元素是一個字典，包含：
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
    if not story_params_list:
        print("沒有需要重新生成的故事。")
        return
    
    print(f"\n{'='*80}")
    print(f"🔄 重新生成 {len(story_params_list)} 個故事")
    print(f"{'='*80}\n")
    
    # 載入模板
    template = load_template_file()
    
    # 確保輸出目錄相對於腳本目錄
    base_dir = SCRIPT_DIR
    
    # 按故事類型分組
    stories_by_type = {}
    for params in story_params_list:
        story_type = params['story_type']
        if story_type not in stories_by_type:
            stories_by_type[story_type] = []
        stories_by_type[story_type].append(params)
    
    total_success = 0
    total_fail = 0
    
    # 為每個故事類型生成對應的輸出目錄
    for story_type, params_list in stories_by_type.items():
        print(f"\n{'='*80}")
        print(f"📖 重新生成故事類型: {story_type} ({len(params_list)} 個)")
        print(f"{'='*80}\n")
        
        # 獲取字數限制（中文字）
        total_word_limit = get_total_word_limit(story_type)
        if total_word_limit > 0:
            print(f"   📏 每個故事目標字數: {total_word_limit} 字")
        
        # 創建輸出目錄（相對於腳本目錄）
        output_dir = os.path.join(base_dir, f"stories_{story_type.replace(' ', '_')}")
        print(f"💾 輸出目錄: {output_dir}")
        
        print(f"\n開始生成故事...\n")
        
        success_count = 0
        fail_count = 0
        
        for idx, params in enumerate(params_list, 1):
            char_combo = f"{params['char_a_id']}{params['char_a_trait']}_{params['char_b_id']}{params['char_b_trait']}"
            location_combo = f"{params['world_id']}{params['location_id']}"
            print(f"[{idx}/{len(params_list)}] 生成: {char_combo} + {location_combo} + {params['prop_id']}...")
            
            success = generate_single_story(
                params['story_type'],
                params['char_a_id'],
                params['char_a_trait'],
                params['char_b_id'],
                params['char_b_trait'],
                params['world_id'],
                params['location_id'],
                params['prop_id'],
                template,
                output_dir
            )
            
            if success:
                success_count += 1
                total_success += 1
            else:
                fail_count += 1
                total_fail += 1
        
        print(f"\n✨ {story_type} 完成!")
        print(f"   ✓ 成功: {success_count} 個")
        if fail_count > 0:
            print(f"   ❌ 失敗: {fail_count} 個")
    
    # 顯示總體總結
    print(f"\n{'='*80}")
    print(f"🎉 重新生成完成!")
    print(f"{'='*80}")
    print(f"   ✓ 總成功: {total_success} 個")
    if total_fail > 0:
        print(f"   ❌ 總失敗: {total_fail} 個")
    print(f"{'='*80}\n")


def generate_stories_for_type(story_type, template):
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

    template = load_template_file() 
    story_types = get_all_story_types()

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
    main()
