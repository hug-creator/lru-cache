"""LRU 缓存单元测试。"""

import threading
import time

import pytest

from lru import LRUCache, TTLCache, ThreadSafeLRUCache


def test_put_get():
    c = LRUCache(3)
    c.put(1, "a")
    c.put(2, "b")
    assert c.get(1) == "a"
    assert c.get(2) == "b"


def test_get_miss_returns_none():
    c = LRUCache(2)
    assert c.get("不存在") is None


def test_put_updates_existing():
    c = LRUCache(2)
    c.put(1, "old")
    c.put(1, "new")
    assert c.get(1) == "new"
    assert len(c) == 1


def test_evict_least_recently_used():
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.get(1)          # 访问 1，1 变最近使用
    c.put(3, "c")     # 容量满，应淘汰最久未使用的 2
    assert c.get(1) == "a"
    assert c.get(2) is None
    assert c.get(3) == "c"


def test_capacity_one():
    c = LRUCache(1)
    c.put(1, "a")
    c.put(2, "b")     # 淘汰 1
    assert c.get(1) is None
    assert c.get(2) == "b"


def test_invalid_capacity():
    with pytest.raises(ValueError):
        LRUCache(0)
    with pytest.raises(ValueError):
        LRUCache(-1)


def test_hit_rate():
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.get(1)      # hit
    c.get(2)      # hit
    c.get(99)     # miss
    assert c.hits == 2
    assert c.misses == 1
    assert abs(c.hit_rate - 2 / 3) < 1e-9


def test_peek_does_not_change_order():
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.peek(1)         # 只读，不刷新顺序
    c.put(3, "c")     # 淘汰 1（最久未使用）
    assert c.get(1) is None
    assert c.get(2) == "b"


def test_clear():
    c = LRUCache(3)
    c.put(1, "a")
    c.put(2, "b")
    c.get(1)
    c.clear()
    assert len(c) == 0
    assert c.hits == 0 and c.misses == 0  # clear 同时重置命中率统计
    assert c.get(1) is None


def test_dict_like_interface():
    c = LRUCache(2)
    c["x"] = 1
    c["y"] = 2
    assert c["x"] == 1
    assert "x" in c
    assert "z" not in c


def test_thread_safe_concurrent():
    c = ThreadSafeLRUCache(50)
    err = []

    def worker(base):
        try:
            for i in range(2000):
                k = base + (i % 100)
                c.put(k, i)
                c.get(k)
        except Exception as e:  # pragma: no cover
            err.append(e)

    threads = [threading.Thread(target=worker, args=(t * 100,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not err
    assert len(c) == 50


def test_ttl_not_expired():
    c = TTLCache(3, ttl=10.0)
    c.put(1, "a")
    assert c.get(1) == "a"


def test_ttl_expired_returns_none():
    c = TTLCache(3, ttl=0.05)
    c.put(1, "a")
    time.sleep(0.08)
    assert c.get(1) is None        # 已过期
    assert len(c) == 0             # 过期条目被惰性删除
    assert 1 not in c


def test_ttl_per_key_override():
    c = TTLCache(3, ttl=10.0)
    c.put(1, "a")                 # 默认 10s
    c.put(2, "b", ttl=0.05)       # 单独指定 0.05s
    time.sleep(0.08)
    assert c.get(1) == "a"        # 未过期
    assert c.get(2) is None       # 已过期


def test_ttl_invalid():
    with pytest.raises(ValueError):
        TTLCache(3, ttl=0)
