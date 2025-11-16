"""
測試腳本：比較並行與非並行 TTS 生成的速度

使用方法:
    python test_tts_speed.py

注意: 需要先設置 Django 環境和 TTS 服務
"""
import os
import sys
import time
import django
from pathlib import Path

# 設置 Django 環境
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from stories.tts_service import TTSService
from django.conf import settings


# 測試文字 - 包含多個段落
TEST_TEXT = """
Once upon a time, in a magical forest far away, there lived a brave little rabbit named Luna. 
Luna was known throughout the forest for her courage and kindness. Every morning, she would 
venture out to help her friends, whether they needed food, shelter, or just a friendly ear.

One sunny day, Luna discovered that the forest's magical crystal had been stolen by a mischievous 
squirrel. The crystal was the source of all the forest's magic, and without it, the flowers were 
withering and the animals were losing their special abilities. Luna knew she had to act quickly.

She gathered her friends: a wise old owl, a swift deer, and a clever fox. Together, they formed 
a plan to retrieve the crystal. The owl would scout from above, the deer would run messages 
between the team, and the fox would use her cunning to outsmart the squirrel.

After a long journey through dark caves and over rushing rivers, they finally found the squirrel's 
hideout. The squirrel was surprised to see them, but Luna approached with kindness instead of 
anger. She explained how important the crystal was to everyone in the forest, including the squirrel.

Touched by Luna's words, the squirrel realized his mistake and returned the crystal. The forest 
magic was restored, and all the animals celebrated together. From that day forward, Luna and the 
squirrel became great friends, and the forest was more harmonious than ever before.

The end of this wonderful adventure teaches us that kindness and understanding can solve even the 
most difficult problems. Sometimes, approaching others with compassion is more powerful than force.
"""


def format_time(seconds):
    """格式化時間顯示"""
    if seconds < 1:
        return f"{seconds * 1000:.2f} 毫秒"
    elif seconds < 60:
        return f"{seconds:.2f} 秒"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes} 分 {secs:.2f} 秒"


def test_non_parallel(tts_service, text, language='en', voice=None, cache_bypass=False, save_path=None):
    """測試非並行模式"""
    print("\n" + "=" * 70)
    print("🔄 測試非並行模式 (parallel=False)")
    print("=" * 70)
    
    # 如果啟用快取繞過，在文字末尾添加唯一標識符
    test_text = text
    if cache_bypass:
        test_text = text + f" [NON_PARALLEL_TEST_{int(time.time())}]"
    
    start_time = time.time()
    
    try:
        audio_content = tts_service.generate_audio(
            text=test_text,
            language=language,
            voice=voice,
            parallel=False  # 關閉並行模式
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if audio_content:
            # 獲取音訊大小
            audio_content.seek(0)
            audio_size = len(audio_content.read())
            audio_content.seek(0)
            
            # 保存音訊檔案
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(audio_content.read())
                audio_content.seek(0)
                print(f"💾 音訊已保存到: {save_path}")
            
            print(f"✅ 生成成功")
            print(f"⏱️  執行時間: {format_time(elapsed_time)}")
            print(f"📦 音訊大小: {audio_size / 1024:.2f} KB")
            return elapsed_time, True, audio_size, save_path
        else:
            print(f"❌ 生成失敗")
            return elapsed_time, False, 0, None
            
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"❌ 發生錯誤: {e}")
        return elapsed_time, False, 0, None


