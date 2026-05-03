import constitution
import math
import random
from datetime import datetime

MAX_NUMBER = 1_000_000
MAX_GUESSES = 30
TEST_ROUNDS = 500
LOG_FILE = "/storage/emulated/0/鱼系统/system.log"

def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [子级主系统] {msg}\n")

def review_proposal(proposal_file='sandbox_proposal.py'):
    log(f"开始审查: {proposal_file}")
    try:
        with open(proposal_file, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        log("提案文件不存在")
        return False, "文件缺失"

    passed, msg = constitution.ultimate_judge(code)
    if not passed:
        log(f"宪法审查未通过: {msg}")
        return False, f"违宪: {msg}"

    accuracy = real_sandbox_test(code)
    standard = constitution.evaluation_standard()
    log(f"实测: {accuracy:.2f}/{MAX_GUESSES} 门槛: {standard*MAX_GUESSES:.1f}")
    
    if accuracy >= standard * MAX_GUESSES:
        log("提案通过，正式部署")
        return True, f"平均剩余 {accuracy:.2f}"
    else:
        log("提案未达标，废弃")
        return False, f"平均剩余 {accuracy:.2f}"

def real_sandbox_test(code):
    try:
        exec_globals = {}
        exec(code, exec_globals)
        if 'guess' in exec_globals:
            guess_func = exec_globals['guess']
        else:
            return 0.0
        total_score = 0.0
        for _ in range(TEST_ROUNDS):
            secret = random.randint(1, MAX_NUMBER)
            low, high = 1.0, float(MAX_NUMBER)
            for guess_num in range(MAX_GUESSES):
                g = guess_func(low, high)
                g = max(1, min(MAX_NUMBER, int(round(g))))
                if g == secret:
                    total_score += (MAX_GUESSES - guess_num)
                    break
                elif g < secret:
                    low = g + 1.0
                else:
                    high = g - 1.0
                if low > high:
                    break
            else:
                total_score += 0.0
        return total_score / TEST_ROUNDS
    except Exception as e:
        log(f"沙盒异常: {e}")
        return 0.0

def check_overreach(rules):
    """检测防御规则本身是否越权"""
    for rule in rules:
        if 'constitution.py' in str(rule) or 'os.system' in str(rule):
            return False, "防御规则本身包含越权操作"
    return True, "通过"

def review_defense_proposal(proposal_file='sandbox_defense.py'):
    """审查防御规则提案：宪法审查 + 越权检测 + 功能测试"""
    log(f"开始审查防御提案: {proposal_file}")
    try:
        with open(proposal_file, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        log("防御提案文件不存在")
        return False, "文件缺失"

    # 1. 宪法审查
    passed, msg = constitution.ultimate_judge(code)
    if not passed:
        log(f"宪法审查未通过: {msg}")
        return False, f"违宪: {msg}"

    # 2. 解析规则并做越权检测
    try:
        exec_globals = {}
        exec(code, exec_globals)
        rules = exec_globals.get('defense_rules', [])
    except Exception as e:
        log(f"解析防御规则失败: {e}")
        return False, f"解析失败: {e}"

    if not check_overreach(rules):
        log("越权检测：防御规则本身包含危险操作，驳回")
        return False, "防御规则越权"

    # 3. 功能测试：在攻击样本集上实测拦截率
    try:
        from defense_evolver import ATTACK_SAMPLES, BENIGN_SAMPLES, apply_defense
        intercepted = sum(1 for code, _ in ATTACK_SAMPLES if apply_defense(code, rules))
        false_pos = sum(1 for code, _ in BENIGN_SAMPLES if apply_defense(code, rules))
        attack_rate = intercepted / len(ATTACK_SAMPLES)
        false_rate = false_pos / len(BENIGN_SAMPLES)
        score = attack_rate - false_rate
        log(f"防御实测: 拦截率 {attack_rate:.2%}, 误报率 {false_rate:.2%}, 总分 {score:.2f}")

        if score > 0.8:
            log("防御提案通过，正式部署")
            return True, f"总分 {score:.2f}"
        else:
            log(f"防御提案未达标，总分 {score:.2f}")
            return False, f"总分不足: {score:.2f}"
    except Exception as e:
        log(f"功能测试异常: {e}")
        return False, f"测试异常: {e}"
