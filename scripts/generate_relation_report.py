#!/usr/bin/env python3
"""
Relationship Mapping Report Generator
======================================
Analyzes pipeline_metrics_detailed.json to generate a comprehensive
relationship mapping report for the Points of You RAG system.

Usage:
    python generate_relation_report.py [input_file] [output_file]

Arguments:
    input_file  - Path to pipeline metrics JSON (default: pipeline_metrics_detailed.json)
    output_file - Path to save report (default: RELATIONSHIP_MAPPING_REPORT.md)

Example:
    python generate_relation_report.py
    python generate_relation_report.py custom_metrics.json custom_report.md
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def load_metrics(filepath):
    """Load the pipeline metrics JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {filepath}: {e}")
        sys.exit(1)


def analyze_relationships(data):
    """Analyze relationship data from pipeline metrics"""
    
    # Overall statistics
    total_files = len(data['file_metrics'])
    files_with_relationships = [f for f in data['file_metrics'] if f.get('relationships_found', 0) > 0]
    total_relationships = sum(f.get('relationships_found', 0) for f in data['file_metrics'])
    
    # Category breakdown
    category_stats = defaultdict(lambda: {
        'files': 0, 'relationships': 0, 'chunks': 0, 'tags': 0, 'embeddings': 0
    })
    subcategory_stats = defaultdict(lambda: {
        'files': 0, 'relationships': 0, 'chunks': 0, 'tags': 0, 'embeddings': 0
    })
    
    # File type breakdown
    success_count = sum(1 for f in data['file_metrics'] if f.get('success', False))
    failed_count = sum(1 for f in data['file_metrics'] if not f.get('success', False))
    
    # Total metrics
    total_chunks = sum(f.get('chunks_created', 0) for f in data['file_metrics'])
    total_tags = sum(f.get('tags_generated', 0) for f in data['file_metrics'])
    total_embeddings = sum(f.get('embeddings_created', 0) for f in data['file_metrics'])
    
    # Detailed file analysis
    for file_metric in data['file_metrics']:
        path = file_metric['file_path']
        parts = path.replace('/', '\\').split('\\')
        
        if len(parts) >= 3:
            category = parts[1]  # e.g., "Activities" or "Trainings"
            subcategory = parts[2]  # e.g., "CANVASES", "FACES", "AI", "BTC24"
            
            category_stats[category]['files'] += 1
            category_stats[category]['relationships'] += file_metric.get('relationships_found', 0)
            category_stats[category]['chunks'] += file_metric.get('chunks_created', 0)
            category_stats[category]['tags'] += file_metric.get('tags_generated', 0)
            category_stats[category]['embeddings'] += file_metric.get('embeddings_created', 0)
            
            subcategory_stats[subcategory]['files'] += 1
            subcategory_stats[subcategory]['relationships'] += file_metric.get('relationships_found', 0)
            subcategory_stats[subcategory]['chunks'] += file_metric.get('chunks_created', 0)
            subcategory_stats[subcategory]['tags'] += file_metric.get('tags_generated', 0)
            subcategory_stats[subcategory]['embeddings'] += file_metric.get('embeddings_created', 0)
    
    return {
        'total_files': total_files,
        'files_with_relationships': len(files_with_relationships),
        'total_relationships': total_relationships,
        'success_count': success_count,
        'failed_count': failed_count,
        'total_chunks': total_chunks,
        'total_tags': total_tags,
        'total_embeddings': total_embeddings,
        'category_stats': dict(category_stats),
        'subcategory_stats': dict(subcategory_stats),
        'relationship_files': files_with_relationships
    }


