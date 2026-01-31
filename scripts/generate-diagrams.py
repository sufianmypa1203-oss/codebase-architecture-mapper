#!/usr/bin/env python3
"""
Diagram Generator - Phase 2
Generates Mermaid diagrams showing system relationships.
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

def generate_system_overview(systems: dict) -> str:
    """Generate the main system overview diagram."""
    
    lines = ["graph TB"]
    
    # Color scheme
    colors = {
        'external': '#ff6b6b',  # Red
        'core': '#ffd93d',      # Yellow
        'feature': '#6bcf7f'    # Green
    }
    
    # Classify systems
    external = ['flinks', 'supabase']
    core = ['auth', 'api', 'utils', 'ui']
    
    # Add subgraphs
    external_systems = [s for s in external if s in systems]
    core_systems = [s for s in core if s in systems]
    feature_systems = [s for s in systems.keys() if s not in external + core + ['other']]
    
    if external_systems:
        lines.append('    subgraph External["🌐 External Services"]')
        for s in external_systems:
            name = systems[s]['name']
            lines.append(f'        {s.upper()}["{name}"]')
        lines.append('    end')
    
    if core_systems:
        lines.append('    subgraph Core["⚙️ Core Systems"]')
        for s in core_systems:
            name = systems[s]['name']
            lines.append(f'        {s.upper()}["{name}"]')
        lines.append('    end')
    
    if feature_systems:
        lines.append('    subgraph Features["🎯 Features"]')
        for s in feature_systems:
            name = systems[s]['name']
            lines.append(f'        {s.upper()}["{name}"]')
        lines.append('    end')
    
    # Add connections based on dependencies
    for name, data in systems.items():
        if name == 'other':
            continue
        for dep in data.get('depends_on', []):
            if dep in systems and dep != 'other':
                lines.append(f'    {name.upper()} --> {dep.upper()}')
    
    # Add styling
    lines.append('')
    for s in external_systems:
        lines.append(f'    style {s.upper()} fill:{colors["external"]}')
    for s in core_systems:
        lines.append(f'    style {s.upper()} fill:{colors["core"]}')
    for s in feature_systems:
        lines.append(f'    style {s.upper()} fill:{colors["feature"]}')
    
    return '\n'.join(lines)

def generate_data_flow(systems: dict) -> str:
    """Generate a data flow diagram."""
    
    lines = ["graph LR"]
    
    # Common data flow patterns
    flows = [
        ('User', 'UI'),
        ('UI', 'API'),
        ('API', 'AUTH'),
        ('API', 'SUPABASE'),
    ]
    
    # Add user node
    lines.append('    User((👤 User))')
    
    # Add system nodes
    for name, data in systems.items():
        if name == 'other':
            continue
        lines.append(f'    {name.upper()}["{data["name"]}"]')
    
    # Add flows
    for source, target in flows:
        if target.lower() in systems or target == 'User':
            lines.append(f'    {source} --> {target}')
    
    # Add feature connections to database
    feature_systems = [s for s in systems.keys() if s not in ['auth', 'api', 'utils', 'ui', 'supabase', 'flinks', 'other']]
    for feature in feature_systems:
        if 'supabase' in systems:
            lines.append(f'    {feature.upper()} --> SUPABASE')
    
    return '\n'.join(lines)

def generate_dependency_map(systems: dict) -> str:
    """Generate a dependency relationship diagram."""
    
    lines = ["graph TD"]
    
    # Add all systems
    for name, data in systems.items():
        if name == 'other':
            continue
        count = data.get('file_count', 0)
        lines.append(f'    {name.upper()}["{data["name"]}<br/>{count} files"]')
    
    # Add all dependency arrows
    for name, data in systems.items():
        if name == 'other':
            continue
        for dep in data.get('depends_on', []):
            if dep in systems and dep != 'other':
                lines.append(f'    {name.upper()} -.-> {dep.upper()}')
    
    # Add color based on file count
    for name, data in systems.items():
        if name == 'other':
            continue
        count = data.get('file_count', 0)
        if count > 20:
            lines.append(f'    style {name.upper()} fill:#ff6b6b')
        elif count > 10:
            lines.append(f'    style {name.upper()} fill:#ffd93d')
        else:
            lines.append(f'    style {name.upper()} fill:#6bcf7f')
    
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 3:
        print("Usage: generate-diagrams.py <systems.json> <output_directory>")
        print("\nExample:")
        print("  python generate-diagrams.py systems.json docs/architecture/diagrams")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = Path(sys.argv[2])
    
    # Read input
    if input_file == '-':
        data = json.load(sys.stdin)
    else:
        with open(input_file, 'r') as f:
            data = json.load(f)
    
    systems = data.get('systems', {})
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_info(f"Generating diagrams in: {output_dir}")
    
    # Generate system overview
    overview = generate_system_overview(systems)
    (output_dir / 'system-overview.mmd').write_text(overview)
    log_success("Created: system-overview.mmd")
    
    # Generate data flow
    data_flow = generate_data_flow(systems)
    (output_dir / 'data-flow.mmd').write_text(data_flow)
    log_success("Created: data-flow.mmd")
    
    # Generate dependency map
    dep_map = generate_dependency_map(systems)
    (output_dir / 'dependency-map.mmd').write_text(dep_map)
    log_success("Created: dependency-map.mmd")
    
    log_success("All diagrams generated!")

if __name__ == '__main__':
    main()
