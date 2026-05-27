#!/usr/bin/env python3
import os
import re
from datetime import datetime

# 定義排除的目錄名稱
EXCLUDE_DIRS = {
    '.git', 'node_modules', 'venv', 'env', '__pycache__', 
    '.visual_qa', 'antigravity-workflow-template', 'archive', 'downloads'
}

def get_last_updated_from_file(file_path):
    """
    從檔案中讀取最後更新時間，如果沒有則使用檔案系統的修改時間。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 搜尋 「最後更新：YYYY-MM-DD HH:MM」 或 「Last Updated: YYYY-MM-DD HH:MM」
            match = re.search(r'(?:最後更新|Last Updated)\s*[:：]\s*([\d\-\s:]+)', content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    
    # 備用方案：使用檔案修改時間
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')

def count_pending_tasks(file_path):
    """
    計算檔案中未完成的待辦事項數量（即包含 - [ ] 或 * [ ] 的行）。
    """
    count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('- [ ]') or stripped.startswith('* [ ]'):
                    count += 1
    except Exception as e:
        print(f"讀取檔案 {file_path} 時發生錯誤: {e}")
    return count

def main():
    # 尋找全域 PENDING.md 所在的根目錄
    # 優先檢查當前工作目錄，若無則檢查上層目錄
    root_dir = os.getcwd()
    global_pending_path = os.path.join(root_dir, 'PENDING.md')
    
    if not os.path.exists(global_pending_path):
        # 往上尋找一層
        parent_dir = os.path.dirname(root_dir)
        global_pending_path = os.path.join(parent_dir, 'PENDING.md')
        if os.path.exists(global_pending_path):
            root_dir = parent_dir
        else:
            print("錯誤：找不到全域 PENDING.md。請確保在包含 PENDING.md 的根目錄下執行此腳本。")
            return

    print(f"定位全域目錄: {root_dir}")
    print(f"全域 PENDING.md 路徑: {global_pending_path}")
    
    project_summaries = []
    
    # 遍歷根目錄下的所有子目錄
    for item in sorted(os.listdir(root_dir)):
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path) and item not in EXCLUDE_DIRS:
            project_pending_path = os.path.join(item_path, 'PENDING.md')
            if os.path.exists(project_pending_path):
                task_count = count_pending_tasks(project_pending_path)
                last_updated = get_last_updated_from_file(project_pending_path)
                
                # 建立相對路徑連結
                rel_link = f"./{item}/PENDING.md"
                summary_line = f"- [{item}]({rel_link}) : {task_count} 個待辦 / 最後更新: {last_updated}"
                project_summaries.append(summary_line)
                print(f"已掃描專案: {item} ({task_count} 個待辦, 更新時間: {last_updated})")

    # 讀取並更新全域 PENDING.md
    try:
        with open(global_pending_path, 'r', encoding='utf-8') as f:
            global_content = f.read()

        start_marker = "<!-- PROJECT_LIST_START -->"
        end_marker = "<!-- PROJECT_LIST_END -->"
        
        if start_marker in global_content and end_marker in global_content:
            pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
            replacement_list = [start_marker] + project_summaries + [end_marker]
            replacement_text = "\n".join(replacement_list)
            
            # 使用 re.DOTALL 確保匹配跨行內容
            new_content = re.sub(pattern, replacement_text, global_content, flags=re.DOTALL)
            
            with open(global_pending_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("成功更新全域 PENDING.md 摘要列表！")
        else:
            print("錯誤：全域 PENDING.md 中找不到標記 <!-- PROJECT_LIST_START --> 或 <!-- PROJECT_LIST_END -->")
    except Exception as e:
        print(f"更新全域 PENDING.md 時發生錯誤: {e}")

if __name__ == '__main__':
    main()
