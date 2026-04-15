"""
Multi-Core Load Balancing Scheduler
=====================================
Main Streamlit Application
Author  : [Your Name]
College : [Your College]
Year    : 2024–25

Run:  streamlit run app.py
"""

import streamlit as st
import time
import copy
import pandas as pd

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Core Load Balancer",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Local Imports ────────────────────────────────────────────────────────────
from utils.scheduler import MultiCoreScheduler, Process, run_comparison
from utils.visualizations import (
    make_core_gauges, make_gantt, make_load_pie,
    make_utilization_heatmap, make_imbalance_meter,
    make_metrics_timeline, make_comparison_chart,
    make_comparison_radar, make_process_table,
)
from utils.export import export_csv, export_pdf_report

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import fonts */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #0D1117 !important;
    color: #E6EDF3 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1117 0%, #161B22 100%) !important;
    border-right: 1px solid #30363D !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 16px 20px !important;
    transition: border-color 0.2s;
}
[data-testid="stMetric"]:hover {
    border-color: #58A6FF;
}
[data-testid="stMetricLabel"] {
    color: #8B949E !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="stMetricValue"] {
    color: #E6EDF3 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 26px !important;
    font-weight: 600;
}

/* Tabs */
[data-testid="stTabs"] button {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500;
    color: #8B949E !important;
    border-bottom: 2px solid transparent !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #58A6FF !important;
    border-bottom: 2px solid #58A6FF !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
}

/* Buttons */
.stButton > button {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600;
    border-radius: 8px !important;
    border: 1px solid #30363D !important;
    transition: all 0.2s;
}
.stButton > button:hover {
    border-color: #58A6FF !important;
    background: rgba(88,166,255,0.1) !important;
}

/* Selectbox & Slider */
[data-testid="stSelectbox"], [data-testid="stNumberInput"] {
    background: #161B22;
}

/* Section headers */
.section-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #58A6FF;
    margin: 12px 0 6px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid #21262D;
}

