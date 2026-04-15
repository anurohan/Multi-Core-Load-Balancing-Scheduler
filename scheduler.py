"""
Multi-Core Load Balancing Scheduler Engine
==========================================
Core simulation logic for dynamic load balancing across CPU cores.
Implements: Least-Loaded Core Assignment, Work Stealing, Aging, FCFS, RR, Priority.
"""

import random
import time
import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import copy


# ─────────────────────────────────────────────
#  DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class Process:
    """Represents a single process in the system."""
    pid: int
    name: str
    arrival_time: int
    burst_time: int
    remaining_time: int
    priority: int                   # 1 (highest) – 10 (lowest)
    process_type: str               # "CPU-bound" | "I/O-bound"
    color: str = "#4CAF50"

    # Scheduler-assigned fields
    assigned_core: int = -1
    start_time: int = -1
    finish_time: int = -1
    waiting_time: int = 0
    turnaround_time: int = 0
    response_time: int = -1
    age: int = 0                    # Aging counter for starvation prevention
    migrations: int = 0
    status: str = "Waiting"         # Waiting | Running | Completed | Migrated

    # Gantt tracking
    gantt_segments: List[dict] = field(default_factory=list)

    def __post_init__(self):
        self.remaining_time = self.burst_time


@dataclass
class CPUCore:
    """Represents a single CPU core."""
    core_id: int
    utilization: float = 0.0
    load: int = 0                   # total remaining burst time of queued processes
    current_process: Optional[Process] = None
    process_queue: List[Process] = field(default_factory=list)
    total_busy_time: int = 0
    idle_time: int = 0

    @property
    def queue_length(self) -> int:
        return len(self.process_queue)

    @property
    def total_load(self) -> int:
        q_load = sum(p.remaining_time for p in self.process_queue)
        cur_load = self.current_process.remaining_time if self.current_process else 0
        return q_load + cur_load


# ─────────────────────────────────────────────
#  HELPER: PROCESS COLORS
# ─────────────────────────────────────────────

PROCESS_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
    "#F0B27A", "#82E0AA", "#F1948A", "#AED6F1", "#A9DFBF",
    "#F9E79F", "#D7BDE2", "#A3E4D7", "#FAD7A0", "#A9CCE3",
]


# ─────────────────────────────────────────────
#  SCHEDULER CLASS
# ─────────────────────────────────────────────

