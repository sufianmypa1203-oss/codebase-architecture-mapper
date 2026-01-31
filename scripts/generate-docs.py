#!/usr/bin/env python3
"""
Documentation Generator - Phase 2
Generates markdown documentation for each identified system.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# ANSI Colors
class Colors:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def log_info(msg): print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}", file=sys.stderr)
def log_success(msg): print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}", file=sys.stderr)

def generate_overview(data: dict, output_dir: Path) -> None:
    """Generate the main OVERVIEW.md file."""
    
    systems = data.get('systems', {})
    summary = data.get('summary', {})
    scan_info = data.get('scan_data', {})
    
    # Build system summary table
    system_rows = []
    for name, sys_data in sorted(systems.items(), key=lambda x: -x[1]['file_count']):
        if name == 'other':
            continue
        system_rows.append(f"| {sys_data['name']} | {sys_data['file_count']} | {sys_data['total_lines']:,} | {sys_data['description']} |")
    
    # Build Mermaid diagram
    mermaid_lines = ["graph TB"]
    
    # Group systems by type
    external = ['flinks', 'supabase']
    core = ['auth', 'api', 'utils', 'ui']
    features = [s for s in systems.keys() if s not in external + core + ['other']]
    
    # Add subgraphs
    if any(s in systems for s in external):
        mermaid_lines.append('    subgraph "External Services"')
        for s in external:
            if s in systems:
                mermaid_lines.append(f'        {s.upper()}["{systems[s]["name"]}"]')
        mermaid_lines.append('    end')
    
    if any(s in systems for s in core):
        mermaid_lines.append('    subgraph "Core Systems"')
        for s in core:
            if s in systems:
                mermaid_lines.append(f'        {s.upper()}["{systems[s]["name"]}"]')
        mermaid_lines.append('    end')
    
    if features:
        mermaid_lines.append('    subgraph "Features"')
        for s in features:
            if s in systems and s != 'other':
                mermaid_lines.append(f'        {s.upper()}["{systems[s]["name"]}"]')
        mermaid_lines.append('    end')
    
    # Add connections
    for name, sys_data in systems.items():
        if name == 'other':
            continue
        for dep in sys_data.get('depends_on', []):
            if dep in systems and dep != 'other':
                mermaid_lines.append(f'    {name.upper()} --> {dep.upper()}')
    
    mermaid = '\n'.join(mermaid_lines)
    
    # Generate markdown
    content = f"""# Architecture Overview

> Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} by Codebase Architecture Mapper

## System Map

```mermaid
{mermaid}
```

## Summary

| Metric | Value |
|--------|-------|
| Total Systems | {summary.get('total_systems', 0)} |
| Total Files | {summary.get('total_files', 0):,} |
| Total Lines | {summary.get('total_lines', 0):,} |

## Systems

| System | Files | Lines | Purpose |
|--------|-------|-------|---------|
{chr(10).join(system_rows)}

## Quick Links

"""
    
    for name, sys_data in sorted(systems.items()):
        if name != 'other':
            content += f"- [{sys_data['name']}](systems/{name}.md)\n"
    
    content += """
## Diagrams

- [System Overview](diagrams/system-overview.mmd)
- [Data Flow](diagrams/data-flow.mmd)
"""
    
    # Write file
    overview_path = output_dir / 'OVERVIEW.md'
    overview_path.write_text(content)
    log_success(f"Created: {overview_path}")

def generate_system_doc(name: str, sys_data: dict, output_dir: Path) -> None:
    """Generate documentation for a single system with full business context."""
    
    if name == 'other':
        return
    
    # Group files by directory
    files_by_dir = {}
    for file_path in sys_data.get('files', [])[:50]:
        dir_name = str(Path(file_path).parent)
        if dir_name not in files_by_dir:
            files_by_dir[dir_name] = []
        files_by_dir[dir_name].append(Path(file_path).name)
    
    # Build file table
    file_rows = []
    for dir_name, files in sorted(files_by_dir.items()):
        for f in files[:10]:
            file_rows.append(f"| `{dir_name}/{f}` |")
    
    # Build dependency info
    depends_on = sys_data.get('depends_on', [])
    imported_by = sys_data.get('imported_by', [])
    used_by = sys_data.get('used_by', [])
    business_rules = sys_data.get('business_rules', [])
    
    depends_str = ', '.join([f"[{d.title()}]({d}.md)" for d in depends_on]) if depends_on else 'None'
    imported_str = ', '.join([f"[{i.title()}]({i}.md)" for i in imported_by]) if imported_by else 'None'
    used_by_str = ', '.join(used_by) if used_by else 'Not specified'
    
    # Build business rules section
    rules_section = ""
    if business_rules:
        rules_section = "\n## ⚠️ Business Rules\n\n"
        for rule in business_rules:
            rules_section += f"> **{rule}**\n>\n"
    
    # Build used_by section
    used_by_section = ""
    if used_by:
        used_by_section = f"\n**Consumers:** {used_by_str}\n"
    
    # Fingerprint badge
    fingerprint_badge = "✅ Core System" if sys_data.get('has_fingerprint') else "📁 Directory Group"
    
    content = f"""# {sys_data['name']} System

> Last Updated: {datetime.now().strftime('%Y-%m-%d')} | {fingerprint_badge}

## Overview

{sys_data.get('description', 'No description available.')}
{used_by_section}
{rules_section}
## Statistics

| Metric | Value |
|--------|-------|
| Files | {sys_data.get('file_count', 0)} |
| Lines of Code | {sys_data.get('total_lines', 0):,} |
| Directories | {len(sys_data.get('directories', []))} |

## Dependencies

**Depends On:** {depends_str}

**Used By:** {imported_str}

## Key Directories

"""
    
    for dir_name in sorted(sys_data.get('directories', []))[:10]:
        content += f"- `{dir_name}/`\n"
    
    content += """
## Key Files

| File |
|------|
"""
    content += '\n'.join(file_rows[:20])
    
    if sys_data.get('file_count', 0) > 20:
        content += f"\n\n*...and {sys_data['file_count'] - 20} more files*"
    
    content += """

## Notes

<!-- Add any manual notes about this system here -->
- Architecture decisions
- Known issues
- Future improvements
"""
    
    # Write file
    system_path = output_dir / 'systems' / f'{name}.md'
    system_path.parent.mkdir(parents=True, exist_ok=True)
    system_path.write_text(content)
    log_success(f"Created: {system_path}")

def main():
    if len(sys.argv) < 3:
        print("Usage: generate-docs.py <systems.json> <output_directory>")
        print("\nExample:")
        print("  python generate-docs.py systems.json docs/architecture")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = Path(sys.argv[2])
    
    # Read input
    if input_file == '-':
        data = json.load(sys.stdin)
    else:
        with open(input_file, 'r') as f:
            data = json.load(f)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'systems').mkdir(exist_ok=True)
    (output_dir / 'diagrams').mkdir(exist_ok=True)
    
    # Generate documentation
    log_info(f"Generating documentation in: {output_dir}")
    
    generate_overview(data, output_dir)
    
    for name, sys_data in data.get('systems', {}).items():
        generate_system_doc(name, sys_data, output_dir)
    
    log_success(f"Documentation complete! Open {output_dir}/OVERVIEW.md")

if __name__ == '__main__':
    main()
