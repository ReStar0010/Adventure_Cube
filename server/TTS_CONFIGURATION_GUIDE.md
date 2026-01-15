# TTS (Text-to-Speech) 配置指南

## 問題：語音聽起來像機器人？

目前默認使用的是 `gTTS`（免費但品質較低）。要獲得更好的語音品質，建議切換到 **Azure Cognitive Services** 或 **Google Vertex AI**。

## 快速解決方案

### 選項 1：使用 Azure Cognitive Services（推薦）

Azure 提供高品質的神經語音（Neural Voices），聽起來更自然、有情感。

#### 步驟 1：獲取 Azure 憑證

1. 前往 [Azure Portal](https://portal.azure.com/)
2. 創建一個 "Speech Services" 資源
3. 獲取：
   - **Key**（金鑰）
   - **Region**（區域，例如：`eastus`, `westus2`）

#### 步驟 2：安裝依賴

```bash
pip install azure-cognitiveservices-speech
```

#### 步驟 3：配置環境變數

在 `.env` 文件中添加：

```env
TTS_PROVIDER=azure
AZURE_SPEECH_KEY=your_azure_key_here
AZURE_SPEECH_REGION=your_azure_region_here
```

#### 步驟 4：重啟服務器

```bash
python manage.py runserver
```

### 選項 2：使用 Google Vertex AI

Google Vertex AI 也提供高品質的 Neural2 語音。

#### 步驟 1：設置 Google Cloud 憑證

1. 在 [Google Cloud Console](https://console.cloud.google.com/) 創建項目
2. 啟用 "Cloud Text-to-Speech API"
3. 創建服務帳戶並下載 JSON 憑證文件

#### 步驟 2：安裝依賴

```bash
pip install google-cloud-texttospeech
```

#### 步驟 3：配置環境變數

在 `.env` 文件中添加：

```env
TTS_PROVIDER=vertex_ai
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
VERTEX_AI_PROJECT_ID=your-project-id
VERTEX_AI_LOCATION=us-central1
```

#### 步驟 4：重啟服務器

```bash
python manage.py runserver
```

## 語音品質對比

| 服務 | 品質 | 自然度 | 情感表達 | 成本 |
|------|------|--------|----------|------|
| gTTS | ⭐⭐ | 低 | 無 | 免費 |
| Azure Neural | ⭐⭐⭐⭐⭐ | 高 | 優秀 | 按使用量付費 |
| Vertex AI Neural2 | ⭐⭐⭐⭐⭐ | 高 | 優秀 | 按使用量付費 |

## 可用的語音選項

### Azure 推薦語音（適合兒童故事）

- **英文**：
  - `en-US-AriaNeural` - 溫暖、自然的女性聲音（默認）
  - `en-US-JennyNeural` - 友好、親切的女性聲音
  - `en-US-GuyNeural` - 溫暖的男性聲音

- **繁體中文**：
  - `zh-TW-HsiaoChenNeural` - 溫暖、友好的女性聲音（默認）
  - `zh-TW-YunJheNeural` - 親切的男性聲音

- **簡體中文**：
  - `zh-CN-XiaoxiaoNeural` - 富有表現力的女性聲音（默認）

### Vertex AI 推薦語音

- **英文**：
  - `en-US-Neural2-F` - 溫暖、友好的女性聲音（默認）
  - `en-US-Neural2-D` - 友好的男性聲音

- **繁體中文**：
  - `zh-TW-Standard-B` - 溫暖的女性聲音（默認）

## 自定義語音參數

### Azure SSML 參數

代碼中已自動應用以下優化：

- **語速**：90%（更適合講故事）
- **音調**：+5%（更溫暖、友好）
- **自動停頓**：句子間自然停頓

### Vertex AI 參數

- **語速**：90%（更適合講故事）
- **音調**：+2 半音（更溫暖）
- **音量增益**：+3dB（更清晰）

## 測試不同語音

你可以在生成音頻時指定不同的語音：

```python
# 在 views.py 中，可以傳遞 voice 參數
tts_service.generate_audio(
    text=story_text,
    language='zh-TW',
    voice='zh-TW-HsiaoYuNeural'  # 嘗試不同的語音
)
```

## 成本估算

### Azure Speech Services

- **免費額度**：每月 50 萬字符
- **付費**：$4/100 萬字符（標準神經語音）
- **典型故事**：約 500-1000 字符
- **每月可生成**：約 500-1000 個故事（免費額度內）

### Google Vertex AI

- **免費額度**：每月 400 萬字符
- **付費**：$4/100 萬字符（Neural2）
- **典型故事**：約 500-1000 字符
- **每月可生成**：約 4000-8000 個故事（免費額度內）

## 故障排除

### 問題：Azure TTS 失敗，回退到 gTTS

**解決方案**：
1. 檢查 `AZURE_SPEECH_KEY` 和 `AZURE_SPEECH_REGION` 是否正確設置
2. 確認 Azure 帳戶有足夠的額度
3. 檢查網絡連接

### 問題：Vertex AI TTS 失敗

**解決方案**：
1. 確認 `GOOGLE_APPLICATION_CREDENTIALS` 路徑正確
2. 確認已啟用 "Cloud Text-to-Speech API"
3. 檢查項目 ID 和區域設置

## 進一步優化

如果需要更進階的語音控制，可以修改 `tts_service.py` 中的 `_create_ssml_for_story` 方法來：

- 調整特定詞語的語速和音調
- 添加情感標記
- 控制停頓時間
- 添加背景音樂（需要額外處理）

## 總結

**強烈建議**：切換到 Azure 或 Vertex AI 以獲得更好的語音品質。免費額度通常足夠開發和測試使用。

