#!/usr/bin/env python3
"""
Watch Script - Pipeline Results Ranking
=======================================

This script scans through all output directories, finds all summary.json files,
and creates a ranking table based on evaluation results.

Features:
- Scans all <dataset>/<prompt>/<model>/<timestamp>/ directories
- Extracts average_position and final_score_percentage from summary.json
- Creates a ranking table with emojis for easy visual identification
- Saves results to ranking.txt in the same directory
"""

import json
import os
import glob
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Emoji mappings for visual identification
DATASET_EMOJIS = {
    'all_5': '🧪',
    'all_450': '💫',
}

PROMPT_EMOJIS = {
    'dxgpt_dev': '🔬',
    'dxgpt_dev_v2': '🧠',
    'juanjo_classic': '👌'
}

MODEL_EMOJIS = {
    'gpt_4o_summary': '🟡',
    'o3_images': '🔴',
}

def get_emoji(category: str, name: str) -> str:
    """Get emoji for a specific category and name"""
    emoji_maps = {
        'dataset': DATASET_EMOJIS,
        'prompt': PROMPT_EMOJIS,
        'model': MODEL_EMOJIS
    }
    
    emoji_map = emoji_maps.get(category, {})
    
    # Try exact match first
    if name in emoji_map:
        return emoji_map[name]
    
    # Try partial match
    for key, emoji in emoji_map.items():
        if key in name or name in key:
            return emoji
    
    # Default emojis
    defaults = {
        'dataset': '📋',
        'prompt': '📝',
        'model': '🤖'
    }
    return defaults.get(category, '❓')

def extract_experiment_info(summary_data: Dict) -> Tuple[str, str, str, str]:
    """Extract dataset, prompt, model, and timestamp from summary data"""
    config = summary_data.get('configuration', {})
    
    # Extract dataset name from dataset_path
    dataset_path = config.get('dataset_path', 'unknown')
    dataset_name = os.path.splitext(os.path.basename(dataset_path))[0] if dataset_path else 'unknown'
    
    # Extract timestamp
    timestamp = config.get('timestamp', 'unknown')
    
    # For prompt and model, we need to infer from the path structure
    # This will be filled by the calling function
    return dataset_name, 'unknown', 'unknown', timestamp

def scan_for_summaries(output_dir: str) -> List[Dict]:
    """
    Scan output directory for all summary.json files
    
    Args:
        output_dir: Path to output directory
        
    Returns:
        List of experiment results with rankings
    """
    results = []
    
    # Pattern to find all summary.json files
    pattern = os.path.join(output_dir, '**', 'summary.json')
    summary_files = glob.glob(pattern, recursive=True)
    
    print(f"🔍 Found {len(summary_files)} summary.json files")
    
    for summary_file in summary_files:
        try:
            # Parse the directory structure to extract components
            # Expected path: output/<dataset>/<prompt>/<model>/<timestamp>/summary.json
            path_parts = summary_file.replace(output_dir, '').strip(os.sep).split(os.sep)
            
            if len(path_parts) >= 4:
                dataset_name = path_parts[0]
                prompt_name = path_parts[1]
                model_name = path_parts[2]
                timestamp = path_parts[3]
            else:
                print(f"⚠️  Skipping file with unexpected path structure: {summary_file}")
                continue
            
            # Load summary data
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            
            # Extract key metrics
            global_stats = summary_data.get('global', {})
            average_position = global_stats.get('average_position', 99.0)
            final_score_percentage = global_stats.get('final_score_percentage', 0.0)
            total_cases = global_stats.get('total_cases', 0)
            matched_cases = global_stats.get('matched_cases', 0)
            
            # Get emojis
            dataset_emoji = get_emoji('dataset', dataset_name)
            prompt_emoji = get_emoji('prompt', prompt_name)
            model_emoji = get_emoji('model', model_name)
            
            # Create experiment identifier
            experiment_id = f"{dataset_name}-{prompt_name}-{model_name}"
            
            # Create result entry
            result = {
                'experiment_id': experiment_id,
                'dataset_name': dataset_name,
                'prompt_name': prompt_name,
                'model_name': model_name,
                'timestamp': timestamp,
                'average_position': average_position,
                'final_score_percentage': final_score_percentage,
                'total_cases': total_cases,
                'matched_cases': matched_cases,
                'dataset_emoji': dataset_emoji,
                'prompt_emoji': prompt_emoji,
                'model_emoji': model_emoji,
                'summary_file': summary_file
            }
            
            results.append(result)
            
        except Exception as e:
            print(f"⚠️  Error processing {summary_file}: {str(e)}")
            continue
    
    return results

