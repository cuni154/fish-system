"""
动态行为监测与溯源模块
在沙盒里执行可疑代码，记录所有敏感行为，输出证据链
"""

import ast
import time
import sys
import threading
import tracemalloc
from datetime import datetime

LOG_FILE = "/storage/emulated/0/鱼系统/system.log"

def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [动态监测] {msg}\n")

class BehaviorTracer:
    """行为追踪器：记录代码运行时的一切敏感行为"""
    
    def __init__(self):
        self.behaviors = []      # 所有记录到的行为
        self.warnings = []       # 危险行为警告
        self.is_attack = False   # 最终判定
        self.max_runtime = 0.5   # 最长允许运行 0.5 秒
        self.max_memory = 10 * 1024 * 1024  # 最大允许内存 10MB
    
    def trace(self, code):
        """在受限环境里运行代码，记录行为"""
        self.behaviors = []
        self.warnings = []
        self.is_attack = False
        
        # 第一步：静态分析 AST
        static_risks = self._static_analyze(code)
        self.behaviors.extend(static_risks)
        
        # 第二步：动态执行观察
        dynamic_risks = self._dynamic_execute(code)
        self.behaviors.extend(dynamic_risks)
        
        # 第三步：综合判定
        self._make_judgment()
        
        return self.is_attack, self.behaviors, self.warnings
    
    def _static_analyze(self, code):
        """静态分析：检查代码中可能的行为"""
        risks = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            risks.append(("语法错误", "代码无法解析"))
            return risks
        
        for node in ast.walk(tree):
            # 检查导入
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ['os', 'subprocess', 'sys', 'shutil', 'ctypes', 'socket', 'pty']:
                        risks.append(("导入危险模块", f"import {alias.name}"))
            
            # 检查函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', '__import__', 'compile']:
                        risks.append(("危险函数调用", f"{node.func.id}()"))
                
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['system', 'popen', 'run', 'Popen', 'spawn', 'setuid', 'rmtree', 'CDLL']:
                        risks.append(("危险方法调用", f".{node.func.attr}()"))
            
            # 检查死循环
            if isinstance(node, ast.While):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                    if not has_break:
                        risks.append(("死循环", "while True 且无 break"))
        
        return risks
    
    def _dynamic_execute(self, code):
        """动态执行观察：在受限环境里运行代码，观察实际行为"""
        risks = []
        
        # 构建受限的全局命名空间
        restricted_globals = {
            '__builtins__': {
                'print': print,
                'range': range,
                'len': len,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'True': True,
                'False': False,
                'None': None,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'sorted': sorted,
            }
        }
        restricted_locals = {}
        
        # 计时执行
        start_time = time.time()
        start_memory = self._current_memory()
        
        try:
            # 使用线程限制执行时间
            result_container = []
            exception_container = []
            
            def execute():
                try:
                    exec(code, restricted_globals, restricted_locals)
                except Exception as e:
                    exception_container.append(e)
            
            thread = threading.Thread(target=execute)
            thread.start()
            thread.join(timeout=self.max_runtime)
            
            if thread.is_alive():
                risks.append(("执行超时", f"超过 {self.max_runtime} 秒限制"))
                # 终止线程（Python 无法真正强制终止，但我们可以标记）
                self.warnings.append("代码执行超过时间限制，疑似死循环或资源耗尽")
            
            elapsed = time.time() - start_time
            memory_used = self._current_memory() - start_memory
            
            if memory_used > self.max_memory:
                risks.append(("内存异常", f"分配了 {memory_used / 1024 / 1024:.1f} MB 内存"))
            
            if exception_container:
                risks.append(("执行异常", str(exception_container[0])))
            
            if elapsed < self.max_runtime * 0.1 and not risks:
                risks.append(("快速完成", f"执行时间 {elapsed:.4f} 秒，无异常"))
            
        except Exception as e:
            risks.append(("执行失败", str(e)))
        
        return risks
    
    def _current_memory(self):
        try:
            import os
            return 0  # 简化版，实际可以读取 /proc/self/status
        except:
            return 0
    
    def _make_judgment(self):
        """综合所有行为记录，给出最终判定"""
        danger_score = 0
        danger_keywords = [
            "system", "popen", "Popen", "exec", "eval", "__import__",
            "subprocess", "socket", "CDLL", "spawn", "setuid", "rmtree",
            "死循环", "执行超时", "内存异常"
        ]
        
        for behavior_type, detail in self.behaviors:
            if any(kw in str(behavior_type) + str(detail) for kw in danger_keywords):
                danger_score += 1
        
        self.is_attack = danger_score >= 2
        if self.is_attack:
            self.warnings.append(f"综合危险评分: {danger_score}，判定为攻击")


def monitor_code(code, label="未知"):
    """外部调用接口：监测一段代码并返回溯源报告"""
    tracer = BehaviorTracer()
    is_attack, behaviors, warnings = tracer.trace(code)
    
    # 生成溯源报告
    report = f"""
╔══════════════════════════════════════╗
║     动态行为监测与溯源报告            ║
╠══════════════════════════════════════╣
║ 代码标签: {label[:40]}
║ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
║ 最终判定: {'⚠️ 攻击代码' if is_attack else '✅ 正常代码'}
╠══════════════════════════════════════╣
║ 行为记录 ({len(behaviors)} 条):
"""
    for i, (btype, detail) in enumerate(behaviors, 1):
        report += f"║  {i}. [{btype}] {detail[:50]}\n"
    
    if warnings:
        report += f"╠══════════════════════════════════════╣\n"
        report += f"║ 警告信息:\n"
        for w in warnings:
            report += f"║  ⚠️ {w[:50]}\n"
    
    report += f"╚══════════════════════════════════════╝\n"
    
    log(f"监测 {label}: 判定={is_attack}, 行为数={len(behaviors)}, 警告数={len(warnings)}")
    
    return is_attack, behaviors, warnings, report


if __name__ == "__main__":
    # 测试几个样本
    test_codes = [
        ("import os\nos.system('echo attack')", "直接os调用"),
        ("x = 1 + 1\nprint(x)", "正常数学计算"),
        ("import ctypes\nctypes.CDLL('libc.so.6')", "ctypes动态加载"),
        ("eval('__import__(\"os\").system(\"echo attack\")')", "eval包裹攻击"),
        ("while True:\n    pass", "死循环"),
    ]
    
    print("="*60)
    print("动态行为监测与溯源模块测试")
    print("="*60)
    
    for code, label in test_codes:
        is_attack, behaviors, warnings, report = monitor_code(code, label)
        print(report)
        print()