/* Status badge */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
}
.badge-running { background: rgba(63,185,80,0.15); color: #3FB950; border: 1px solid #3FB950; }
.badge-idle    { background: rgba(139,148,158,0.1); color: #8B949E; border: 1px solid #30363D; }
.badge-warn    { background: rgba(210,153,34,0.15); color: #D29922; border: 1px solid #D29922; }
.badge-error   { background: rgba(248,81,73,0.15);  color: #F85149; border: 1px solid #F85149; }

/* Log box */
.log-box {
    background: #0D1117;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 10px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #8B949E;
    max-height: 300px;
    overflow-y: auto;
    line-height: 1.6;
}

/* Divider */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #30363D, transparent);
    margin: 16px 0;
}

/* Big title */
.hero-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(90deg, #58A6FF, #BC8CFF, #3FB950);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
}
.hero-sub {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    color: #8B949E;
    margin-top: 2px;
}

/* Info card */
.info-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-left: 3px solid #58A6FF;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
    font-size: 13px;
    line-height: 1.6;
}
.concept-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-left: 3px solid #3FB950;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ───────────────────────────────────────────────────────
def init_state():
    defaults = {
        "scheduler": None,
        "running": False,
        "tick_speed": 0.3,
        "num_cores": 4,
        "algorithm": "Dynamic",
        "pid_counter": 0,
        "comparison_results": {},
        "simulation_done": False,
        "last_tick_time": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_scheduler() -> MultiCoreScheduler:
    if st.session_state.scheduler is None:
        st.session_state.scheduler = MultiCoreScheduler(
            num_cores=st.session_state.num_cores,
            algorithm=st.session_state.algorithm,
        )
    return st.session_state.scheduler


def next_pid() -> int:
    st.session_state.pid_counter += 1
    return st.session_state.pid_counter


init_state()

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="hero-title">⚡ ML Scheduler</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Multi-Core Load Balancing</p>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── System Config ─────────────────────────────────────────────────────────
    st.markdown('<p class="section-header">⚙ System Configuration</p>', unsafe_allow_html=True)

    num_cores = st.selectbox(
        "CPU Cores",
        options=[4, 8, 12, 16],
        index=[4, 8, 12, 16].index(st.session_state.num_cores),
        key="core_select",
    )

    algorithm = st.selectbox(
        "Scheduling Algorithm",
        options=["Dynamic", "FCFS", "RoundRobin", "Priority"],
        index=["Dynamic", "FCFS", "RoundRobin", "Priority"].index(st.session_state.algorithm),
        help="Dynamic = Multi-Core Load Balancer (our algorithm)",
    )

    if num_cores != st.session_state.num_cores or algorithm != st.session_state.algorithm:
        st.session_state.num_cores = num_cores
        st.session_state.algorithm = algorithm
        st.session_state.scheduler = None
        st.session_state.simulation_done = False

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Simulation Controls ───────────────────────────────────────────────────
    st.markdown('<p class="section-header">▶ Simulation Controls</p>', unsafe_allow_html=True)

    tick_speed = st.slider(
        "Simulation Speed (sec/tick)",
        min_value=0.05, max_value=1.5, value=0.3, step=0.05,
        format="%.2f s",
    )
    st.session_state.tick_speed = tick_speed

    col_play, col_pause, col_reset = st.columns(3)
    with col_play:
        if st.button("▶ Play", use_container_width=True):
            if not st.session_state.simulation_done:
                st.session_state.running = True
    with col_pause:
        if st.button("⏸ Pause", use_container_width=True):
            st.session_state.running = False
    with col_reset:
        if st.button("↺ Reset", use_container_width=True):
            st.session_state.running = False
            st.session_state.scheduler = None
            st.session_state.pid_counter = 0
            st.session_state.comparison_results = {}
            st.session_state.simulation_done = False
            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Process Generator ──────────────────────────────────────────────────────
    st.markdown('<p class="section-header">⊕ Process Generator</p>', unsafe_allow_html=True)

    gen_tab, manual_tab = st.tabs(["Random", "Manual"])

    with gen_tab:
        g_count = st.number_input("Count", min_value=1, max_value=50, value=8, step=1)
        g_max_arrival = st.slider("Max Arrival Time", 0, 30, 10)
        g_max_burst = st.slider("Max Burst Time", 2, 30, 15)
        if st.button("⚡ Generate", use_container_width=True):
            sched = get_scheduler()
            sched.generate_random_processes(
                count=int(g_count),
                max_arrival=int(g_max_arrival),
                max_burst=int(g_max_burst),
            )
            st.session_state.simulation_done = False
            st.success(f"Generated {g_count} processes")

    with manual_tab:
        m_arrival = st.number_input("Arrival Time", 0, 100, 0, key="m_arr")
        m_burst = st.number_input("Burst Time", 1, 50, 5, key="m_burst")
        m_priority = st.slider("Priority (1=High)", 1, 10, 5, key="m_pri")
        m_type = st.selectbox("Type", ["CPU-bound", "I/O-bound"], key="m_type")
        if st.button("+ Add Process", use_container_width=True):
            sched = get_scheduler()
            pid = next_pid()
            p = Process(
                pid=pid, name=f"P{pid}",
                arrival_time=int(m_arrival),
                burst_time=int(m_burst),
                remaining_time=int(m_burst),
                priority=int(m_priority),
                process_type=m_type,
            )
            sched.add_process(p)
            st.session_state.simulation_done = False
            st.success(f"Added P{pid}")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Comparison Mode ────────────────────────────────────────────────────────
    st.markdown('<p class="section-header">📊 Comparison Mode</p>', unsafe_allow_html=True)

    if st.button("Run All 4 Algorithms", use_container_width=True):
        sched = get_scheduler()
        if sched.all_processes:
            with st.spinner("Running comparison..."):
                st.session_state.comparison_results = run_comparison(
                    sched.all_processes, st.session_state.num_cores
                )
            st.success("Comparison complete!")
        else:
            st.warning("Add processes first.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Export ─────────────────────────────────────────────────────────────────
    st.markdown('<p class="section-header">📤 Export Results</p>', unsafe_allow_html=True)

    sched_export = get_scheduler()
    metrics_export = sched_export.get_metrics()

    csv_bytes = export_csv(sched_export.all_processes, metrics_export)
    st.download_button(
        "⬇ Download CSV",
        data=csv_bytes,
        file_name="scheduler_results.csv",
        mime="text/csv",
        use_container_width=True,
    )

    pdf_bytes = export_pdf_report(
        sched_export.all_processes, metrics_export,
        st.session_state.comparison_results or None
    )
    st.download_button(
        "⬇ Download PDF Report",
        data=pdf_bytes,
        file_name="scheduler_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN AREA — TABS
# ─────────────────────────────────────────────────────────────────────────────
sched = get_scheduler()

# Header row
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<h2 class="hero-title">Multi-Core Load Balancing Scheduler</h2>',
                unsafe_allow_html=True)
    st.markdown(
        f'<p class="hero-sub">Algorithm: <b>{sched.algorithm}</b> &nbsp;|&nbsp; '
        f'Cores: <b>{sched.num_cores}</b> &nbsp;|&nbsp; '
        f'Tick: <b>{sched.current_tick}</b> &nbsp;|&nbsp; '
        f'Processes: <b>{len(sched.all_processes)}</b></p>',
        unsafe_allow_html=True,
    )
with col_status:
    if st.session_state.running:
        st.markdown('<span class="badge badge-running">● RUNNING</span>',
                    unsafe_allow_html=True)
    elif st.session_state.simulation_done:
        st.markdown('<span class="badge badge-error">✔ DONE</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-idle">◉ PAUSED</span>',
                    unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Quick Metrics Row ──────────────────────────────────────────────────────────
metrics = sched.get_metrics()
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Avg Wait Time", f"{metrics['avg_waiting_time']:.1f}",
          help="Average ticks a process spends waiting")
m2.metric("Avg Turnaround", f"{metrics['avg_turnaround_time']:.1f}",
          help="Average ticks from arrival to completion")
m3.metric("Throughput", f"{metrics['throughput']:.3f}",
          help="Processes completed per tick")
m4.metric("CPU Utilization", f"{metrics['cpu_utilization']:.1f}%",
          help="Aggregate CPU busy percentage")
m5.metric("Migrations", str(metrics['total_migrations']),
          help="Work-stealing migrations performed")
m6.metric("Completed", f"{metrics['completed']}/{metrics['total']}",
          help="Processes finished / total")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🖥️ Dashboard",
    "📊 Analytics",
    "🔄 Comparison",
    "📋 Processes",
    "📜 Logs",
    "❓ Help",
])

# ════════════════════════════════════════════
#  TAB 1: DASHBOARD
# ════════════════════════════════════════════
with tabs[0]:
    # Gauges
    st.markdown("### CPU Core Utilization")
    gauge_fig = make_core_gauges(sched.cores)
    st.plotly_chart(gauge_fig, use_container_width=True, key="gauges")

    # Gantt + Load
    col_g, col_p = st.columns([2, 1])
    with col_g:
        st.markdown("### Gantt Chart")
        gantt_fig = make_gantt(sched.gantt_data, sched.num_cores)
        st.plotly_chart(gantt_fig, use_container_width=True, key="gantt")
    with col_p:
        st.markdown("### Load Distribution")
        pie_fig = make_load_pie(sched.cores)
        st.plotly_chart(pie_fig, use_container_width=True, key="load_pie")

        imb_fig = make_imbalance_meter(sched.imbalance_history)
        st.plotly_chart(imb_fig, use_container_width=True, key="imbalance")

    # Heatmap
    st.markdown("### Core Utilization Heatmap (Last 60 ticks)")
    heatmap_fig = make_utilization_heatmap(sched.utilization_history, sched.num_cores)
    st.plotly_chart(heatmap_fig, use_container_width=True, key="heatmap")

# ════════════════════════════════════════════
#  TAB 2: ANALYTICS
# ════════════════════════════════════════════
with tabs[1]:
    st.markdown("### Performance Metrics Over Time")
    timeline_fig = make_metrics_timeline(
        sched.utilization_history,
        sched.throughput_history,
        sched.imbalance_history,
        sched.num_cores,
    )
    st.plotly_chart(timeline_fig, use_container_width=True, key="timeline")

    # Detailed metrics table
    st.markdown("### Detailed Performance Metrics")
    metric_data = {
        "Metric": [
            "Average Waiting Time",
            "Average Turnaround Time",
            "Average Response Time",
            "Throughput (procs/tick)",
            "CPU Utilization %",
            "Load Imbalance Factor",
            "Total Migrations",
            "Starvation Events Prevented",
            "Processes Completed",
            "Total Processes",
        ],
        "Value": [
    f"{metrics['avg_waiting_time']:.1f}",
    f"{metrics['avg_turnaround_time']:.1f}",
    f"{metrics['avg_response_time']:.1f}",
    f"{metrics['throughput']:.3f}",
    f"{metrics['cpu_utilization']:.1f}%",
    f"{metrics['load_imbalance_factor']:.4f}",
    str(metrics['total_migrations']),
    str(metrics['starvation_prevented']),
    f"{metrics['completed']}/{metrics['total']}",
    str(metrics['total']),
],
        "Description": [
            "Ticks a process waits before first execution",
            "Total time from arrival to completion",
            "Time from arrival to first CPU slice",
            "Completed processes per simulation tick",
            "Aggregate utilization across all cores",
            "Normalized (max−min)/max load difference",
            "Inter-core process migrations performed",
            "Priority boosts applied via aging",
            "Processes that finished execution",
            "Total processes in the simulation",
        ],
    }
    df_metrics = pd.DataFrame(metric_data)
    st.dataframe(
        df_metrics,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Metric": st.column_config.TextColumn(width="medium"),
            "Value": st.column_config.TextColumn(width="small"),
            "Description": st.column_config.TextColumn(width="large"),
        },
    )

# ════════════════════════════════════════════
#  TAB 3: COMPARISON
# ════════════════════════════════════════════
with tabs[2]:
    if not st.session_state.comparison_results:
        st.info(
            "🔄 No comparison data yet. Add processes and click **Run All 4 Algorithms** "
            "in the sidebar to compare Dynamic vs FCFS vs Round Robin vs Priority Scheduling."
        )
    else:
        cr = st.session_state.comparison_results

        st.markdown("### Algorithm Comparison - Bar Charts")
        bar_fig = make_comparison_chart(cr)
        st.plotly_chart(bar_fig, use_container_width=True, key="comp_bar")

        col_r, col_t = st.columns([1, 1])
        with col_r:
            st.markdown("### Radar / Spider Chart")
            radar_fig = make_comparison_radar(cr)
            st.plotly_chart(radar_fig, use_container_width=True, key="comp_radar")
        with col_t:
            st.markdown("### Comparison Table")
            rows = []
            for algo, res in cr.items():
                rows.append({
                    "Algorithm": algo,
                    "Avg Wait": res.get("avg_waiting_time", "-"),
                    "Avg TAT": res.get("avg_turnaround_time", "-"),
                    "Avg Response": res.get("avg_response_time", "-"),
                    "Throughput": res.get("throughput", "-"),
                    "CPU Util%": res.get("cpu_utilization", "-"),
                    "Migrations": res.get("total_migrations", "-"),
                    "Starvation Prev.": res.get("starvation_prevented", "-"),
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        # Highlight best
        st.markdown("### 🏆 Winner Analysis")
        for metric, label, lower_is_better in [
            ("avg_waiting_time", "Avg Waiting Time", True),
            ("avg_turnaround_time", "Avg Turnaround Time", True),
            ("throughput", "Throughput", False),
            ("cpu_utilization", "CPU Utilization %", False),
        ]:
            vals = {a: cr[a].get(metric, 0) for a in cr}
            if lower_is_better:
                best = min(vals, key=vals.get)
            else:
                best = max(vals, key=vals.get)
            icon = "🥇" if best == "Dynamic" else "📌"
            st.markdown(
                f'<div class="info-card">{icon} <b>{label}</b>: '
                f'Best = <b>{best}</b> ({vals[best]:.3f})</div>',
                unsafe_allow_html=True,
            )

# ════════════════════════════════════════════
#  TAB 4: PROCESSES
# ════════════════════════════════════════════
with tabs[3]:
    st.markdown("### Process Queue & Execution Status")
    if not sched.all_processes:
        st.info("No processes added yet. Use the sidebar to generate or add processes.")
    else:
        proc_fig = make_process_table(sched.all_processes)
        st.plotly_chart(proc_fig, use_container_width=True, key="proc_table")

        # Per-core queues
        st.markdown("### Per-Core Queue Status")
        core_cols = st.columns(min(sched.num_cores, 4))
        for i, core in enumerate(sched.cores):
            col = core_cols[i % 4]
            with col:
                cur = core.current_process
                cur_str = f"▶ {cur.name}" if cur else "Idle"
                util_color_str = (
                    "#3FB950" if core.utilization < 50
                    else "#D29922" if core.utilization < 80
                    else "#F85149"
                )
                st.markdown(
                    f'<div class="info-card" style="border-left-color:{util_color_str}">'
                    f'<b>Core-{core.core_id}</b><br>'
                    f'Current: <code>{cur_str}</code><br>'
                    f'Queue: {core.queue_length} processes<br>'
                    f'Utilization: {core.utilization:.1f}%<br>'
                    f'Total Load: {core.total_load} ticks'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if (i + 1) % 4 == 0 and i + 1 < sched.num_cores:
                core_cols = st.columns(min(sched.num_cores - i - 1, 4))

# ════════════════════════════════════════════
#  TAB 5: LOGS
# ════════════════════════════════════════════
with tabs[4]:
    st.markdown("### System Event Log")
    col_lf, col_lc = st.columns([1, 1])
    with col_lf:
        log_filter = st.text_input("Filter logs", placeholder="e.g. MIGRATION or Core-2")
    with col_lc:
        show_last = st.slider("Show last N entries", 20, 500, 100)

    logs = sched.log_entries[-show_last:]
    if log_filter:
        logs = [l for l in logs if log_filter.upper() in l.upper()]

    log_html = "<br>".join(
        f'<span style="color:{"#3FB950" if "COMPLET" in l else "#58A6FF" if "MIGRAT" in l else "#FFA657" if "AGING" in l else "#8B949E"}">{l}</span>'
        for l in reversed(logs)
    ) or "No log entries yet."

    st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
#  TAB 6: HELP
# ════════════════════════════════════════════
with tabs[5]:
    st.markdown("## ❓ OS Concepts & Help")

    concepts = [
        ("🖥️ Multi-Core Scheduling",
         "Modern CPUs have multiple cores that can execute processes simultaneously. "
         "The OS scheduler must decide which process runs on which core. "
         "Efficient scheduling improves throughput, reduces latency, and maximizes CPU utilization."),
        ("⚖️ Load Balancing",
         "Load balancing ensures that no core is overwhelmed while others sit idle. "
         "The imbalance factor = (max_load − min_load) / max_load. "
         "Our algorithm assigns new processes to the least-loaded core at all times."),
        ("🔄 Work Stealing",
         "When imbalance exceeds 30%, the scheduler performs work stealing: "
         "it migrates processes from the busiest core to the least-loaded core. "
         "This is used in Java's ForkJoinPool, Go's goroutine scheduler, and Linux CFS."),
        ("⚡ Aging (Starvation Prevention)",
         "Low-priority processes can starve if high-priority processes keep arriving. "
         "Aging increments a process's age counter each tick. When age exceeds the threshold, "
         "its priority is boosted by 1. This guarantees eventual execution."),
        ("📊 Key Metrics",
         "• Waiting Time = Turnaround − Burst | time spent in queue\n"
         "• Turnaround Time = Finish − Arrival | total lifecycle time\n"
         "• Response Time = First CPU − Arrival | perceived responsiveness\n"
         "• Throughput = Completed / Total Ticks | work done per unit time\n"
         "• CPU Utilization = Busy Ticks / (Cores × Total Ticks)"),
        ("🆚 Algorithm Comparison",
         "• FCFS: Simple, no preemption, prone to convoy effect\n"
         "• Round Robin: Fair time-slicing, good for interactive systems\n"
         "• Priority: Better for real-time, but risks starvation\n"
         "• Dynamic (Ours): Combines least-loaded assignment + work stealing + aging"),
        ("🎮 How to Use This Simulator",
         "1. Choose number of CPU cores (4/8/12/16)\n"
         "2. Select algorithm (Dynamic recommended)\n"
         "3. Generate random processes OR add manually\n"
         "4. Press ▶ Play to start the simulation\n"
         "5. Watch core gauges, Gantt chart and metrics update in real-time\n"
         "6. Click 'Run All 4 Algorithms' to compare\n"
         "7. Export results as CSV or PDF"),
    ]

    for title, content in concepts:
        with st.expander(title, expanded=False):
            st.markdown(
                f'<div class="concept-card"><pre style="white-space:pre-wrap;'
                f'font-family:Space Grotesk,sans-serif;font-size:13px;'
                f'color:#E6EDF3;background:transparent;border:none">{content}</pre></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown(
        '<div class="info-card">💡 <b>Pro Tip:</b> For the best demo, generate 10–15 processes '
        'with mixed burst times, then run the Dynamic algorithm and compare against FCFS. '
        'Notice how Dynamic achieves lower average waiting time and better load balance.</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  AUTO-ADVANCE SIMULATION LOOP
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.running and not st.session_state.simulation_done:
    time.sleep(st.session_state.tick_speed)

    sched = get_scheduler()
    if sched.all_processes:
        still_going = sched.tick()
        all_done = (len(sched.completed_processes) == len(sched.all_processes)
                    and len(sched.all_processes) > 0)
        if not still_going or all_done:
            st.session_state.running = False
            st.session_state.simulation_done = True
    else:
        st.session_state.running = False

    st.rerun()
