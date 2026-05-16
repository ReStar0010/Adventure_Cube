#!/usr/bin/env python3
"""
Script to fetch rows from 1106_prompt.csv and format them according to context-engineering format.
"""

import csv
import sys
import re
from pathlib import Path


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


def fetch_row_by_index(csv_path, row_index):
    """
    Fetch a specific row from CSV by index (0-based, excluding header).
    
    Args:
        csv_path: Path to CSV file
        row_index: Index of row to fetch (0-based, excluding header)
        
    Returns:
        Dictionary containing row data, or None if not found
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        if row_index < 0 or row_index >= len(rows):
            return None
            
        return rows[row_index]


def fetch_row_by_phase_id(csv_path, phase_id):
    """
    Fetch a row from CSV by Phase_ID.
    
    Args:
        csv_path: Path to CSV file
        phase_id: Phase_ID to search for
        
    Returns:
        Dictionary containing row data, or None if not found
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Phase_ID') == phase_id:
                return row
    return None


def fetch_all_rows(csv_path):
    """
    Fetch all rows from CSV.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        List of dictionaries containing row data
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def main():
    """Main function to handle command line arguments."""
    # Default CSV path
    csv_path = Path(__file__).parent / '1106_prompt.csv'
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fetch_prompt.py <row_index>                    # Fetch row by index (0-based)")
        print("  python fetch_prompt.py <row_index> --save <file>     # Save to file")
        print("  python fetch_prompt.py --phase <phase_id>            # Fetch row by Phase_ID")
        print("  python fetch_prompt.py --phase <phase_id> --save <file>  # Save to file")
        print("  python fetch_prompt.py --all                         # Fetch all rows")
        print("  python fetch_prompt.py --list                        # List all rows with indices")
        sys.exit(1)
    
    # Check for --save option
    save_file = None
    if '--save' in sys.argv:
        save_idx = sys.argv.index('--save')
        if save_idx + 1 < len(sys.argv):
            save_file = sys.argv[save_idx + 1]
            # Remove --save and filename from argv for easier processing
            sys.argv = [arg for arg in sys.argv if arg != '--save' and arg != save_file]
    
    if sys.argv[1] == '--all':
        # Fetch all rows
        rows = fetch_all_rows(csv_path)
        output = []
        for idx, row in enumerate(rows):
            output.append(f"\n{'='*80}")
            output.append(f"Row {idx} - Phase_ID: {row.get('Phase_ID', 'N/A')}")
            output.append(f"{'='*80}")
            formatted = format_prompt_for_agent(row)
            output.append(formatted)
        
        result = '\n'.join(output)
        if save_file:
            with open(save_file, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Saved all rows to {save_file}")
        else:
            print(result)
    
    elif sys.argv[1] == '--list':
        # List all rows with indices
        rows = fetch_all_rows(csv_path)
        print(f"Total rows: {len(rows)}\n")
        for idx, row in enumerate(rows):
            phase_id = row.get('Phase_ID', 'N/A')
            theme = row.get('Theme', 'N/A')
            archetype_name = row.get('Archetype_Name', 'N/A')
            dramatic_structure = row.get('Dramatic_Structure', 'N/A')
            print(f"  [{idx:3d}] Phase_ID: {phase_id:25s} | Theme: {theme:8s} | "
                  f"Archetype: {archetype_name:20s} | Structure: {dramatic_structure}")
    
    elif sys.argv[1] == '--phase' and len(sys.argv) > 2:
        # Fetch by Phase_ID
        phase_id = sys.argv[2]
        row = fetch_row_by_phase_id(csv_path, phase_id)
        if row:
            formatted = format_prompt_for_agent(row)
            if save_file:
                with open(save_file, 'w', encoding='utf-8') as f:
                    f.write(formatted)
                print(f"Saved prompt to {save_file}")
            else:
                print(formatted)
        else:
            print(f"Error: Phase_ID '{phase_id}' not found in CSV.")
            sys.exit(1)
    
    else:
        # Fetch by index
        try:
            row_index = int(sys.argv[1])
            row = fetch_row_by_index(csv_path, row_index)
            if row:
                formatted = format_prompt_for_agent(row)
                if save_file:
                    with open(save_file, 'w', encoding='utf-8') as f:
                        f.write(formatted)
                    print(f"Saved prompt to {save_file}")
                else:
                    print(formatted)
            else:
                print(f"Error: Row index {row_index} out of range.")
                sys.exit(1)
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid row index.")
            sys.exit(1)


if __name__ == '__main__':
    main()

