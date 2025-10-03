"""
Visualization and Analysis Tool for Pipeline Metrics
Generates charts and analysis from instrumentation reports
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime


class MetricsVisualizer:
    """Visualize pipeline metrics from instrumentation reports"""
    
    def __init__(self, report_path: str = "reports/pipeline_report.json"):
        self.report_path = report_path
        self.report = self._load_report()
    
    def _load_report(self) -> Dict[str, Any]:
        """Load report from JSON file"""
        try:
            with open(self.report_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Report file not found: {self.report_path}")
            print("Run the instrumented pipeline first to generate the report.")
            sys.exit(1)
    
    def print_summary(self):
        """Print text summary of metrics"""
        summary = self.report['summary']
        
        print("\n" + "="*70)
        print("📊 PIPELINE METRICS SUMMARY")
        print("="*70)
        print(f"\n⏱️  Duration: {summary['pipeline_duration_formatted']}")
        print(f"📁 Files: {summary['processed_files']}/{summary['total_files']} processed")
        print(f"✓  Success Rate: {summary['success_rate']:.2f}%")
        print(f"💾 Cache Hit Rate: {summary['cache_hit_rate']:.2f}%")
        
        print("\n" + "-"*70)
        print("STAGE BREAKDOWN")
        print("-"*70)
        
        for stage_num, stage in sorted(self.report['stages'].items(), key=lambda x: int(x[0])):
            print(f"\n{stage['stage_name']} (Stage {stage_num})")
            print(f"  Duration: {stage['duration_formatted']}")
            print(f"  Items: {stage['items_processed']} processed, {stage['items_failed']} failed")
            print(f"  Success: {stage['success_rate']:.2f}%")
            print(f"  Memory: {stage['memory_end_mb'] - stage['memory_start_mb']:+.2f} MB")
        
        if self.report.get('performance'):
            perf = self.report['performance']
            print("\n" + "-"*70)
            print("PERFORMANCE")
            print("-"*70)
            print(f"  Avg File Time: {perf['avg_file_time_formatted']}")
            print(f"  Throughput: {perf['files_per_second']:.2f} files/sec")
            print(f"  Avg Chunks/File: {perf['avg_chunks_per_file']:.2f}")
            
            if perf.get('api_stats'):
                for api, stats in perf['api_stats'].items():
                    print(f"\n  {api}:")
                    print(f"    Calls: {stats['count']}")
                    print(f"    Total Time: {stats['total_time_formatted']}")
                    print(f"    Avg Time: {stats['avg_time_formatted']}")
        
        print("\n" + "="*70 + "\n")
    
    def plot_stage_duration(self, save_path: str = "stage_duration.png"):
        """Plot bar chart of stage durations"""
        stages = self.report['stages']
        
        stage_names = [s['stage_name'] for s in sorted(stages.values(), key=lambda x: x['stage_number'])]
        durations = [s['duration'] for s in sorted(stages.values(), key=lambda x: x['stage_number'])]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(range(len(stage_names)), durations, color='steelblue')
        
        # Color the bars
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        for i, bar in enumerate(bars):
            bar.set_color(colors[i % len(colors)])
        
        ax.set_xlabel('Pipeline Stage', fontsize=12, fontweight='bold')
        ax.set_ylabel('Duration (seconds)', fontsize=12, fontweight='bold')
        ax.set_title('Pipeline Stage Duration', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(stage_names)))
        ax.set_xticklabels(stage_names, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, duration) in enumerate(zip(bars, durations)):
            height = bar.get_height()
            label = f"{duration:.2f}s"
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   label, ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Saved: {save_path}")
        plt.close()
    
    def plot_stage_breakdown_pie(self, save_path: str = "stage_breakdown.png"):
        """Plot pie chart of time spent in each stage"""
        breakdown = self.report.get('stage_breakdown', {})
        
        if not breakdown:
            print("⚠️  No stage breakdown data available")
            return
        
        labels = [f"Stage {s[-1]}" for s in breakdown.keys()]
        percentages = [b['percentage'] for b in breakdown.values()]
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(
            percentages, 
            labels=labels, 
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )
        
        # Enhance text
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        ax.set_title('Time Distribution Across Stages', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Saved: {save_path}")
        plt.close()
    
    def plot_memory_usage(self, save_path: str = "memory_usage.png"):
        """Plot memory usage across stages"""
        stages = self.report['stages']
        
        stage_names = [s['stage_name'] for s in sorted(stages.values(), key=lambda x: x['stage_number'])]
        memory_start = [s['memory_start_mb'] for s in sorted(stages.values(), key=lambda x: x['stage_number'])]
        memory_end = [s['memory_end_mb'] for s in sorted(stages.values(), key=lambda x: x['stage_number'])]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(stage_names))
        ax.plot(x, memory_start, marker='o', label='Start', linewidth=2, color='steelblue')
        ax.plot(x, memory_end, marker='s', label='End', linewidth=2, color='coral')
        
        ax.set_xlabel('Pipeline Stage', fontsize=12, fontweight='bold')
        ax.set_ylabel('Memory Usage (MB)', fontsize=12, fontweight='bold')
        ax.set_title('Memory Usage Across Pipeline Stages', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(stage_names, rotation=45, ha='right')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Saved: {save_path}")
        plt.close()
    
    def plot_success_rate(self, save_path: str = "success_rate.png"):
        """Plot success rate by stage"""
        stages = self.report['stages']
        
        stage_names = [f"Stage {s['stage_number']}" for s in sorted(stages.values(), key=lambda x: x['stage_number'])]
        success_rates = [s['success_rate'] for s in sorted(stages.values(), key=lambda x: x['stage_number'])]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(range(len(stage_names)), success_rates, color='green', alpha=0.7)
        
        ax.set_xlabel('Success Rate (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Pipeline Stage', fontsize=12, fontweight='bold')
        ax.set_title('Success Rate by Stage', fontsize=14, fontweight='bold')
        ax.set_yticks(range(len(stage_names)))
        ax.set_yticklabels(stage_names)
        ax.set_xlim([0, 105])
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (bar, rate) in enumerate(zip(bars, success_rates)):
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2.,
                   f'{rate:.1f}%', ha='left', va='center', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Saved: {save_path}")
        plt.close()
    
    def plot_file_processing_time(self, detailed_metrics_path: str = "reports/pipeline_metrics_detailed.json", 
                                   save_path: str = "file_times.png", top_n: int = 20):
        """Plot processing time distribution for files"""
        try:
            with open(detailed_metrics_path, 'r') as f:
                detailed = json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Detailed metrics file not found: {detailed_metrics_path}")
            return
        
        file_metrics = detailed.get('file_metrics', [])
        
        if not file_metrics:
            print("⚠️  No file metrics available")
            return
        
        # Sort by total time
        sorted_files = sorted(file_metrics, key=lambda x: x['total_time'], reverse=True)[:top_n]
        
        file_names = [Path(f['file_path']).name[:30] for f in sorted_files]
        times = [f['total_time'] for f in sorted_files]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(range(len(file_names)), times, color='coral')
        
        ax.set_xlabel('Processing Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('File', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {top_n} Slowest Files', fontsize=14, fontweight='bold')
        ax.set_yticks(range(len(file_names)))
        ax.set_yticklabels(file_names, fontsize=8)
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Saved: {save_path}")
        plt.close()
    
    def plot_api_timing(self, save_path: str = "api_timing.png"):
        """Plot API call timing statistics"""
        perf = self.report.get('performance', {})
        api_stats = perf.get('api_stats', {})
        
        if not api_stats:
            print("⚠️  No API statistics available")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        for api_name, stats in api_stats.items():
            # Call count
            ax1.bar(api_name, stats['count'], color='steelblue')
            ax1.set_ylabel('Number of Calls', fontsize=12, fontweight='bold')
            ax1.set_title('API Call Count', fontsize=12, fontweight='bold')
            ax1.grid(axis='y', alpha=0.3)
            
            # Timing
            categories = ['Min', 'Avg', 'Max']
            times = [stats['min_time'], stats['avg_time'], stats['max_time']]
            
            ax2.bar(categories, times, color=['green', 'orange', 'red'])
            ax2.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
            ax2.set_title(f'{api_name} - Call Duration', fontsize=12, fontweight='bold')
            ax2.grid(axis='y', alpha=0.3)
            
            # Add value labels
            for i, (cat, time) in enumerate(zip(categories, times)):
                ax2.text(i, time, f'{time:.3f}s', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Saved: {save_path}")
        plt.close()
    
    def generate_all_visualizations(self, output_dir: str = "visualizations"):
        """Generate all available visualizations"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\n📊 Generating visualizations in {output_dir}/\n")
        
        self.plot_stage_duration(str(output_path / "stage_duration.png"))
        self.plot_stage_breakdown_pie(str(output_path / "stage_breakdown.png"))
        self.plot_memory_usage(str(output_path / "reports" / "memory_usage.png"))
        self.plot_success_rate(str(output_path / "success_rate.png"))
        self.plot_file_processing_time(save_path=str(output_path / "file_times.png"))
        self.plot_api_timing(str(output_path / "api_timing.png"))
        
        print(f"\n✅ All visualizations saved to {output_dir}/\n")
    
    def generate_html_report(self, output_path: str = "pipeline_report.html"):
        """Generate HTML report with visualizations"""
        # Generate visualizations first
        viz_dir = "visualizations"
        self.generate_all_visualizations(viz_dir)
        
        summary = self.report['summary']
        stages = self.report['stages']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Pipeline Instrumentation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            margin-top: 0;
            color: #667eea;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .visualization {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .visualization img {{
            max-width: 100%;
            height: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Pipeline Instrumentation Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="metric-card">
            <h3>⏱️ Total Duration</h3>
            <div class="metric-value">{summary['pipeline_duration_formatted']}</div>
        </div>
        <div class="metric-card">
            <h3>📁 Files Processed</h3>
            <div class="metric-value">{summary['processed_files']}/{summary['total_files']}</div>
        </div>
        <div class="metric-card">
            <h3>✅ Success Rate</h3>
            <div class="metric-value">{summary['success_rate']:.1f}%</div>
        </div>
        <div class="metric-card">
            <h3>💾 Cache Hit Rate</h3>
            <div class="metric-value">{summary['cache_hit_rate']:.1f}%</div>
        </div>
    </div>
    
    <div class="visualization">
        <h2>Stage Duration</h2>
        <img src="{viz_dir}/stage_duration.png" alt="Stage Duration">
    </div>
    
    <div class="visualization">
        <h2>Time Distribution</h2>
        <img src="{viz_dir}/stage_breakdown.png" alt="Stage Breakdown">
    </div>
    
    <div class="visualization">
        <h2>Memory Usage</h2>
        <img src="{viz_dir}/reports/memory_usage.png" alt="Memory Usage">
    </div>
    
    <div class="visualization">
        <h2>Success Rate by Stage</h2>
        <img src="{viz_dir}/success_rate.png" alt="Success Rate">
    </div>
    
    <div class="visualization">
        <h2>Slowest Files</h2>
        <img src="{viz_dir}/file_times.png" alt="File Processing Times">
    </div>
    
    <div class="visualization">
        <h2>API Call Statistics</h2>
        <img src="{viz_dir}/api_timing.png" alt="API Timing">
    </div>
    
    <div class="visualization">
        <h2>Detailed Stage Metrics</h2>
        <table>
            <tr>
                <th>Stage</th>
                <th>Duration</th>
                <th>Items Processed</th>
                <th>Success Rate</th>
                <th>Memory Change</th>
            </tr>
