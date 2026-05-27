# 🌌 AI Collaborative Todo & Workflow Template (Antigravity Workflow Template)

This project provides a structured, highly efficient, and "Confirmation Gate"-enabled AI collaborative workflow template. It is designed for developers running multiple concurrent projects, solving common issues such as bloated memory files (Context Bloat), sluggish AI decision-making, and cases where the AI edits code prematurely upon starting work without explicit confirmation.

---

## 📂 Project Structure

This project contains the following core components ready to be deployed into the workspace:

* 📄 **`CLAUDE.md`**: The core rule file defining the standard operating procedures (SOPs) for "Start Work" and "End Work", including strict human-agent confirmation rules.
* 📁 **`templates/`**:
  * 📄 **`PENDING_global.md`**: The global todo list summary template. Located at the root of the workspace, acting as an index for all projects.
  * 📄 **`PENDING_project.md`**: The project-specific todo list template. Located inside each project subdirectory, categorizing tasks into four levels: **Immediate**, **This Week**, **Next Round**, and **Tech Debt/Optimization**.
* 📁 **`scripts/`**:
  * 🐍 **`sync_pending.py`**: An automated Python synchronization script. Scans each project directory for pending task counts and update timestamps, then automatically writes the summaries to the root `PENDING.md`.
* 📄 **`PENDING.md`**: A sample global summary file for reference and testing.

---

## ⚙️ Deployment & Configuration Guide

### 1. Workspace Directory Setup

The recommended directory structure for the workspace is as follows:

```text
c:\Users\etrny\.gemini\antigravity\scratch\ (Workspace Root)
├── PENDING.md                   <-- Renamed from templates/PENDING_global.md
├── CLAUDE.md                    <-- Copied from CLAUDE.md of this project
├── scripts/
│   └── sync_pending.py          <-- Copied from scripts/sync_pending.py of this project
├── project_A/ (Project A)
│   ├── PENDING.md               <-- Copied and filled from templates/PENDING_project.md
│   └── ...
└── project_B/ (Project B)
    ├── PENDING.md               <-- Copied and filled from templates/PENDING_project.md
    └── ...
```

### 2. Deployment Steps

1. **Copy Files**:
   - Copy `templates/PENDING_global.md` to the workspace root and rename it to `PENDING.md`.
   - Copy `CLAUDE.md` to the workspace root (or to project subdirectories if project-specific overrides are needed).
   - Copy `scripts/sync_pending.py` to the workspace `scripts/` directory.
2. **Create Project Todo Files**:
   - Copy `templates/PENDING_project.md` into each active project subdirectory, rename it to `PENDING.md`, and fill in the active tasks.
3. **Run Synchronization**:
   - Every time a project's todo list is modified, execute the following command at the workspace root:
     ```powershell
     python scripts/scripts/sync_pending.py
     ```
   - The script automatically counts unchecked tasks in each project, formats the link, and updates the section between `<!-- PROJECT_LIST_START -->` and `<!-- PROJECT_LIST_END -->` markers inside the root `PENDING.md`.

---

## 🔄 "Start/End Work" Flow with Confirmation Gate

This template implements a safety gate within `CLAUDE.md` to ensure control remains with the user:

### 🟢 1. "Start Work" SOP
1. The AI Assistant automatically runs `git pull` to sync the local workspace with the remote repository.
2. The AI Assistant reads the global `PENDING.md` and the current project's `PENDING.md`.
3. The AI Assistant lists the task outline and initial action recommendations in the chat, then **stops and waits**.
4. **【Confirmation Gate】**: The AI Assistant remains paused. No file modifications, code writing, or script execution tools **shall be called** until the user replies with "Confirm", "Agree", or specific instructions.

### 🔴 2. "End Work" SOP
1. The AI Assistant automatically scans for secrets and sensitive keys to prevent leaks.
2. The AI Assistant cleans up the project's `PENDING.md` (removing completed tasks, keeping only active ones).
3. The AI Assistant runs `sync_pending.py` to update the task count and update time inside the global `PENDING.md`.
4. The AI Assistant displays `git diff` changes, drafts a Conventional Commit message, and runs `git commit` and `git push` upon user confirmation.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).
