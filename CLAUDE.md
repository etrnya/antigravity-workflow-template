# AI 協作規範與工作流指南 (CLAUDE.md)

本檔案定義了 AI 助理在與使用者協作時必須嚴格遵守的運作規則與開發標準。本規範旨在確保上下文精簡、提升判斷精準度、導入測試優先機制，並透過規則分層與狀態總帳確立系統一致性與安全審計制度。

---

## ⚖️ 規則憲法與優先等級 (Rule Hierarchy)

當不同的規範、決策或指令發生衝突時，AI 助理必須嚴格遵守以下優先權順序（高優先順序規則自動覆蓋低優先順序規則）。若發生衝突，AI 助理必須停頓並向使用者回報：

1. **安全憲法 (Safety Rules - 絕對優先)**：`CLAUDE.md` 中規定的安全界線（如禁止遞迴刪除、強制 `-LiteralPath`、防止金鑰外洩）。
2. **Git 狀態原則 (Git Governance - 絕對優先)**：Preflight Check 的狀態限制，禁止在危險狀態下自動推送。
3. **風險分級確認閘 (Risk-based Gate)**：人機安全邊界授權。
4. **架構決策紀錄 (ADR Decisions)**：`UserManual/ADR/` 中已通過的架構決策。
5. **工作流 SOP**：開工與收工的標準作業程序。
6. **專案約定俗成 (Project Conventions)**：個別子專案的既有代碼風格與規範。

---

## 🟢 核心指令：開工 (Start Work / Startup)

當使用者輸入關鍵字「**開工**」或「**我來了**」時，AI 助理必須執行以下標準作業程序（SOP）：

1. **環境同步**：
   - 執行 `git pull` 以確保本地代碼與待辦清單與遠端同步。
2. **讀取狀態與知識**：
   - 讀取全域與專案的 `PENDING.md`。
   - 讀取系統狀態總帳 `system-state/ledger.json`，核對當前分支與 Git commit 狀態是否與總帳一致。
   - 讀取 `UserManual/troubleshooting.md` 以繼承歷史避坑經驗。
   - 讀取 `UserManual/ADR/` 索引，確保理解已確立的架構決策。
3. **建立今日行動大綱**：
   - 僅列出專案待辦檔中分類為「立即 (Immediate)」與「本週 (This Week)」的待辦任務。
   - 評估任務風險等級，列出今日的第一步行動建議。
4. **人機確認閘 (Confirmation Gate)**：
   - AI 助理列出規劃與風險等級評估後，必須停止動作，等待使用者授權後方可執行代碼修改。

---

## 🔴 核心指令：收工 (End Work / Wrap-up)

當使用者輸入關鍵字「**收工**」或「**下班了**」時，AI 助理必須執行以下標準作業程序（SOP）：

1. **安全與品質驗證**：
   - 執行品質驗證（如 `npm run test`、Lint 檢查、型別檢查等），確保代碼可正常運行。
   - 掃描代碼檔案，防範敏感金鑰（API Key）外洩。
2. **整理專案待辦**：
   - 將已完成任務從專案 `PENDING.md` 中移至歷史提交，維持活躍待辦精簡。
3. **執行狀態與總帳同步**：
   - 執行 `python scripts/sync_pending.py` 自動更新全域 `PENDING.md` 摘要，並自動重算且寫入 `system-state/ledger.json` 以確保狀態強一致。
4. **生成執行軌跡 (Execution Trace)**：
   - 審查當前對話中 AI 助理執行的所有變更，並在 `reports/traces/` 下生成或追加當天的行為審計檔（例如 `reports/traces/YYYY-MM-DD_trace.json`），格式參照行為審計規範。
5. **Git 提交前安全檢查 (Preflight Check)**：
   - 在進行 any Commit 或 Push 之前，必須執行並輸出：`git status`、`git branch` 與 `git log --oneline --decorate -5`。
   - **狀態安全分級**：
     * **Fast-forward / Untracked**：可由 AI 助理正常操作並更新。
     * **Rebase conflict (衝突中) / Detached HEAD (游離分支) / Diverged branches (分支分歧)**：**嚴禁自動處置**，必須立刻停止並請求人工協助。
     * **Force push needed (需要強推)**：**永久禁止執行**。
   - 若發生遠端 Pull 拒絕，優先建立並切換至臨時沙盒分支（如 `temp/refactor-xxx`）或執行 Worktree 隔離，嚴禁使用盲目 `stash` 以防覆蓋或丟失歷史棧。
