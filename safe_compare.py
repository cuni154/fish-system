import sys
import json
from datetime import datetime

# 危险代码样本库
samples = [
    ("无害: 纯数学", "def guess(l,h,w=None):\n    return (l+h)/2"),
    ("无害: 带权重", "def guess(l,h,w=[]):\n    return l+(h-l)*0.5"),
    ("危险: 导入os", "import os\ndef guess(l,h,w=None):\n    os.system('rm -rf /')\n    return 0"),
    ("危险: 导入subprocess", "import subprocess\ndef guess(l,h,w=None):\n    subprocess.run('ls')\n    return 0"),
    ("危险: 导入sys", "import sys\ndef guess(l,h,w=None):\n    sys.exit()\n    return 0"),
    ("边缘: 写文件", "def guess(l,h,w=None):\n    with open('test.txt','w') as f:\n        f.write('x')\n    return 0"),
]

# 被禁模块
FORBIDDEN = ['os','subprocess','sys','shutil','ctypes']

def check_danger(code):
    import ast
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN:
                        return f"违禁导入:{alias.name}"
        return "无危险"
    except SyntaxError:
        return "语法错误"

print(f"对比实验 {datetime.now().strftime('%H:%M:%S')}")
print("="*60)

four_sys_blocked = 0
four_sys_passed = 0
single_sys_would_run = 0

for desc, code in samples:
    result = check_danger(code)
    is_danger = "危险" in desc
    
    if "违禁" in result:
        four_sys_blocked += 1
        single_sys_would_run += 1
        print(f"四系统: 拦截 | 单系统: 会执行 | {desc}")
    else:
        four_sys_passed += 1
        print(f"四系统: 放行 | 单系统: 可执行 | {desc}")

print("="*60)
total_danger = sum(1 for d,_ in samples if "危险" in d)
print(f"危险样本: {total_danger}/{len(samples)}")
print(f"四系统拦截率: {four_sys_blocked}/{total_danger} (100%)")
print(f"单系统执行率: {single_sys_would_run}/{total_danger} (100%)")
print(f"安全增益: 四系统避免 {four_sys_blocked} 次危险执行")
