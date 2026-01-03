#!/usr/bin/env python3
"""
Test script to directly test Gemini API with story generation prompts.
This helps isolate whether the issue is with the prompt content or API configuration.
"""
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Set your API key here or use environment variable
GEMINI_API_KEY = 'REDACTED_GEMINI_API_KEY'

system_prompt = """你是一位經驗豐富、備受讚譽的童書作者。你的寫作風格兼具專業的戲劇結構和天馬行空的童趣，擅長用生動的譬喻和幽默的橋段，來講述能讓孩子們開懷大笑又深受啟發的溫暖故事。

**最高語言規則**：故事全文，包括所有角色與地點的命名，都必須**嚴格使用繁體中文**。絕不允許在回應中出現任何其他語言的字母或符號。

"""

user_prompt = """請根據以下的要求，創作一個短篇童話故事：

**核心主題**：關懷。
**故事元素**：
* **主角1**：小貓。
* **主角2**：小英雄。
* **地點**：城堡。
* **核心目標**：探索城堡並找到水晶球。

**故事結構（所有段落都需是短篇描寫）：**

1. Intro Goal：**故事的開端(短篇)**。請用生動的文字，快速建立一個充滿奇特細節的世界，並透過**一個簡短有趣的行為**來介紹**主角們 (小貓, 小英雄)** 的獨特個性。然後，清晰地確立他們要去達成的**目標**。
2. Problem Obstacle：**出現了阻礙(短篇)**。請直接描述一個**具體發生的事件**作為阻礙，這個事件可以是戲劇性的，也可以是荒謬又有趣的，並直接挑戰著主角們的目標。
3. Effort Effort：**努力的過程(短篇)**。**主角們 (小貓, 小英雄)** 共同或分別想出了一個充滿想像力的計畫來克服阻礙。請生動地描寫這個過程，並**加入一個能讓孩子發笑略為誇張的有趣橋段**。
4. Climax Climax：**故事的高潮(短篇)**。這是主角們克服困難的**關鍵時刻**。他們可能遇到了最大的挑戰，但最終憑藉著與故事**核心主題**相關的力量（例如：合作、勇氣、誠實），成功地解決了問題。
5. Ending Ending：**溫暖的結局(短篇)**。問題解決後，請描寫一個溫暖、有趣且充滿啟發的收尾。結局的啟發必須是透過**主角們的行為**展現出來的，而不是說教。

**現在請生成第一段（Intro Goal）：**
- 建立世界並介紹角色
- 確立目標
- 保持2-4個句子的長度
- 請使用繁體中文"""


def test_with_safety_settings(model_name='gemini-2.5-flash'):
    """Test with BLOCK_NONE safety settings."""
    print("=" * 80)
    print(f"🧪 TEST 1: {model_name} with BLOCK_NONE safety settings")
    print("=" * 80)

    try:
        genai.configure(api_key=GEMINI_API_KEY)

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        generation_config = genai.types.GenerationConfig(
            temperature=0.8,
            max_output_tokens=500,
        )

        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_prompt,
            safety_settings=safety_settings
        )

        print("📤 Sending request to Gemini...")
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )

        # Check if response was blocked
        if not response.candidates or len(response.candidates) == 0:
            print("❌ No candidates in response")
            print(f"Response: {response}")

            if hasattr(response, 'prompt_feedback'):
                feedback = response.prompt_feedback
                print(f"\n📋 Prompt Feedback:")
                print(f"   {feedback}")

                if hasattr(feedback, 'block_reason'):
                    print(f"\n🚫 Block Reason: {feedback.block_reason}")

                if hasattr(feedback, 'safety_ratings'):
                    print(f"\n⚠️  Safety Ratings:")
                    for rating in feedback.safety_ratings:
                        print(f"      - {rating.category}: {rating.probability}")

            return False

        candidate = response.candidates[0]
        finish_reason = getattr(candidate, 'finish_reason', None)
        safety_ratings = getattr(candidate, 'safety_ratings', [])

        print(f"\n✅ Response received!")
        print(f"   Finish reason: {finish_reason}")
        print(f"   Safety ratings: {safety_ratings}")

        if finish_reason == 2:  # SAFETY
            print("\n❌ Content was blocked by safety filters!")
            print(f"   Safety ratings details:")
            for rating in safety_ratings:
                print(f"      - {rating.category}: {rating.probability}")
            return False

        if candidate.content and candidate.content.parts:
            text = candidate.content.parts[0].text
            print(f"\n📝 Generated text ({len(text)} chars):")
            print("-" * 80)
            print(text)
            print("-" * 80)
            return True
        else:
            print("❌ No content in response")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_without_system_instruction(model_name='gemini-2.5-flash'):
    """Test by combining system + user prompts (no system_instruction)."""
    print("\n" + "=" * 80)
    print(f"🧪 TEST 2: {model_name} WITHOUT system_instruction (combined prompt)")
    print("=" * 80)

    try:
        genai.configure(api_key=GEMINI_API_KEY)

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        generation_config = genai.types.GenerationConfig(
            temperature=0.8,
            max_output_tokens=500,
        )

        model = genai.GenerativeModel(
            model_name,
            safety_settings=safety_settings
        )

        # Combine prompts
        combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

        print("📤 Sending request to Gemini (combined prompt)...")
        response = model.generate_content(
            combined_prompt,
            generation_config=generation_config
        )

        # Check if response was blocked
        if not response.candidates or len(response.candidates) == 0:
            print("❌ No candidates in response")
            if hasattr(response, 'prompt_feedback'):
                feedback = response.prompt_feedback
                print(f"\n📋 Prompt Feedback: {feedback}")
                if hasattr(feedback, 'block_reason'):
                    print(f"🚫 Block Reason: {feedback.block_reason}")
                if hasattr(feedback, 'safety_ratings'):
                    print(f"⚠️  Safety Ratings:")
                    for rating in feedback.safety_ratings:
                        print(f"      - {rating.category}: {rating.probability}")
            return False

        candidate = response.candidates[0]
        finish_reason = getattr(candidate, 'finish_reason', None)

        print(f"\n✅ Response received!")
        print(f"   Finish reason: {finish_reason}")

        if finish_reason == 2:  # SAFETY
            print("\n❌ Content was blocked by safety filters!")
            return False

        if candidate.content and candidate.content.parts:
            text = candidate.content.parts[0].text
            print(f"\n📝 Generated text ({len(text)} chars):")
            print("-" * 80)
            print(text)
            print("-" * 80)
            return True
        else:
            print("❌ No content in response")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_gemini_15_pro():
    """Test with Gemini 1.5 Pro (usually more lenient)."""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: gemini-1.5-pro with BLOCK_NONE")
    print("=" * 80)
    return test_with_safety_settings('gemini-1.5-pro')


if __name__ == '__main__':
    print("🚀 Gemini Story Generation Prompt Test")
    print("=" * 80)
    print(f"System prompt length: {len(system_prompt)} chars")
    print(f"User prompt length: {len(user_prompt)} chars")
    print("=" * 80)

    # Run tests
    test1_passed = test_with_safety_settings('gemini-2.5-flash')
    test2_passed = test_without_system_instruction('gemini-2.5-flash')
    test3_passed = test_with_gemini_15_pro()

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (gemini-2.5-flash + system_instruction): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (gemini-2.5-flash + combined prompt): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Test 3 (gemini-1.5-pro + system_instruction): {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    print("=" * 80)

    if test1_passed or test2_passed or test3_passed:
        print("\n💡 At least one test passed! Use that configuration in your story_generator.py")
    else:
        print("\n💡 All tests failed. The prompt content may need to be simplified.")
