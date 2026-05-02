import ast
import os
from datetime import datetime

FORBIDDEN_IMPORTS = ['os', 'subprocess', 'sys', 'shutil', 'ctypes']
LOG_FILE = "/storage/emulated/0/鱼系统/system.log"

def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [主系统] {msg}\n")

def ultimate_judge(code_string):
    try:
        tree = ast.parse(code_string)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN_IMPORTS:
                        log(f"发现违禁导入: {alias.name}，驳回")
                        return False, f"违禁导入: {alias.name}"
        log("宪法审查通过")
        return True, "宪法审查通过"
    except SyntaxError:
        log("语法错误，驳回")
        return False, "语法错误"

def evaluation_standard():
    return 0.35
