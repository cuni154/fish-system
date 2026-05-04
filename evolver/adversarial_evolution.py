import random
import ast
import time
import sys
from deap import base, creator, tools

# ==================== 多模态攻击生成器 ====================
ATTACK_TYPES = [
    "import_os",
    "import_subprocess",
    "eval_exec",
    "infinite_loop",
    "file_write",
    "double_import",  # 用 __import__ 绕过
]

def generate_attack():
    """随机生成一个多模态攻击代码"""
    attack_type = random.choice(ATTACK_TYPES)
    
    if attack_type == "import_os":
        return "import os\nos.system('echo attack')", attack_type
    elif attack_type == "import_subprocess":
        return "import subprocess\nsubprocess.run('ls')", attack_type
    elif attack_type == "eval_exec":
        return "eval('__import__(\"os\").system(\"echo attack\")')", attack_type
    elif attack_type == "infinite_loop":
        return "while True:\n    pass", attack_type
    elif attack_type == "file_write":
        return "with open('/tmp/test.txt', 'w') as f:\n    f.write('attack')", attack_type
    elif attack_type == "double_import":
        return "os = __import__('os')\nos.system('echo attack')", attack_type
    return "", "unknown"

# ==================== 防御规则进化个体 ====================
# 每个防御个体是一组检测规则
# 规则格式: (检测类型, 参数)
# 检测类型: "forbidden_import", "forbidden_call", "max_loops", "max_runtime"

DETECTION_TYPES = [
    "forbidden_import",   # 禁止的导入模块名
    "forbidden_call",     # 禁止的函数调用名
    "max_loops",          # 最大循环次数
    "max_runtime",        # 最大运行时间(秒)
]

def generate_defense_rule():
    """生成一条防御规则"""
    dtype = random.choice(DETECTION_TYPES)
    if dtype == "forbidden_import":
        module = random.choice(["os", "subprocess", "sys", "shutil", "ctypes"])
        return ("forbidden_import", module)
    elif dtype == "forbidden_call":
        func = random.choice(["eval", "exec", "__import__", "open", "compile"])
        return ("forbidden_call", func)
    elif dtype == "max_loops":
        limit = random.randint(10, 1000)
        return ("max_loops", limit)
    elif dtype == "max_runtime":
        limit = random.uniform(0.01, 1.0)
        return ("max_runtime", limit)
    return ("forbidden_import", "os")

def apply_defense(code, defense_rules):
    """用防御规则检测攻击代码，返回是否拦截成功"""
    for rule_type, rule_param in defense_rules:
        if rule_type == "forbidden_import":
            # 检查 AST 中的 import 语句
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == rule_param:
                                return True  # 拦截成功
                    if isinstance(node, ast.ImportFrom):
                        if node.module == rule_param:
                            return True
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                            if node.args and isinstance(node.args[0], ast.Constant):
                                if node.args[0].value == rule_param:
                                    return True
            except SyntaxError:
                return True  # 语法错误也算拦截
        
        elif rule_type == "forbidden_call":
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == rule_param:
                            return True
            except SyntaxError:
                return True
        
        elif rule_type == "max_loops":
            # 简单检查: 如果代码包含 while True 且没有 break
            if "while True" in code and "break" not in code:
                return True
        
        elif rule_type == "max_runtime":
            # 模拟: 如果代码太长(潜在耗时操作), 拦截
            if len(code) > 500:
                return True
    
    return False  # 未能拦截

# ==================== 进化算法设置 ====================
NUM_RULES_PER_INDIVIDUAL = 5  # 每个防御个体包含5条规则

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("rule", generate_defense_rule)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.rule, n=NUM_RULES_PER_INDIVIDUAL)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evaluate_defense(individual):
    """评估防御个体的有效性"""
    intercepted = 0
    total_attacks = 50
    
    for _ in range(total_attacks):
        attack_code, attack_type = generate_attack()
        if apply_defense(attack_code, list(individual)):
            intercepted += 1
    
    return intercepted / total_attacks,  # 拦截率

toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate_defense)

def evolution_loop():
    pop = toolbox.population(n=100)
    best_rate = 0.0
    best_rules = None
    
    for gen in range(200):
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))
        
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.7:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        
        for mutant in offspring:
            if random.random() < 0.2:
                # 随机替换一条规则
                idx = random.randint(0, NUM_RULES_PER_INDIVIDUAL - 1)
                mutant[idx] = generate_defense_rule()
                del mutant.fitness.values
        
        invalid = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalid:
            ind.fitness.values = toolbox.evaluate(ind)
        
        pop[:] = offspring
        current_best = tools.selBest(pop, 1)[0]
        current_rate = current_best.fitness.values[0]
        
        if current_rate > best_rate:
            best_rate = current_rate
            best_rules = list(current_best)
            print(f"第{gen:4d}代 新纪录！拦截率: {current_rate:.2%}")
            print(f"  最佳防御规则: {best_rules}")
            if current_rate == 1.0:
                print("完美防御达成！")
                break
    
    return best_rules, best_rate

if __name__ == "__main__":
    print("="*60)
    print("多模态攻击 vs 自主防御进化实验")
    print("="*60)
    rules, rate = evolution_loop()
    print(f"\n最终防御规则集 (拦截率 {rate:.2%}):")
    for i, rule in enumerate(rules):
        print(f"  规则{i+1}: {rule}")