def generate_report(metrics_file, output_file):
    """Generate the relationship mapping report"""
    
    print(f"📊 Loading pipeline metrics from: {metrics_file}")
    data = load_metrics(metrics_file)
    
    print("🔍 Analyzing relationships...")
    analysis = analyze_relationships(data)
    
    # Generate report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("RELATIONSHIP MAPPING REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Source: {metrics_file}")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("EXECUTIVE SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append(f"Total Files Analyzed:          {analysis['total_files']:,}")
    report_lines.append(f"Files Successfully Processed:  {analysis['success_count']:,} ({analysis['success_count']/analysis['total_files']*100:.1f}%)")
    report_lines.append(f"Files Failed:                  {analysis['failed_count']:,} ({analysis['failed_count']/analysis['total_files']*100:.1f}%)")
    report_lines.append(f"Files with Relationships:      {analysis['files_with_relationships']:,}")
    report_lines.append(f"Total Relationships Found:     {analysis['total_relationships']:,}")
    report_lines.append(f"Total Chunks Created:          {analysis['total_chunks']:,}")
    report_lines.append(f"Total Tags Generated:          {analysis['total_tags']:,}")
    report_lines.append(f"Total Embeddings Created:      {analysis['total_embeddings']:,}")
    report_lines.append("")
    
    # Pipeline Summary
    summary = data.get('summary', {})
    report_lines.append("PIPELINE EXECUTION")
    report_lines.append("-" * 80)
    report_lines.append(f"Start Time:     {summary.get('start_time', 'N/A')}")
    report_lines.append(f"End Time:       {summary.get('end_time', 'N/A')}")
    report_lines.append(f"Duration:       {summary.get('pipeline_duration_formatted', 'N/A')}")
    report_lines.append(f"Success Rate:   {summary.get('success_rate', 0):.1f}%")
    report_lines.append(f"Cache Hit Rate: {summary.get('cache_hit_rate', 0):.1f}%")
    report_lines.append("")
    
    # Category Breakdown
    report_lines.append("CATEGORY BREAKDOWN")
    report_lines.append("-" * 80)
    report_lines.append(f"{'Category':<15} {'Files':<8} {'Chunks':<8} {'Tags':<8} {'Embed':<8} {'Relations':<10}")
    report_lines.append("-" * 80)
    
    for category, stats in sorted(analysis['category_stats'].items()):
        report_lines.append(
            f"{category:<15} {stats['files']:<8} {stats['chunks']:<8} "
            f"{stats['tags']:<8} {stats['embeddings']:<8} {stats['relationships']:<10}"
        )
    report_lines.append("")
    
    # Subcategory Breakdown (Top 15)
    report_lines.append("SUBCATEGORY BREAKDOWN (Top 15)")
    report_lines.append("-" * 80)
    report_lines.append(f"{'Subcategory':<15} {'Files':<8} {'Chunks':<8} {'Tags':<8} {'Embed':<8} {'Relations':<10}")
    report_lines.append("-" * 80)
    
    sorted_subcats = sorted(analysis['subcategory_stats'].items(), 
                           key=lambda x: x[1]['files'], reverse=True)
    
    for subcategory, stats in sorted_subcats[:15]:
        report_lines.append(
            f"{subcategory:<15} {stats['files']:<8} {stats['chunks']:<8} "
            f"{stats['tags']:<8} {stats['embeddings']:<8} {stats['relationships']:<10}"
        )
    
    if len(sorted_subcats) > 15:
        report_lines.append(f"... and {len(sorted_subcats) - 15} more subcategories")
    report_lines.append("")
    
    # Relationship Analysis
    report_lines.append("RELATIONSHIP ANALYSIS")
    report_lines.append("-" * 80)
    
    if analysis['files_with_relationships'] == 0:
        report_lines.append("⚠️  WARNING: No relationships were found in any files.")
        report_lines.append("")
        report_lines.append("POTENTIAL CAUSES:")
        report_lines.append("  1. Files may not contain markdown-style links [text](path)")
        report_lines.append("  2. Relationship extraction stage may not have run properly")
        report_lines.append("  3. Content may use different linking conventions")
        report_lines.append("  4. Files may be standalone without cross-references")
        report_lines.append("")
        report_lines.append("RECOMMENDATIONS:")
        report_lines.append("  • Review Stage 3 (Relationship Mapping) execution logs")
        report_lines.append("  • Check if files contain markdown links or other reference patterns")
        report_lines.append("  • Consider implementing additional relationship detection methods")
        report_lines.append("  • Verify that relationship extraction regex patterns are correct")
    else:
        report_lines.append(f"✓ Found {analysis['files_with_relationships']} files with relationships")
        report_lines.append(f"✓ Total relationships detected: {analysis['total_relationships']}")
        report_lines.append("")
        report_lines.append("TOP FILES WITH MOST RELATIONSHIPS:")
        report_lines.append("")
        
        # Sort by relationship count
        sorted_rel_files = sorted(analysis['relationship_files'], 
                                 key=lambda x: x.get('relationships_found', 0), 
                                 reverse=True)
        
        for file_info in sorted_rel_files[:25]:  # Top 25
            path = file_info['file_path']
            rel_count = file_info.get('relationships_found', 0)
            file_size = file_info.get('file_size', 0)
            report_lines.append(f"  • {path}")
            report_lines.append(f"    Relationships: {rel_count} | Size: {file_size:,} bytes")
        
        if len(sorted_rel_files) > 25:
            report_lines.append("")
            report_lines.append(f"  ... and {len(sorted_rel_files) - 25} more files")
    
    report_lines.append("")
    
    # Error Analysis
    report_lines.append("ERROR ANALYSIS")
    report_lines.append("-" * 80)
    
    error_types = defaultdict(int)
    error_messages = defaultdict(list)
    
    for file_metric in data['file_metrics']:
        if not file_metric.get('success', False):
            error_msg = file_metric.get('error_message', 'Unknown error')
            # Extract error type
            if 'api_key' in error_msg.lower():
                error_type = "Missing API Key"
            elif 'openai' in error_msg.lower():
                error_type = "OpenAI Error"
            else:
                error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg[:50]
            
            error_types[error_type] += 1
            if len(error_messages[error_type]) < 3:
                error_messages[error_type].append(file_metric['file_path'])
    
    if error_types:
        report_lines.append(f"❌ Total Errors: {sum(error_types.values())}")
        report_lines.append("")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  {error_type}: {count} occurrences")
            for example_file in error_messages[error_type][:2]:
                report_lines.append(f"    - {example_file}")
            report_lines.append("")
    else:
        report_lines.append("✓ No errors detected")
        report_lines.append("")
    
    # Database Schema Mapping
    report_lines.append("DATABASE SCHEMA MAPPING")
    report_lines.append("-" * 80)
    report_lines.append("The relationship data maps to the following database structure:")
    report_lines.append("")
    report_lines.append("Table: cross_references")
    report_lines.append("  • source_document_id  : UUID of source document")
    report_lines.append("  • target_document_id  : UUID of target document")
    report_lines.append("  • reference_type      : 'markdown_link', 'related', 'parent-child', etc.")
    report_lines.append("  • relationship_strength: 0.0 to 1.0 (confidence score)")
    report_lines.append("  • context             : Description or link text")
    report_lines.append("")
    report_lines.append("Relationship Types:")
    report_lines.append("  • markdown_link : Direct markdown hyperlinks [text](path)")
    report_lines.append("  • parent-child  : Hierarchical folder relationships")
    report_lines.append("  • cross-series  : References across different card series")
    report_lines.append("  • example       : Activity references to card examples")
    report_lines.append("  • semantic      : Similarity based on embeddings")
    report_lines.append("")
    
    # Recommendations
    report_lines.append("RECOMMENDATIONS")
    report_lines.append("-" * 80)
    
    if analysis['total_embeddings'] == 0:
        report_lines.append("🔴 CRITICAL: No embeddings generated")
        report_lines.append("   • Set OPENAI_API_KEY environment variable")
        report_lines.append("   • Re-run pipeline to generate embeddings")
        report_lines.append("")
    
    if analysis['total_relationships'] == 0:
        report_lines.append("🟡 ENHANCE RELATIONSHIP DETECTION")
        report_lines.append("   • Add detection for implicit relationships (folder structure, naming)")
        report_lines.append("   • Detect card references (e.g., 'FACES-001', 'FLOW-042')")
        report_lines.append("   • Parse canvas building block connections")
        report_lines.append("   • Review Canvas_Card_Mapping.md for explicit relationships")
        report_lines.append("")
    
    report_lines.append("🟢 IMPLEMENT SEMANTIC SIMILARITY")
    report_lines.append("   • Once embeddings exist, compute cosine similarity between documents")
    report_lines.append("   • Automatically discover related content based on meaning")
    report_lines.append("   • Create relationship_strength scores based on embedding distance")
    report_lines.append("")
    
    report_lines.append("🟢 MANUAL RELATIONSHIP ENRICHMENT")
    report_lines.append("   • Map activities to their associated card collections")
    report_lines.append("   • Link training materials to practical activities")
    report_lines.append("   • Connect journey narratives to specific card stories")
    report_lines.append("")
    
    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)
    
    # Write report
    report_text = '\n'.join(report_lines)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"✅ Report generated: {output_file}")
    print(f"📄 Lines: {len(report_lines)}")
    print(f"📦 Size: {len(report_text):,} bytes")
    
    return analysis


