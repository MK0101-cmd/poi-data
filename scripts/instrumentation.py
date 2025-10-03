"""
Pipeline Instrumentation Module
Tracks performance, progress, and metrics for stages 1-6
"""

import time
import psutil
import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
from collections import defaultdict


@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage"""
    stage_name: str
    stage_number: int
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    items_processed: int = 0
    items_failed: int = 0
    bytes_processed: int = 0
    memory_start_mb: float = 0.0
    memory_end_mb: float = 0.0
    memory_peak_mb: float = 0.0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['duration_formatted'] = self._format_duration(self.duration)
        d['success_rate'] = self._calculate_success_rate()
        return d
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 1:
            return f"{seconds*1000:.2f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.2f}h"
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage"""
        total = self.items_processed + self.items_failed
        if total == 0:
            return 0.0
        return (self.items_processed / total) * 100


@dataclass
class FileMetrics:
    """Metrics for individual file processing"""
    file_path: str
    file_size: int
    stage_1_time: float = 0.0  # Discovery
    stage_2_time: float = 0.0  # Extraction
    stage_3_time: float = 0.0  # Relationship mapping
    stage_4_time: float = 0.0  # Chunking
    stage_5_time: float = 0.0  # Tag generation
    stage_6_time: float = 0.0  # Embedding generation
    total_time: float = 0.0
    chunks_created: int = 0
    tags_generated: int = 0
    embeddings_created: int = 0
    relationships_found: int = 0
    success: bool = True
    error_message: Optional[str] = None


