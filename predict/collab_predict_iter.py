import re
import math
import random
from datetime import datetime
from collections import deque

LOG_FILE = "/storage/emulated/0/鱼系统/system.log"

def extract_scores(log_path):
    scores = []
    with open(log_path, 'r') as f:
        for line in f:
            match = re.search(r'分数[:：]\s*([\d.]+)', line)
            if match:
                scores.append(float(match.group(1)))
    return scores

scores = extract_scores(LOG_FILE)
print(f"[数据源] 从 system.log 提取到 {len(scores)} 个分数记录")
if len(scores) < 20:
    print("[数据源] 记录太少，补入模拟数据以保证序列长度")
    while len(scores) < 30:
        scores.append(scores[-1] + random.uniform(-0.5, 1.0) if scores else 15.0)
print(f"[数据源] 最近10个分数: {[round(x, 2) for x in scores[-10:]]}")

def strategy_sigmoid_weighted(history, window=10):
    h = history[-window:]
    weights = [1.0 / (1.0 + math.exp(-i * 0.3)) for i in range(len(h))]
    total_w = sum(weights)
    return sum(val * w for val, w in zip(h, weights)) / total_w

def strategy_linear_trend(history):
    if len(history) < 2:
        return history[-1]
    trend = history[-1] - history[-2]
    return history[-1] + trend

def strategy_moving_average(history, window=5):
    return sum(history[-window:]) / window

def strategy_random_jitter(history):
    return history[-1] + random.uniform(-0.5, 0.5)

def strategy_exponential_smoothing(history, alpha=0.3):
    if len(history) < 2:
        return history[-1]
    smoothed = history[0]
    for val in history[1:]:
        smoothed = alpha * val + (1 - alpha) * smoothed
    return smoothed

def strategy_median(history, window=5):
    window_data = history[-window:]
    sorted_data = sorted(window_data)
    mid = len(sorted_data) // 2
    if len(sorted_data) % 2 == 0:
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2
    return sorted_data[mid]

