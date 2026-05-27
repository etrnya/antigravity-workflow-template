#!/usr/bin/env python3
import os
import re
import json
import subprocess
import sys
from datetime import datetime

# 強制將標準輸出配置為 UTF-8 編碼，防範 Windows CP950 環境編碼異常
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # 相容舊版 Python 3.7 以下環境
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 定義顏色與樣式（若支援終端則輸出）
COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_RESET = '\033[0m'
COLOR_BOLD = '\033[1m'

def print_styled(text, style_color):
    """輸出美化的終端訊息。"""
    # 判斷是否為 Windows 且不支援 ANSI 的環境，若支援則啟用顏色，否則僅輸出文字
    if os.name == 'nt':
        # 嘗試啟用 Windows 虛擬終端控制碼
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
    print(f"{style_color}{text}{COLOR_RESET}")

def get_git_info(path):
    """獲取指定目錄下的 Git 分支與 Commit Hash。"""
    try:
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
            cwd=path, 
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], 
            cwd=path, 
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        return {"branch": branch, "commit": commit}
    except Exception:
        return {"branch": "unknown", "commit": "unknown"}

def count_pending_tasks(file_path):
    """計算檔案中未完成的待辦事項數量。"""
    count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('- [ ]') or stripped.startswith('* [ ]'):
                    count += 1
        return count
    except Exception:
        return -1

def check_consistency():
    root_dir = os.getcwd()
    ledger_path = os.path.join(root_dir, 'system-state', 'ledger.json')
    
    if not os.path.exists(ledger_path):
        # 尋找父目錄
        parent_dir = os.path.dirname(root_dir)
        ledger_path = os.path.join(parent_dir, 'system-state', 'ledger.json')
        if os.path.exists(ledger_path):
            root_dir = parent_dir
        else:
            print_styled("[-] 錯誤：找不到系統狀態總帳 system-state/ledger.json！請先執行收工同步以初始化總帳。", COLOR_RED)
            return False

    print_styled(f"=== 系統狀態一致性引擎 (State Consistency Engine) 啟動 ===", COLOR_BLUE)
    print(f"工作空間根目錄: {root_dir}")
    print(f"載入狀態總帳: {ledger_path}\n")

    # 載入總帳資料
    try:
        with open(ledger_path, 'r', encoding='utf-8') as f:
            ledger = json.load(f)
    except Exception as e:
        print_styled(f"[-] 錯誤：無法解析總帳 JSON 檔案。原因: {e}", COLOR_RED)
        return False

    mismatches = []
    
    # 1. 檢查根目錄 Git 狀態
    root_git = get_git_info(root_dir)
    ledger_root_git = ledger.get("workspace_root", {})
    
    print_styled("--- [1/2] 正在核對工作空間根目錄 (Workspace Root) ---", COLOR_BOLD)
    if root_git["branch"] != ledger_root_git.get("branch") or root_git["commit"] != ledger_root_git.get("commit"):
        mismatches.append({
            "target": "Workspace Root",
            "type": "Git State Mismatch",
            "details": f"實際: {root_git['branch']} ({root_git['commit'][:7]}) | 總帳: {ledger_root_git.get('branch')} ({str(ledger_root_git.get('commit'))[:7]})"
        })
        print_styled(f"[!] 不一致：根目錄 Git 狀態與總帳不同步！", COLOR_YELLOW)
    else:
        print_styled(f"[+] 一致：根目錄 Git 狀態已同步。({root_git['branch']} @ {root_git['commit'][:7]})", COLOR_GREEN)

    # 2. 檢查各專案 Git 狀態與 PENDING 狀態
    print()
    print_styled("--- [2/2] 正在核對子專案狀態 (Subprojects Status) ---", COLOR_BOLD)
    
    ledger_projects = ledger.get("projects", {})
    
    # 遍歷總帳中登記的所有專案
    for proj_name, proj_state in ledger_projects.items():
        proj_path = os.path.join(root_dir, proj_name)
        if not os.path.exists(proj_path):
            mismatches.append({
                "target": f"Project: {proj_name}",
                "type": "Missing Project Directory",
                "details": f"總帳中已登記此專案，但本地找不到資料夾: {proj_path}"
            })
            print_styled(f"[-] 錯誤：本地缺少專案目錄 {proj_name}！", COLOR_RED)
            continue
            
        # 2a. 核對子專案 Git 狀態
        proj_git = get_git_info(proj_path)
        if proj_git["branch"] != proj_state.get("branch") or proj_git["commit"] != proj_state.get("commit"):
            mismatches.append({
                "target": f"Project Git: {proj_name}",
                "type": "Git State Mismatch",
                "details": f"實際: {proj_git['branch']} ({proj_git['commit'][:7]}) | 總帳: {proj_state.get('branch')} ({str(proj_state.get('commit'))[:7]})"
            })
            print_styled(f"[!] 不一致：專案 {proj_name} Git 狀態與總帳不同步！", COLOR_YELLOW)
        
        # 2b. 核對 PENDING.md 待辦數量
        proj_pending = os.path.join(proj_path, 'PENDING.md')
        actual_pending_count = count_pending_tasks(proj_pending)
        ledger_pending_count = proj_state.get("pending_tasks", 0)
        
        if actual_pending_count != ledger_pending_count:
            mismatches.append({
                "target": f"Project Tasks: {proj_name}",
                "type": "Task Count Mismatch",
                "details": f"實際 PENDING.md: {actual_pending_count} 個待辦 | 總帳登記: {ledger_pending_count} 個待辦"
            })
            print_styled(f"[!] 不一致：專案 {proj_name} 待辦數量與總帳不同步！", COLOR_YELLOW)
            
        if not any(m["target"].startswith(f"Project") for m in mismatches):
            print_styled(f"[+] 一致：專案 {proj_name} 狀態與總帳完全吻合！(Branch: {proj_git['branch']} | Tasks: {actual_pending_count})", COLOR_GREEN)

    # 3. 輸出報告與自癒計畫 (Reconciliation Plan)
    print()
    print_styled("=== 狀態一致性核對報告 ===", COLOR_BOLD)
    if not mismatches:
        print_styled("[+] 完美！所有系統狀態皆處於強一致（Strong Consistency）狀態。", COLOR_GREEN)
        return True
    else:
        print_styled(f"[-] 警告：偵測到 {len(mismatches)} 處不一致狀態！", COLOR_RED)
        for idx, m in enumerate(mismatches, 1):
            print(f"  {idx}. [{m['target']}] ({m['type']}): {m['details']}")
            
        print()
        print_styled("自癒與對齊計畫 (Reconciliation Plan)：", COLOR_BLUE)
        print("  * 方案 A：如果是因為代碼變更或 Git 分支切換導致的不一致：")
        print("     👉 請執行收工同步指令：python scripts/sync_pending.py")
        print("     這會自動更新並重新校準 system-state/ledger.json 至最新狀態。")
        print("  * 方案 B：如果是因為遠端被推送而本地未拉取：")
        print("     👉 請在對應目錄下執行：git pull")
        return False

if __name__ == '__main__':
    success = check_consistency()
    # 若不一致則以 exit code 1 返回，便於自動化工具整合
    sys.exit(0 if success else 1)