def main():
    """Main entry point"""
    # Parse command line arguments
    if len(sys.argv) > 3:
        print("Usage: python generate_relation_report.py [input_file] [output_file]")
        sys.exit(1)
    
    metrics_file = sys.argv[1] if len(sys.argv) > 1 else 'reports/pipeline_metrics_detailed.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'RELATIONSHIP_MAPPING_REPORT.md'
    
    # Check if input file exists
    if not Path(metrics_file).exists():
        print(f"❌ Error: Input file not found: {metrics_file}")
        print(f"💡 Tip: Make sure the pipeline has been run to generate metrics")
        sys.exit(1)
    
    # Generate report
    print("=" * 80)
    print("RELATIONSHIP MAPPING REPORT GENERATOR")
    print("=" * 80)
    print()
    
    analysis = generate_report(metrics_file, output_file)
    
    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files Analyzed:    {analysis['total_files']:,}")
    print(f"Relationships:     {analysis['total_relationships']:,}")
    print(f"Chunks Created:    {analysis['total_chunks']:,}")
    print(f"Tags Generated:    {analysis['total_tags']:,}")
    print(f"Embeddings:        {analysis['total_embeddings']:,}")
    print(f"Success Rate:      {analysis['success_count']/analysis['total_files']*100:.1f}%")
    print("=" * 80)
    print()
    print(f"✨ Report saved to: {output_file}")


if __name__ == '__main__':
    main()

