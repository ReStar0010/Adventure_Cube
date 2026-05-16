#!/usr/bin/env python3
"""
Script to test story generation speed for the latest 5 prompts from CSV.
Measures generation time vs generated text length and creates a visualization.
"""

import csv
import sys
import re
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple

# Try to import required libraries (lazy loading)
HAS_GEMINI = False
HAS_PLOTTING = False

def check_dependencies():
    """Check and import required dependencies."""
    global HAS_GEMINI, HAS_PLOTTING, genai, plt, np
    
    # Check for google-generativeai
    try:
        import google.generativeai as genai
        HAS_GEMINI = True
    except ImportError:
        print("❌ Error: google-generativeai not installed. Install with: pip install google-generativeai")
        sys.exit(1)
    
    # Check for matplotlib and numpy
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        HAS_PLOTTING = True
    except ImportError:
        print("⚠️  Warning: matplotlib or numpy not installed. Chart generation will be skipped.")
        print("   Install with: pip install matplotlib numpy")
        HAS_PLOTTING = False


def clean_html_tags(text):
    """
    Convert HTML tags to plain text formatting.
    - <br> and <br><br> become newlines
    - **text** remains as markdown bold
    """
    if not text:
        return ''
    # Replace <br> and <br><br> with newlines
    text = re.sub(r'<br>\s*<br>', '\n\n', text)
    text = re.sub(r'<br>', '\n', text)
    return text.strip()


def count_words_chinese(text: str) -> int:
    """
    Count words/characters in text, handling both Chinese and English.
    For Chinese text, counts characters (字).
    For English text, counts words separated by spaces.
    For mixed text, uses a hybrid approach.
    
    Args:
        text: Input text (can be Chinese, English, or mixed)
        
    Returns:
        Word/character count
    """
    if not text:
        return 0
    
    # Remove markdown formatting and extra whitespace
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold markers
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Remove code markers
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.strip()
    
    # Count Chinese characters (CJK Unified Ideographs)
    # This includes: Chinese, Japanese Kanji, Korean Hanja
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    
    # Count English words (sequences of letters separated by spaces/punctuation)
    # Split by whitespace and punctuation, then count non-empty sequences of letters
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    
    # Count other characters (numbers, punctuation, etc.) as separate units
    # But exclude spaces and common punctuation that don't count as words
    other_chars = len(re.findall(r'[^\u4e00-\u9fff\sa-zA-Z]', text))
    
    # For Chinese-dominant text, count characters
    # For English-dominant text, count words
    # For mixed, use a weighted approach
    if chinese_chars > english_words * 2:
        # Chinese-dominant: count Chinese characters + English words
        return chinese_chars + english_words
    elif english_words > chinese_chars * 2:
        # English-dominant: count words
        return english_words
    else:
        # Mixed: count Chinese characters + English words
        return chinese_chars + english_words


def format_prompt_for_agent(row, clean_html=True):
    """
    Format a CSV row into context-engineering prompt format.
    
    Args:
        row: Dictionary containing CSV row data
        clean_html: Whether to convert HTML tags to newlines
        
    Returns:
        Formatted prompt string
    """
    # Extract fields from row
    meta_instruction_prompt = row.get('Meta_Instruction_Prompt', '')
    # The CSV has a column alignment issue - the actual Prompt_Instruction 
    # is in the empty column (trailing comma creates empty column name)
    prompt_instruction = row.get('', '') or row.get('Prompt_Instruction', '')
    
    # Clean HTML tags if requested
    if clean_html:
        meta_instruction_prompt = clean_html_tags(meta_instruction_prompt)
        prompt_instruction = clean_html_tags(prompt_instruction)
    
    # Format the prompt according to context-engineering format
    formatted_prompt = f"""# system_prompt
{meta_instruction_prompt}

# user_prompt
{prompt_instruction}
"""
    
    return formatted_prompt


def fetch_latest_n_rows(csv_path: Path, n: int = 5) -> List[Dict]:
    """
    Fetch the latest N rows from CSV.
    
    Args:
        csv_path: Path to CSV file
        n: Number of rows to fetch (default: 5)
        
    Returns:
        List of dictionaries containing row data
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # Return the last N rows
        return rows[-n:] if len(rows) >= n else rows


def load_credentials(credential_path: Path) -> Dict:
    """
    Load API credentials from JSON file.
    
    Args:
        credential_path: Path to credential.json
        
    Returns:
        Dictionary containing credentials
    """
    with open(credential_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_story_with_gemini(prompt: str, api_key: str, min_words: int = 1500) -> Tuple[str, float]:
    """
    Generate a story using Gemini API and measure the time.
    
    Args:
        prompt: The formatted prompt for story generation
        api_key: Google API key for Gemini
        min_words: Minimum number of words required in the generated text (default: 1500)
        
    Returns:
        Tuple of (generated_text, generation_time_seconds)
    """
    if not HAS_GEMINI:
        check_dependencies()
    
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Add word count requirement and placeholder instructions to the prompt
        enhanced_prompt = f"""{prompt}

