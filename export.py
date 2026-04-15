"""
Export Utilities
================
CSV and PDF export functions for the scheduler results.
"""

import io
import csv
import pandas as pd
from typing import List


def export_csv(all_processes: list, metrics: dict) -> bytes:
    """Export process results and summary metrics to a CSV file in memory."""
    output = io.StringIO()

    writer = csv.writer(output)

    # ── Summary Section ─────────────
    writer.writerow(["=== SUMMARY METRICS ==="])
    for k, v in metrics.items():
        writer.writerow([k.replace("_", " ").title(), v])
    writer.writerow([])

    # ── Process Details ──────────────
    writer.writerow(["=== PROCESS DETAILS ==="])
    headers = ["PID", "Name", "Arrival Time", "Burst Time", "Priority", "Type",
               "Assigned Core", "Status", "Start Time", "Finish Time",
               "Waiting Time", "Turnaround Time", "Response Time", "Migrations"]
    writer.writerow(headers)

    for p in all_processes:
        writer.writerow([
            p.pid, p.name, p.arrival_time, p.burst_time, p.priority, p.process_type,
            p.assigned_core, p.status, p.start_time, p.finish_time,
            p.waiting_time, p.turnaround_time, p.response_time, p.migrations
        ])

    return output.getvalue().encode("utf-8")


def export_pdf_report(all_processes: list, metrics: dict,
                      comparison_results: dict = None) -> bytes:
    """Generate a simple but professional PDF report using fpdf2."""
    try:
        from fpdf import FPDF, XPos, YPos
    except ImportError:
        # Return a text/plain fallback if fpdf2 is not installed
        content = "PDF export requires fpdf2. Run: pip install fpdf2\n\n"
        content += "=== METRICS ===\n"
        for k, v in metrics.items():
            content += f"{k}: {v}\n"
        return content.encode("utf-8")

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(13, 17, 23)
            self.rect(0, 0, 210, 20, "F")
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(88, 166, 255)
            self.cell(0, 18, "Multi-Core Load Balancing Scheduler", align="C",
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(140, 148, 158)
            self.cell(0, 10, f"Page {self.page_no()} | Multi-Core Load Balancing Scheduler",
                      align="C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 25, 15)

    # ── Title ─────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(88, 166, 255)
    pdf.ln(4)
    pdf.cell(0, 12, "Simulation Report", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(140, 148, 158)
    pdf.cell(0, 8, "Dynamic Load Balancing | Multi-Core OS Scheduler",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # ── Summary Metrics ───────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(63, 185, 80)
    pdf.cell(0, 8, "Performance Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    metric_labels = {
        "avg_waiting_time": "Average Waiting Time",
        "avg_turnaround_time": "Average Turnaround Time",
        "avg_response_time": "Average Response Time",
        "throughput": "Throughput (procs/tick)",
        "cpu_utilization": "CPU Utilization %",
        "load_imbalance_factor": "Load Imbalance Factor",
        "total_migrations": "Total Migrations",
        "starvation_prevented": "Starvation Events Prevented",
        "completed": "Completed Processes",
        "total": "Total Processes",
    }

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(230, 237, 243)
    for k, v in metrics.items():
        label = metric_labels.get(k, k.replace("_", " ").title())
        pdf.set_fill_color(22, 27, 34)
        pdf.cell(110, 7, label, fill=True, border=0)
        pdf.set_fill_color(33, 38, 45)
        pdf.cell(65, 7, str(v), fill=True, border=0,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # ── Comparison Table ──────────────────────
    if comparison_results:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(63, 185, 80)
        pdf.cell(0, 8, "Algorithm Comparison", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

        headers = ["Algorithm", "Avg Wait", "Avg TAT", "Throughput", "CPU Util%"]
        col_w = [50, 35, 35, 35, 35]
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(33, 38, 45)
        pdf.set_text_color(88, 166, 255)
        for h, w in zip(headers, col_w):
            pdf.cell(w, 8, h, fill=True, border=1)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(230, 237, 243)
        for algo, res in comparison_results.items():
            row = [
                algo,
                str(res.get("avg_waiting_time", "-")),
                str(res.get("avg_turnaround_time", "-")),
                str(res.get("throughput", "-")),
                str(res.get("cpu_utilization", "-")),
            ]
            fill = (22, 27, 34) if list(comparison_results.keys()).index(algo) % 2 == 0 else (33, 38, 45)
            pdf.set_fill_color(*fill)
            for val, w in zip(row, col_w):
                pdf.cell(w, 7, val, fill=True, border=1)
            pdf.ln()
        pdf.ln(6)

    # ── Process Table ─────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(63, 185, 80)
    pdf.cell(0, 8, "Process Details", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    p_headers = ["Name", "Burst", "Priority", "Core", "Status", "Wait", "TAT", "Migrations"]
    p_widths = [20, 18, 20, 22, 28, 18, 18, 28]
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(33, 38, 45)
    pdf.set_text_color(88, 166, 255)
    for h, w in zip(p_headers, p_widths):
        pdf.cell(w, 7, h, fill=True, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(230, 237, 243)
    for i, p in enumerate(all_processes):
        fill = (22, 27, 34) if i % 2 == 0 else (33, 38, 45)
        pdf.set_fill_color(*fill)
        row = [p.name, str(p.burst_time), str(p.priority),
               f"Core-{p.assigned_core}" if p.assigned_core >= 0 else "-",
               p.status, str(p.waiting_time), str(p.turnaround_time), str(p.migrations)]
        for val, w in zip(row, p_widths):
            pdf.cell(w, 6, val[:14], fill=True, border=1)
        pdf.ln()

    return bytes(pdf.output())
