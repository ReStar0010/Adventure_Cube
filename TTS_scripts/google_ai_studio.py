#!/usr/bin/env python3
"""
使用 Gemini Preview TTS 生成語音音頻

安裝依賴:
    pip install google-genai

使用方法:
    1. 設置環境變數:
       export GEMINI_API_KEY="your-api-key-here"
    
    2. 基本使用（單說話人）:
       python google_ai_studio.py --text "你好，這是一個測試"
    
    3. 多說話人對話:
       python google_ai_studio.py --text "Speaker 1: 你好！Speaker 2: 很高興見到你！" --multi-speaker
    
    4. 自定義語音:
       python google_ai_studio.py --text "測試文本" --voice "Zephyr"
    
    5. 使用風格指示:
       python google_ai_studio.py --text "你好" --style "溫暖且友好"
    
    6. 調整溫度參數:
       python google_ai_studio.py --text "測試" --temperature 0.8
    
    7. 使用不同模型:
       python google_ai_studio.py --text "測試" --model gemini-2.5-pro-preview-tts
    
    8. 指定輸出文件:
       python google_ai_studio.py --text "測試" --output output.wav

可調整的 TTS 參數:
    1. 語音選擇 (--voice):
       - Zephyr: 溫暖、友好的女性聲音（預設）
       - Puck: 活潑、年輕的聲音
       - Charon: 深沉、成熟的聲音
       - Fenrir: 強壯、有力的聲音
       - Kore: 清晰、專業的女性聲音
    
    2. 模型選擇 (--model):
       - gemini-2.5-flash-preview-tts: 快速響應（預設）
       - gemini-2.5-pro-preview-tts: 更高品質
    
    3. 風格指示 (--style):
       用自然語言描述語音風格，例如：
       - "明亮且熱情" - 適合活潑的內容
       - "沉穩且專業" - 適合正式場合
       - "溫暖且友好" - 適合故事講述
       - "活潑且年輕" - 適合兒童內容
       - "溫柔且親切" - 適合安慰性內容
    
    4. 溫度參數 (--temperature):
       - 範圍: 0.0-2.0（預設: 1.0）
       - 較低值（0.0-0.5）: 更一致、可預測
       - 中等值（0.5-1.5）: 平衡自然度和一致性
       - 較高值（1.5-2.0）: 更多樣、更有創造性
    
    5. 多說話人模式 (--multi-speaker):
       - 自動檢測文本中的 "Speaker 1:", "Speaker 2:" 等標記
       - 可自定義每個說話人的語音 (--speaker-voices)
"""

import argparse
import mimetypes
import os
import re
import struct
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ 錯誤: 未安裝 google-genai 套件")
    print("   請執行: pip install google-genai")
    sys.exit(1)


def save_binary_file(file_name: str, data: bytes):
    """保存二進制文件"""
    try:
        with open(file_name, "wb") as f:
            f.write(data)
        file_size = len(data) / 1024
        print(f"✅ 文件已保存: {file_name} ({file_size:.2f} KB)")
    except Exception as e:
        print(f"❌ 保存文件失敗: {e}")


