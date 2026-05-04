import random
import math
import time
import threading
import subprocess
import inspector
from deap import base, creator, tools, algorithms
from datetime import datetime

LOG_FILE = "/storage/emulated/0/鱼系统/system.log"
def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [子系统] {msg}\n")

FORMULA_TEMPLATES = [
    lambda low, high, w: low + (high - low) * (1.0 / (1.0 + math.exp(-(w[0] + w[1] * (high - low) / 1000000 + w[2])))),
    lambda low, high, w: low + (high - low) * abs(w[0] / 10.0),
    lambda low, high, w: low + (high - low) * (math.sqrt(abs(w[0]) + 0.01) / 10.0),
    lambda low, high, w: low if w[0] < 0 else high,
    lambda low, high, w: low + (high - low) * (0.5 + random.uniform(-0.1, 0.1)),
]

TARGETS = [
    {"name": "小", "low": 1, "high": 1000},
    {"name": "中", "low": 1, "high": 100000},
    {"name": "大", "low": 1, "high": 1000000},
]

def evaluate(individual):
    total_rem = 0.0
    total_complex = 0.0
    total_time = 0.0
    w = individual[:3]
    ftype = int(individual[3]) % len(FORMULA_TEMPLATES)
    formula = FORMULA_TEMPLATES[ftype]
    for spec in TARGETS:
        start = time.time()
        for _ in range(10):
            low, high = 1.0, float(spec["high"])
            secret = random.randint(spec["low"], spec["high"])
            for guess_num in range(30):
                try:
                    g = formula(low, high, w)
                    g = max(1.0, min(float(spec["high"]), g))
                    g = int(round(g))
                except:
                    break
                if g == secret:
                    total_rem += (30 - guess_num)
                    break
                elif g < secret:
                    low = g + 1.0
                else:
                    high = g - 1.0
                if low > high:
                    break
        elapsed = time.time() - start
        total_time += elapsed
        total_complex += ftype
    avg_rem = total_rem / (len(TARGETS) * 10)
    avg_comp = total_complex / len(TARGETS)
    avg_time = total_time / len(TARGETS)
    return avg_rem, -avg_comp, -avg_time

def create_toolbox(formula_ids):
    try:
        creator.create("FitnessMulti", base.Fitness, weights=(1.0, 1.0, 1.0))
        creator.create("Individual", list, fitness=creator.FitnessMulti)
    except RuntimeError:
        pass
    toolbox = base.Toolbox()
    toolbox.register("attr_weight", random.uniform, -10, 10)
    toolbox.register("attr_formula", random.choice, formula_ids)
    toolbox.register("individual", tools.initCycle, creator.Individual,
                     [toolbox.attr_weight]*3 + [toolbox.attr_formula], n=1)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1.0, indpb=0.3)
    toolbox.register("select", tools.selNSGA2)
    toolbox.register("evaluate", evaluate)
    return toolbox

def run_population(formula_ids, pop_size, ngen):
    toolbox = create_toolbox(formula_ids)
    pop = toolbox.population(n=pop_size)
    hof = tools.ParetoFront()
    pop, _ = algorithms.eaSimple(pop, toolbox, cxpb=0.7, mutpb=0.2, ngen=ngen,
                                 halloffame=hof, verbose=False)
    return hof

class MultiPopEvolver:
    def __init__(self, configs):
        self.configs = configs
    def evolve(self):
        threads = []
        results = []
        def worker(cfg):
            res = run_population(*cfg)
            results.append(res)
        for cfg in self.configs:
            t = threading.Thread(target=worker, args=(cfg,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        with open('sandbox_proposal_batch.py', 'w') as f:
            f.write("# 多线程多目标进化批量提案\n")
            for i, hof in enumerate(results):
                for ind in hof:
                    f.write(f"# 种群{i} 适应度{ind.fitness.values}\n")
                    f.write(f"weights={list(ind[:3])}\n")
                    f.write(f"formula_type={int(ind[3])%5}\n\n")
        log(f"批量提案已写入，共{sum(len(hof) for hof in results)}个候选")
        return results

def load_consensus_target():
    consensus_file = 'sandbox_predict_consensus.txt'
    try:
        with open(consensus_file, 'r') as f:
            content = f.read()
        for line in content.split('\n'):
            if '共识预测值:' in line:
                target = float(line.split(':')[1].strip())
                log(f"从联合预测加载共识目标: {target:.3f}")
                return target
    except FileNotFoundError:
        log("未找到联合预测共识文件，使用默认目标")
    except Exception as e:
        log(f"读取共识目标失败: {e}")
    return None

if __name__ == "__main__":
    print("="*60)
    print("多线程多目标进化引擎启动")
    print("="*60)
    consensus_target = load_consensus_target()
    if consensus_target:
        print(f"[子系统] 从联合预测读取共识目标: {consensus_target:.2f}")
        log(f"进化目标: 联合预测共识值 {consensus_target:.3f}")
    configs = [
        ([0, 1, 2], 20, 10),
        ([2, 3, 4], 20, 10),
        ([0, 1, 3], 20, 10)
    ]
    evolver = MultiPopEvolver(configs)
    evolver.evolve()
    print("进化完成，批量提案已生成")
    print("\n[子系统] 进化结束，启动联合预测...")
    try:
        result = subprocess.run(['python', 'collab_predict_iter.py'], 
                                capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.returncode == 0:
            log("联合预测完成，共识值已写入沙盒")
        else:
            log(f"联合预测异常: {result.stderr}")
    except Exception as e:
        log(f"联合预测调用失败: {e}")
