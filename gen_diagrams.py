"""生成 LRU 缓存项目的说明图（数据结构示意 / 流程图 / benchmark 柱状图）。

输出到 docs/ 目录，供 README 或答辩 PPT 使用。
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Rectangle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs"))
os.makedirs(OUT, exist_ok=True)

C_EDGE = "#2E7D32"
C_TEXT = "#1B1B1B"
FS = 13
FS_TITLE = 16


def _char_w(ch):
    o = ord(ch)
    if o > 0x2E80:
        return 0.30
    if ch == " ":
        return 0.13
    return 0.165


def _measure(text):
    lines = text.split("\n")
    w = max((sum(_char_w(c) for c in line) for line in lines), default=0)
    return w, len(lines)


def _node_size(text, kind):
    w, lines = _measure(text)
    if kind == "decision":
        return w * 1.5 + 1.6, lines * 0.62 + 1.0
    return w + 1.3, lines * 0.58 + 0.55


FILL = {"start": "#C8E6C9", "process": "#E8F5E9", "decision": "#FFF8E1", "end": "#FFCDD2"}
TC = {"start": "#1B5E20", "process": "#1B1B1B", "decision": "#7A5C00", "end": "#8B1A1A"}


def _box(ax, cx, cy, w, h, text, kind):
    if kind == "decision":
        d = Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)],
                    facecolor=FILL[kind], edgecolor="#B8860B", linewidth=1.2, closed=True)
        ax.add_patch(d)
    else:
        box = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                             boxstyle="round,pad=0.03,rounding_size=0.14",
                             facecolor=FILL[kind], edgecolor=C_EDGE, linewidth=1.2)
        ax.add_patch(box)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=FS, color=TC.get(kind, C_TEXT), linespacing=1.5)


def _arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=C_EDGE, lw=1.4))


def draw_flow(filename, title, steps):
    n = len(steps)
    sizes = [_node_size(t, k) for t, k in steps]
    heights = [h for w, h in sizes]
    max_w = max(w for w, h in sizes)
    gap = 0.7
    body_h = sum(heights) + gap * (n - 1)
    top_pad, bottom_pad = 1.4, 0.6
    total_h = body_h + top_pad + bottom_pad
    W = max_w + 2.0

    fig, ax = plt.subplots(figsize=(W * 0.72, total_h * 0.72))
    ax.set_xlim(0, W)
    ax.set_ylim(0, total_h)
    ax.axis("off")
    cx = W / 2
    ax.text(cx, total_h - 0.5, title, ha="center", fontsize=FS_TITLE, fontweight="bold", color=C_TEXT)

    ys = []
    y = total_h - top_pad
    for (text, kind), (w, h) in zip(steps, sizes):
        y -= h / 2
        ys.append(y)
        _box(ax, cx, y, w, h, text, kind)
        y -= h / 2 + gap

    for i in range(n - 1):
        _arrow(ax, cx, ys[i] - heights[i] / 2, cx, ys[i + 1] + heights[i + 1] / 2)

    fig.savefig(os.path.join(OUT, filename), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("生成:", filename)


def draw_structure(filename):
    """数据结构示意图：哈希表 + 双向链表。"""
    fig, ax = plt.subplots(figsize=(13, 7.5))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.text(7.5, 8.5, "LRU 缓存数据结构：哈希表 + 双向链表", ha="center",
            fontsize=FS_TITLE, fontweight="bold", color=C_TEXT)

    # 双向链表（横向）
    y = 5.8
    node_x = {"head": 2.0, "A": 4.8, "B": 7.6, "C": 10.4, "tail": 13.0}
    labels = ["head", "A", "B", "C", "tail"]
    bw, bh = 1.5, 0.75
    for lb in labels:
        x = node_x[lb]
        color = "#C8E6C9" if lb == "head" else ("#FFCDD2" if lb == "tail" else "#E8F5E9")
        ax.add_patch(FancyBboxPatch((x - bw / 2, y - bh / 2), bw, bh,
                                    boxstyle="round,pad=0.03,rounding_size=0.1",
                                    facecolor=color, edgecolor=C_EDGE, linewidth=1.4))
        ax.text(x, y, lb, ha="center", va="center", fontsize=14, fontweight="bold")

    # 链表节点间箭头：head->A、A<->B、B<->C、C->tail
    for a, b, both in [("head", "A", False), ("A", "B", True), ("B", "C", True), ("C", "tail", False)]:
        xa, xb = node_x[a], node_x[b]
        ax.annotate("", xy=(xb - bw / 2 - 0.03, y), xytext=(xa + bw / 2 + 0.03, y),
                    arrowprops=dict(arrowstyle="-|>", color=C_EDGE, lw=1.6))
        if both:
            ax.annotate("", xy=(xa + bw / 2 + 0.03, y + 0.22), xytext=(xb - bw / 2 - 0.03, y + 0.22),
                        arrowprops=dict(arrowstyle="-|>", color="#888888", lw=1.3))
    ax.text(7.5, y + 1.0, "最近使用", ha="center", fontsize=11, color="#2E7D32")
    ax.text(7.5, y - 1.35, "最久未使用（满了先淘汰它）", ha="center", fontsize=11, color="#C62828")

    # 哈希表（左下）
    hx, hy = 4.6, 1.9
    hw, hh = 6.0, 2.6
    ax.add_patch(Rectangle((hx - hw / 2, hy - hh / 2), hw, hh, fill=False,
                           edgecolor="#444444", linewidth=1.4))
    ax.text(hx, hy + hh / 2 + 0.45, "哈希表  key → 节点指针", ha="center", fontsize=12, fontweight="bold")
    rows = [("key1", "A"), ("key2", "B"), ("key3", "C")]
    for i, (k, node) in enumerate(rows):
        ry = hy + hh / 2 - 0.55 - i * 0.85
        ax.text(hx - 1.2, ry, k, ha="center", va="center", fontsize=12)
        ax.text(hx + 1.2, ry, f"→ {node}", ha="center", va="center", fontsize=12, color="#1565C0")
        # 从哈希表指向链表节点
        ax.annotate("", xy=(node_x[node], y - bh / 2 - 0.05), xytext=(hx + 2.2, ry),
                    arrowprops=dict(arrowstyle="-|>", color="#1565C0", lw=1.4,
                                    connectionstyle="arc3,rad=-0.25"))

    fig.savefig(os.path.join(OUT, filename), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("生成:", filename)


def draw_benchmark(filename):
    """benchmark 命中率对比柱状图（真实数据）。"""
    caps = ["5", "10", "20", "50", "100"]
    lru = [24.93, 39.89, 56.81, 80.83, 99.90]
    fifo = [22.41, 35.08, 50.75, 76.24, 99.90]
    lfu = [40.68, 51.07, 64.00, 84.41, 99.90]

    x = list(range(len(caps)))
    w = 0.26
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar([i - w for i in x], lru, w, label="LRU", color="#2E7D32")
    ax.bar(x, fifo, w, label="FIFO", color="#9E9E9E")
    ax.bar([i + w for i in x], lfu, w, label="LFU", color="#1565C0")

    ax.set_xticks(x)
    ax.set_xticklabels(caps)
    ax.set_xlabel("缓存容量", fontsize=13)
    ax.set_ylabel("命中率（%）", fontsize=13)
    ax.set_title("LRU vs FIFO vs LFU 命中率对比（Zipf 热点分布）", fontsize=15, fontweight="bold")
    ax.legend(fontsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_ylim(0, 110)
    for i in range(len(caps)):
        ax.text(i - w, lru[i] + 1, f"{lru[i]:.0f}", ha="center", fontsize=8)
        ax.text(i, fifo[i] + 1, f"{fifo[i]:.0f}", ha="center", fontsize=8)
        ax.text(i + w, lfu[i] + 1, f"{lfu[i]:.0f}", ha="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, filename), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("生成:", filename)


if __name__ == "__main__":
    draw_structure("LRU_数据结构示意图.png")

    draw_flow("get_流程图.png", "get 操作流程图", [
        ("开始", "start"),
        ("哈希表查找 key", "process"),
        ("命中？\n（否 → 返回 None）", "decision"),
        ("将节点移到链表头部", "process"),
        ("返回 value", "process"),
        ("结束", "end"),
    ])

    draw_flow("put_流程图.png", "put 操作流程图", [
        ("开始", "start"),
        ("key 已存在？\n（是 → 更新 value 并移到头部）", "decision"),
        ("新建节点，插入链表头部", "process"),
        ("容量已满？\n（否 → 结束）", "decision"),
        ("淘汰链表尾部节点", "process"),
        ("结束", "end"),
    ])

    draw_benchmark("benchmark_命中率对比.png")

    print("\n全部生成 ->", OUT)