"""
        
        for stage_num, stage in sorted(stages.items(), key=lambda x: int(x[0])):
            html += f"""
            <tr>
                <td>{stage['stage_name']}</td>
                <td>{stage['duration_formatted']}</td>
                <td>{stage['items_processed']}</td>
                <td>{stage['success_rate']:.1f}%</td>
                <td>{stage['memory_end_mb'] - stage['memory_start_mb']:+.2f} MB</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"📄 HTML report saved to: {output_path}")
        print(f"   Open in browser: file://{Path(output_path).absolute()}")


if __name__ == "__main__":
    """
    Usage:
        python visualize_metrics.py                          # Print summary
        python visualize_metrics.py --visualize              # Generate all visualizations
        python visualize_metrics.py --html                   # Generate HTML report
        python visualize_metrics.py --report reports/pipeline_report.json  # Use specific report file
    """
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize pipeline metrics')
    parser.add_argument('--report', default='reports/pipeline_report.json', help='Path to report JSON file')
    parser.add_argument('--visualize', action='store_true', help='Generate all visualizations')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--output-dir', default='visualizations', help='Output directory for visualizations')
    
    args = parser.parse_args()
    
    # Check if matplotlib is available
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
    except ImportError:
        print("⚠️  matplotlib not installed. Install with: pip install matplotlib")
        print("    Text summary will be shown instead.")
        args.visualize = False
        args.html = False
    
    visualizer = MetricsVisualizer(args.report)
    
    # Always print summary
    visualizer.print_summary()
    
    if args.visualize:
        visualizer.generate_all_visualizations(args.output_dir)
    
    if args.html:
        visualizer.generate_html_report()