class MultiCoreScheduler:
    """
    Dynamic Multi-Core Load Balancing Scheduler.

    Algorithm:
      1. Assign new arrivals to the least-loaded core (load = sum of remaining burst times).
      2. Each time quantum, execute one unit on the current process of every core.
      3. Every REBALANCE_INTERVAL ticks, check imbalance factor; if > IMBALANCE_THRESHOLD,
         perform work-stealing: steal processes from the busiest core to the idlest core.
      4. Apply aging: increment age for all waiting processes; if age > AGING_THRESHOLD,
         boost priority to prevent starvation.
    """

    REBALANCE_INTERVAL = 5       # ticks between rebalancing passes
    IMBALANCE_THRESHOLD = 0.3    # 30 % imbalance triggers migration
    AGING_THRESHOLD = 10         # ticks before priority boost
    TIME_QUANTUM = 2             # Round-Robin quantum (for RR comparison)

    def __init__(self, num_cores: int = 4, algorithm: str = "Dynamic"):
        self.num_cores = num_cores
        self.algorithm = algorithm          # "Dynamic" | "FCFS" | "RoundRobin" | "Priority"
        self.cores: List[CPUCore] = [CPUCore(core_id=i) for i in range(num_cores)]
        self.all_processes: List[Process] = []
        self.completed_processes: List[Process] = []
        self.current_tick: int = 0
        self.total_migrations: int = 0
        self.starvation_events_prevented: int = 0
        self.log_entries: List[str] = []
        self.gantt_data: List[dict] = []
        self.imbalance_history: List[float] = []
        self.utilization_history: Dict[int, List[float]] = {i: [] for i in range(num_cores)}
        self.throughput_history: List[float] = []
        self._completed_at_last_tick: int = 0
        self._rr_quantum_counters: Dict[int, int] = {i: 0 for i in range(num_cores)}

    # ── Process Generation ─────────────────────

    def add_process(self, process: Process):
        """Add a single process to the scheduler's incoming queue."""
        process.color = PROCESS_COLORS[process.pid % len(PROCESS_COLORS)]
        self.all_processes.append(process)
        self.log(f"[T={self.current_tick}] Process {process.name} (PID={process.pid}) "
                 f"added | Burst={process.burst_time} | Priority={process.priority} | "
                 f"Type={process.process_type}")

    def generate_random_processes(self, count: int = 10, max_arrival: int = 20,
                                   max_burst: int = 20) -> List[Process]:
        """Generate a batch of random processes."""
        processes = []
        pid_start = max((p.pid for p in self.all_processes), default=0) + 1
        types = ["CPU-bound", "I/O-bound"]
        for i in range(count):
            pid = pid_start + i
            p = Process(
                pid=pid,
                name=f"P{pid}",
                arrival_time=random.randint(0, max_arrival),
                burst_time=random.randint(2, max_burst),
                remaining_time=0,
                priority=random.randint(1, 10),
                process_type=random.choice(types),
            )
            p.remaining_time = p.burst_time
            self.add_process(p)
            processes.append(p)
        return processes

    # ── Core Assignment Logic ──────────────────

    def _least_loaded_core(self) -> CPUCore:
        """Return the core with the smallest total load (sum of remaining times)."""
        return min(self.cores, key=lambda c: c.total_load)

    def _busiest_core(self) -> CPUCore:
        return max(self.cores, key=lambda c: c.total_load)

    def _assign_to_core(self, process: Process, core: CPUCore):
        """Assign a process to a specific core."""
        process.assigned_core = core.core_id
        process.status = "Waiting"
        core.process_queue.append(process)
        self.log(f"[T={self.current_tick}] ✅ {process.name} assigned to Core-{core.core_id} "
                 f"(load={core.total_load})")

    def _assign_to_core_rr_priority(self, process: Process):
        """For comparison algorithms: assign round-robin across cores."""
        core = self.cores[process.pid % self.num_cores]
        self._assign_to_core(process, core)

    # ── Arrival Handling ───────────────────────

    def _handle_arrivals(self):
        """Move newly arrived processes onto cores."""
        for p in self.all_processes:
            if p.status == "Waiting" and p.arrival_time == self.current_tick and p.assigned_core == -1:
                if self.algorithm == "Dynamic":
                    core = self._least_loaded_core()
                    self._assign_to_core(p, core)
                else:
                    self._assign_to_core_rr_priority(p)

        # Also pick up processes that arrived before we started (arrival_time < current)
        for p in self.all_processes:
            if p.arrival_time <= self.current_tick and p.assigned_core == -1 and p.status == "Waiting":
                if self.algorithm == "Dynamic":
                    core = self._least_loaded_core()
                    self._assign_to_core(p, core)
                else:
                    self._assign_to_core_rr_priority(p)

    # ── Work Stealing / Rebalancing ────────────

    def _rebalance(self):
        """
        Work-Stealing Rebalance:
        If load imbalance factor > threshold, migrate processes from busiest to least loaded.
        Imbalance Factor = (max_load - min_load) / max_load
        """
        loads = [c.total_load for c in self.cores]
        max_load = max(loads)
        min_load = min(loads)

        if max_load == 0:
            return

        imbalance = (max_load - min_load) / max_load
        self.imbalance_history.append(round(imbalance, 4))

        if imbalance > self.IMBALANCE_THRESHOLD:
            busiest = self._busiest_core()
            idlest = self._least_loaded_core()
            if busiest.core_id == idlest.core_id:
                return
            # Steal half the queue from the busiest core
            steal_count = max(1, len(busiest.process_queue) // 2)
            stolen = busiest.process_queue[:steal_count]
            busiest.process_queue = busiest.process_queue[steal_count:]

            for p in stolen:
                p.assigned_core = idlest.core_id
                p.migrations += 1
                p.status = "Migrated"
                idlest.process_queue.append(p)
                self.total_migrations += 1
                self.log(f"[T={self.current_tick}] 🔄 MIGRATION: {p.name} "
                         f"Core-{busiest.core_id} → Core-{idlest.core_id} "
                         f"(imbalance={imbalance:.2%})")
        else:
            self.imbalance_history.append(imbalance)  # duplicate to keep length consistent

    # ── Aging (Starvation Prevention) ─────────

    def _apply_aging(self):
        """
        Increment age for all waiting processes.
        If age exceeds threshold, boost priority (lower number = higher priority).
        """
        for core in self.cores:
            for p in core.process_queue:
                p.age += 1
                if p.age > 0 and p.age % self.AGING_THRESHOLD == 0:
                    old_priority = p.priority
                    p.priority = max(1, p.priority - 1)
                    if p.priority < old_priority:
                        self.starvation_events_prevented += 1
                        self.log(f"[T={self.current_tick}] ⚡ AGING: {p.name} priority boosted "
                                 f"{old_priority} → {p.priority} (age={p.age})")

    # ── Core Execution Step ────────────────────

    def _sort_queue(self, core: CPUCore):
        """Sort the core's queue according to the selected algorithm."""
        if self.algorithm in ("Dynamic", "Priority"):
            core.process_queue.sort(key=lambda p: p.priority)
        elif self.algorithm == "FCFS":
            core.process_queue.sort(key=lambda p: p.arrival_time)
        # RoundRobin: FIFO, no sorting needed

    def _execute_cores(self):
        """Execute one time unit on each core."""
        for core in self.cores:
            # If no running process, pick next from queue
            if core.current_process is None:
                self._sort_queue(core)
                if core.process_queue:
                    next_p = core.process_queue.pop(0)
                    core.current_process = next_p
                    next_p.status = "Running"
                    if next_p.start_time == -1:
                        next_p.start_time = self.current_tick
                    if next_p.response_time == -1:
                        next_p.response_time = self.current_tick - next_p.arrival_time
                    self.log(f"[T={self.current_tick}] ▶ Core-{core.core_id} starts {next_p.name}")

            # Execute current process for 1 tick
            if core.current_process:
                p = core.current_process
                p.remaining_time -= 1
                core.total_busy_time += 1

                # Record gantt segment
                self.gantt_data.append({
                    "core": f"Core-{core.core_id}",
                    "core_id": core.core_id,
                    "pid": p.pid,
                    "name": p.name,
                    "start": self.current_tick,
                    "end": self.current_tick + 1,
                    "color": p.color,
                    "priority": p.priority,
                    "type": p.process_type,
                })

                # Round-Robin: preempt after quantum
                if self.algorithm == "RoundRobin":
                    self._rr_quantum_counters[core.core_id] = \
                        self._rr_quantum_counters.get(core.core_id, 0) + 1
                    if self._rr_quantum_counters[core.core_id] >= self.TIME_QUANTUM and p.remaining_time > 0:
                        self._rr_quantum_counters[core.core_id] = 0
                        core.process_queue.append(p)
                        p.status = "Waiting"
                        core.current_process = None
                        self.log(f"[T={self.current_tick}] ⏱ RR preempt: {p.name} on Core-{core.core_id}")
                        continue

                # Check completion
                if p.remaining_time <= 0:
                    p.finish_time = self.current_tick + 1
                    p.turnaround_time = p.finish_time - p.arrival_time
                    p.waiting_time = p.turnaround_time - p.burst_time
                    p.status = "Completed"
                    self.completed_processes.append(p)
                    core.current_process = None
                    self.log(f"[T={self.current_tick}] ✔ {p.name} COMPLETED on Core-{core.core_id} "
                             f"| TAT={p.turnaround_time} | WT={p.waiting_time}")
            else:
                core.idle_time += 1

    # ── Utilization Tracking ───────────────────

    def _update_utilization(self):
        for core in self.cores:
            total = core.total_busy_time + core.idle_time
            util = (core.total_busy_time / total * 100) if total > 0 else 0.0
            core.utilization = round(util, 1)
            self.utilization_history[core.core_id].append(core.utilization)

    # ── Throughput Tracking ────────────────────

    def _update_throughput(self):
        completed_this_tick = len(self.completed_processes) - self._completed_at_last_tick
        self._completed_at_last_tick = len(self.completed_processes)
        self.throughput_history.append(completed_this_tick)

    # ── Main Tick ──────────────────────────────

    def tick(self) -> bool:
        """
        Advance the simulation by one time unit.
        Returns True if there is still work remaining, False if simulation is complete.
        """
        self._handle_arrivals()
        self._apply_aging()

        if self.algorithm == "Dynamic" and self.current_tick % self.REBALANCE_INTERVAL == 0:
            self._rebalance()

        self._execute_cores()
        self._update_utilization()
        self._update_throughput()
        self.current_tick += 1

        # Check if there is remaining work
        has_waiting = any(
            p.status not in ("Completed",) for p in self.all_processes
        )
        has_running = any(c.current_process is not None or len(c.process_queue) > 0
                          for c in self.cores)
        return has_waiting or has_running

    def run_full(self, max_ticks: int = 200):
        """Run the simulation to completion (used for comparison mode)."""
        for _ in range(max_ticks):
            still_running = self.tick()
            if not still_running and len(self.completed_processes) == len(self.all_processes):
                break

    # ── Metrics ────────────────────────────────

    def get_metrics(self) -> dict:
        if not self.completed_processes:
            return {
                "avg_waiting_time": 0, "avg_turnaround_time": 0,
                "avg_response_time": 0, "throughput": 0,
                "cpu_utilization": 0, "load_imbalance_factor": 0,
                "total_migrations": 0, "starvation_prevented": 0,
                "completed": 0, "total": len(self.all_processes),
            }

        wt = [p.waiting_time for p in self.completed_processes]
        tat = [p.turnaround_time for p in self.completed_processes]
        rt = [p.response_time for p in self.completed_processes if p.response_time >= 0]

        total_time = self.current_tick if self.current_tick > 0 else 1
        total_busy = sum(c.total_busy_time for c in self.cores)
        total_possible = self.num_cores * total_time
        cpu_util = (total_busy / total_possible * 100) if total_possible > 0 else 0

        loads = [c.total_load for c in self.cores]
        max_load = max(loads) if loads else 0
        min_load = min(loads) if loads else 0
        imbalance = ((max_load - min_load) / max_load) if max_load > 0 else 0

        return {
            "avg_waiting_time": round(sum(wt) / len(wt), 2),
            "avg_turnaround_time": round(sum(tat) / len(tat), 2),
            "avg_response_time": round(sum(rt) / len(rt), 2) if rt else 0,
            "throughput": round(len(self.completed_processes) / total_time, 3),
            "cpu_utilization": round(cpu_util, 1),
            "load_imbalance_factor": round(imbalance, 4),
            "total_migrations": self.total_migrations,
            "starvation_prevented": self.starvation_events_prevented,
            "completed": len(self.completed_processes),
            "total": len(self.all_processes),
        }

    def log(self, msg: str):
        self.log_entries.append(msg)
        if len(self.log_entries) > 500:
            self.log_entries = self.log_entries[-500:]

    def reset(self):
        """Full reset of the scheduler."""
        self.__init__(self.num_cores, self.algorithm)


# ─────────────────────────────────────────────
#  COMPARISON ENGINE
# ─────────────────────────────────────────────

def run_comparison(processes_template: List[Process], num_cores: int) -> dict:
    """
    Run all four algorithms on the same process set and return their metrics.
    """
    results = {}
    for algo in ["Dynamic", "FCFS", "RoundRobin", "Priority"]:
        sched = MultiCoreScheduler(num_cores=num_cores, algorithm=algo)
        # Deep copy processes so each run is independent
        for p in processes_template:
            fresh = Process(
                pid=p.pid, name=p.name, arrival_time=p.arrival_time,
                burst_time=p.burst_time, remaining_time=p.burst_time,
                priority=p.priority, process_type=p.process_type,
            )
            sched.add_process(fresh)
        sched.run_full(max_ticks=500)
        results[algo] = sched.get_metrics()
    return results
