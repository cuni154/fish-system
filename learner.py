import random
import math
import inspector
from deap import base, creator, tools
from datetime import datetime

LOG_FILE = "/storage/emulated/0/鱼系统/system.log"
def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [子系统] {msg}\n")

TARGETS = [
    {"name": "小", "low": 1, "high": 1000},
    {"name": "中", "low": 1, "high": 100000},
    {"name": "大", "low": 1, "high": 1000000},
]

# ========== 公式模板库（AI可以变异组合这些结构） ==========
FORMULA_TEMPLATES = [
    # type 0: sigmoid
    lambda low, high, w: low + (high - low) * (1.0 / (1.0 + math.exp(-(w[0] + w[1] * (high - low) / 1000000 + w[2])))),
    # type 1: 线性比例
    lambda low, high, w: low + (high - low) * abs(w[0] / 10.0),
    # type 2: 平方根折中
    lambda low, high, w: low + (high - low) * (math.sqrt(abs(w[0]) + 0.01) / 10.0),
    # type 3: 倾向于端点
    lambda low, high, w: low if w[0] < 0 else high,
    # type 4: 随机抖动折中
    lambda low, high, w: low + (high - low) * (0.5 + random.uniform(-0.1, 0.1)),
]

NUM_WEIGHTS = 3  # 每个公式最多用3个权重
NUM_FEATURES = NUM_WEIGHTS + 1  # 前3个是权重，最后一个是公式类型索引

def play_game(individual, target_spec):
    low, high = 1.0, float(target_spec["high"])
    secret = random.randint(target_spec["low"], target_spec["high"])
    weights = individual[:NUM_WEIGHTS]
    formula_type = int(individual[NUM_WEIGHTS]) % len(FORMULA_TEMPLATES)
    formula = FORMULA_TEMPLATES[formula_type]
    
    for guesses_left in range(30, 0, -1):
        try:
            guess = formula(low, high, weights)
            guess = max(1.0, min(float(target_spec["high"]), guess))
            guess = int(round(guess))
        except:
            return 0.0
        
        if guess == secret:
            return guesses_left
        elif guess < secret:
            low = guess + 1.0
        else:
            high = guess - 1.0
        if low > high:
            break
    return 0.0

def evaluate(individual):
    total = 0.0
    for _ in range(30):
        for spec in TARGETS:
            total += play_game(individual, spec)
    return total / (30 * len(TARGETS)),

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)
toolbox = base.Toolbox()
toolbox.register("attr_weight", random.uniform, -10, 10)
toolbox.register("attr_formula", random.randint, 0, len(FORMULA_TEMPLATES) - 1)
toolbox.register("individual", tools.initCycle, creator.Individual,
                 [toolbox.attr_weight]*NUM_WEIGHTS + [toolbox.attr_formula], n=1)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("mate", tools.cxBlend, alpha=0.5)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1.0, indpb=0.3)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate)

def make_plugin_code(individual):
    weights = list(individual[:NUM_WEIGHTS])
    formula_type = int(individual[NUM_WEIGHTS]) % len(FORMULA_TEMPLATES)
    formula_desc = ["sigmoid", "线性比例", "平方根", "端点倾向", "随机抖动"][formula_type]
    
    # 根据公式类型生成不同的 guess 函数
    if formula_type == 0:
        code = f'''import math
def guess(low, high, weights={weights}):
    w0, w1, w2 = weights[0], weights[1], weights[2]
    ratio = 1.0 / (1.0 + math.exp(-(w0 + w1 * (high - low) / 1000000 + w2)))
    return low + (high - low) * ratio
'''
    elif formula_type == 1:
        code = f'''def guess(low, high, weights={weights}):
    w0 = weights[0]
    ratio = abs(w0 / 10.0)
    return low + (high - low) * ratio
'''
    elif formula_type == 2:
        code = f'''import math
def guess(low, high, weights={weights}):
    w0 = weights[0]
    ratio = math.sqrt(abs(w0) + 0.01) / 10.0
    return low + (high - low) * ratio
'''
    elif formula_type == 3:
        code = f'''def guess(low, high, weights={weights}):
    return low if weights[0] < 0 else high
'''
    elif formula_type == 4:
        code = f'''import random
def guess(low, high, weights={weights}):
    ratio = 0.5 + random.uniform(-0.1, 0.1)
    return low + (high - low) * ratio
'''
    else:
        code = f'''def guess(low, high, weights={weights}):
    return (low + high) / 2
'''
    return code, formula_desc

def evolution_loop():
    POP_SIZE = 150
    MAX_GEN = 1_000_000
    NO_IMPROVE_LIMIT = 5000
    best_score = 0.0
    no_improve = 0
    best_individual = None
    proposal_version = 0

    pop = toolbox.population(n=POP_SIZE)
    log("进化引擎启动（可变异公式结构）")

    for gen in range(MAX_GEN):
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))
        for c1, c2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.8:
                toolbox.mate(c1, c2)
        for m in offspring:
            if random.random() < 0.3:
                toolbox.mutate(m)
        for ind in offspring:
            del ind.fitness.values
        invalid = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalid:
            ind.fitness.values = toolbox.evaluate(ind)
        pop[:] = offspring

        current_best = tools.selBest(pop, 1)[0]
        current_score = current_best.fitness.values[0]

        if current_score > best_score:
            best_score = current_score
            no_improve = 0
            best_individual = list(current_best)
            proposal_version += 1
            plugin_code, formula_desc = make_plugin_code(current_best)
            print(f"第{gen:6d}代 新纪录！{formula_desc} 平均剩余: {best_score:.2f}/30")
            with open('sandbox_proposal.py', 'w') as f:
                f.write(f"# 提案 v{proposal_version} | 公式: {formula_desc} | 第{gen}代 | 分数: {best_score:.2f}\n")
                f.write(plugin_code)
            log(f"新提案 v{proposal_version} [{formula_desc}] 写入附加系统 分数:{best_score:.2f}")
        else:
            no_improve += 1
            if gen % 500 == 0:
                print(f"第{gen:6d}代 当前最佳: {best_score:.2f}")
            if no_improve >= NO_IMPROVE_LIMIT:
                print(f"连续{NO_IMPROVE_LIMIT}代无进步，进化停止。")
                break

    log(f"进化结束 最终分数:{best_score:.2f}")
    return best_individual

if __name__ == "__main__":
    print("="*60)
    print("[子系统] 鱼系统学习引擎启动（可探索不同公式结构）")
    print("="*60)
    best_ind = evolution_loop()
    if best_ind:
        print("\n[子系统] 提交最终提案给检察总长...")
        success, msg = inspector.review_proposal()
        if success:
            print(f"[子系统] 通过: {msg}")
        else:
            print(f"[子系统] 否决: {msg}")
    print("[子系统] 周期结束")
class DefenseEvolver:
    """防御规则进化体 — 受宪法约束的子模块"""
    
    def evolve(self):
        # ... 遗传算法进化防御规则 ...
        best_rules = self.run_evolution()
        
        # 写入附加系统（和其他提案走同一通道）
        with open('sandbox_defense.py', 'w') as f:
            f.write(self.format_rules(best_rules))
        
        # 提交审查（不能在沙盒外执行任何规则）
        return best_rules