"""LRU（Least Recently Used，最近最少使用）缓存。

核心思路：**哈希表 + 双向链表**，把 get / put 都做到 O(1)。

- 哈希表：``key -> 节点``，O(1) 定位到具体节点
- 双向链表：维护访问顺序，最近访问在头部、最久未使用在尾部；
  命中 / 插入时把节点移到头部，容量满时淘汰尾部节点

纯标准库实现，零第三方依赖。
"""

from __future__ import annotations

import threading
import time
from typing import Dict, Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class _Node(Generic[K, V]):
    """双向链表节点。"""

    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: K, value: V) -> None:
        self.key = key
        self.value = value
        self.prev: Optional[_Node] = None
        self.next: Optional[_Node] = None


class LRUCache(Generic[K, V]):
    """基于哈希表 + 双向链表的 LRU 缓存，get / put 均 O(1)。"""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity 必须为正整数")
        self.capacity = capacity
        self._cache: Dict[K, _Node] = {}
        # 哨兵头尾节点，避免判空、简化边界处理
        self._head: _Node = _Node(None, None)  # type: ignore[arg-type]
        self._tail: _Node = _Node(None, None)  # type: ignore[arg-type]
        self._head.next = self._tail
        self._tail.prev = self._head
        # 命中率统计
        self.hits = 0
        self.misses = 0

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: K) -> bool:
        return key in self._cache

    def __getitem__(self, key: K) -> Optional[V]:
        return self.get(key)

    def __setitem__(self, key: K, value: V) -> None:
        self.put(key, value)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def get(self, key: K) -> Optional[V]:
        """读取 key 对应值；命中则将其标记为最近使用并返回，未命中返回 None。"""
        node = self._cache.get(key)
        if node is None:
            self.misses += 1
            return None
        self.hits += 1
        self._move_to_head(node)
        return node.value

    def put(self, key: K, value: V) -> None:
        """写入 key -> value；已存在则更新并移到头部，不存在则插入，容量满时淘汰最久未使用。"""
        node = self._cache.get(key)
        if node is not None:
            node.value = value
            self._move_to_head(node)
            return
        node = _Node(key, value)
        self._cache[key] = node
        self._add_to_head(node)
        if len(self._cache) > self.capacity:
            self._evict_tail()

    def peek(self, key: K) -> Optional[V]:
        """只读查询，不改变访问顺序、不影响命中率统计。"""
        node = self._cache.get(key)
        return node.value if node is not None else None

    def items(self):
        """按「最近使用 -> 最久使用」的顺序返回 (key, value) 列表。"""
        result = []
        node = self._head.next
        while node is not self._tail:
            result.append((node.key, node.value))
            node = node.next
        return result

    def clear(self) -> None:
        self._cache.clear()
        self._head.next = self._tail
        self._tail.prev = self._head
        self.hits = 0
        self.misses = 0

    # ---- 内部链表操作 ----

    def _add_to_head(self, node: _Node) -> None:
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node  # type: ignore[union-attr]
        self._head.next = node

    def _remove_node(self, node: _Node) -> None:
        node.prev.next = node.next  # type: ignore[union-attr]
        node.next.prev = node.prev  # type: ignore[union-attr]

    def _move_to_head(self, node: _Node) -> None:
        self._remove_node(node)
        self._add_to_head(node)

    def _evict_tail(self) -> None:
        node = self._tail.prev
        self._remove_node(node)  # type: ignore[arg-type]
        del self._cache[node.key]  # type: ignore[arg-type]


class ThreadSafeLRUCache(LRUCache[K, V]):
    """线程安全的 LRU 缓存，用可重入锁保护所有读写操作。"""

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self._lock = threading.RLock()

    def get(self, key: K) -> Optional[V]:
        with self._lock:
            return super().get(key)

    def put(self, key: K, value: V) -> None:
        with self._lock:
            super().put(key, value)

    def peek(self, key: K) -> Optional[V]:
        with self._lock:
            return super().peek(key)

    def __len__(self) -> int:
        with self._lock:
            return super().__len__()


class TTLCache(LRUCache[K, V]):
    """带 TTL（Time-To-Live，存活时间）的 LRU 缓存。

    条目在 put 后 ``ttl`` 秒内有效，``get`` 时惰性检查，过期即删除并视为未命中。
    每个条目也可在 ``put`` 时单独指定 ttl 覆盖默认值。
    """

    def __init__(self, capacity: int, ttl: float) -> None:
        super().__init__(capacity)
        if ttl <= 0:
            raise ValueError("ttl 必须为正数")
        self.ttl = ttl
        self._expire_at: Dict[K, float] = {}

    def put(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        effective = ttl if ttl is not None else self.ttl
        super().put(key, value)
        self._expire_at[key] = time.monotonic() + effective

    def get(self, key: K) -> Optional[V]:
        node = self._cache.get(key)
        if node is None:
            self.misses += 1
            return None
        if time.monotonic() >= self._expire_at.get(key, 0):
            # 已过期：惰性删除
            self._remove_node(node)
            del self._cache[key]
            self._expire_at.pop(key, None)
            self.misses += 1
            return None
        self.hits += 1
        self._move_to_head(node)
        return node.value

    def _evict_tail(self) -> None:
        node = self._tail.prev
        self._remove_node(node)  # type: ignore[arg-type]
        del self._cache[node.key]  # type: ignore[arg-type]
        self._expire_at.pop(node.key, None)  # type: ignore[arg-type]

    def clear(self) -> None:
        super().clear()
        self._expire_at.clear()
