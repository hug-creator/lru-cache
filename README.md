# LRU 缓存（Least Recently Used）

![Tests](https://github.com/hug-creator/lru-cache/actions/workflows/test.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)

基于 **哈希表 + 双向链表** 的 LRU 缓存实现，`get` / `put` 均为 **O(1)** 时间复杂度。纯标准库，零第三方依赖。

## 核心思路

LRU（最近最少使用）缓存需要同时满足两个诉求：

| 诉求 | 数据结构 | 为什么 |
| --- | --- | --- |
| O(1) 定位到 key | **哈希表** | `key -> 节点` 直接映射 |
| O(1) 维护访问顺序 | **双向链表** | 命中时摘除再插头部、淘汰尾部，指针操作 O(1) |

- **命中 / 写入**：把节点移到链表头部（最近使用）
- **容量满**：淘汰链表尾部（最久未使用）

只用哈希表或只用链表都无法同时做到 O(1) 的查找和顺序维护，两者结合才是 LRU 的精髓。

## 复杂度

| 操作 | 时间复杂度 |
| --- | --- |
| `get` | O(1) |
| `put` | O(1) |
| `peek` | O(1) |

## 用法

```python
from lru import LRUCache, TTLCache, ThreadSafeLRUCache

cache = LRUCache(2)

cache.put(1, "a")
cache.put(2, "b")
cache.get(1)       # "a"，1 变为最近使用
cache.put(3, "c")  # 容量满，淘汰最久未使用的 2

print(cache.get(2))  # None（已被淘汰）
print(cache.get(3))  # "c"

# 命中率统计
print(cache.hits, cache.misses, cache.hit_rate)

# 线程安全版本
tc = ThreadSafeLRUCache(100)
tc.put("key", "value")

# 带 TTL（存活时间）的缓存：条目过期自动失效
ttl_cache = TTLCache(capacity=3, ttl=5.0)
ttl_cache.put("session", "token")
ttl_cache.put("temp", "data", ttl=0.5)   # 单独指定更短的过期时间
```

也支持字典式接口：`cache[k]`、`cache[k] = v`、`k in cache`、`len(cache)`。

## 可视化

```bash
pip install gradio matplotlib pandas python-dotenv
python app.py          # 浏览器打开 http://127.0.0.1:7861
```

界面实时展示缓存内容（最近 → 最久）、命中率与链表结构，适合演示与调试。

## 测试与 benchmark

```bash
python -m pytest tests/ -v   # 15 个用例
python benchmark.py          # LRU vs FIFO vs LFU 命中率对比
```

### benchmark 实测（Zipf 热点分布，100 key、10 万次访问）

| 缓存容量 | LRU | FIFO | LFU |
| --- | --- | --- | --- |
| 5 | 24.93% | 22.41% | 40.68% |
| 10 | 39.89% | 35.08% | 51.07% |
| 20 | 56.81% | 50.75% | 64.00% |
| 50 | 80.83% | 76.24% | 84.41% |
| 100 | 99.90% | 99.90% | 99.90% |

> LFU 对「稳定热点」最优，LRU 对「时间局部性」敏感（次优），FIFO 最弱——不同淘汰策略各有适用场景。

## 目录结构

```
lru_cache/
├── lru.py           # 核心：LRUCache + ThreadSafeLRUCache + TTLCache
├── app.py           # Gradio 可视化界面（缓存状态 + 链表 + 命中率）
├── benchmark.py     # LRU / FIFO / LFU 命中率对比
└── tests/
    └── test_lru.py  # 15 个 pytest 用例
```

## 简历亮点

- **哈希表 + 双向链表**组合实现 O(1) get/put，是面试最高频的数据结构题
- **哨兵节点**简化链表边界处理，避免大量判空
- 支持**线程安全版本**（可重入锁）、**TTL 过期**（惰性删除）与**命中率统计**
- benchmark 对比 LRU / FIFO / LFU 三种淘汰策略，体现对缓存替换算法的理解
- Gradio 可视化缓存链表结构与命中率，便于演示与调试
