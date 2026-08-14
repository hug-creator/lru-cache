"""LRU 缓存可视化（Gradio 界面）。

实时展示缓存内容（最近 -> 最久）、命中率与链表结构。
配置从 .env 读取（load_dotenv + os.getenv），默认 127.0.0.1:7861。
"""

import os

from dotenv import load_dotenv

load_dotenv()

import gradio as gr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from lru import LRUCache

HOST = os.getenv("GRADIO_HOST", "127.0.0.1")
PORT = int(os.getenv("GRADIO_PORT", "7861"))


def render_state(cache: LRUCache) -> str:
    items = cache.items()
    if not items:
        return "缓存为空"
    lines = [f"**缓存内容**（最近 -> 最久，共 {len(items)} 项）："]
    for i, (k, v) in enumerate(items, 1):
        lines.append(f"{i}. `{k}` = `{v}`")
    return "\n".join(lines)


def render_rate(cache: LRUCache) -> str:
    total = cache.hits + cache.misses
    return f"命中 {cache.hits} / 未命中 {cache.misses}，命中率 **{cache.hit_rate:.2%}**"


def render_plot(cache: LRUCache):
    items = cache.items()
    fig, ax = plt.subplots(figsize=(11, 3))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis("off")

    labels = ["head"] + [str(k) for k, _ in items] + ["tail"]
    total = len(labels)
    xs = [1 + i * (10 / max(total - 1, 1)) for i in range(total)]

    for x, label in zip(xs, labels):
        if label == "head":
            color = "#C8E6C9"
        elif label == "tail":
            color = "#FFCDD2"
        else:
            color = "#E8F5E9"
        box = FancyBboxPatch(
            (x - 0.62, 1.7), 1.24, 0.7,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            facecolor=color, edgecolor="#2E7D32", linewidth=1.2,
        )
        ax.add_patch(box)
        ax.text(x, 2.05, label, ha="center", va="center", fontsize=9)

    for i in range(total - 1):
        ax.annotate(
            "", xy=(xs[i + 1] - 0.62, 2.05), xytext=(xs[i] + 0.62, 2.05),
            arrowprops=dict(arrowstyle="-|>", color="#2E7D32", lw=1.3),
        )

    ax.text(6, 0.55, "← 最近使用          最久使用 →", ha="center", fontsize=10, color="#555555")
    fig.tight_layout()
    return fig


def do_op(op: str, key: str, value: str, cache: LRUCache):
    if not key or not key.strip():
        raise gr.Error("key 不能为空")
    key = key.strip()
    if op == "put":
        cache.put(key, value)
        msg = f"✅ 写入 `{key}` = `{value}`"
    else:
        result = cache.get(key)
        msg = f"✅ 读取 `{key}` = `{result}`" if result is not None else f"❌ `{key}` 未命中"
    return msg, render_state(cache), render_rate(cache), render_plot(cache)


def clear_cache(cache: LRUCache):
    cache.clear()
    return "已清空", render_state(cache), render_rate(cache), render_plot(cache)


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="LRU 缓存可视化") as demo:
        gr.Markdown("# LRU 缓存可视化")
        gr.Markdown("哈希表 + 双向链表，`get` / `put` 均 O(1)。观察缓存内容与链表结构随访问的变化。")

        cache = gr.State(LRUCache(5))

        with gr.Row():
            op = gr.Radio(["put", "get"], value="put", label="操作")
            key = gr.Textbox(label="key")
            value = gr.Textbox(label="value（put 时填写）")

        with gr.Row():
            btn = gr.Button("执行", variant="primary")
            btn_clear = gr.Button("清空")

        out_msg = gr.Markdown()
        out_state = gr.Markdown()
        with gr.Row():
            out_rate = gr.Markdown()
            out_plot = gr.Plot(label="链表结构")

        btn.click(do_op, [op, key, value, cache], [out_msg, out_state, out_rate, out_plot])
        btn_clear.click(clear_cache, [cache], [out_msg, out_state, out_rate, out_plot])

    return demo


if __name__ == "__main__":
    build_demo().launch(server_name=HOST, server_port=PORT)