def test_parallel(tts_service, text, language='en', voice=None, cache_bypass=False, save_path=None):
    """測試並行模式"""
    print("\n" + "=" * 70)
    print("⚡ 測試並行模式 (parallel=True)")
    print("=" * 70)
    
    # 如果啟用快取繞過，在文字末尾添加唯一標識符
    test_text = text
    if cache_bypass:
        test_text = text + f" [PARALLEL_TEST_{int(time.time())}]"
    
    # 先檢查會分割成幾個段落
    paragraphs = tts_service._split_into_paragraphs(test_text, min_length=50)
    print(f"📝 文字將被分割為 {len(paragraphs)} 個段落")
    for i, para in enumerate(paragraphs, 1):
        print(f"   段落 {i}: {len(para)} 字元")
    
    start_time = time.time()
    
    try:
        audio_content = tts_service.generate_audio(
            text=test_text,
            language=language,
            voice=voice,
            parallel=True  # 啟用並行模式
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if audio_content:
            # 獲取音訊大小
            audio_content.seek(0)
            audio_size = len(audio_content.read())
            audio_content.seek(0)
            
            # 保存音訊檔案
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(audio_content.read())
                audio_content.seek(0)
                print(f"💾 音訊已保存到: {save_path}")
            
            print(f"✅ 生成成功")
            print(f"⏱️  執行時間: {format_time(elapsed_time)}")
            print(f"📦 音訊大小: {audio_size / 1024:.2f} KB")
            return elapsed_time, True, audio_size, save_path
        else:
            print(f"❌ 生成失敗")
            return elapsed_time, False, 0, None
            
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return elapsed_time, False, 0, None


def compare_results(non_parallel_time, parallel_time, non_parallel_success, parallel_success):
    """比較測試結果"""
    print("\n" + "=" * 70)
    print("📊 速度比較結果")
    print("=" * 70)
    
    if not non_parallel_success:
        print("❌ 非並行模式測試失敗，無法比較")
        return
    
    if not parallel_success:
        print("❌ 並行模式測試失敗，無法比較")
        return
    
    speedup = non_parallel_time / parallel_time if parallel_time > 0 else 0
    time_saved = non_parallel_time - parallel_time
    
    print(f"\n⏱️  非並行模式時間: {format_time(non_parallel_time)}")
    print(f"⚡ 並行模式時間:    {format_time(parallel_time)}")
    print(f"💾 節省時間:         {format_time(time_saved)}")
    print(f"🚀 速度提升:         {speedup:.2f}x")
    
    if speedup > 1:
        percentage = ((non_parallel_time - parallel_time) / non_parallel_time) * 100
        print(f"📈 效能提升:         {percentage:.1f}%")
    elif speedup < 1:
        percentage = ((parallel_time - non_parallel_time) / non_parallel_time) * 100
        print(f"⚠️  並行模式較慢:     {percentage:.1f}% (可能是網路延遲或 API 限制)")
    else:
        print("➡️  兩種模式速度相同")


def main():
    """主測試函數"""
    print("\n" + "=" * 70)
    print("🎙️  TTS 並行 vs 非並行速度測試")
    print("=" * 70)
    
    # 顯示配置資訊
    print(f"\n📋 測試配置:")
    print(f"   TTS Provider: {settings.TTS_PROVIDER}")
    print(f"   Cache Enabled: {settings.TTS_CACHE_ENABLED}")
    print(f"   測試文字長度: {len(TEST_TEXT)} 字元")
    print(f"   測試文字段落數: {len(TEST_TEXT.split(chr(10) + chr(10)))} 個段落")
    
    # 初始化 TTS 服務
    try:
        tts_service = TTSService()
        print(f"\n✅ TTS 服務初始化成功")
    except Exception as e:
        print(f"\n❌ TTS 服務初始化失敗: {e}")
        return
    
    # 使用快取繞過以確保公平測試
    cache_bypass = True
    print("\n💡 為了公平比較，將為每次測試添加唯一標識符以繞過快取")
    
    # 建立輸出目錄
    output_dir = Path(BASE_DIR) / 'test_output'
    output_dir.mkdir(exist_ok=True)
    
    # 生成檔案名稱（包含時間戳記）
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    non_parallel_path = output_dir / f'non_parallel_{timestamp}.mp3'
    parallel_path = output_dir / f'parallel_{timestamp}.mp3'
    
    print(f"\n📁 音訊檔案將保存到: {output_dir}")
    
    # 執行測試
    print("\n" + "=" * 70)
    print("開始測試...")
    print("=" * 70)
    
    # 測試 1: 非並行模式
    non_parallel_time, non_parallel_success, non_parallel_size, non_parallel_file = test_non_parallel(
        tts_service, TEST_TEXT, language='en', cache_bypass=cache_bypass, save_path=non_parallel_path
    )
    
    # 等待一下，避免 API 限制
    print("\n⏳ 等待 2 秒以避免 API 速率限制...")
    time.sleep(2)
    
    # 測試 2: 並行模式
    parallel_time, parallel_success, parallel_size, parallel_file = test_parallel(
        tts_service, TEST_TEXT, language='en', cache_bypass=cache_bypass, save_path=parallel_path
    )
    
    # 比較結果
    compare_results(
        non_parallel_time, 
        parallel_time, 
        non_parallel_success, 
        parallel_success
    )
    
    # 音訊大小比較
    if non_parallel_success and parallel_success:
        print("\n" + "=" * 70)
        print("📦 音訊大小比較")
        print("=" * 70)
        print(f"非並行模式: {non_parallel_size / 1024:.2f} KB")
        print(f"並行模式:   {parallel_size / 1024:.2f} KB")
        size_diff = abs(non_parallel_size - parallel_size)
        if size_diff > 0:
            print(f"大小差異:   {size_diff / 1024:.2f} KB")
            print("(差異可能來自段落間的靜音間隔)")
    
    print("\n" + "=" * 70)
    print("✅ 測試完成！")
    print("=" * 70)
    
    # 顯示保存的音訊檔案
    if non_parallel_success or parallel_success:
        print("\n" + "=" * 70)
        print("🎵 生成的音訊檔案")
        print("=" * 70)
        if non_parallel_success and non_parallel_file:
            print(f"非並行模式: {non_parallel_file}")
        if parallel_success and parallel_file:
            print(f"並行模式:   {parallel_file}")
        print("\n💡 您現在可以播放這兩個檔案來比較音質差異")
        print("   (並行模式會在段落間加入 500ms 靜音)")
    
    # 建議
    print("\n" + "=" * 70)
    print("💡 建議")
    print("=" * 70)
    if parallel_success and non_parallel_success:
        if parallel_time < non_parallel_time:
            print("✓ 並行模式較快，建議在生產環境中使用")
        else:
            print("⚠ 並行模式較慢，可能是因為:")
            print("   - API 速率限制")
            print("   - 網路延遲")
            print("   - 段落數量較少，並行化優勢不明顯")
            print("💡 對於較長的文字（多個段落），並行模式通常會更快")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被用戶中斷")
    except Exception as e:
        print(f"\n\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

