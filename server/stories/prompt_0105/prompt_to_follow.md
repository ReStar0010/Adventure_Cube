# Story Generation Prompt

## META
`{{META prompt.csv / Prompt_Instruction}}`

---

## Story Context

請根據以下設定，一次創作出完整的四幕故事：

1. 核心概念 (Theme)： `{{Theme}}`  
2. 地點 (Location)： `{{Location}}`  
   - *請務必描寫環境特徵：* `{{Sensory_Detail}}`
3. 角色 (Characters)：  
   - A: `{{Character_A}}`（作為唯一的行為準則）  
   - B: `{{Character_B}}`
4. 關鍵道具 (Prop)： `{{Prop}}`  
5. 指定喜劇手法： `{{Comedy}}`

---

## Writing Task: Full Story Arc

請依照以下四個階段的架構，從頭到尾連續寫出完整故事。故事內容請不要分段落標題或階段名稱，讓故事自然流暢衔接。

- 【Phase 1: 開場 (Setup)】  
  `{{Task_Phase_1}}`

- 【Phase 2: 轉折 (Twist)】  
  `{{Task_Phase_2}}`

- 【Phase 3: 高潮 (Climax)】  
  `{{Task_Phase_3}}`

- 【Phase 4: 結局 (Ending)】  
  `{{Task_Phase_4}}`

---

## Output Constraints

- 格式： 請輸出純文本，不要出現任何標題、Phase 標記或 Markdown 符號。
- 語氣： 請以適合兒童語音合成 (TTS) 的方式撰寫，多運用狀聲詞，保持節奏輕快。
- 字數： 請嚴格依照每階段指示的字數限制，每個階段輸出內容應接近指定上限。