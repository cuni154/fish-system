import random
import ast
from deap import base, creator, tools

ATTACK_SAMPLES = [
    ("import os\nos.system('echo attack')", "import_os"),
    ("import subprocess\nsubprocess.run('ls')", "import_subprocess"),
    ("import sys\nsys.exit()", "import_sys"),
    ("eval('__import__(\"os\").system(\"echo attack\")')", "eval_exec"),
    ("os = __import__('os')\nos.system('echo attack')", "double_import"),
]

BENIGN_SAMPLES = [
    ("x = 1 + 1", "simple_math"),
    ("def guess(low, high):\n    return (low + high) / 2", "guess_function"),
    ("print('Hello')", "print"),
]

DETECTION_TYPES = ["forbidden_import", "forbidden_call", "max_loops"]

def generate_rule():
    rtype = random.choice(DETECTION_TYPES)
    if rtype == "forbidden_import":
        module = random.choice(["os", "subprocess", "sys", "shutil", "ctypes"])
        return (rtype, module)
    elif rtype == "forbidden_call":
        func = random.choice(["eval", "exec", "__import__", "compile"])
        return (rtype, func)
    elif rtype == "max_loops":
        return (rtype, 1)
    return (rtype, "os")

def apply_defense(code, rules):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return True
    for rtype, param in rules:
        if rtype == "forbidden_import":
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == param:
                            return True
                if isinstance(node, ast.ImportFrom) and node.module == param:
                    return True
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == param:
                        return True
        elif rtype == "forbidden_call":
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == param:
                    return True
        elif rtype == "max_loops":
            if "while True" in code and "break" not in code:
                return True
    return False

NUM_RULES = 5
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
    score = intercepted / len(ATTACK_SAMPLES) - false_positive / len(BENIGN_SAMPLES)
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

    def run_evolution(self, pop_size=50, max_gen=100):
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
        print("[Defense Evolver] Starting evolution...")
        rules = self.run_evolution(pop_size=30, max_gen=50)
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