class PipelineInstrumentation:
    """
    Comprehensive instrumentation for pipeline stages 1-6
    Tracks timing, memory, progress, errors, and generates reports
    """
    
    def __init__(self, enable_file_tracking: bool = True):
        self.enable_file_tracking = enable_file_tracking
        
        # Stage metrics
        self.stage_metrics: Dict[int, StageMetrics] = {}
        
        # File-level metrics
        self.file_metrics: Dict[str, FileMetrics] = {}
        
        # Overall metrics
        self.pipeline_start_time: float = 0.0
        self.pipeline_end_time: float = 0.0
        self.total_files: int = 0
        self.processed_files: int = 0
        self.failed_files: int = 0
        
        # Performance tracking
        self.api_calls: Dict[str, List[float]] = defaultdict(list)
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        
        # Current state
        self.current_file: Optional[str] = None
        self.current_stage: Optional[int] = None
        
        # Process info
        self.process = psutil.Process(os.getpid())
        
    def start_pipeline(self):
        """Mark pipeline start"""
        self.pipeline_start_time = time.time()
        print("\n" + "="*70)
        print("🚀 PIPELINE INSTRUMENTATION STARTED")
        print("="*70)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Process ID: {os.getpid()}")
        print(f"Initial Memory: {self._get_memory_mb():.2f} MB")
        print("="*70 + "\n")
    
    def end_pipeline(self):
        """Mark pipeline end"""
        self.pipeline_end_time = time.time()
        duration = self.pipeline_end_time - self.pipeline_start_time
        
        print("\n" + "="*70)
        print("✅ PIPELINE INSTRUMENTATION COMPLETED")
        print("="*70)
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Duration: {self._format_duration(duration)}")
        print(f"Final Memory: {self._get_memory_mb():.2f} MB")
        print(f"Files Processed: {self.processed_files}/{self.total_files}")
        print(f"Success Rate: {self._get_success_rate():.2f}%")
        print("="*70 + "\n")
    
    def start_stage(self, stage_number: int, stage_name: str):
        """Start tracking a pipeline stage"""
        self.current_stage = stage_number
        
        if stage_number not in self.stage_metrics:
            self.stage_metrics[stage_number] = StageMetrics(
                stage_name=stage_name,
                stage_number=stage_number
            )
        
        metrics = self.stage_metrics[stage_number]
        metrics.start_time = time.time()
        metrics.memory_start_mb = self._get_memory_mb()
        
        print(f"\n{'─'*70}")
        print(f"📊 Stage {stage_number}: {stage_name}")
        print(f"{'─'*70}")
        print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Memory: {metrics.memory_start_mb:.2f} MB")
    
    def end_stage(self, stage_number: int):
        """End tracking a pipeline stage"""
        if stage_number not in self.stage_metrics:
            return
        
        metrics = self.stage_metrics[stage_number]
        metrics.end_time = time.time()
        metrics.duration = metrics.end_time - metrics.start_time
        metrics.memory_end_mb = self._get_memory_mb()
        metrics.memory_peak_mb = max(metrics.memory_start_mb, metrics.memory_end_mb)
        
        print(f"\n✓ Stage {stage_number} Complete")
        print(f"Duration: {self._format_duration(metrics.duration)}")
        print(f"Processed: {metrics.items_processed} items")
        if metrics.items_failed > 0:
            print(f"Failed: {metrics.items_failed} items")
        print(f"Memory Change: {metrics.memory_end_mb - metrics.memory_start_mb:+.2f} MB")
        print(f"{'─'*70}")
        
        self.current_stage = None
    
    def track_file_start(self, file_path: str, file_size: int):
        """Start tracking individual file processing"""
        if not self.enable_file_tracking:
            return
        
        self.current_file = file_path
        
        if file_path not in self.file_metrics:
            self.file_metrics[file_path] = FileMetrics(
                file_path=file_path,
                file_size=file_size
            )
    
    def track_file_end(self, file_path: str, success: bool = True, error: Optional[str] = None):
        """End tracking individual file processing"""
        if not self.enable_file_tracking or file_path not in self.file_metrics:
            return
        
        metrics = self.file_metrics[file_path]
        metrics.success = success
        metrics.error_message = error
        
        # Calculate total time
        metrics.total_time = sum([
            metrics.stage_1_time,
            metrics.stage_2_time,
            metrics.stage_3_time,
            metrics.stage_4_time,
            metrics.stage_5_time,
            metrics.stage_6_time
        ])
        
        if success:
            self.processed_files += 1
        else:
            self.failed_files += 1
        
        self.current_file = None
    
    def record_stage_time(self, stage_number: int, file_path: str, duration: float):
        """Record stage processing time for a file"""
        if not self.enable_file_tracking or file_path not in self.file_metrics:
            return
        
        metrics = self.file_metrics[file_path]
        
        if stage_number == 1:
            metrics.stage_1_time = duration
        elif stage_number == 2:
            metrics.stage_2_time = duration
        elif stage_number == 3:
            metrics.stage_3_time = duration
        elif stage_number == 4:
            metrics.stage_4_time = duration
        elif stage_number == 5:
            metrics.stage_5_time = duration
        elif stage_number == 6:
            metrics.stage_6_time = duration
    
    def increment_processed(self, stage_number: int, count: int = 1):
        """Increment processed items counter for a stage"""
        if stage_number in self.stage_metrics:
            self.stage_metrics[stage_number].items_processed += count
    
    def increment_failed(self, stage_number: int, count: int = 1):
        """Increment failed items counter for a stage"""
        if stage_number in self.stage_metrics:
            self.stage_metrics[stage_number].items_failed += count
    
    def add_bytes_processed(self, stage_number: int, bytes_count: int):
        """Add to bytes processed counter"""
        if stage_number in self.stage_metrics:
            self.stage_metrics[stage_number].bytes_processed += bytes_count
    
    def record_error(self, stage_number: int, error: Exception, context: Dict[str, Any] = None):
        """Record an error for a stage"""
        if stage_number not in self.stage_metrics:
            return
        
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        self.stage_metrics[stage_number].errors.append(error_info)
        print(f"\n⚠️  Error in Stage {stage_number}: {error_info['error_type']}: {error_info['error_message']}")
        
        if self.current_file:
            print(f"   File: {self.current_file}")
    
    def record_warning(self, stage_number: int, warning: str):
        """Record a warning for a stage"""
        if stage_number in self.stage_metrics:
            self.stage_metrics[stage_number].warnings.append(warning)
    
    def record_api_call(self, api_name: str, duration: float):
        """Record API call timing"""
        self.api_calls[api_name].append(duration)
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_misses += 1
    
    def update_file_metrics(self, file_path: str, **kwargs):
        """Update file metrics with custom values"""
        if file_path in self.file_metrics:
            for key, value in kwargs.items():
                if hasattr(self.file_metrics[file_path], key):
                    setattr(self.file_metrics[file_path], key, value)
    
    def print_progress(self, current: int, total: int, prefix: str = "Progress"):
        """Print progress bar"""
        bar_length = 50
        filled = int(bar_length * current / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        percent = 100 * current / total
        
        print(f"\r{prefix}: |{bar}| {current}/{total} ({percent:.1f}%)", end='', flush=True)
        
        if current == total:
            print()  # New line when complete
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive pipeline report"""
        total_duration = self.pipeline_end_time - self.pipeline_start_time
        
        report = {
            'summary': {
                'pipeline_duration': total_duration,
                'pipeline_duration_formatted': self._format_duration(total_duration),
                'start_time': datetime.fromtimestamp(self.pipeline_start_time).isoformat(),
                'end_time': datetime.fromtimestamp(self.pipeline_end_time).isoformat(),
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'failed_files': self.failed_files,
                'success_rate': self._get_success_rate(),
                'cache_hit_rate': self._get_cache_hit_rate()
            },
            'stages': {
                num: metrics.to_dict() 
                for num, metrics in sorted(self.stage_metrics.items())
            },
            'performance': self._generate_performance_metrics(),
            'errors': self._aggregate_errors(),
            'top_slowest_files': self._get_slowest_files(10),
            'stage_breakdown': self._get_stage_breakdown()
        }
        
        return report
    
    def print_report(self):
        """Print detailed text report"""
        print("\n" + "="*70)
        print("📊 PIPELINE INSTRUMENTATION REPORT")
        print("="*70)
        
        # Summary
        print("\n┌─ SUMMARY " + "─"*57 + "┐")
        report = self.generate_report()
        summary = report['summary']
        
        print(f"│ Total Duration    : {summary['pipeline_duration_formatted']:<53} │")
        print(f"│ Files Processed   : {summary['processed_files']}/{summary['total_files']:<49} │")
        print(f"│ Success Rate      : {summary['success_rate']:.2f}%{' '*48} │")
        print(f"│ Cache Hit Rate    : {summary['cache_hit_rate']:.2f}%{' '*48} │")
        print("└" + "─"*68 + "┘")
        
        # Stage breakdown
        print("\n┌─ STAGE BREAKDOWN " + "─"*50 + "┐")
        for stage_num, metrics in sorted(self.stage_metrics.items()):
            print(f"│ Stage {stage_num}: {metrics.stage_name:<54} │")
            print(f"│   Duration    : {self._format_duration(metrics.duration):<50} │")
            print(f"│   Processed   : {metrics.items_processed} items{' '*43} │")
            print(f"│   Success Rate: {metrics._calculate_success_rate():.2f}%{' '*48} │")
            if metrics.items_failed > 0:
                print(f"│   Failed      : {metrics.items_failed} items{' '*43} │")
            print(f"│   Memory Δ    : {metrics.memory_end_mb - metrics.memory_start_mb:+.2f} MB{' '*44} │")
            print("│" + "─"*68 + "│")
        print("└" + "─"*68 + "┘")
        
        # Performance
        print("\n┌─ PERFORMANCE METRICS " + "─"*46 + "┐")
        perf = report['performance']
        print(f"│ Avg File Time     : {perf['avg_file_time_formatted']:<50} │")
        print(f"│ Throughput        : {perf['files_per_second']:.2f} files/sec{' '*37} │")
        print(f"│ Avg Chunks/File   : {perf['avg_chunks_per_file']:.2f}{' '*47} │")
        if perf['api_stats']:
            print(f"│ OpenAI API Calls  : {perf['api_stats']['openai_embeddings']['count']} calls{' '*42} │")
            print(f"│ API Avg Time      : {perf['api_stats']['openai_embeddings']['avg_time_formatted']:<50} │")
            print(f"│ API Total Time    : {perf['api_stats']['openai_embeddings']['total_time_formatted']:<50} │")
        print("└" + "─"*68 + "┘")
        
        # Errors
        if report['errors']:
            print("\n┌─ ERRORS " + "─"*59 + "┐")
            for error in report['errors'][:5]:  # Show top 5
                print(f"│ Stage {error['stage']}: {error['type']:<55} │")
                print(f"│   {error['message'][:64]:<64} │")
            if len(report['errors']) > 5:
                print(f"│ ... and {len(report['errors']) - 5} more errors{' '*40} │")
            print("└" + "─"*68 + "┘")
        
        # Top slowest files
        if report['top_slowest_files']:
            print("\n┌─ TOP 10 SLOWEST FILES " + "─"*44 + "┐")
            for i, file_info in enumerate(report['top_slowest_files'][:10], 1):
                file_name = Path(file_info['file_path']).name
                print(f"│ {i:2}. {file_name[:45]:<45} {file_info['total_time_formatted']:>8} │")
            print("└" + "─"*68 + "┘")
        
        print("\n" + "="*70 + "\n")
    
    def save_report(self, output_path: str = "reports/pipeline_report.json"):
        """Save report to JSON file"""
        report = self.generate_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved to: {output_path}")
    
    def save_detailed_metrics(self, output_path: str = "reports/pipeline_metrics_detailed.json"):
        """Save detailed file-level metrics"""
        if not self.enable_file_tracking:
            print("⚠️  File tracking is disabled. No detailed metrics to save.")
            return
        
        detailed = {
            'file_metrics': [
                asdict(metrics) for metrics in self.file_metrics.values()
            ],
            'summary': self.generate_report()['summary']
        }
        
        with open(output_path, 'w') as f:
            json.dump(detailed, f, indent=2)
        
        print(f"📄 Detailed metrics saved to: {output_path}")
    
    # Helper methods
    
    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 1:
            return f"{seconds*1000:.2f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.2f}h"
    
    def _get_success_rate(self) -> float:
        """Calculate overall success rate"""
        total = self.processed_files + self.failed_files
        if total == 0:
            return 0.0
        return (self.processed_files / total) * 100
    
    def _get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100
    
    def _generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate performance metrics"""
        total_duration = self.pipeline_end_time - self.pipeline_start_time
        
        # File-level stats
        if self.file_metrics:
            file_times = [m.total_time for m in self.file_metrics.values() if m.success]
            avg_file_time = sum(file_times) / len(file_times) if file_times else 0
            
            chunks = [m.chunks_created for m in self.file_metrics.values() if m.success]
            avg_chunks = sum(chunks) / len(chunks) if chunks else 0
        else:
            avg_file_time = 0
            avg_chunks = 0
        
        # API stats
        api_stats = {}
        for api_name, times in self.api_calls.items():
            if times:
                api_stats[api_name] = {
                    'count': len(times),
                    'total_time': sum(times),
                    'total_time_formatted': self._format_duration(sum(times)),
                    'avg_time': sum(times) / len(times),
                    'avg_time_formatted': self._format_duration(sum(times) / len(times)),
                    'min_time': min(times),
                    'max_time': max(times)
                }
        
        return {
            'avg_file_time': avg_file_time,
            'avg_file_time_formatted': self._format_duration(avg_file_time),
            'files_per_second': self.processed_files / total_duration if total_duration > 0 else 0,
            'avg_chunks_per_file': avg_chunks,
            'api_stats': api_stats
        }
    
    def _aggregate_errors(self) -> List[Dict[str, Any]]:
        """Aggregate all errors across stages"""
        all_errors = []
        
        for stage_num, metrics in self.stage_metrics.items():
            for error in metrics.errors:
                all_errors.append({
                    'stage': stage_num,
                    'stage_name': metrics.stage_name,
                    'type': error['error_type'],
                    'message': error['error_message'],
                    'timestamp': error['timestamp'],
                    'context': error['context']
                })
        
        return sorted(all_errors, key=lambda x: x['timestamp'])
    
    def _get_slowest_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest files by processing time"""
        if not self.file_metrics:
            return []
        
        sorted_files = sorted(
            self.file_metrics.values(),
            key=lambda x: x.total_time,
            reverse=True
        )
        
        return [{
            'file_path': m.file_path,
            'total_time': m.total_time,
            'total_time_formatted': self._format_duration(m.total_time),
            'file_size': m.file_size,
            'chunks_created': m.chunks_created
        } for m in sorted_files[:limit]]
    
    def _get_stage_breakdown(self) -> Dict[str, Any]:
        """Get time breakdown by stage"""
        if not self.file_metrics:
            return {}
        
        stage_times = {
            'stage_1': [],
            'stage_2': [],
            'stage_3': [],
            'stage_4': [],
            'stage_5': [],
            'stage_6': []
        }
        
        for metrics in self.file_metrics.values():
            if metrics.success:
                stage_times['stage_1'].append(metrics.stage_1_time)
                stage_times['stage_2'].append(metrics.stage_2_time)
                stage_times['stage_3'].append(metrics.stage_3_time)
                stage_times['stage_4'].append(metrics.stage_4_time)
                stage_times['stage_5'].append(metrics.stage_5_time)
                stage_times['stage_6'].append(metrics.stage_6_time)
        
        breakdown = {}
        for stage, times in stage_times.items():
            if times:
                breakdown[stage] = {
                    'total': sum(times),
                    'total_formatted': self._format_duration(sum(times)),
                    'avg': sum(times) / len(times),
                    'avg_formatted': self._format_duration(sum(times) / len(times)),
                    'min': min(times),
                    'max': max(times),
                    'percentage': (sum(times) / sum([sum(t) for t in stage_times.values()])) * 100 if sum([sum(t) for t in stage_times.values()]) > 0 else 0
                }
        
        return breakdown


# Decorator for timing functions
def timed_stage(stage_number: int):
    """Decorator to automatically track stage timing"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'instrumentation'):
                inst = self.instrumentation
                
                # Record start
                file_path = kwargs.get('file_path') or (args[0] if args else None)
                start_time = time.time()
                
                try:
                    result = func(self, *args, **kwargs)
                    
                    # Record success
                    duration = time.time() - start_time
                    if file_path and isinstance(file_path, str):
                        inst.record_stage_time(stage_number, file_path, duration)
                    inst.increment_processed(stage_number)
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    duration = time.time() - start_time
                    inst.increment_failed(stage_number)
                    inst.record_error(stage_number, e, {'file_path': file_path})
                    raise
            else:
                return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test instrumentation
    import random
    
    inst = PipelineInstrumentation(enable_file_tracking=True)
    inst.start_pipeline()
    inst.total_files = 10
    
    # Simulate pipeline
    for stage in range(1, 7):
        stage_names = [
            "File Discovery",
            "Content Extraction",
            "Relationship Mapping",
            "Content Chunking",
            "Tag Generation",
            "Embedding Generation"
        ]
        
        inst.start_stage(stage, stage_names[stage-1])
        
        # Simulate processing
        for i in range(10):
            file_path = f"test_file_{i}.md"
            inst.track_file_start(file_path, 1024 * (i+1))
            
            time.sleep(random.uniform(0.01, 0.05))
            inst.record_stage_time(stage, file_path, random.uniform(0.01, 0.05))
            
            if stage == 6:  # Embedding stage
                inst.record_api_call('openai_embeddings', random.uniform(0.1, 0.3))
            
            inst.track_file_end(file_path, success=True)
            inst.print_progress(i+1, 10, f"Stage {stage}")
        
        inst.end_stage(stage)
    
    inst.end_pipeline()
    inst.print_report()
    inst.save_report("test_report.json")
    inst.save_detailed_metrics("test_metrics.json")

