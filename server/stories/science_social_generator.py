#!/usr/bin/env python3
"""
Science / Social 故事生成器
依 Story_Variables.json 的 20 個組合，直接填入模板變數後生成故事。
不依賴 short_story_generator，流程簡潔獨立。
"""
import json
import os
import random
import google.generativeai as genai

# ========== 設定區 ==========
GEMINI_API_KEY = "AIzaSyCqadx5k7aFDRF6IcHsii_TUXMfxk9ieeE"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(SCRIPT_DIR, "prompt_0105")
# ============================


def load_json(filename):
    with open(os.path.join(DATA_FOLDER, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def load_text(filename):
    with open(os.path.join(DATA_FOLDER, filename), "r", encoding="utf-8") as f:
        return f.read()


def get_phase_instruction(story_type, phase_name):
    """從短篇故事模板.json 取得 Phase 指令"""
    templates = load_json("短篇故事模板.json")
    for row in templates:
        if row.get("story_type", "").strip() != story_type.strip():
            continue
        pn = row.get("phase_name", "").strip()
        if pn.startswith(phase_name.strip()):
            inst = row.get("prompt_instruction", [])
            return "\n".join(inst) if isinstance(inst, list) else (str(inst) or "")
    return ""


def get_phase_word_limit(story_type, phase_name):
    """取得 Phase 字數上限"""
    templates = load_json("短篇故事模板.json")
    for row in templates:
        if row.get("story_type", "").strip() != story_type.strip():
            continue
        if row.get("phase_name", "").strip().startswith(phase_name.strip()):
            return str(row.get("word_limit", "") or "")
    return ""


def get_total_word_limit(story_type):
    """計算該故事類型所有 Phase 的總字數"""
    templates = load_json("短篇故事模板.json")
    total = 0
    for row in templates:
        if row.get("story_type", "").strip() == story_type.strip():
            total += int(row.get("word_limit") or 0)
    return total


def fill_template(combo):
    """
    直接以 combo（Story_Variables 單筆）填入 prompt_to_follow 模板。
    """
    story_id = combo.get("story_id", "")
    story_type = (combo.get("story_type") or "").strip()
    character_id = combo.get("character_id", "")
    var_theme = combo.get("var_theme", "")
    var_problem = combo.get("var_problem", "")
    var_action = combo.get("var_action", "")

    # 角色與地點
    characters = load_json("Character_Personas.json")
    char = next((c for c in characters if c.get("character_id") == character_id and c.get("persona_id") == "T01"), None)
    character_info = f"{char.get('name', '')} ({char.get('persona', '')})" if char else ""

    locations = load_json("Location.json")
    loc = random.choice(locations) if locations else None
    location_name = loc.get("location", "魔法城堡").split("(")[0].strip() if loc else "魔法城堡"
    sensory_detail = loc.get("details", location_name) if loc else ""

    # Phase 與字數
    phase_names = ("Intro", "Problem", "Effort", "Result") if story_type == "Science" else ("Intro", "Problem", "Action", "Result")
    task_1 = get_phase_instruction(story_type, phase_names[0])
    task_2 = get_phase_instruction(story_type, phase_names[1])
    task_3 = get_phase_instruction(story_type, phase_names[2])
    task_4 = get_phase_instruction(story_type, phase_names[3])
    w1 = get_phase_word_limit(story_type, phase_names[0])
    w2 = get_phase_word_limit(story_type, phase_names[1])
    w3 = get_phase_word_limit(story_type, phase_names[2])
    w4 = get_phase_word_limit(story_type, phase_names[3])

    # 替換 Phase 內的變數
    replacements = {
        "{Character}": character_info,
        "{Location}": location_name,
        "{Phenomenon}": var_problem if story_type == "Science" else var_theme,
        "{Topic}": var_theme,
        "{Var_Theme}": var_theme,
        "{Var_Problem}": var_problem,
        "{Var_Action}": var_action,
        "{{Experiment}}": var_action,
        "{Situation}": var_theme,
        "{Rule}": var_problem,
        "{Mistake}": var_action,
    }
    for k, v in replacements.items():
        task_1 = task_1.replace(k, str(v))
        task_2 = task_2.replace(k, str(v))
        task_3 = task_3.replace(k, str(v))
        task_4 = task_4.replace(k, str(v))

    # 主模板
    template = load_text("prompt_to_follow.md")
    meta_prompt = load_text("META_prompt.md")

    replacements_main = {
        "{{META prompt.csv / Prompt_Instruction}}": meta_prompt,
        "{{Theme}}": story_type,
        "{Theme}": story_type,
        "{{Location}}": location_name,
        "{Location}": location_name,
        "{{Sensory_Detail}}": sensory_detail,
        "{Sensory_Detail}": sensory_detail,
        "{{Character_A}}": character_info,
        "{Character_A}": character_info,
        "{{Character_B}}": "",
        "{Character_B}": "",
        "{Character}": character_info,
        "{{Prop}}": "",
        "{Prop}": "",
        "{{Comedy}}": "",
        "{Comedy}": "",
        "{{Logic_setup}}": "",
    }
    for k, v in replacements_main.items():
        template = template.replace(k, str(v))

    template = template.replace("{{Task_Phase_1}}", f"{task_1}\n(字數上限：{w1})")
    template = template.replace("{{Task_Phase_2}}", f"{task_2}\n(字數上限：{w2})")
    template = template.replace("{{Task_Phase_3}}", f"{task_3}\n(字數上限：{w3})")
    template = template.replace("{{Task_Phase_4}}", f"{task_4}\n(字數上限：{w4})")

    return template


def generate_with_gemini(user_prompt, max_words=0):
    genai.configure(api_key=GEMINI_API_KEY)
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    model = genai.GenerativeModel("gemini-2.0-flash", safety_settings=safety_settings)
    if max_words > 0:
        user_prompt += f"\n\n[重要] 請確保完整故事的總字數約為 {max_words} 字（中文字）。請嚴格控制字數，不要超過此限制。"
    response = model.generate_content(user_prompt, generation_config=genai.types.GenerationConfig(temperature=0.7))
    return response.candidates[0].content.parts[0].text.strip()


def format_output(story):
    """移除 [Story Setup] 與元數據行"""
    lines = story.split("\n")
    result = []
    skip = False
    for line in lines:
        if "[Story Setup]" in line:
            skip = True
            continue
        if skip:
            if line.strip().startswith(">") or not line.strip():
                continue
            skip = False
        if line.strip().startswith(">"):
            continue
        result.append(line)
    return "\n".join(result).strip()


def generate_one(combo, output_dir):
    """生成單一故事"""
    story_id = combo.get("story_id", "")
    story_type = combo.get("story_type", "")
    filled = fill_template(combo)
    total_words = get_total_word_limit(story_type)
    try:
        raw = generate_with_gemini(filled, max_words=total_words)
        text = format_output(raw)
    except Exception as e:
        print(f"   ❌ {story_id} 生成失敗: {e}")
        return False
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{story_id}_TW_V1.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    wc = len([c for c in text if "\u4e00" <= c <= "\u9fff"])
    print(f"   ✓ [{story_id}] 完成 - {wc} 字")
    return True


def get_all_combos():
    """取得 Story_Variables.json 所有組合（flat list）。"""
    data = load_json("Story_Variables.json")
    if isinstance(data, list):
        return data
    return data.get("Science", []) + data.get("Social", [])


def get_combo_by_story_id(story_id):
    """依 story_id 取得對應的 combo。"""
    for c in get_all_combos():
        if (c.get("story_id") or "").strip() == (story_id or "").strip():
            return c
    return None


def regenerate_science_social_stories(story_ids, output_dir=None, output_dir_suffix=""):
    """
    重新生成指定的 Science/Social 故事。
    可由 story_filter.py 呼叫，用於補齊被過濾掉的故事。

    Args:
        story_ids: 要重新生成的 story_id 列表，例如 ["SCI_PRI_01", "NEI_DRG_02"]
        output_dir: 輸出目錄；若為 None 則使用 stories_Science_Social + output_dir_suffix
        output_dir_suffix: 目錄後綴（例如 "_2"），與 output_dir 二選一使用

    Returns:
        tuple: (成功數, 失敗數)
    """
    if not story_ids:
        print("沒有需要重新生成的 Science/Social 故事。")
        return 0, 0

    combos = []
    for sid in story_ids:
        c = get_combo_by_story_id(sid)
        if c:
            combos.append(c)
        else:
            print(f"  ⚠️  找不到 story_id: {sid}")

    if not combos:
        print("無有效組合可重新生成。")
        return 0, 0

    out = output_dir or os.path.join(SCRIPT_DIR, f"stories_Science_Social{output_dir_suffix}")

    print(f"\n🔄 重新生成 {len(combos)} 個 Science/Social 故事 -> {out}")
    ok, fail = 0, 0
    for i, combo in enumerate(combos, 1):
        sid = combo.get("story_id", "")
        print(f"[{i}/{len(combos)}] {sid}...")
        if generate_one(combo, out):
            ok += 1
        else:
            fail += 1
    return ok, fail


def main():
    combos = get_all_combos()
    if not isinstance(combos, list):
        combos = combos.get("Science", []) + combos.get("Social", [])

    output_dir = os.path.join(SCRIPT_DIR, "stories_Science_Social")
    total_words = get_total_word_limit("Science") if combos else 0

    print(f"\n{'='*80}")
    print(f"📖 生成 Science/Social 故事 (共 {len(combos)} 個)")
    print(f"{'='*80}\n")
    print(f"   📏 每個故事目標字數: {total_words} 字")
    print(f"💾 輸出目錄: {output_dir}\n")

    ok, fail = 0, 0
    for i, combo in enumerate(combos, 1):
        sid = combo.get("story_id", "")
        print(f"[{i}/{len(combos)}] {sid}...")
        if generate_one(combo, output_dir):
            ok += 1
        else:
            fail += 1

    print(f"\n{'='*80}")
    print("🎉 完成!")
    print(f"   ✓ 成功: {ok} 個" + (f"   ❌ 失敗: {fail} 個" if fail else ""))
    print(f"   📁 {output_dir}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
