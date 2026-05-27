#!/usr/bin/env python3
import os
import re
import traceback
from datetime import datetime

# 定義排除的目錄名稱
EXCLUDE_DIRS = {
    '.git', 'node_modules', 'venv', 'env', '__pycache__', 
    '.visual_qa', 'antigravity-workflow-template', 'archive', 'downloads'
}

def log_sync_error(root_dir, project_name, error_msg, tb_str):
    """
    將同步錯誤記錄至全域 reports/pending_sync_errors.log 中，以便後續排除。
    """
    try:
        reports_dir = os.path.join(root_dir, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        log_path = os.path.join(reports_dir, 'pending_sync_errors.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] Project: {project_name}\n")
            f.write(f"Error: {error_msg}\n")
            f.write(f"Traceback:\n{tb_str}\n")
            f.write("="*60 + "\n")
    except Exception as e:
        print(f"寫入錯誤日誌失敗: {e}")

def get_last_updated_from_file(file_path, root_dir=None, project_name=None):
    """
    從檔案中讀取最後更新時間，如果讀取失敗或找不到則採用檔案系統修改時間作為降級回退方案。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'(?:最後更新|Last Updated)\s*[:：]\s*([\d\-\s:]+)', content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    except Exception as e:
        error_msg = str(e)
        tb_str = traceback.format_exc()
        print(f"警告：讀取 {project_name} 更新時間失敗，以系統時間進行降級回退。")
        if root_dir and project_name:
            log_sync_error(root_dir, project_name, error_msg, tb_str)
    
    try:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return "未知 (Unknown)"

def count_pending_tasks(file_path, root_dir=None, project_name=None):
    """
    計算檔案中未完成的待辦事項數量（即包含 - [ ] 或 * [ ] 的行）。
    若發生解析異常則返回 -1 進入降級模式，防止全域同步中斷。
    """
    count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('- [ ]') or stripped.startswith('* [ ]'):
                    count += 1
    except Exception as e:
        error_msg = str(e)
        tb_str = traceback.format_exc()
        print(f"警告：讀取專案 {project_name} 待辦清單失敗，將以降級模式處理。")
        if root_dir and project_name:
            log_sync_error(root_dir, project_name, error_msg, tb_str)
        return -1
    return count

def main():
    # 尋找全域 PENDING.md 所在的根目錄
    root_dir = os.getcwd()
    global_pending_path = os.path.join(root_dir, 'PENDING.md')
    
    if not os.path.exists(global_pending_path):
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
                task_count = count_pending_tasks(project_pending_path, root_dir, item)
                last_updated = get_last_updated_from_file(project_pending_path, root_dir, item)
                
                # 建立相對路徑連結
                rel_link = f"./{item}/PENDING.md"
                if task_count == -1:
                    summary_line = f"- [{item}]({rel_link}) : ⚠️ 降級模式 (讀取失敗，詳見 reports/pending_sync_errors.log) / 最後更新: {last_updated}"
                else:
                    summary_line = f"- [{item}]({rel_link}) : {task_count} 個待辦 / 最後更新: {last_updated}"
                
                project_summaries.append(summary_line)
                print(f"已掃描專案: {item} ({'⚠️ 讀取失敗' if task_count == -1 else str(task_count) + ' 個待辦'}, 更新時間: {last_updated})")

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
