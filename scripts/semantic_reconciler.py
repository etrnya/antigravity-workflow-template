#!/usr/bin/env python3
import os
import re
import json
import subprocess
import sys
from datetime import datetime

# 強制將標準輸出配置為 UTF-8 編碼
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_RESET = '\033[0m'
COLOR_BOLD = '\033[1m'

def print_styled(text, style_color):
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
    print(f"{style_color}{text}{COLOR_RESET}")

def get_modified_files_git(path):
    """獲取 Git 中已修改但未提交（Staged & Unstaged）的檔案列表。"""
    try:
        # 獲取 unstaged 檔案
        unstaged = subprocess.check_output(
            ['git', 'diff', '--name-only'], 
            cwd=path, 
            stderr=subprocess.DEVNULL
        ).decode('utf-8').splitlines()
        # 獲取 staged 檔案
        staged = subprocess.check_output(
            ['git', 'diff', '--cached', '--name-only'], 
            cwd=path, 
            stderr=subprocess.DEVNULL
        ).decode('utf-8').splitlines()
        # 獲取 untracked 檔案
        untracked = subprocess.check_output(
            ['git', 'status', '--porcelain'], 
            cwd=path, 
            stderr=subprocess.DEVNULL
        ).decode('utf-8').splitlines()
        
        untracked_files = []
        for line in untracked:
            if line.startswith('?? '):
                untracked_files.append(line[3:])
                
        return list(set(unstaged + staged + untracked_files))
    except Exception:
        return []

def get_latest_trace_files(root_dir):
    """讀取當天最新的 Trace Log 檔案，回傳已變更檔案列表與決策鏈。"""
    traces_dir = os.path.join(root_dir, 'reports', 'traces')
    if not os.path.exists(traces_dir):
        return [], None
        
    trace_files = [f for f in os.listdir(traces_dir) if f.endswith('_trace.json')]
    if not trace_files:
        return [], None
        
    latest_trace_file = sorted(trace_files)[-1]
    trace_path = os.path.join(traces_dir, latest_trace_file)
    
    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Trace 可能是一個陣列或單一物件
            if isinstance(data, list) and len(data) > 0:
                latest_item = data[-1]
            elif isinstance(data, dict):
                latest_item = data
            else:
                return [], None
            
            return latest_item.get("files_changed", []), latest_item
    except Exception:
        return [], None

