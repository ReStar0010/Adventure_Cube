#!/usr/bin/env python3
"""
簡單故事生成器 - 使用 prompt_to_follow.txt 模板
Simple story generator using prompt_to_follow.txt template
"""
import csv
import json
import random
import sys
import os
import google.generativeai as genai

# ========== 設定區 ==========
GEMINI_API_KEY = "REDACTED_GEMINI_API_KEY"  # 請填入你的 API Key

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
    """載入 prompt_to_follow.txt 模板"""
    template_path = os.path.join(DATA_FOLDER, "prompt_to_follow.txt")
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

def get_phase_word_limit(story_type, phase_name):
    """從短篇故事模板.json 提取特定 Phase 的字數限制
    
    Args:
        story_type: 故事類型
        phase_name: Phase 名稱（如 "Setup", "Twist", "Climax", "Ending"）
    
    Returns:
        int: 該 Phase 的字數限制，如果找不到則返回 0
    """
    templates = load_json("短篇故事模板.json")
    for row in templates:
        story_type_match = row.get('story_type', '').strip() == story_type.strip()
        phase_name_value = row.get('phase_name', '').strip()
        phase_match = phase_name_value.startswith(phase_name.strip())
        
        if story_type_match and phase_match:
            word_limit = row.get('word_limit', 0)
            return int(word_limit) if word_limit else 0
    return 0

def get_total_word_limit(story_type):
    """計算指定故事類型所有 Phase 的總字數限制
    
    Args:
        story_type: 故事類型
    
    Returns:
        int: 所有 Phase 的總字數限制
    """
    templates = load_json("短篇故事模板.json")
    total = 0
    
    # 遍歷所有模板，找出屬於該故事類型的所有 phase
    for row in templates:
        if row.get('story_type', '').strip() == story_type.strip():
            word_limit = row.get('word_limit', 0)
            total += int(word_limit) if word_limit else 0
    
    return total


def get_random_elements(story_type):
    """隨機選擇角色、道具、背景"""
    # 載入資料（使用 JSON 格式）
    characters = load_json("Character_Personas.json")
    props = load_json("Props.json")
    backgrounds = load_json("Location.json")
    funny_incidents = load_json("Funny_incidents.json")
    
    # 隨機選擇
    char_a = random.choice(characters)
    char_b = random.choice(characters)
    prop = random.choice(props)
    background = random.choice(backgrounds)
    comedy = random.choice(funny_incidents)
    
    # 提取地點和環境特徵
    location_full = background.get('location', '神奇的地方')
    # 地點名稱通常是括號前的部分
    location_name = location_full.split('(')[0].strip() if '(' in location_full else location_full
    sensory_detail = background.get('details', location_full)  # 使用 details 欄位作為環境特徵
    
    # 隨機選擇 persona1 或 persona2
    char_a_persona = random.choice([char_a.get('persona1', ''), char_a.get('persona2', '')])
    char_b_persona = random.choice([char_b.get('persona1', ''), char_b.get('persona2', '')])
    
    return {
        'Hero_Info': f"{char_a.get('name', '小英雄')} ({char_a_persona})",
        'Sidekick_Info': f"{char_b.get('name', '小夥伴')} ({char_b_persona})",
        'Prop_Info': f"{prop.get('prop_name', '神奇道具')} (邏輯：{prop.get('prop_logic', '')})",
        'Location': location_name,
        'Sensory_Detail': sensory_detail,
        'Comedy': f"{comedy.get('trope', '')} ({comedy.get('description', '')})",
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
    """使用 Gemini 生成故事
    
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
        final_prompt = user_prompt + word_limit_note
    
    response = model.generate_content(
        final_prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.7)
    )
    
    return response.candidates[0].content.parts[0].text.strip()

def main(story_type):
    """主程式"""
    print(f"\n{'='*80}")
    print(f"📖 生成故事類型: {story_type}")
    print(f"{'='*80}\n")
    
    # 1. 載入模板
    print("⏳ 載入 prompt_to_follow.txt 模板...")
    template = load_template_file()
    print(f"   ✓ 已載入模板 ({len(template)} 字)")
    
    # 2. 隨機選擇元素
    print("⏳ 隨機選擇故事元素...")
    elements = get_random_elements(story_type)
    print(f"   主角: {elements['Hero_Info']}")
    print(f"   夥伴: {elements['Sidekick_Info']}")
    print(f"   道具: {elements['Prop_Info'][:60]}...")
    print(f"   地點: {elements['Location']}")
    print(f"   喜劇手法: {elements['Comedy'][:60]}...")
    
    # 3. 填充模板
    print("\n⏳ 填充模板變數...")
    filled_prompt = fill_template(template, story_type, elements)
    print(f"   ✓ 模板已填充 ({len(filled_prompt)} 字)")
    
    # 3.5. 獲取字數限制
    total_word_limit = get_total_word_limit(story_type)
    if total_word_limit > 0:
        print(f"   📏 目標總字數: {total_word_limit} 字（根據各 Phase 的 word_limit 計算）")
    
    # 4. 生成故事
    print(f"\n{'='*80}")
    print("開始生成完整故事...")
    if total_word_limit > 0:
        print(f"目標字數: {total_word_limit} 字")
    print(f"{'='*80}\n")
    
    story = generate_with_gemini(filled_prompt, max_words=total_word_limit)
    
    # 5. 獲取主題
    theme = story_type
    
    # 6. 格式化輸出（與示例文件格式一致）
    formatted_output = format_output_file(story_type, elements, story, theme)
    
    # 7. 顯示完整故事
    print(f"\n{'='*80}")
    print("📖 完整故事")
    print(f"{'='*80}\n")
    print(formatted_output)
    
    print(f"\n{'='*80}")
    print(f"✨ 完成! 總字數: {len(story)} 字", end="")
    if total_word_limit > 0:
        print(f" (目標: {total_word_limit} 字)")
        if len(story) > total_word_limit:
            print(f"⚠️  超過目標字數 {len(story) - total_word_limit} 字")
        elif len(story) < total_word_limit * 0.8:
            print(f"⚠️  低於目標字數 {total_word_limit - len(story)} 字")
        else:
            print("✓ 字數符合目標範圍")
    else:
        print()
    print(f"{'='*80}")
    
    # 8. 儲存到檔案（使用與示例相同的格式）
    filename = f"story_{story_type.replace(' ', '_')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(formatted_output)
    
    print(f"\n💾 故事已儲存至: {filename}")


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ 錯誤: 請先在腳本中設定 GEMINI_API_KEY")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("用法: python short_story_generator.py <故事類型>")
        print("\n可用的故事類型:")
        print("   - adventure comdey")
        print("   - Sharing")
        print("   - Bed Time")
        print("   - Nature")
        sys.exit(1)
    
    story_type = sys.argv[1]
    main(story_type)