def generate_audio(
    text: str,
    api_key: Optional[str] = None,
    output_file: Optional[str] = None,
    voice_name: str = "Zephyr",
    multi_speaker: bool = False,
    temperature: float = 1.0,
    model: str = "gemini-2.5-flash-preview-tts",
    style_instruction: Optional[str] = None,
    custom_speaker_voices: Optional[dict] = None,
):
    """
    使用 Gemini Preview TTS 生成音頻
    
    Args:
        text: 要轉換為語音的文本
        api_key: Gemini API 密鑰（如果為 None，則從環境變數讀取）
        output_file: 輸出文件路徑（如果為 None，則自動生成）
        voice_name: 語音名稱（單說話人模式）
        multi_speaker: 是否使用多說話人模式
        temperature: 生成溫度（0.0-2.0），控制語音的多樣性和自然度
        model: 使用的模型（預設: gemini-2.5-flash-preview-tts，也可用 gemini-2.5-pro-preview-tts）
        style_instruction: 風格指示（用自然語言描述語音風格，例如："明亮且熱情"、"沉穩且專業"、"溫暖且友好"）
        custom_speaker_voices: 自定義說話人語音映射（多說話人模式），格式：{"Speaker 1": "Zephyr", "Speaker 2": "Puck"}
    """
    # 獲取 API 密鑰
    if api_key is None:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ 錯誤: 未找到 GEMINI_API_KEY")
        print("   請設置環境變數: export GEMINI_API_KEY='your-api-key'")
        print("   或使用 --api-key 參數")
        sys.exit(1)
    
    # 初始化客戶端
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"❌ 初始化 Gemini 客戶端失敗: {e}")
        sys.exit(1)
    
    # 構建文本內容（如果提供了風格指示，將其添加到文本中）
    final_text = text
    if style_instruction:
        # 將風格指示添加到文本開頭
        final_text = f"Read aloud in a {style_instruction} tone: {text}"
        print(f"🎨 風格指示: {style_instruction}")
    
    # 構建內容
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=final_text)],
        ),
    ]
    
    # 構建語音配置
    if multi_speaker:
        # 多說話人模式：自動檢測文本中的 "Speaker 1:", "Speaker 2:" 等標記
        speaker_voice_configs = []
        
        # 檢測所有說話人
        speaker_pattern = re.compile(r'(Speaker\s+\d+):', re.IGNORECASE)
        speakers = set(speaker_pattern.findall(text))
        
        if not speakers:
            print("⚠️  警告: 未檢測到 'Speaker X:' 格式，將使用單說話人模式")
            multi_speaker = False
        else:
            # 預設語音列表
            default_voices = ["Zephyr", "Puck", "Charon", "Fenrir", "Kore"]
            
            for i, speaker in enumerate(sorted(speakers, key=lambda x: int(re.search(r'\d+', x).group()))):
                # 如果提供了自定義語音映射，使用它；否則使用預設
                if custom_speaker_voices and speaker in custom_speaker_voices:
                    voice = custom_speaker_voices[speaker]
                else:
                    voice = default_voices[i % len(default_voices)]
                
                speaker_voice_configs.append(
                    types.SpeakerVoiceConfig(
                        speaker=speaker,
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        ),
                    )
                )
                print(f"🎤 {speaker}: 使用語音 '{voice}'")
    
    # 構建生成配置
    if multi_speaker:
        speech_config = types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=speaker_voice_configs
            ),
        )
    else:
        # 單說話人模式
        speech_config = types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice_name
                )
            ),
        )
        print(f"🎤 使用語音: {voice_name}")
    
    generate_content_config = types.GenerateContentConfig(
        temperature=temperature,
        response_modalities=["audio"],
        speech_config=speech_config,
    )
    
    # 生成音頻
    print(f"🎙️  正在生成音頻...")
    print(f"   模型: {model}")
    print(f"   文本長度: {len(text)} 字符")
    print(f"   溫度: {temperature}")
    
    audio_chunks = []
    file_index = 0
    
    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            
            # 處理音頻數據
            if (chunk.candidates[0].content.parts[0].inline_data 
                and chunk.candidates[0].content.parts[0].inline_data.data):
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                
                if file_extension is None:
                    file_extension = ".wav"
                    data_buffer = convert_to_wav(inline_data.data, inline_data.mime_type)
                
                audio_chunks.append((data_buffer, file_extension))
                file_index += 1
                print(f"   收到音頻片段 {file_index}")
            
            # 處理文本響應（如果有）
            if hasattr(chunk, 'text') and chunk.text:
                print(f"📝 {chunk.text}")
    
    except Exception as e:
        print(f"❌ 生成音頻時發生錯誤: {e}")
        sys.exit(1)
    
    if not audio_chunks:
        print("❌ 未收到任何音頻數據")
        sys.exit(1)
    
    # 保存音頻文件
    if len(audio_chunks) == 1:
        # 單個音頻文件
        data_buffer, file_extension = audio_chunks[0]
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"gemini_tts_{timestamp}{file_extension}"
        
        save_binary_file(output_file, data_buffer)
    else:
        # 多個音頻片段
        print(f"📦 收到 {len(audio_chunks)} 個音頻片段，將分別保存")
        
        base_name = output_file or "gemini_tts"
        if output_file:
            base_name = Path(output_file).stem
        
        for i, (data_buffer, file_extension) in enumerate(audio_chunks):
            chunk_file = f"{base_name}_part{i+1}{file_extension}"
            save_binary_file(chunk_file, data_buffer)
        
        print(f"💡 提示: 可以使用音頻編輯軟體將這些片段合併")

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def main():
    """主函數：解析命令行參數並生成音頻"""
    parser = argparse.ArgumentParser(
        description='使用 Gemini Preview TTS 生成語音音頻',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 基本使用（需要設置環境變數 GEMINI_API_KEY）
  export GEMINI_API_KEY="your-api-key"
  python "AI Studio Code.py" --text "你好，這是一個測試"
  
  # 使用 API 密鑰參數
  python "AI Studio Code.py" --text "Hello world" --api-key "your-api-key"
  
  # 多說話人對話
  python "AI Studio Code.py" --text "Speaker 1: 你好！Speaker 2: 很高興見到你！" --multi-speaker
  
  # 自定義語音和輸出文件
  python "AI Studio Code.py" --text "測試文本" --voice "Puck" --output my_audio.wav
  
  # 從文件讀取文本
  python google_ai_studio.py --text-file story.txt --output story_audio.wav
  
  # 使用風格指示
  python google_ai_studio.py --text "你好世界" --style "溫暖且友好"
  
  # 使用不同的模型
  python google_ai_studio.py --text "測試" --model gemini-2.5-pro-preview-tts
  
  # 多說話人模式 + 自定義語音映射
  python google_ai_studio.py --text "Speaker 1: 你好！Speaker 2: 很高興見到你！" \
    --multi-speaker --speaker-voices "Speaker 1:Zephyr,Speaker 2:Puck"

可用的預設語音:
  - Zephyr: 溫暖、友好的女性聲音（預設）
  - Puck: 活潑、年輕的聲音
  - Charon: 深沉、成熟的聲音
  - Fenrir: 強壯、有力的聲音
  - Kore: 清晰、專業的女性聲音

可用的模型:
  - gemini-2.5-flash-preview-tts: 快速響應（預設）
  - gemini-2.5-pro-preview-tts: 更高品質

風格指示範例:
  - "明亮且熱情" - 適合活潑的內容
  - "沉穩且專業" - 適合正式場合
  - "溫暖且友好" - 適合故事講述
  - "活潑且年輕" - 適合兒童內容
  - "溫柔且親切" - 適合安慰性內容

注意:
  - 多說話人模式需要文本中包含 "Speaker 1:", "Speaker 2:" 等標記
  - 如果未指定輸出文件，將自動生成帶時間戳的文件名
  - 溫度參數影響語音的自然度和多樣性（0.0-2.0）
        """
    )
    
    parser.add_argument(
        '--text', '-t',
        type=str,
        help='要轉換為語音的文本'
    )
    
    parser.add_argument(
        '--text-file', '-f',
        type=str,
        help='包含文本的文件路徑（將讀取文件內容作為文本）'
    )
    
    parser.add_argument(
        '--api-key', '-k',
        type=str,
        default=None,
        help='Gemini API 密鑰（如果未提供，將從環境變數 GEMINI_API_KEY 讀取）'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='輸出音頻文件路徑（預設: 自動生成帶時間戳的文件名）'
    )
    
    parser.add_argument(
        '--voice', '-v',
        type=str,
        default='Zephyr',
        choices=['Zephyr', 'Puck', 'Charon', 'Fenrir', 'Kore'],
        help='語音名稱（單說話人模式，預設: Zephyr）'
    )
    
    parser.add_argument(
        '--multi-speaker',
        action='store_true',
        help='啟用多說話人模式（自動檢測文本中的 Speaker 1:, Speaker 2: 等標記）'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        default=1.0,
        help='生成溫度（0.0-2.0，預設: 1.0）。較低值更一致，較高值更多樣'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='gemini-2.5-flash-preview-tts',
        choices=['gemini-2.5-flash-preview-tts', 'gemini-2.5-pro-preview-tts'],
        help='使用的 TTS 模型（預設: gemini-2.5-flash-preview-tts）'
    )
    
    parser.add_argument(
        '--style',
        type=str,
        default=None,
        help='語音風格指示（用自然語言描述，例如："明亮且熱情"、"沉穩且專業"、"溫暖且友好"、"活潑且年輕"）'
    )
    
    parser.add_argument(
        '--speaker-voices',
        type=str,
        default=None,
        help='自定義說話人語音映射（多說話人模式），格式：Speaker 1:Zephyr,Speaker 2:Puck'
    )
    
    args = parser.parse_args()
    
    # 驗證參數
    if not args.text and not args.text_file:
        parser.error("必須提供 --text 或 --text-file 參數")
    
    if args.text and args.text_file:
        parser.error("不能同時使用 --text 和 --text-file 參數")
    
    # 讀取文本
    if args.text_file:
        try:
            with open(args.text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            print(f"📄 從文件讀取文本: {args.text_file} ({len(text)} 字符)")
        except Exception as e:
            print(f"❌ 讀取文件失敗: {e}")
            sys.exit(1)
    else:
        text = args.text
    
    # 驗證溫度範圍
    if args.temperature < 0.0 or args.temperature > 2.0:
        print(f"⚠️  警告: 溫度值 {args.temperature} 超出建議範圍 (0.0-2.0)，將使用該值")
    
    # 解析自定義說話人語音映射
    custom_speaker_voices = None
    if args.speaker_voices:
        try:
            custom_speaker_voices = {}
            for mapping in args.speaker_voices.split(','):
                if ':' in mapping:
                    speaker, voice = mapping.split(':', 1)
                    custom_speaker_voices[speaker.strip()] = voice.strip()
            print(f"🎤 自定義說話人語音映射: {custom_speaker_voices}")
        except Exception as e:
            print(f"⚠️  警告: 解析說話人語音映射失敗: {e}，將使用預設映射")
            custom_speaker_voices = None
    
    # 生成音頻
    generate_audio(
        text=text,
        api_key=args.api_key,
        output_file=args.output,
        voice_name=args.voice,
        multi_speaker=args.multi_speaker,
        temperature=args.temperature,
        model=args.model,
        style_instruction=args.style,
        custom_speaker_voices=custom_speaker_voices,
    )


if __name__ == "__main__":
    main()
