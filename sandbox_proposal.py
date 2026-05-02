# 提案 v9 | 公式: 随机抖动 | 第750代 | 分数: 17.12
import random
def guess(low, high, weights=[28198207513051.34, -125834066596.7945, 8488977628361.051]):
    ratio = 0.5 + random.uniform(-0.1, 0.1)
    return low + (high - low) * ratio
