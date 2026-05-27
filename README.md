# 🌌 AI 協作待辦與工作流範本專案 (Antigravity Workflow Template)

本專案旨在提供一套結構化、高效率且具備「確認閘（Confirmation Gate）」的 AI 協作工作流範本。特別針對多專案並行開發之使用者，解決 Memory 檔案過大、上下文膨脹（Context Bloat）導致 AI 判斷力鈍化，以及開工時 AI 未經確認即擅自動手修改代碼等痛點。

---

## 📂 專案結構說明

本專案包含以下核心元件，可直接部署至協作工作空間中：

* 📄 **`CLAUDE.md`**：核心規則檔。定義了「開工」與「收工」的標準作業程序（SOP），並明確規範了人機確認機制。
* 📁 **`templates/`**：
  * 📄 **`PENDING_global.md`**：全域待辦清單摘要範本。放置於工作空間根目錄下，作為所有專案的狀態索引。
  * 📄 **`PENDING_project.md`**：專案待辦清單範本。放置於各專案子目錄下，將待辦事項清晰劃分為：**立即處理**、**本週計畫**、**下輪規劃**與**技術債/優化**四個維度。
* 📁 **`scripts/`**：
  * 🐍 **`sync_pending.py`**：自動同步 Python 腳本。執行時會掃描各專案目錄下的待辦事項數量與更新時間，並自動將摘要寫入全域 `PENDING.md` 中。
* 📄 **`PENDING.md`**：全域摘要範例檔，供參考與測試使用。

---

## ⚙️ 部署與設定指南

### 1. 初始化工作空間目錄

建議的工作空間目錄結構如下：

```text
c:\Users\etrny\.gemini\antigravity\scratch\ (工作空間根目錄)
├── PENDING.md                   <-- 由 templates/PENDING_global.md 重新命名而來
├── CLAUDE.md                    <-- 複製本專案的 CLAUDE.md
├── scripts/
│   └── sync_pending.py          <-- 複製本專案的 sync_pending.py
├── project_A/ (專案 A)
│   ├── PENDING.md               <-- 由 templates/PENDING_project.md 複製並填寫
│   └── ...
└── project_B/ (專案 B)
    ├── PENDING.md               <-- 由 templates/PENDING_project.md 複製並填寫
    └── ...
```

### 2. 部署步驟

1. **複製檔案**：
   - 將 `templates/PENDING_global.md` 複製到工作空間根目錄，並更名為 `PENDING.md`。
   - 將 `CLAUDE.md` 複製到工作空間根目錄（若個別專案有特殊規則，亦可複製到專案子目錄中）。
   - 將 `scripts/sync_pending.py` 複製到工作空間的 `scripts/` 資料夾下。
2. **為各專案建立待辦檔**：
   - 將 `templates/PENDING_project.md` 複製到各個並行專案的子目錄下，更名為 `PENDING.md`，並填入該專案目前的待辦事項。
3. **執行同步**：
   - 每次編輯任何專案的待辦清單後，在根目錄下執行：
     ```powershell
     python scripts/sync_pending.py
     ```
   - 腳本會自動計算各專案中未勾選的待辦項目數量，並將最後更新時間與連結寫入全域 `PENDING.md` 的 `<!-- PROJECT_LIST_START -->` 與 `<!-- PROJECT_LIST_END -->` 標記區間中。

---

## 🔄 「開工與收工」工作流與人機確認閘

本範本特別在 `CLAUDE.md` 中設計了安全防護機制，以確保開發主導權掌握在使用者手中：

### 🟢 1. 說「開工」時的流程 (Startup SOP)
1. AI 助理自動執行 `git pull` 同步遠端代碼。
2. AI 助理讀取全域 `PENDING.md` 與當前專案的 `PENDING.md`。
3. AI 助理僅在對話中**列出任務大綱與今日行動建議，並停止等待**。
4. **【人機確認閘】**：AI 助理此時處於暫停狀態。在使用者輸入「確認」、「同意」或具體指令前，**嚴禁執行任何檔案修改、程式碼編寫或腳本執行工具**。

### 🔴 2. 說「收工」時的流程 (Wrap-up SOP)
1. AI 助理自動掃描敏感檔案防止金鑰外洩。
2. AI 助理自動更新專案待辦檔（已完成事項移出，僅保留 active 事項）。
3. AI 助理調用 `sync_pending.py`，將最新待辦數量與更新時間同步至根目錄的 `PENDING.md`。
4. AI 助理展示 `git diff` 變更摘要，生成 Conventional Commit 訊息，並在使用者確認後自動執行 `git commit` 與 `git push` 上傳至 GitHub。

---

## 📝 授權許可

本專案採用 [MIT License](LICENSE) 授權。
