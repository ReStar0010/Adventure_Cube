#!/usr/bin/env python3
"""
批量使用 Gemini Preview TTS 生成語音音頻

安裝依賴:
    pip install google-genai

使用方法:
    1. 設置環境變數:
       export GEMINI_API_KEY="your-api-key-here"
    
    2. 基本使用（處理 0110_Stroies 目錄下的所有文件）:
       python google_ai_studio_batched.py
    
    3. 指定輸入和輸出目錄:
       python google_ai_studio_batched.py --input-dir 0110_Stroies --output-dir audio_output
    
    4. 自定義語音和模型:
       python google_ai_studio_batched.py --voice "Puck" --model gemini-2.5-pro-preview-tts
    
    5. 使用風格指示:
       python google_ai_studio_batched.py --style "溫暖且友好"
    
    6. 並行處理（加速批量生成）:
       python google_ai_studio_batched.py --workers 8
"""

import argparse
import mimetypes
import os
import re
import struct
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import List, Optional, Tuple

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
        return True
    except Exception as e:
        print(f"❌ 保存文件失敗: {e}")
        return False


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
    for param in parts:  # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass  # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass  # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}


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
) -> Tuple[bool, Optional[str]]:
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
    
    Returns:
        Tuple[bool, Optional[str]]: (成功與否, 輸出文件路徑或錯誤訊息)
    """
    # 獲取 API 密鑰
    if api_key is None:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        error_msg = "未找到 GEMINI_API_KEY"
        print(f"❌ 錯誤: {error_msg}")
        return False, error_msg
    
    # 初始化客戶端
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        error_msg = f"初始化 Gemini 客戶端失敗: {e}"
        print(f"❌ {error_msg}")
        return False, error_msg
    
    # 構建文本內容（如果提供了風格指示，將其添加到文本中）
    final_text = text
    if style_instruction:
        # 將風格指示添加到文本開頭
        final_text = f"Read aloud in a {style_instruction} tone: {text}"
    
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
    
    generate_content_config = types.GenerateContentConfig(
        temperature=temperature,
        response_modalities=["audio"],
        speech_config=speech_config,
    )
    
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
    
    except Exception as e:
        error_msg = f"生成音頻時發生錯誤: {e}"
        print(f"❌ {error_msg}")
        return False, error_msg
    
    if not audio_chunks:
        error_msg = "未收到任何音頻數據"
        print(f"❌ {error_msg}")
        return False, error_msg
    
    # 保存音頻文件
    if len(audio_chunks) == 1:
        # 單個音頻文件
        data_buffer, file_extension = audio_chunks[0]
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"gemini_tts_{timestamp}{file_extension}"
        
        if save_binary_file(output_file, data_buffer):
            return True, output_file
        else:
            return False, "保存文件失敗"
    else:
        # 多個音頻片段
        print(f"📦 收到 {len(audio_chunks)} 個音頻片段，將分別保存")
        
        base_name = output_file or "gemini_tts"
        if output_file:
            base_name = Path(output_file).stem
        
        saved_files = []
        for i, (data_buffer, file_extension) in enumerate(audio_chunks):
            chunk_file = f"{base_name}_part{i+1}{file_extension}"
            if save_binary_file(chunk_file, data_buffer):
                saved_files.append(chunk_file)
        
        if saved_files:
            return True, base_name  # 返回基礎名稱
        else:
            return False, "保存文件失敗"


def _process_single_file(
    txt_file: Path,
    output_path: Path,
    file_index: int,
    total_files: int,
    api_key: Optional[str],
    voice_name: str,
    multi_speaker: bool,
    temperature: float,
    model: str,
    style_instruction: Optional[str],
    custom_speaker_voices: Optional[dict],
    print_lock: Lock,
) -> Tuple[bool, str]:
    """
    處理單個文件的輔助函數（用於並行處理）
    
    Returns:
        Tuple[bool, str]: (成功與否, 文件名或錯誤訊息)
    """
    with print_lock:
        print(f"\n[{file_index}/{total_files}] 處理: {txt_file.name}")
    
    # 讀取文本內容
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read()
        with print_lock:
            print(f"   文本長度: {len(text)} 字符")
    except Exception as e:
        with print_lock:
            print(f"❌ 讀取文件失敗: {e}")
        return False, txt_file.name
    
    # 生成輸出文件名
    output_filename = txt_file.stem + ".wav"
    output_file = output_path / output_filename
    
    # 生成音頻
    success, result = generate_audio(
        text=text,
        api_key=api_key,
        output_file=str(output_file),
        voice_name=voice_name,
        multi_speaker=multi_speaker,
        temperature=temperature,
        model=model,
        style_instruction=style_instruction,
        custom_speaker_voices=custom_speaker_voices,
    )
    
    if success:
        with print_lock:
            print(f"✅ 成功: {output_file.name}")
        return True, txt_file.name
    else:
        with print_lock:
            print(f"❌ 失敗: {result}")
        return False, txt_file.name


def process_batch(
    input_dir: str,
    output_dir: str,
    api_key: Optional[str] = None,
    voice_name: str = "Zephyr",
    multi_speaker: bool = False,
    temperature: float = 1.0,
    model: str = "gemini-2.5-flash-preview-tts",
    style_instruction: Optional[str] = None,
    custom_speaker_voices: Optional[dict] = None,
    max_workers: int = 4,
) -> Tuple[int, int]:
    """
    批量處理目錄下的所有文本文件
    
    Args:
        input_dir: 輸入目錄路徑
        output_dir: 輸出目錄路徑
        api_key: Gemini API 密鑰
        voice_name: 語音名稱
        multi_speaker: 是否使用多說話人模式
        temperature: 生成溫度
        model: 使用的模型
        style_instruction: 風格指示
        custom_speaker_voices: 自定義說話人語音映射
        max_workers: 最大並行工作線程數（預設: 4）
    
    Returns:
        Tuple[int, int]: (成功數量, 失敗數量)
    """
    # 驗證輸入目錄
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"❌ 錯誤: 輸入目錄不存在: {input_dir}")
        return 0, 0
    
    if not input_path.is_dir():
        print(f"❌ 錯誤: 輸入路徑不是目錄: {input_dir}")
        return 0, 0
    
    # 創建輸出目錄
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 獲取所有 .txt 文件
    txt_files = list(input_path.glob("*.txt"))
    
    if not txt_files:
        print(f"⚠️  警告: 在 {input_dir} 中未找到任何 .txt 文件")
        return 0, 0
    
    print(f"📁 找到 {len(txt_files)} 個文本文件")
    print(f"📂 輸出目錄: {output_dir}")
    if style_instruction:
        print(f"🎨 風格指示: {style_instruction}")
    print(f"🎤 語音: {voice_name}")
    print(f"🤖 模型: {model}")
    print(f"⚡ 並行工作線程數: {max_workers}")
    print("-" * 60)
    
    success_count = 0
    fail_count = 0
    failed_files = []
    print_lock = Lock()
    
    # 使用線程池並行處理文件
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任務
        future_to_file = {
            executor.submit(
                _process_single_file,
                txt_file,
                output_path,
                i + 1,
                len(txt_files),
                api_key,
                voice_name,
                multi_speaker,
                temperature,
                model,
                style_instruction,
                custom_speaker_voices,
                print_lock,
            ): txt_file
            for i, txt_file in enumerate(txt_files)
        }
        
        # 收集結果
        for future in as_completed(future_to_file):
            success, file_name = future.result()
            if success:
                success_count += 1
            else:
                fail_count += 1
                failed_files.append(file_name)
    
    # 顯示處理摘要
    print("\n" + "=" * 60)
    print("📊 處理摘要:")
    print(f"   ✅ 成功: {success_count} 個文件")
    print(f"   ❌ 失敗: {fail_count} 個文件")
    
    if failed_files:
        print(f"\n失敗的文件:")
        for file in failed_files:
            print(f"   - {file}")
    
    return success_count, fail_count


def main():
    """主函數：解析命令行參數並批量處理文件"""
    parser = argparse.ArgumentParser(
        description='批量使用 Gemini Preview TTS 生成語音音頻',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 基本使用（處理 0110_Stroies 目錄下的所有文件）
  export GEMINI_API_KEY="your-api-key"
  python google_ai_studio_batched.py
  
  # 指定輸入和輸出目錄
  python google_ai_studio_batched.py --input-dir 0110_Stroies --output-dir audio_output
  
  # 自定義語音和模型
  python google_ai_studio_batched.py --voice "Puck" --model gemini-2.5-pro-preview-tts
  
  # 使用風格指示
  python google_ai_studio_batched.py --style "溫暖且友好"
  
  # 多說話人模式
  python google_ai_studio_batched.py --multi-speaker
  
  # 並行處理（使用 8 個工作線程加速處理）
  python google_ai_studio_batched.py --workers 8

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
        """
    )
    
    # 獲取腳本所在目錄
    script_dir = Path(__file__).parent
    
    parser.add_argument(
        '--input-dir', '-i',
        type=str,
        default=str(script_dir / "0110_Stroies"),
        help='輸入目錄路徑（預設: 0110_Stroies）'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default=str(script_dir / "audio_output"),
        help='輸出目錄路徑（預設: audio_output）'
    )
    
    parser.add_argument(
        '--api-key', '-k',
        type=str,
        default=None,
        help='Gemini API 密鑰（如果未提供，將從環境變數 GEMINI_API_KEY 讀取）'
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
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='並行處理的工作線程數（預設: 4）。建議值：2-8，取決於 API 速率限制和網絡帶寬'
    )
    
    args = parser.parse_args()
    
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
    
    # 驗證並行度
    if args.workers < 1:
        print(f"⚠️  警告: 工作線程數 {args.workers} 無效，將使用 1")
        args.workers = 1
    elif args.workers > 16:
        print(f"⚠️  警告: 工作線程數 {args.workers} 過高，建議使用 2-8 之間的值")
    
    # 批量處理
    success_count, fail_count = process_batch(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        api_key=args.api_key,
        voice_name=args.voice,
        multi_speaker=args.multi_speaker,
        temperature=args.temperature,
        model=args.model,
        style_instruction=args.style,
        custom_speaker_voices=custom_speaker_voices,
        max_workers=args.workers,
    )
    
    # 退出碼
    if fail_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