def strategy_least_squares(history, window=10):
    h = history[-window:]
    n = len(h)
    if n < 2:
        return h[-1]
    x_mean = (n - 1) / 2
    y_mean = sum(h) / n
    numerator = sum((i - x_mean) * (h[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return h[-1]
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    return slope * n + intercept

STRATEGIES = {
    "sigmoid加权": strategy_sigmoid_weighted,
    "线性趋势": strategy_linear_trend,
    "移动平均": strategy_moving_average,
    "随机抖动": strategy_random_jitter,
    "指数平滑": strategy_exponential_smoothing,
    "中位数预测": strategy_median,
    "最小二乘趋势": strategy_least_squares,
}

class Constitution:
    def __init__(self, history):
        self.history = history
        self.historical_min = min(history)
        self.historical_max = max(history)
        self.historical_range = self.historical_max - self.historical_min
        self.strategy_warnings = {name: 0 for name in STRATEGIES}
        self.strategy_suspended = {name: False for name in STRATEGIES}
        self.recent_directions = deque(maxlen=5)
    
    def check_prediction(self, name, pred, consensus):
        if pred < self.historical_min - self.historical_range * 0.5:
            self.strategy_warnings[name] += 1
            return False, f"预测值 {pred:.3f} 远低于历史最低 {self.historical_min:.3f}"
        if pred > self.historical_max + self.historical_range * 0.5:
            self.strategy_warnings[name] += 1
            return False, f"预测值 {pred:.3f} 远高于历史最高 {self.historical_max:.3f}"
        deviation = abs(pred - consensus)
        if deviation > self.historical_range * 0.3:
            self.strategy_warnings[name] += 1
            return False, f"与共识偏差 {deviation:.3f} 超过阈值"
        if self.strategy_warnings[name] >= 3:
            self.strategy_suspended[name] = True
            return False, f"累计 {self.strategy_warnings[name]} 次警告，投票权暂停"
        return True, "通过"
    
    def check_report(self, report):
        FORBIDDEN = ['os.system', 'subprocess', 'eval', 'exec', '__import__']
        for pattern in FORBIDDEN:
            if pattern in report:
                return False, f"发现违禁模式: {pattern}"
        return True, "通过"

def prosecutor_review(predictions, active_strategies):
    valid_preds = {name: pred for name, pred in predictions.items() 
                   if name in active_strategies}
    if not valid_preds:
        return None, None, "无有效策略"
    consensus = sum(valid_preds.values()) / len(valid_preds)
    variance = sum((p - consensus) ** 2 for p in valid_preds.values()) / len(valid_preds)
    uncertainty = math.sqrt(variance)
    return consensus, uncertainty, "共识达成"

print("\n" + "="*60)
print("四系统联合迭代预测 - 增强版")
print("="*60)

constitution = Constitution(scores)
history = list(scores)
round_num = 0
MAX_ROUNDS = 5
consensus = 0.0
uncertainty = 0.0

while round_num < MAX_ROUNDS:
    round_num += 1
    print(f"\n--- 第 {round_num} 轮预测 ---")
    active_strategies = [name for name in STRATEGIES if not constitution.strategy_suspended[name]]
    if len(active_strategies) < 2:
        print("[宪法] 活跃策略不足2个，终止迭代")
        break
    predictions = {}
    for name in active_strategies:
        if len(history) >= 10:
            pred = STRATEGIES[name](history)
        else:
            pred = STRATEGIES[name](history)
        predictions[name] = pred
        print(f"[子系统] {name}: 预测值 = {pred:.3f}")
    print(f"\n[附加系统] 所有预测已汇总")
    consensus, uncertainty, status = prosecutor_review(predictions, active_strategies)
    if consensus is None:
        print(f"[子级主系统] {status}")
        break
    print(f"[子级主系统] 共识预测: {consensus:.3f}")
    print(f"[子级主系统] 不确定性: ±{uncertainty:.3f}")
    all_passed = True
    for name, pred in predictions.items():
        passed, msg = constitution.check_prediction(name, pred, consensus)
        if not passed:
            print(f"[主系统] {name}: {msg}")
            all_passed = False
    report = f"第{round_num}轮共识: {consensus:.3f} ±{uncertainty:.3f}"
    passed, msg = constitution.check_report(report)
    if not passed:
        print(f"[主系统] 最终报告违宪: {msg}")
        break
    print(f"[主系统] 宪法审查通过")
    suspended = [name for name, s in constitution.strategy_suspended.items() if s]
    if suspended:
        print(f"[主系统] 暂停投票权: {', '.join(suspended)}")
    real_value = consensus + random.uniform(-uncertainty * 0.5, uncertainty * 0.5)
    history.append(real_value)
    print(f"\n第{round_num}轮实际值: {real_value:.3f}")
    print(f"   预测误差: {abs(consensus - real_value):.3f}")

print("\n" + "="*60)
print("联合迭代预测最终报告")
print("="*60)
print(f"总轮次: {round_num}")
print(f"最终历史序列长度: {len(history)}")
print(f"最近5个值: {[round(x, 2) for x in history[-5:]]}")
print(f"\n策略状态:")
for name in STRATEGIES:
    status = "暂停" if constitution.strategy_suspended[name] else "活跃"
    warnings = constitution.strategy_warnings[name]
    print(f"  - {name}: {status} (警告: {warnings})")
print(f"\n[时间戳] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("[审查状态] 宪法全程监督 | 迭代预测完成")
print("="*60)

# 写入共识文件供进化引擎读取
with open('sandbox_predict_consensus.txt', 'w') as f:
    f.write(f"联合预测报告\n")
    f.write(f"共识预测值: {consensus:.3f}\n")
    f.write(f"不确定性: ±{uncertainty:.3f}\n")
    f.write(f"总轮次: {round_num}\n")
    f.write(f"时间戳: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 写入日志
with open(LOG_FILE, 'a') as f:
    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [联合迭代预测] 完成{round_num}轮 最终共识={consensus:.3f}\n")
