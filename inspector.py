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