def create_ranking_table(results: List[Dict]) -> str:
    """Create a formatted ranking table"""
    if not results:
        return "No results found."
    
    # Filter out incomplete runs (0 matched cases might indicate incomplete evaluation)
    complete_results = [r for r in results if r['matched_cases'] > 0 or r['total_cases'] == 0]
    incomplete_results = [r for r in results if r['matched_cases'] == 0 and r['total_cases'] > 0]
    
    # Sort by average_position (lower is better), then by final_score_percentage (higher is better)
    sorted_results = sorted(complete_results, key=lambda x: (x['average_position'], -x['final_score_percentage']))
    
    # Create table header
    table_lines = []
    table_lines.append("🏆 PIPELINE RESULTS RANKING")
    table_lines.append("=" * 80)
    table_lines.append("")
    table_lines.append("Legend:")
    table_lines.append("🏆 Rank | 📊 Dataset | 📝 Prompt | 🤖 Model | 🎯 Score | 📈 Success%")
    table_lines.append("Average Position = Lower is Better | Success Rate = Higher is Better")
    table_lines.append("")
    table_lines.append("-" * 80)
    
    # Create table rows
    for i, result in enumerate(sorted_results, 1):
        rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}"
        
        # Format the experiment name with emojis
        experiment_display = f"{result['dataset_emoji']} {result['prompt_emoji']} {result['model_emoji']} {result['experiment_id']}"
        
        # Format metrics
        avg_pos = f"{result['average_position']:.3f}"
        success_rate = f"{result['final_score_percentage']:.1f}%"
        case_info = f"({result['matched_cases']}/{result['total_cases']})"
        
        # Create row
        row = f"{rank_emoji} │ {experiment_display:<45} │ {avg_pos:>6} │ {success_rate:>7} {case_info}"
        table_lines.append(row)
    
    table_lines.append("-" * 80)
    table_lines.append(f"📊 Total experiments: {len(sorted_results)}")
    if incomplete_results:
        table_lines.append(f"⚠️  Incomplete runs found: {len(incomplete_results)} (not ranked)")
    table_lines.append(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(table_lines)

def create_detailed_breakdown(results: List[Dict]) -> str:
    """Create a detailed breakdown by category"""
    if not results:
        return ""
    
    # Filter out incomplete runs for statistics
    complete_results = [r for r in results if r['matched_cases'] > 0 or r['total_cases'] == 0]
    
    lines = []
    lines.append("\n\n🔍 DETAILED BREAKDOWN")
    lines.append("=" * 80)
    
    # Group by dataset
    lines.append("\n📊 BY DATASET:")
    dataset_groups = {}
    for result in complete_results:
        dataset = result['dataset_name']
        if dataset not in dataset_groups:
            dataset_groups[dataset] = []
        dataset_groups[dataset].append(result)
    
    for dataset, group in sorted(dataset_groups.items()):
        avg_score = sum(r['average_position'] for r in group) / len(group)
        avg_success = sum(r['final_score_percentage'] for r in group) / len(group)
        emoji = get_emoji('dataset', dataset)
        lines.append(f"  {emoji} {dataset:<20} │ {len(group):2d} runs │ Avg: {avg_score:.3f} │ Success: {avg_success:.1f}%")
    
    # Group by prompt
    lines.append("\n📝 BY PROMPT:")
    prompt_groups = {}
    for result in complete_results:
        prompt = result['prompt_name']
        if prompt not in prompt_groups:
            prompt_groups[prompt] = []
        prompt_groups[prompt].append(result)
    
    for prompt, group in sorted(prompt_groups.items()):
        avg_score = sum(r['average_position'] for r in group) / len(group)
        avg_success = sum(r['final_score_percentage'] for r in group) / len(group)
        emoji = get_emoji('prompt', prompt)
        lines.append(f"  {emoji} {prompt:<20} │ {len(group):2d} runs │ Avg: {avg_score:.3f} │ Success: {avg_success:.1f}%")
    
    # Group by model
    lines.append("\n🤖 BY MODEL:")
    model_groups = {}
    for result in complete_results:
        model = result['model_name']
        if model not in model_groups:
            model_groups[model] = []
        model_groups[model].append(result)
    
    for model, group in sorted(model_groups.items()):
        avg_score = sum(r['average_position'] for r in group) / len(group)
        avg_success = sum(r['final_score_percentage'] for r in group) / len(group)
        emoji = get_emoji('model', model)
        lines.append(f"  {emoji} {model:<20} │ {len(group):2d} runs │ Avg: {avg_score:.3f} │ Success: {avg_success:.1f}%")
    
    return "\n".join(lines)

def main():
    """Main function to generate ranking report"""
    print("👁️  Pipeline Results Watcher")
    print("=" * 40)
    
    # Get output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    
    if not os.path.exists(output_dir):
        print(f"❌ Output directory not found: {output_dir}")
        return
    
    # Scan for summaries
    results = scan_for_summaries(output_dir)
    
    if not results:
        print("❌ No summary.json files found")
        return
    
    # Create ranking table
    ranking_table = create_ranking_table(results)
    
    # Create detailed breakdown
    detailed_breakdown = create_detailed_breakdown(results)
    
    # Combine reports
    full_report = ranking_table + detailed_breakdown
    
    # Save to file
    ranking_file = os.path.join(output_dir, 'ranking.txt')
    try:
        with open(ranking_file, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        print(f"✅ Ranking report saved to: {ranking_file}")
        
        # Also display the ranking table
        print("\n" + ranking_table)
        
    except Exception as e:
        print(f"❌ Error saving ranking file: {str(e)}")
        # Still display the results
        print("\n" + ranking_table)

if __name__ == "__main__":
    main()