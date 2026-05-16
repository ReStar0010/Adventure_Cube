# Azure TTS 設定指南

## 問題

執行 `tts_azure_tuned.py` 時出現 401 認證錯誤，因為沒有設定有效的 Azure 憑證。

## 解決方案

### 步驟 1：取得 Azure 憑證

1. 前往 [Azure Portal](https://portal.azure.com/)
2. 搜尋並選擇 **Speech Services**
3. 如果沒有，點擊「建立」創建新的 Speech Services 資源
4. 進入資源後，點擊左側選單的 **Keys and Endpoint**
5. 複製以下資訊：
   - **Key 1** 或 **Key 2**（任選一個）
   - **Location/Region**（例如：eastus、westus2、southeastasia）

### 步驟 2：設定環境變數（推薦）

在終端機中執行：

```bash
# 設定 Azure 憑證
export AZURE_SPEECH_KEY='your_actual_key_here'
export AZURE_SPEECH_REGION='eastus'  # 替換成您的實際 region

# 驗證設定
python3 test_azure_credentials.py
```

### 步驟 3：測試連線

```bash
# 應該顯示 "Connection successful!"
python3 test_azure_credentials.py
```

### 步驟 4：使用 tts_azure_tuned.py

設定好憑證後，就可以使用腳本了：

```bash
# 基本使用
python3 tts_azure_tuned.py --text "測試文本"

# 調整參數
python3 tts_azure_tuned.py \
  --text "從前，在一個遙遠的魔法森林裡，住著一隻勇敢的小兔子。" \
  --voice zh-TW-HsiaoChenNeural \
  --rate 0.9 \
  --pitch 5 \
  --volume 10 \
  --express-as-style cheerful \
  --output my_test.mp3
```

## 替代方案：使用命令列參數

如果不想設定環境變數，可以直接在命令中提供：

```bash
python3 tts_azure_tuned.py \
  --azure-key YOUR_ACTUAL_KEY \
  --azure-region eastus \
  --text "測試文本"
```

## 常見問題

### Q: 為什麼會出現 401 錯誤？

A: 401 錯誤表示認證失敗，可能原因：
- API key 無效或過期
- Region 設定錯誤
- 沒有設定環境變數

### Q: 如何確認憑證是否有效？

A: 執行測試腳本：

```bash
python3 test_azure_credentials.py
```

如果顯示 "Connection successful!"，表示憑證有效。

### Q: 環境變數設定後為什麼還是無效？

A: 環境變數只在當前終端機 session 有效。如果開啟新的終端機，需要重新設定。

要永久設定，可以加入到 shell 配置檔：

```bash
# For bash
echo 'export AZURE_SPEECH_KEY="your_key"' >> ~/.bashrc
echo 'export AZURE_SPEECH_REGION="eastus"' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'export AZURE_SPEECH_KEY="your_key"' >> ~/.zshrc
echo 'export AZURE_SPEECH_REGION="eastus"' >> ~/.zshrc
source ~/.zshrc
```

### Q: 可以使用 .env 檔案嗎？

A: 可以。創建 `.env` 檔案：

```bash
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=eastus
```

然後在執行前載入：

```bash
export $(cat .env | xargs)
python3 tts_azure_tuned.py --text "測試"
```

## 成本

- **免費額度**：每月 50 萬字符
- **付費**：$4/100 萬字符（標準神經語音）
- **典型故事**：約 500-1000 字符

每月免費額度可生成約 500-1000 個故事。

## 支援

如有問題，請檢查：
1. Azure Portal 中的 Speech Services 資源狀態
2. API key 是否正確複製（沒有多餘空格）
3. Region 名稱是否正確（例如：eastus，不是 East US）
