"""
harmonize_brand_colors.py - Senior Developer Refactoring
Replaces legacy teal/blue design tokens (#20515d, #163942, #2f7585, #e8f1f4, #00b395)
with the unified Rentora Brand Orange design system across all templates.
"""
import os
import re

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')

REPLACEMENTS = [
    # Primary teal to Rentora Orange
    ('#20515d', '#FF5F00'),
    ('#163942', '#E05300'),
    ('#2f7585', '#FF7A29'),
    ('#e8f1f4', '#FFF2EA'),
    ('#00b395', '#FF5F00'),
    ('#cde2e8', '#FFDBCF'),
    ('#00c9a7', '#FF5F00'),
    ('#050811', '#0F172A'),
]

def harmonize():
    total_files_modified = 0
    total_replacements = 0

    for root, _, files in os.walk(TEMPLATES_DIR):
        for f in files:
            if not f.endswith('.html'):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            
            modified_content = content
            file_replacements = 0
            for old_val, new_val in REPLACEMENTS:
                count = modified_content.count(old_val)
                if count > 0:
                    modified_content = modified_content.replace(old_val, new_val)
                    file_replacements += count

            if file_replacements > 0:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(modified_content)
                rel_path = os.path.relpath(path, TEMPLATES_DIR)
                print(f"[UPDATED] {rel_path} ({file_replacements} color replacements)")
                total_files_modified += 1
                total_replacements += file_replacements

    print(f"\nHarmonization complete! Updated {total_files_modified} files with {total_replacements} replacements.")

if __name__ == '__main__':
    harmonize()

