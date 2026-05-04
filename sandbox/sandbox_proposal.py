# 提案 v11 | 公式: 随机抖动 | 第2004代 | 分数: 17.19
import random
def guess(low, high, weights=[-3.678542754816504e+30, 1.8513462992456328e+29, -4.9153154075877357e+30]):
    ratio = 0.5 + random.uniform(-0.1, 0.1)
    return low + (high - low) * ratio
