"""LRU vs FIFO vs LFU 缓存策略命中率对比。

模拟带热点分布的访问序列（Zipf 分布），对比三种淘汰策略在不同缓存容量下的命中率。
"""

import random
from collections import OrderedDict

from lru import LRUCache


def gen_access_sequence(n_keys: int, n_access: int, skew: float = 1.0):
    """生成带热点分布的访问序列：key 越小访问越频繁（Zipf 分布）。"""
    weights = [1.0 / (i + 1) ** skew for i in range(n_keys)]
    keys = list(range(n_keys))
    return random.choices(keys, weights=weights, k=n_access)


def simulate_lru(seq, capacity: int) -> float:
    c = LRUCache(capacity)
    hits = 0
    for k in seq:
        if c.get(k) is not None:
            hits += 1
        else:
            c.put(k, k)
    return hits / len(seq)


def simulate_fifo(seq, capacity: int) -> float:
    d: OrderedDict = OrderedDict()
    hits = 0
    for k in seq:
        if k in d:
            hits += 1
        else:
            d[k] = True
            if len(d) > capacity:
                d.popitem(last=False)  # FIFO：淘汰最早进入的
    return hits / len(seq)


def simulate_lfu(seq, capacity: int) -> float:
    d = {}
    freq = {}
    hits = 0
    for k in seq:
        if k in d:
            hits += 1
            freq[k] += 1
        else:
            d[k] = True
            freq[k] = 1
            if len(d) > capacity:
                victim = min(d, key=lambda x: freq[x])  # 淘汰访问频率最低的
                del d[victim]
                del freq[victim]
    return hits / len(seq)


def main() -> None:
    random.seed(42)
    n_keys = 100
    n_access = 100_000
    seq = gen_access_sequence(n_keys, n_access, skew=1.0)

    print("=" * 62)
    print("LRU vs FIFO vs LFU 命中率对比（Zipf 热点分布）")
    print(f"key 总数 {n_keys}，访问次数 {n_access:,}")
    print("=" * 62)
    print(f"{'缓存容量':<12}{'LRU':>12}{'FIFO':>12}{'LFU':>12}")
    print("-" * 62)
    for cap in [5, 10, 20, 50, 100]:
        lru = simulate_lru(seq, cap)
        fifo = simulate_fifo(seq, cap)
        lfu = simulate_lfu(seq, cap)
        print(f"{cap:<12}{lru:>11.2%}{fifo:>11.2%}{lfu:>11.2%}")

    print("-" * 62)
    print("结论：容量越接近热点数据规模命中率越高；LFU 对稳定热点最优，")
    print("      LRU 对时间局部性敏感、次优，FIFO 最弱。")


if __name__ == "__main__":
    main()