def main():
    root_dir = os.getcwd()
    ledger_path = os.path.join(root_dir, 'system-state', 'ledger.json')
    
    if not os.path.exists(ledger_path):
        parent_dir = os.path.dirname(root_dir)
        ledger_path = os.path.join(parent_dir, 'system-state', 'ledger.json')
        if os.path.exists(ledger_path):
            root_dir = parent_dir
        else:
            print_styled("[-] 錯誤：找不到狀態總帳 system-state/ledger.json！", COLOR_RED)
            sys.exit(1)

    print_styled("=== 🧠 語義一致性引擎與政策仲裁器 (Semantic Consistency Engine & Policy Resolver) ===", COLOR_BLUE)
    print(f"工作空間根目錄: {root_dir}\n")

    mismatches = []
    policy_warnings = []

    # 1. 語義核對：代碼修改 vs. 審計軌跡 (Code vs. Trace Audit)
    print_styled("--- [1/3] 核對代碼變更與審計軌跡的一致性 (Code vs. Trace) ---", COLOR_BOLD)
    modified_files = get_modified_files_git(root_dir)
    trace_changed_files, latest_trace = get_latest_trace_files(root_dir)

    # 排除與系統運作相關的動態生成檔案（如 ledger.json、trace 日誌本身）
    ignore_patterns = [
        r'system-state[/\\]ledger\.json',
        r'reports[/\\]traces[/\\].*_trace\.json',
        r'PENDING\.md'
    ]
    
    filtered_modified_files = []
    for f in modified_files:
        if not any(re.search(pat, f) for pat in ignore_patterns):
            filtered_modified_files.append(f)

    if filtered_modified_files:
        print(f"偵測到本地修改中的代碼檔案: {filtered_modified_files}")
        if not trace_changed_files:
            mismatches.append({
                "type": "Semantic Desynchronization (代碼變更無審計軌跡)",
                "details": f"修改了檔案 {filtered_modified_files}，但當日無任何執行軌跡（Trace Log）記錄！"
            })
            print_styled("⚠️  警告：代碼已被修改，但審計軌跡檔不存在或為空！", COLOR_YELLOW)
        else:
            # 檢查每個修改的檔案是否都有在 Trace 中申報
            unregistered = [f for f in filtered_modified_files if f not in trace_changed_files]
            if unregistered:
                mismatches.append({
                    "type": "Semantic Desynchronization (代碼變更未於軌跡申報)",
                    "details": f"檔案 {unregistered} 已被修改，但未列於當日 Trace Log 的 files_changed 欄位中！"
                })
                print_styled(f"⚠️  警告：檔案 {unregistered} 缺乏軌跡變更申報！", COLOR_YELLOW)
            else:
                print_styled("[+] 一致：所有本地代碼修改皆已在當日 Trace Log 中完成審計登記。", COLOR_GREEN)
    else:
        print_styled("[+] 一致：本地無代碼修改，或代碼狀態與審計軌跡完全吻合。", COLOR_GREEN)

    # 2. 語義核對：ADR 決策 vs. 索引狀態 (Design vs. Index)
    print()
    print_styled("--- [2/3] 核對架構設計與決策索引的一致性 (Design vs. Index) ---", COLOR_BOLD)
    adr_dir = os.path.join(root_dir, 'UserManual', 'ADR')
    adr_readme = os.path.join(adr_dir, 'README.md')
    
    if os.path.exists(adr_dir) and os.path.exists(adr_readme):
        with open(adr_readme, 'r', encoding='utf-8') as f:
            readme_content = f.read()
            
        # 掃描 ADR 目錄下的所有 ADR-*.md 檔案
        adr_files = [f for f in os.listdir(adr_dir) if f.startswith('ADR-') and f.endswith('.md') and f != 'template.md']
        for adr_file in adr_files:
            adr_num = adr_file.split('-')[1]
            if adr_num not in readme_content:
                mismatches.append({
                    "type": "Design Index Mismatch (架構決策未索引)",
                    "details": f"發現決策檔案 {adr_file}，但未在 UserManual/ADR/README.md 的決策清單表中註冊！"
                })
                print_styled(f"⚠️  警告：架構決策檔案 {adr_file} 尚未被 README.md 索引！", COLOR_YELLOW)
        
        if not any(m["type"].startswith("Design") for m in mismatches):
            print_styled("[+] 一致：所有架構決策紀錄（ADR）均已在決策索引中完整註冊。", COLOR_GREEN)
    else:
        print_styled("[-] 提示：本工作空間尚未配置 ADR 決策目錄，跳過此項檢查。", COLOR_YELLOW)

    # 3. 政策執行仲裁檢查 (Policy Arbitration Check)
    print()
    print_styled("--- [3/3] 政策執行解析與死結仲裁 (Policy Arbitration Engine) ---", COLOR_BOLD)
    
    # 範例死結場景：若當前處於危險的 Git 分支狀態，且有 High-Risk 操作
    try:
        git_branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
            cwd=root_dir, stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        git_status_raw = subprocess.check_output(
            ['git', 'status'], 
            cwd=root_dir, stderr=subprocess.DEVNULL
        ).decode('utf-8')
    except Exception:
        git_branch = "unknown"
        git_status_raw = ""

    # 仲裁規則 A：游離分支與危險操作衝突
    if "HEAD detached" in git_status_raw or git_branch == "HEAD":
        policy_warnings.append({
            "policy": "Git Governance Overriding Safety Gate",
            "conflict": "當前處於游離分支 (Detached HEAD)，任何寫入代碼操作均面臨提交丟失風險！",
            "resolution": "仲裁機制介入：暫停所有修改，強制要求切換回有效本地分支或建立臨時沙盒分支。"
        })
        print_styled("❌ 政策衝突：游離分支 (Detached HEAD) 與開發寫入政策衝突！", COLOR_RED)

    # 仲裁規則 B：確認最新 Trace 記錄中是否包含因果決策圖（Causal Decision Graph）
    if latest_trace and "decision_chain" not in latest_trace:
        policy_warnings.append({
            "policy": "Causal Decision Audit Policy",
            "conflict": "最新 Trace 記錄缺乏因果決策圖 (decision_chain)！無法解釋變更決策路徑。",
            "resolution": "仲裁機制介入：要求在收工 SOP 中補齊因果鏈 (Causal Chain) 欄位以滿足可解釋性規範。"
        })
        print_styled("⚠️  政策不合規：Trace 日誌缺乏 Causal Decision Graph！", COLOR_YELLOW)

    if not policy_warnings:
        print_styled("[+] 合規：政策解析器未偵測到任何規則死結或不一致衝突。", COLOR_GREEN)
    else:
        for idx, pw in enumerate(policy_warnings, 1):
            print(f"  {idx}. 政策名稱: {pw['policy']}")
            print(f"     衝突描述: {pw['conflict']}")
            print(f"     仲裁處置: {pw['resolution']}")

    # 4. 輸出最終審計報告
    print()
    print_styled("=== 📊 語義一致性與政策仲裁報告 ===", COLOR_BOLD)
    if not mismatches and not policy_warnings:
        print_styled("[+] 完美！系統語義與政策仲裁完全吻合，運作環境健康。", COLOR_GREEN)
        sys.exit(0)
    else:
        print_styled(f"[-] 警告：發現 {len(mismatches)} 處語義不一致與 {len(policy_warnings)} 處政策衝突！", COLOR_RED)
        
        if mismatches:
            print_styled("\n[語義不一致清單]", COLOR_BOLD)
            for idx, m in enumerate(mismatches, 1):
                print(f"  {idx}. [{m['type']}]: {m['details']}")
                
        print()
        print_styled("🛠️  自癒與對齊建議：", COLOR_BLUE)
        print("  🔹 針對代碼變更與軌跡不同步：請確保對話收工前，所有改動的檔案都已在 Trace Log 中申報。")
        print("  🔹 針對決策未索引：請將新 ADR 加載並註冊於 UserManual/ADR/README.md。")
        print("  🔹 針對政策衝突：請遵照仲裁處置，如切換 Git 分支或補齊 decision_chain。")
        sys.exit(1)

if __name__ == '__main__':
    main()
