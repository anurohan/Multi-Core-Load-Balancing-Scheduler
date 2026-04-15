"""
Visualization Utilities
=======================
All Plotly chart builders for the Multi-Core Load Balancing Scheduler dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import math
from typing import List, Dict

# ── Color Palette ──────────────────────────────────────────────────────────────

THEME = {
    "bg": "#0D1117",
    "surface": "#161B22",
    "surface2": "#21262D",
    "border": "#30363D",
    "text": "#E6EDF3",
    "text_muted": "#8B949E",
    "accent": "#58A6FF",
    "green": "#3FB950",
    "yellow": "#D29922",
    "red": "#F85149",
    "purple": "#BC8CFF",
    "orange": "#FFA657",
    "teal": "#39D353",
}

CORE_COLORS = [
    "#58A6FF", "#3FB950", "#FFA657", "#F85149",
    "#BC8CFF", "#39D353", "#FF7EB9", "#FFD60A",
    "#4FC3F7", "#A5D6A7", "#FFAB91", "#CE93D8",
    "#80DEEA", "#C5E1A5", "#FFCC80", "#EF9A9A",
]

ALGO_COLORS = {
    "Dynamic": "#58A6FF",
    "FCFS": "#F85149",
    "RoundRobin": "#FFA657",
    "Priority": "#BC8CFF",
}


def util_color(util: float) -> str:
    if util < 50:
        return THEME["green"]
    elif util < 80:
        return THEME["yellow"]
    else:
        return THEME["red"]


# ── Core Utilization Gauges ────────────────────────────────────────────────────

def make_core_gauges(cores) -> go.Figure:
    n = len(cores)
    cols = min(4, n)
    rows = (n + cols - 1) // cols if n > 0 else 1

    import math
    specs = [[{"type": "indicator"} for _ in range(cols)] for _ in range(rows)]
    fig = make_subplots(rows=rows, cols=cols, specs=specs,
                        vertical_spacing=0.12, horizontal_spacing=0.08)

    for i, core in enumerate(cores):
        row = i // cols + 1
        col = i % cols + 1
        util = core.utilization
        color = util_color(util)
        q_proc = f"{core.queue_length} queued"
        cur = core.current_process.name if core.current_process else "Idle"

        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=util,
            number={"suffix": "%", "font": {"size": 22, "color": THEME["text"],
                                             "family": "JetBrains Mono, monospace"}},
            title={"text": f"<b>Core {core.core_id}</b><br>"
                           f"<span style='font-size:10px;color:{THEME['text_muted']}'>"
                           f"{cur} · {q_proc}</span>",
                   "font": {"color": THEME["text"], "size": 13}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1,
                         "tickcolor": THEME["border"],
                         "tickfont": {"color": THEME["text_muted"], "size": 9}},
                "bar": {"color": color, "thickness": 0.7},
                "bgcolor": THEME["surface2"],
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#1a3a1a"},
                    {"range": [50, 80], "color": "#3a3010"},
                    {"range": [80, 100], "color": "#3a1010"},
                ],
                "threshold": {
                    "line": {"color": THEME["text"], "width": 2},
                    "thickness": 0.8,
                    "value": 90,
                },
            },
            delta={"reference": 80, "increasing": {"color": THEME["red"]},
                   "decreasing": {"color": THEME["green"]}},
        ), row=row, col=col)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": THEME["text"], "family": "JetBrains Mono, monospace"},
        margin=dict(l=10, r=10, t=30, b=10),
        height=200 * rows,
    )
    return fig


# ── Gantt Chart ────────────────────────────────────────────────────────────────

def make_gantt(gantt_data: List[dict], num_cores: int) -> go.Figure:
    if not gantt_data:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title=dict(text="Gantt Chart — No data yet", font=dict(color=THEME["text_muted"])),
        )
        return fig

    # Build bar segments
    fig = go.Figure()
    seen_pids = set()

    for seg in gantt_data[-500:]:   # limit to last 500 segs for performance
        show_legend = seg["pid"] not in seen_pids
        seen_pids.add(seg["pid"])
        fig.add_trace(go.Bar(
            x=[seg["end"] - seg["start"]],
            y=[seg["core"]],
            base=[seg["start"]],
            orientation="h",
            marker_color=seg["color"],
            marker_line=dict(color="rgba(0,0,0,0.4)", width=0.5),
            name=seg["name"],
            legendgroup=seg["name"],
            showlegend=show_legend,
            hovertemplate=(
                f"<b>{seg['name']}</b><br>"
                f"Core: {seg['core']}<br>"
                f"Time: {seg['start']}–{seg['end']}<br>"
                f"Type: {seg['type']}<br>"
                f"Priority: {seg['priority']}"
                "<extra></extra>"
            ),
            text=seg["name"] if (seg["end"] - seg["start"]) >= 2 else "",
            textfont=dict(size=9, color="white"),
            insidetextanchor="middle",
        ))

    core_order = [f"Core-{i}" for i in range(num_cores)]
    fig.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=THEME["surface"],
        font={"color": THEME["text"], "family": "JetBrains Mono, monospace"},
        xaxis=dict(title="Time (ticks)", gridcolor=THEME["border"],
                   zerolinecolor=THEME["border"],
                   tickfont=dict(color=THEME["text_muted"])),
        yaxis=dict(categoryorder="array", categoryarray=core_order[::-1],
                   gridcolor=THEME["border"],
                   tickfont=dict(color=THEME["text"])),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10),
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=40),
        height=max(250, num_cores * 55),
    )
    return fig


# ── Load Distribution Pie / Heatmap ───────────────────────────────────────────

def make_load_pie(cores) -> go.Figure:
    labels = [f"Core-{c.core_id}" for c in cores]
    values = [max(c.total_load, 0.01) for c in cores]   # avoid all-zero
    colors = [CORE_COLORS[c.core_id % len(CORE_COLORS)] for c in cores]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors,
                    line=dict(color=THEME["bg"], width=3)),
        textfont=dict(size=11, color="white"),
        hovertemplate="<b>%{label}</b><br>Load: %{value}<br>Share: %{percent}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": THEME["text"], "family": "JetBrains Mono, monospace"},
        annotations=[dict(text="Load<br>Share", x=0.5, y=0.5,
                          font_size=13, showarrow=False,
                          font=dict(color=THEME["text"]))],
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        margin=dict(l=10, r=10, t=10, b=10),
        height=280,
    )
    return fig


def make_utilization_heatmap(util_history: Dict[int, List[float]], num_cores: int) -> go.Figure:
    if not util_history or not any(util_history.values()):
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        return fig

    max_len = max(len(v) for v in util_history.values())
    if max_len == 0:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        return fig

    # Build 2D matrix: rows = cores, cols = time ticks (last 60)
    window = 60
    matrix = []
    for cid in range(num_cores):
        hist = util_history.get(cid, [])
        row = hist[-window:] if len(hist) >= window else ([0] * (window - len(hist)) + hist)
        matrix.append(row)

    fig = go.Figure(go.Heatmap(
        z=matrix,
        y=[f"Core-{i}" for i in range(num_cores)],
        colorscale=[
            [0.0, "#1a3a1a"], [0.5, THEME["yellow"]], [1.0, THEME["red"]]
        ],
        zmin=0, zmax=100,
        colorbar=dict(
            title=dict(text="Util%", font=dict(color=THEME["text_muted"])),
            tickfont=dict(color=THEME["text_muted"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovertemplate="Core: %{y}<br>Tick: %{x}<br>Util: %{z:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=THEME["surface"],
        font={"color": THEME["text"], "family": "JetBrains Mono, monospace"},
        xaxis=dict(title="Last 60 ticks", gridcolor=THEME["border"],
                   tickfont=dict(color=THEME["text_muted"])),
        yaxis=dict(gridcolor=THEME["border"], tickfont=dict(color=THEME["text"])),
        margin=dict(l=10, r=10, t=10, b=40),
        height=max(180, num_cores * 40),
    )
    return fig


# ── Imbalance Meter ────────────────────────────────────────────────────────────

def make_imbalance_meter(imbalance_history: List[float]) -> go.Figure:
    current = imbalance_history[-1] if imbalance_history else 0
    color = util_color(current * 100)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(current * 100, 1),
        number={"suffix": "%", "font": {"size": 28, "color": THEME["text"],
                                        "family": "JetBrains Mono, monospace"}},
        title={"text": "<b>Load Imbalance Factor</b>",
               "font": {"color": THEME["text"], "size": 13}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1,
                     "tickcolor": THEME["border"],
                     "tickfont": {"color": THEME["text_muted"], "size": 9}},
            "bar": {"color": color, "thickness": 0.65},
            "bgcolor": THEME["surface2"],
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "#1a3a1a"},
                {"range": [30, 60], "color": "#3a3010"},
                {"range": [60, 100], "color": "#3a1010"},
            ],
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": THEME["text"]},
        margin=dict(l=20, r=20, t=40, b=20),
        height=220,
    )
    return fig


# ── Performance Metrics Over Time ─────────────────────────────────────────────

def make_metrics_timeline(util_history: Dict[int, List[float]],
                           throughput_history: List[float],
                           imbalance_history: List[float],
                           num_cores: int) -> go.Figure:
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("CPU Utilization % per Core", "Throughput (procs/tick)",
                         "Load Imbalance Factor"),
        vertical_spacing=0.12,
        shared_xaxes=True,
    )

    # Row 1: Per-core utilization lines
    for cid in range(num_cores):
        hist = util_history.get(cid, [])
        if hist:
            fig.add_trace(go.Scatter(
                y=hist, mode="lines",
                name=f"Core-{cid}",
                line=dict(color=CORE_COLORS[cid % len(CORE_COLORS)], width=1.5),
                hovertemplate=f"Core-{cid}: %{{y:.1f}}%<extra></extra>",
            ), row=1, col=1)

    # Row 2: Throughput
    if throughput_history:
        # Smoothed rolling average
        window = 5
        smoothed = pd.Series(throughput_history).rolling(window, min_periods=1).mean().tolist()
        fig.add_trace(go.Scatter(
            y=throughput_history, mode="lines",
            name="Raw Throughput",
            line=dict(color=THEME["text_muted"], width=1),
            opacity=0.4,
            showlegend=False,
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            y=smoothed, mode="lines",
            name="Throughput (avg)",
            line=dict(color=THEME["accent"], width=2),
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.1)",
        ), row=2, col=1)

    # Row 3: Imbalance
    if imbalance_history:
        smoothed_imb = pd.Series(imbalance_history).rolling(5, min_periods=1).mean().tolist()
        fig.add_trace(go.Scatter(
            y=[v * 100 for v in smoothed_imb], mode="lines",
            name="Imbalance %",
            line=dict(color=THEME["orange"], width=2),
            fill="tozeroy",
            fillcolor="rgba(255,166,87,0.1)",
        ), row=3, col=1)
        # threshold line
        fig.add_hline(y=30, line_dash="dash", line_color=THEME["yellow"],
                      line_width=1, row=3, col=1,
                      annotation_text="Threshold 30%",
                      annotation_font_color=THEME["yellow"])

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=THEME["surface"],
        font={"color": THEME["text"], "family": "JetBrains Mono, monospace"},
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        margin=dict(l=10, r=10, t=40, b=20),
        height=520,
    )
    for row in range(1, 4):
        fig.update_xaxes(gridcolor=THEME["border"], zerolinecolor=THEME["border"],
                         tickfont=dict(color=THEME["text_muted"]), row=row, col=1)
        fig.update_yaxes(gridcolor=THEME["border"], zerolinecolor=THEME["border"],
                         tickfont=dict(color=THEME["text_muted"]), row=row, col=1)
    return fig


# ── Algorithm Comparison Bar Chart ────────────────────────────────────────────

def make_comparison_chart(comparison_results: dict) -> go.Figure:
    if not comparison_results:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        return fig

    metrics = ["avg_waiting_time", "avg_turnaround_time", "avg_response_time",
               "throughput", "cpu_utilization"]
    labels = ["Avg Wait Time", "Avg Turnaround", "Avg Response", "Throughput", "CPU Util %"]

    fig = make_subplots(rows=1, cols=len(metrics),
                        subplot_titles=labels,
                        horizontal_spacing=0.06)

    algos = list(comparison_results.keys())
    for idx, (metric, label) in enumerate(zip(metrics, labels)):
        for algo in algos:
            val = comparison_results[algo].get(metric, 0)
            fig.add_trace(go.Bar(
                x=[algo],
                y=[val],
                name=algo,
                legendgroup=algo,
                showlegend=(idx == 0),
                marker_color=ALGO_COLORS.get(algo, "#888"),
                marker_line=dict(color="rgba(0,0,0,0.3)", width=1),
                text=[f"{val:.2f}"],
                textposition="outside",
                textfont=dict(size=9, color=THEME["text"]),
            ), row=1, col=idx + 1)

    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=THEME["surface"],
        font={"color": THEME["text"], "family": "JetBrains Mono, monospace"},
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11),
                    orientation="h", yanchor="bottom", y=1.05,
                    xanchor="center", x=0.5),
        margin=dict(l=10, r=10, t=60, b=20),
        height=380,
    )
    for col in range(1, len(metrics) + 1):
        fig.update_xaxes(showticklabels=False, row=1, col=col)
        fig.update_yaxes(gridcolor=THEME["border"],
                         tickfont=dict(color=THEME["text_muted"]),
                         row=1, col=col)
    return fig


def make_comparison_radar(comparison_results: dict) -> go.Figure:
    if not comparison_results:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        return fig

    # Normalize metrics 0–1 (lower is better for wait/turnaround, higher for throughput/util)
    metrics = ["avg_waiting_time", "avg_turnaround_time", "throughput",
               "cpu_utilization", "avg_response_time"]
    labels = ["Wait Time↓", "Turnaround↓", "Throughput↑", "CPU Util↑", "Response↓"]

    # Get max values for normalization
    all_vals = {m: [comparison_results[a].get(m, 0) for a in comparison_results] for m in metrics}
    max_vals = {m: max(v) if max(v) > 0 else 1 for m, v in all_vals.items()}

    fig = go.Figure()
    for algo, color in ALGO_COLORS.items():
        if algo not in comparison_results:
            continue
        vals = []
        for m in metrics:
            raw = comparison_results[algo].get(m, 0)
            normalized = raw / max_vals[m]
            # For "lower is better" metrics, invert
            if m in ("avg_waiting_time", "avg_turnaround_time", "avg_response_time"):
                normalized = 1 - normalized
            vals.append(round(normalized, 3))
        vals.append(vals[0])  # close polygon
        cats = labels + [labels[0]]

        fig.add_trace(go.Scatterpolar(
            r=vals, theta=cats,
            fill="toself",
            name=algo,
            line_color=color,
            fillcolor=color.replace(")", ",0.12)").replace("rgb", "rgba")
                if "rgb" in color else color + "22",
            opacity=0.85,
        ))

    fig.update_layout(
        polar=dict(
            bgcolor=THEME["surface"],
            radialaxis=dict(visible=True, range=[0, 1],
                            tickfont=dict(color=THEME["text_muted"], size=8),
                            gridcolor=THEME["border"]),
            angularaxis=dict(tickfont=dict(color=THEME["text"], size=11),
                             gridcolor=THEME["border"]),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": THEME["text"], "family": "JetBrains Mono, monospace"},
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        margin=dict(l=40, r=40, t=40, b=40),
        height=360,
    )
    return fig


# ── Process Queue Table ───────────────────────────────────────────────────────

def make_process_table(all_processes: list) -> go.Figure:
    if not all_processes:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        return fig

    rows = []
    for p in all_processes:
        status_emoji = {"Running": "▶ Running", "Completed": "✔ Done",
                        "Waiting": "⏳ Waiting", "Migrated": "🔄 Migrated"}.get(p.status, p.status)
        core_str = f"Core-{p.assigned_core}" if p.assigned_core >= 0 else "—"
        rows.append([p.name, p.pid, p.burst_time, p.remaining_time,
                     p.priority, p.process_type, core_str, status_emoji,
                     p.waiting_time, p.turnaround_time, p.migrations])

    df = pd.DataFrame(rows, columns=[
        "Name", "PID", "Burst", "Remaining", "Priority",
        "Type", "Core", "Status", "Wait", "TAT", "Migrations"
    ])

    status_colors = []
    for p in all_processes:
        c = {"Running": THEME["green"], "Completed": THEME["accent"],
             "Waiting": THEME["yellow"], "Migrated": THEME["purple"]}.get(p.status, THEME["text_muted"])
        status_colors.append(c)

    fig = go.Figure(go.Table(
        columnwidth=[70, 45, 55, 75, 65, 90, 75, 110, 50, 60, 80],
        header=dict(
            values=[f"<b>{c}</b>" for c in df.columns],
            fill_color=THEME["surface2"],
            font=dict(color=THEME["accent"], size=11,
                      family="JetBrains Mono, monospace"),
            line_color=THEME["border"],
            align="center",
            height=32,
        ),
        cells=dict(
            values=[df[c] for c in df.columns],
            fill_color=THEME["surface"],
            font=dict(color=THEME["text"], size=10,
                      family="JetBrains Mono, monospace"),
            line_color=THEME["border"],
            align="center",
            height=28,
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=min(600, 60 + len(all_processes) * 28),
    )
    return fig
