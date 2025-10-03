#!/usr/bin/env python3
"""
Pipeline Report Visualizer
==========================
Creates visual charts and HTML dashboard from pipeline_report.json

Usage:
    python visualize_pipeline_report.py [report_file]

Arguments:
    report_file - Path to pipeline report JSON (default: pipeline_report.json)

Output:
    - Individual PNG charts
    - HTML dashboard with all visualizations

Example:
    python visualize_pipeline_report.py
    python visualize_pipeline_report.py pipeline_report.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import base64
from io import BytesIO

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib not installed. Install with: pip install matplotlib")


def load_report(filepath):
    """Load the pipeline report JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {filepath}: {e}")
        sys.exit(1)


def create_stage_duration_chart(data, output_file='stage_durations.png'):
    """Create bar chart of stage durations"""
    stages_data = data.get('stages', {})
    
    stages = []
    durations = []
    colors = []
    
    color_map = {
        1: '#3498db',  # Blue
        2: '#2ecc71',  # Green
        3: '#9b59b6',  # Purple
        4: '#f39c12',  # Orange
        5: '#e74c3c',  # Red
        6: '#1abc9c'   # Turquoise
    }
    
    for stage_num in sorted([int(k) for k in stages_data.keys()]):
        stage = stages_data[str(stage_num)]
        stages.append(f"Stage {stage_num}\n{stage['stage_name']}")
        durations.append(stage['duration'])
        colors.append(color_map.get(stage_num, '#95a5a6'))
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(stages, durations, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}s',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_ylabel('Duration (seconds)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Pipeline Stage', fontsize=12, fontweight='bold')
    ax.set_title('Pipeline Stage Execution Time', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file


def create_success_rate_chart(data, output_file='stage_success_rates.png'):
    """Create bar chart of stage success rates"""
    stages_data = data.get('stages', {})
    
    stages = []
    success_rates = []
    items_processed = []
    items_failed = []
    
    for stage_num in sorted([int(k) for k in stages_data.keys()]):
        stage = stages_data[str(stage_num)]
        stages.append(f"Stage {stage_num}")
        success_rates.append(stage.get('success_rate', 0))
        items_processed.append(stage.get('items_processed', 0))
        items_failed.append(stage.get('items_failed', 0))
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Success rate chart
    colors = ['#2ecc71' if rate == 100 else '#e74c3c' if rate == 0 else '#f39c12' 
              for rate in success_rates]
    bars1 = ax1.bar(stages, success_rates, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    for bar, rate in zip(bars1, success_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax1.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Stage', fontsize=12, fontweight='bold')
    ax1.set_title('Success Rate by Stage', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 105)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.axhline(y=100, color='green', linestyle='--', alpha=0.3, linewidth=2)
    
    # Items processed/failed chart
    x = np.arange(len(stages))
    width = 0.35
    
    bars2 = ax2.bar(x - width/2, items_processed, width, label='Processed', 
                   color='#2ecc71', alpha=0.8, edgecolor='black', linewidth=1.5)
    bars3 = ax2.bar(x + width/2, items_failed, width, label='Failed', 
                   color='#e74c3c', alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax2.set_ylabel('Item Count', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Stage', fontsize=12, fontweight='bold')
    ax2.set_title('Items Processed vs Failed', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(stages)
    ax2.legend(fontsize=10)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file


def create_memory_usage_chart(data, output_file='memory_usage.png'):
    """Create line chart of memory usage across stages"""
    stages_data = data.get('stages', {})
    
    stages = []
    mem_start = []
    mem_end = []
    mem_peak = []
    
    for stage_num in sorted([int(k) for k in stages_data.keys()]):
        stage = stages_data[str(stage_num)]
        stages.append(f"S{stage_num}")
        mem_start.append(stage.get('memory_start_mb', 0))
        mem_end.append(stage.get('memory_end_mb', 0))
        mem_peak.append(stage.get('memory_peak_mb', 0))
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(stages))
    
    ax.plot(x, mem_start, marker='o', linewidth=2, markersize=8, 
            label='Start', color='#3498db', alpha=0.8)
    ax.plot(x, mem_end, marker='s', linewidth=2, markersize=8, 
            label='End', color='#2ecc71', alpha=0.8)
    ax.plot(x, mem_peak, marker='^', linewidth=2, markersize=8, 
            label='Peak', color='#e74c3c', alpha=0.8, linestyle='--')
    
    ax.fill_between(x, mem_start, mem_peak, alpha=0.1, color='red')
    
    ax.set_xticks(x)
    ax.set_xticklabels(stages)
    ax.set_ylabel('Memory (MB)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Stage', fontsize=12, fontweight='bold')
    ax.set_title('Memory Usage Across Pipeline Stages', fontsize=14, fontweight='bold', pad=20)
    ax.legend(fontsize=10, loc='best')
    ax.grid(alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file


def create_file_processing_chart(data, output_file='file_processing.png'):
    """Create chart showing top slowest files"""
    slowest = data.get('top_slowest_files', [])[:10]
    
    if not slowest:
        return None
    
    files = [Path(f['file_path']).name for f in slowest]
    times = [f['total_time'] * 1000 for f in slowest]  # Convert to ms
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(files)))
    bars = ax.barh(files, times, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for bar, time in zip(bars, times):
        width = bar.get_width()
        if width > 0:
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{width:.1f}ms',
                   ha='left', va='center', fontsize=9, fontweight='bold', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    ax.set_xlabel('Processing Time (milliseconds)', fontsize=12, fontweight='bold')
    ax.set_title('Top 10 Slowest Files', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file


def create_error_chart(data, output_file='errors.png'):
    """Create chart showing error distribution"""
    errors = data.get('errors', [])
    
    if not errors:
        # Create "No Errors" chart
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, '✓ No Errors Detected', 
               ha='center', va='center', fontsize=24, 
               fontweight='bold', color='green',
               transform=ax.transAxes)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        return output_file
    
    # Count errors by type and stage
    error_types = {}
    stage_errors = {}
    
    for error in errors:
        error_type = error.get('type', 'Unknown')
        stage = error.get('stage', 0)
        
        error_types[error_type] = error_types.get(error_type, 0) + 1
        stage_errors[f"Stage {stage}"] = stage_errors.get(f"Stage {stage}", 0) + 1
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Error types pie chart
    colors1 = plt.cm.Set3(np.linspace(0, 1, len(error_types)))
    wedges, texts, autotexts = ax1.pie(error_types.values(), labels=error_types.keys(),
                                        autopct='%1.1f%%', colors=colors1,
                                        startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
    ax1.set_title(f'Error Types\n(Total: {len(errors)})', fontsize=14, fontweight='bold')
    
    # Stage errors bar chart
    stages = list(stage_errors.keys())
    counts = list(stage_errors.values())
    colors2 = ['#e74c3c'] * len(stages)
    
    bars = ax2.bar(stages, counts, color=colors2, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax2.set_ylabel('Error Count', fontsize=12, fontweight='bold')
    ax2.set_title('Errors by Stage', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file


def create_overview_dashboard(data, output_file='pipeline_overview.png'):
    """Create comprehensive overview dashboard"""
    summary = data.get('summary', {})
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Main title
    fig.suptitle('Pipeline Execution Dashboard', fontsize=20, fontweight='bold', y=0.98)
    
    # 1. Summary metrics (top left)
    ax1 = fig.add_subplot(gs[0, :])
    ax1.axis('off')
    
    metrics_text = f"""
    📊 PIPELINE SUMMARY
    
    Duration: {summary.get('pipeline_duration_formatted', 'N/A')}  |  Files Processed: {summary.get('processed_files', 0)}/{summary.get('total_files', 0)}  |  Success Rate: {summary.get('success_rate', 0):.1f}%  |  Cache Hit: {summary.get('cache_hit_rate', 0):.1f}%
    
    Start: {summary.get('start_time', 'N/A').split('T')[1] if 'T' in summary.get('start_time', '') else 'N/A'}  |  End: {summary.get('end_time', 'N/A').split('T')[1] if 'T' in summary.get('end_time', '') else 'N/A'}
    """
    
    ax1.text(0.5, 0.5, metrics_text, ha='center', va='center', 
            fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round,pad=1', facecolor='lightblue', alpha=0.3),
            family='monospace')
    
    # 2. Stage durations (middle row, left)
    ax2 = fig.add_subplot(gs[1, 0])
    stages_data = data.get('stages', {})
    stage_names = [f"S{i}" for i in sorted([int(k) for k in stages_data.keys()])]
    stage_durs = [stages_data[str(i)]['duration'] for i in sorted([int(k) for k in stages_data.keys()])]
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(stage_names)))
    ax2.bar(stage_names, stage_durs, color=colors, alpha=0.8, edgecolor='black')
    ax2.set_ylabel('Duration (s)', fontsize=10, fontweight='bold')
    ax2.set_title('Stage Durations', fontsize=11, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. Success rates (middle row, middle)
    ax3 = fig.add_subplot(gs[1, 1])
    success_rates = [stages_data[str(i)].get('success_rate', 0) for i in sorted([int(k) for k in stages_data.keys()])]
    colors_success = ['green' if r == 100 else 'orange' if r > 0 else 'red' for r in success_rates]
    ax3.bar(stage_names, success_rates, color=colors_success, alpha=0.7, edgecolor='black')
    ax3.set_ylabel('Success Rate (%)', fontsize=10, fontweight='bold')
    ax3.set_title('Success Rates', fontsize=11, fontweight='bold')
    ax3.set_ylim(0, 105)
    ax3.axhline(y=100, color='green', linestyle='--', alpha=0.5)
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Items processed (middle row, right)
    ax4 = fig.add_subplot(gs[1, 2])
    items_proc = [stages_data[str(i)].get('items_processed', 0) for i in sorted([int(k) for k in stages_data.keys()])]
    ax4.bar(stage_names, items_proc, color='skyblue', alpha=0.8, edgecolor='black')
    ax4.set_ylabel('Items', fontsize=10, fontweight='bold')
    ax4.set_title('Items Processed', fontsize=11, fontweight='bold')
    ax4.grid(axis='y', alpha=0.3)
    
    # 5. Memory usage (bottom row, left & middle)
    ax5 = fig.add_subplot(gs[2, :2])
    mem_start = [stages_data[str(i)].get('memory_start_mb', 0) for i in sorted([int(k) for k in stages_data.keys()])]
    mem_end = [stages_data[str(i)].get('memory_end_mb', 0) for i in sorted([int(k) for k in stages_data.keys()])]
    x = np.arange(len(stage_names))
    ax5.plot(x, mem_start, marker='o', label='Start', linewidth=2, markersize=6)
    ax5.plot(x, mem_end, marker='s', label='End', linewidth=2, markersize=6)
    ax5.fill_between(x, mem_start, mem_end, alpha=0.2)
    ax5.set_xticks(x)
    ax5.set_xticklabels(stage_names)
    ax5.set_ylabel('Memory (MB)', fontsize=10, fontweight='bold')
    ax5.set_title('Memory Usage', fontsize=11, fontweight='bold')
    ax5.legend(fontsize=9)
    ax5.grid(alpha=0.3)
    
    # 6. Error count (bottom row, right)
    ax6 = fig.add_subplot(gs[2, 2])
    errors = data.get('errors', [])
    if errors:
        stage_errors = {}
        for error in errors:
            stage = f"S{error.get('stage', 0)}"
            stage_errors[stage] = stage_errors.get(stage, 0) + 1
        
        ax6.bar(stage_errors.keys(), stage_errors.values(), color='red', alpha=0.7, edgecolor='black')
        ax6.set_ylabel('Error Count', fontsize=10, fontweight='bold')
        ax6.set_title(f'Errors ({len(errors)} total)', fontsize=11, fontweight='bold')
        ax6.grid(axis='y', alpha=0.3)
    else:
        ax6.text(0.5, 0.5, '✓ No Errors', ha='center', va='center',
                fontsize=14, fontweight='bold', color='green',
                transform=ax6.transAxes)
        ax6.set_title('Error Status', fontsize=11, fontweight='bold')
        ax6.axis('off')
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file


def image_to_base64(image_path):
    """Convert image to base64 for embedding in HTML"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def generate_html_dashboard(data, chart_files, output_file='pipeline_dashboard.html'):
    """Generate HTML dashboard with all charts"""
    summary = data.get('summary', {})
    errors = data.get('errors', [])
    
    # Convert images to base64
    chart_data = {}
    for name, path in chart_files.items():
        if path and Path(path).exists():
            chart_data[name] = image_to_base64(path)
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pipeline Report Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}
        
        .metric-card .label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .metric-card.success .value {{
            color: #28a745;
        }}
        
        .metric-card.warning .value {{
            color: #ffc107;
        }}
        
        .metric-card.danger .value {{
            color: #dc3545;
        }}
        
        .charts {{
            padding: 30px;
        }}
        
        .chart-section {{
            margin-bottom: 40px;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .chart-section h2 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-size: 1.8em;
        }}
        
        .chart-section img {{
            width: 100%;
            height: auto;
            border-radius: 10px;
        }}
        
        .error-list {{
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 20px;
            margin-top: 20px;
            border-radius: 5px;
        }}
        
        .error-item {{
            padding: 15px;
            background: white;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 3px solid #dc3545;
        }}
        
        .error-item strong {{
            color: #dc3545;
        }}
        
        .no-errors {{
            text-align: center;
            padding: 40px;
            color: #28a745;
            font-size: 1.5em;
            font-weight: bold;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .metric-card:hover {{
                transform: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Pipeline Execution Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="label">Total Duration</div>
                <div class="value">{summary.get('pipeline_duration_formatted', 'N/A')}</div>
            </div>
            
            <div class="metric-card">
                <div class="label">Files Scanned</div>
                <div class="value">{summary.get('total_files', 0)}</div>
            </div>
            
            <div class="metric-card {'success' if summary.get('processed_files', 0) > 0 else 'warning'}">
                <div class="label">Files Processed</div>
                <div class="value">{summary.get('processed_files', 0)}</div>
            </div>
            
            <div class="metric-card {'danger' if summary.get('failed_files', 0) > 0 else 'success'}">
                <div class="label">Files Failed</div>
                <div class="value">{summary.get('failed_files', 0)}</div>
            </div>
            
            <div class="metric-card {'success' if summary.get('success_rate', 0) == 100 else 'warning' if summary.get('success_rate', 0) > 0 else 'danger'}">
                <div class="label">Success Rate</div>
                <div class="value">{summary.get('success_rate', 0):.1f}%</div>
            </div>
            
            <div class="metric-card">
                <div class="label">Cache Hit Rate</div>
                <div class="value">{summary.get('cache_hit_rate', 0):.1f}%</div>
            </div>
        </div>
        
        <div class="charts">
            {'<div class="chart-section"><h2>📈 Overview Dashboard</h2><img src="data:image/png;base64,' + chart_data.get('overview', '') + '" alt="Overview Dashboard"></div>' if 'overview' in chart_data else ''}
            
            {'<div class="chart-section"><h2>⏱️ Stage Durations</h2><img src="data:image/png;base64,' + chart_data.get('durations', '') + '" alt="Stage Durations"></div>' if 'durations' in chart_data else ''}
            
            {'<div class="chart-section"><h2>✅ Success Rates</h2><img src="data:image/png;base64,' + chart_data.get('success', '') + '" alt="Success Rates"></div>' if 'success' in chart_data else ''}
            
            {'<div class="chart-section"><h2>💾 Memory Usage</h2><img src="data:image/png;base64,' + chart_data.get('memory', '') + '" alt="Memory Usage"></div>' if 'memory' in chart_data else ''}
            
            {'<div class="chart-section"><h2>🐌 Slowest Files</h2><img src="data:image/png;base64,' + chart_data.get('files', '') + '" alt="Slowest Files"></div>' if 'files' in chart_data else ''}
            
            <div class="chart-section">
                <h2>⚠️ Errors</h2>
                {'<div class="no-errors">✓ No errors detected!</div>' if not errors else ''}
                {'<img src="data:image/png;base64,' + chart_data.get('errors', '') + '" alt="Errors">' if errors and 'errors' in chart_data else ''}
                {f'''<div class="error-list">
                    <h3>Error Details ({len(errors)} total)</h3>
                    {''.join([f'<div class="error-item"><strong>Stage {e.get("stage")}</strong>: {e.get("type")} - {e.get("message", "")[:200]}...</div>' for e in errors[:5]])}
                    {'<p><em>... and ' + str(len(errors) - 5) + ' more errors</em></p>' if len(errors) > 5 else ''}
                </div>''' if errors else ''}
            </div>
        </div>
        
        <div class="footer">
            <p>Pipeline Instrumentation Report • Generated by visualize_pipeline_report.py</p>
            <p>Source: pipeline_report.json</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_file


def main():
    """Main entry point"""
    if not HAS_MATPLOTLIB:
        print("❌ matplotlib is required. Install with: pip install matplotlib")
        sys.exit(1)
    
    # Parse arguments
    report_file = sys.argv[1] if len(sys.argv) > 1 else 'reports/pipeline_report.json'
    
    if not Path(report_file).exists():
        print(f"❌ Error: Report file not found: {report_file}")
        print(f"💡 Tip: Run the pipeline first to generate the report")
        sys.exit(1)
    
    print("=" * 80)
    print("PIPELINE REPORT VISUALIZER")
    print("=" * 80)
    print()
    
    print(f"📊 Loading report: {report_file}")
    data = load_report(report_file)
    
    print("🎨 Generating visualizations...")
    print()
    
    chart_files = {}
    
    # Generate charts
    print("  📊 Creating overview dashboard...")
    chart_files['overview'] = create_overview_dashboard(data)
    
    print("  ⏱️  Creating stage duration chart...")
    chart_files['durations'] = create_stage_duration_chart(data)
    
    print("  ✅ Creating success rate chart...")
    chart_files['success'] = create_success_rate_chart(data)
    
    print("  💾 Creating memory usage chart...")
    chart_files['memory'] = create_memory_usage_chart(data)
    
    print("  🐌 Creating file processing chart...")
    chart_files['files'] = create_file_processing_chart(data)
    
    print("  ⚠️  Creating error chart...")
    chart_files['errors'] = create_error_chart(data)
    
    print()
    print("🌐 Generating HTML dashboard...")
    html_file = generate_html_dashboard(data, chart_files)
    
    print()
    print("=" * 80)
    print("✅ VISUALIZATION COMPLETE")
    print("=" * 80)
    print()
    print("Generated files:")
    for name, path in chart_files.items():
        if path:
            print(f"  • {path}")
    print(f"  • {html_file}")
    print()
    print(f"🌐 Open {html_file} in your browser to view the interactive dashboard!")
    print()


if __name__ == '__main__':
    main()