5. **更新專案履歷**：
   - 檢查並更新 `UserManual/README.md` 的已開發專案表。
6. **對話總結**：
   - 列出今日完成事項與下次開工起點。

---

## 🛡️ 行為與安全決策規範

為了在大規模開發中保持效率與安全平衡，實施以下三層風險分級確認制度：

### 1. 變更風險分級制度 (Risk-based Gate)

| 風險等級 | 適用行為範疇 | AI 助理權限與限制 |
| :--- | :--- | :--- |
| **低風險 (Low)** | 文檔修改（README, 註解）、排版調整、樣式 (CSS) 修改、寫入測試案例。 | 可在不中斷對話的情況下自行編寫並執行驗證，但必須在對話結尾提供變更摘要。 |
| **中風險 (Medium)** | 修改業務邏輯（JS/TS 程式碼、React 元件）、API 路由、自動化指令腳本。 | **必須先列出具體修改計畫與受影響檔案，取得使用者明確回覆（如「同意」、「Go」）後方可執行檔案寫入。** |
| **高風險 (High)** | 檔案與目錄刪除、修改環境變數 (`.env`)、資料庫 Migration、升級/刪除套件依賴、修改本 `CLAUDE.md` 規則。 | **嚴禁一次性執行。必須拆分為單步，且在執行任何破壞性或大規模重構變更前，必須引導使用者建立臨時檢查點分支（如 `git switch -c temp/refactor-xxx`）或使用 `git worktree` 建立沙盒隔離，每一步皆須經人工確認。** |

### 2. 測試與自我審查流程 (Test-First & Self-Review)
AI 助理在修改任何核心邏輯（中/高風險變更）時，必須遵守以下循環：
1. **計畫 (Plan)**：分析影響範圍與測試方案。
2. **修改 (Modify)**：進行代碼編寫，保持修改範疇最小化。
3. **驗證 (Validate)**：主動執行 Lint 檢查與單元測試，確保無語法與運行期錯誤。
4. **自審 (Self-Review)**：審查是否有殘留的除錯代碼或潛在漏洞。
5. **確認 (Approval)**：提報使用者確認後提交 Commit。

### 3. 架構決策記錄 (ADR) 規範
當開發過程中面臨以下重大決策時，AI 助理必須引導使用者於 `UserManual/ADR/` 建立架構決策紀錄（格式參照 `template.md`）：
* 引入新的框架、重大依賴或第三方服務（如 Firebase, Supabase）。
* 改變資料庫設計（如 Schema 結構）或 API 串接模式。
* 調整全域安全規則或工作流 SOP 邏輯。

### 4. 行為審計規範 (Audit Trail)
在收工前，AI 助理必須在 `reports/traces/` 目錄中建立或更新執行軌跡 JSON 檔案，記錄格式如下：
```json
{
  "timestamp": "2026-05-28T00:30:00+08:00",
  "intent": "實施狀態總帳與行為審計系統",
  "risk_level": "Medium",
  "files_changed": [
    "CLAUDE.md",
    "scripts/sync_pending.py"
  ],
  "reasoning": "為滿足 L5 級成熟度 AI 開發作業系統的一致性與可追溯性要求。",
  "approval_level": "Human Approved",
  "git_state_before": "6b87df6",
  "git_state_after": "pending_push"
}
```

---

## 🛠️ 開發與環境準則

1. **語系偏好**：預設對話與所有文件輸出皆為 **繁體中文 (Traditional Chinese)**。
2. **經驗繼承優先**：開發或除錯前，必須優先閱讀 `UserManual/` 下的避坑指南與 ADR。
3. **防止遞迴刪除**：執行刪除時必須使用 `-LiteralPath` 參數，嚴禁使用 `rmdir \` 或多指令拼接。
