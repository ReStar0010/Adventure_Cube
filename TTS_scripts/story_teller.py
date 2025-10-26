import os
import google.generativeai as genai
from google.cloud import texttospeech
from dotenv import load_dotenv
from playsound import playsound

# --- 1. 初始化與設定 ---

def initialize_clients():
    """
    載入環境變數並初始化 Gemini 和 Google Cloud TTS 的客戶端。
    """
    # 載入 .env 檔案中的環境變數
    load_dotenv()

    # 設定 Gemini API 金鑰
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("找不到 Gemini API 金鑰，請檢查 .env 檔案。")
    genai.configure(api_key=gemini_api_key)

    # 設定 Google Cloud 憑證路徑
    # 這個環境變數會被 google-cloud-texttospeech 套件自動讀取
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"
    
    # 初始化 TTS 客戶端
    try:
        tts_client = texttospeech.TextToSpeechClient()
        return tts_client
    except Exception as e:
        print(f"無法初始化 Google Cloud TTS 客戶端，請檢查 gcp_credentials.json 檔案是否存在且有效。")
        print(f"錯誤訊息: {e}")
        return None

# --- 2. 生成故事 ---

def generate_story(prompt: str) -> str:
    """
    使用 Gemini API 根據使用者提示生成故事。
    """
    print("🤖 正在為您生成故事，請稍候...")
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            f"請根據以下的情境與要求，生成一個適合朗讀、約150-200字的短篇故事：\n\n{prompt}"
        )
        story_text = response.text
        print("✅ 故事生成完畢！")
        return story_text
    except Exception as e:
        print(f"❌ 生成故事時發生錯誤: {e}")
        return None

# --- 3. 生成語音 ---

def synthesize_speech(text: str, output_filename: str = "story_audio.mp3"):
    """
    使用 Google Cloud TTS 將文字轉換為語音並儲存為 MP3 檔案。
    """
    print("🎙️ 正在將故事轉換為語音...")
    try:
        tts_client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # 設定語音參數 (可根據需求修改)
        # 語言: cmn-TW (台灣繁體中文)
        # 語音名稱: cmn-TW-Wavenet-A (標準女聲)
        # 更多語音選項: https://cloud.google.com/text-to-speech/docs/voices
        voice = texttospeech.VoiceSelectionParams(
            language_code="cmn-TW",
            name="cmn-TW-Wavenet-A",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # 將語音內容寫入檔案
        with open(output_filename, "wb") as out:
            out.write(response.audio_content)
        
        print(f"✅ 語音檔案已儲存為 {output_filename}")
        return output_filename
    except Exception as e:
        print(f"❌ 生成語音時發生錯誤: {e}")
        return None

# --- 4. 主程式執行流程 ---

def main():
    """
    程式主進入點
    """
    print("--- 歡迎來到 AI 故事生成器 ---")
    
    # 初始化 API
    tts_client = initialize_clients()
    if not tts_client:
        return # 初始化失敗則結束程式

    # 1. 獲取使用者輸入
    user_prompt = input("請輸入您想要的故事情境與要求 (例如：一個關於迷路小貓找到回家的路的溫馨故事):\n> ")

    if not user_prompt:
        print("您沒有輸入任何內容，程式結束。")
        return

    # 2. 生成故事
    story = generate_story(user_prompt)

    if story:
        # 4. 顯示故事結果
        print("\n--- ✨ 為您生成的故事 ✨ ---\n")
        print(story)
        print("\n---------------------------\n")

        # 3. 生成語音
        audio_file = synthesize_speech(story)

        if audio_file:
            # 4. 播放語音
            try:
                print("🔊 即將為您播放故事...")
                playsound(audio_file)
                print("✅ 播放完畢。")
            except Exception as e:
                print(f"❌ 播放音訊時發生錯誤: {e}")
                print(f"您可以手動開啟檔案來聆聽: {audio_file}")

if __name__ == "__main__":
    main()