**重要要求 (Important Requirement):**
請確保生成的故事內容至少包含 {min_words} 個字詞。故事應該詳細、豐富且完整。
Please ensure the generated story contains at least {min_words} words. The story should be detailed, rich, and complete.

**關於提示中的佔位符 (About Placeholders in the Prompt):**
如果提示中包含佔位符（如 [角色1], [角色2], [場景], [小道具] 等），請自行創建合適的角色名稱、場景描述和道具，並將這些佔位符替換為具體的內容。你可以自由發揮創意，選擇符合故事主題的角色、場景和道具。
If the prompt contains placeholders (such as [角色1], [角色2], [場景], [小道具], etc.), please create appropriate character names, scene descriptions, and props yourself, and replace these placeholders with specific content. You can freely use your creativity to choose characters, scenes, and props that fit the story theme.
"""
        
        # Measure generation time
        start_time = time.time()
        response = model.generate_content(enhanced_prompt)
        end_time = time.time()
        
        generation_time = end_time - start_time
        generated_text = response.text if response.text else ""
        
        # Count words/characters in generated text (handles Chinese correctly)
        word_count = count_words_chinese(generated_text)
        
        # Note if below minimum (but don't retry)
        if word_count < min_words:
            print(f"  ⚠️  Note: Generated {word_count} words/characters, less than requested {min_words}.")
        
        return generated_text, generation_time
        
    except Exception as e:
        print(f"❌ Error generating story: {e}")
        return "", 0.0


def test_prompts(prompts: List[Dict], credentials: Dict) -> List[Dict]:
    """
    Test each prompt and collect metrics.
    
    Args:
        prompts: List of prompt dictionaries from CSV
        credentials: Dictionary containing API credentials
        
    Returns:
        List of dictionaries with test results
    """
    results = []
    api_key = credentials.get('googleApiKey', '')
    
    if not api_key:
        print("❌ Error: Google API key not found in credentials")
        return results
    
    print(f"\n{'='*80}")
    print(f"Testing {len(prompts)} prompts...")
    print(f"{'='*80}\n")
    
    for idx, row in enumerate(prompts, 1):
        phase_id = row.get('Phase_ID', 'N/A')
        theme = row.get('Theme', 'N/A')
        dramatic_structure = row.get('Dramatic_Structure', 'N/A')
        
        print(f"[{idx}/{len(prompts)}] Testing Phase_ID: {phase_id}")
        print(f"  Theme: {theme}, Structure: {dramatic_structure}")
        
        # Format the prompt
        formatted_prompt = format_prompt_for_agent(row)
        
        # Generate story and measure time
        print("  ⏳ Generating story (minimum 1500 words)...")
        generated_text, generation_time = generate_story_with_gemini(formatted_prompt, api_key, min_words=1500)
        
        # Calculate text length (number of characters) and word count
        text_length = len(generated_text)
        word_count = count_words_chinese(generated_text)
        
        # Store results
        result = {
            'index': idx,
            'phase_id': phase_id,
            'theme': theme,
            'dramatic_structure': dramatic_structure,
            'text_length': text_length,
            'word_count': word_count,
            'generation_time': generation_time,
            'generated_text': generated_text
        }
        results.append(result)
        
        print(f"  ✅ Generated {word_count} words ({text_length} characters) in {generation_time:.2f} seconds")
        print(f"  📊 Speed: {text_length/generation_time:.1f} chars/sec, {word_count/generation_time:.1f} words/sec")
        
        # Show preview of generated text
        print(f"\n  📖 Preview (first 500 characters):")
        print(f"  {'-'*70}")
        preview = generated_text[:500] + "..." if len(generated_text) > 500 else generated_text
        # Indent each line of preview
        for line in preview.split('\n'):
            print(f"  {line}")
        print(f"  {'-'*70}\n")
    
    return results


def create_chart(results: List[Dict], output_path: Path):
    """
    Create a scatter plot showing correlation between text length and generation time.
    
    Args:
        results: List of test result dictionaries
        output_path: Path to save the chart
    """
    if not HAS_PLOTTING:
        print("⚠️  Skipping chart generation (matplotlib/numpy not available)")
        return
    
    if not results:
        print("❌ No results to plot")
        return
    
    # Extract data - use word count instead of character count
    word_counts = [r.get('word_count', 0) for r in results]
    generation_times = [r['generation_time'] for r in results]
    labels = [f"#{r['index']}\n{r['phase_id'][:15]}" for r in results]
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Scatter plot
    scatter = plt.scatter(word_counts, generation_times, s=200, alpha=0.6, c=range(len(results)), cmap='viridis')
    
    # Add labels for each point
    for i, (x, y, label) in enumerate(zip(word_counts, generation_times, labels)):
        plt.annotate(label, (x, y), xytext=(5, 5), textcoords='offset points', 
                    fontsize=9, alpha=0.7)
    
    # Calculate and plot trend line
    if len(word_counts) > 1:
        z = np.polyfit(word_counts, generation_times, 1)
        p = np.poly1d(z)
        plt.plot(word_counts, p(word_counts), "r--", alpha=0.5, label=f'Trend line (y={z[0]:.4f}x+{z[1]:.2f})')
        plt.legend()
    
    # Calculate correlation coefficient
    correlation = np.corrcoef(word_counts, generation_times)[0, 1]
    
    # Customize the plot
    plt.xlabel('Generated Text Length (words)', fontsize=12, fontweight='bold')
    plt.ylabel('Generation Time (seconds)', fontsize=12, fontweight='bold')
    plt.title(f'Story Generation Speed Analysis\nCorrelation: {correlation:.3f}', 
              fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add statistics text box
    stats_text = f"Total Tests: {len(results)}\n"
    stats_text += f"Avg Words: {np.mean(word_counts):.0f} words\n"
    stats_text += f"Avg Time: {np.mean(generation_times):.2f}s\n"
    stats_text += f"Avg Speed: {np.mean([w/t for w, t in zip(word_counts, generation_times)]):.1f} words/s"
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
             fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Save the chart
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n📊 Chart saved to: {output_path}")
    
    # Also display the chart (comment out if running headless)
    try:
        plt.show()
    except:
        print("⚠️  Could not display chart (running in headless mode?)")


def print_summary(results: List[Dict]):
    """
    Print a summary of the test results.
    
    Args:
        results: List of test result dictionaries
    """
    if not results:
        return
    
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"{'Index':<8} {'Phase_ID':<25} {'Words':<10} {'Chars':<10} {'Time (s)':<12} {'Speed (words/s)':<15}")
    print("-" * 80)
    
    for r in results:
        word_count = r.get('word_count', 0)
        speed = word_count / r['generation_time'] if r['generation_time'] > 0 else 0
        print(f"{r['index']:<8} {r['phase_id'][:24]:<25} {word_count:<10} {r['text_length']:<10} "
              f"{r['generation_time']:<12.2f} {speed:<15.1f}")
    
    # Calculate averages
    word_counts = [r.get('word_count', 0) for r in results]
    text_lengths = [r['text_length'] for r in results]
    generation_times = [r['generation_time'] for r in results]
    speeds = [w/t for w, t in zip(word_counts, generation_times) if t > 0]
    
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
    avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
    avg_time = sum(generation_times) / len(generation_times) if generation_times else 0
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    
    print("-" * 80)
    print(f"{'AVERAGE':<8} {'':<25} {avg_words:<10.0f} {avg_length:<10.0f} {avg_time:<12.2f} {avg_speed:<15.1f}")
    print(f"{'='*80}\n")


def main():
    """Main function."""
    # Check dependencies first
    check_dependencies()
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # File paths
    csv_path = script_dir / '1106_prompt.csv'
    credential_path = script_dir / 'credential.json'
    chart_output = script_dir / 'story_generation_speed_chart.png'
    
    # Check if files exist
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    if not credential_path.exists():
        print(f"❌ Error: Credential file not found at {credential_path}")
        sys.exit(1)
    
    # Load credentials
    print("🔑 Loading credentials...")
    credentials = load_credentials(credential_path)
    
    # Fetch latest 10 rows
    print(f"📄 Fetching latest 10 prompts from {csv_path.name}...")
    prompts = fetch_latest_n_rows(csv_path, n=10)
    
    if not prompts:
        print("❌ Error: No prompts found in CSV")
        sys.exit(1)
    
    print(f"✅ Found {len(prompts)} prompts\n")
    
    # Test each prompt
    results = test_prompts(prompts, credentials)
    
    if not results:
        print("❌ Error: No results generated")
        sys.exit(1)
    
    # Print summary
    print_summary(results)
    
    # Create chart
    print("📊 Creating visualization...")
    create_chart(results, chart_output)
    
    print("\n✅ Test completed successfully!")


if __name__ == '__main__':
    main()

