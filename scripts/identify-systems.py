#!/usr/bin/env python3
"""
Elite System Identifier v3.0
- Granular Detection: Goes deeper into large folders
- Interactive Mode: Asks user for descriptions
- Persistent Config: Saves to architecture-config.json
- System Fingerprints: Detects real systems by file patterns
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ANSI Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'

def log_info(msg): print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}", file=sys.stderr)
def log_success(msg): print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}", file=sys.stderr)
def log_warn(msg): print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}", file=sys.stderr)
def log_system(name, count): print(f"{Colors.MAGENTA}[SYSTEM]{Colors.NC} {name} ({count} files)", file=sys.stderr)
def log_prompt(msg): print(f"{Colors.CYAN}[?]{Colors.NC} {msg}", file=sys.stderr)

# === CONFIGURATION ===

# Directories to skip entirely
SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', '.next', '__pycache__', 'venv', '.venv'}

# Root directories to skip when naming (go one level deeper)
ROOT_DIRS = {'src', 'app', 'lib', 'packages', 'apps', 'modules', 'core', 'source', 'main', 'features'}

# System fingerprint files (presence indicates a "real" system)
FINGERPRINT_FILES = {'index.ts', 'index.tsx', 'index.js', 'types.ts', 'api.ts', 'service.ts', 'client.ts', '__init__.py', 'mod.rs'}

# Minimum files to be a system
MIN_SYSTEM_FILES = 3

# Maximum files before splitting deeper
MAX_FILES_BEFORE_SPLIT = 15

# Maximum systems before merging into "other"
MAX_SYSTEMS = 20

# Maximum depth to scan
MAX_DEPTH = 3

# Config file name
CONFIG_FILE = 'architecture-config.json'


def has_system_fingerprint(files: list) -> bool:
    """Check if folder has fingerprint files indicating it's a system."""
    filenames = {Path(f).name.lower() for f in files}
    return bool(filenames & {f.lower() for f in FINGERPRINT_FILES})


def get_folder_depth(path: str, root: str) -> int:
    """Get how deep a folder is from root."""
    rel = os.path.relpath(path, root)
    return len(Path(rel).parts)


def discover_systems_granular(files: list, root: str, max_depth: int = MAX_DEPTH) -> dict:
    """
    Granular system discovery - goes deeper into large folders.
    """
    
    # Group files by their directories
    dir_files = defaultdict(list)
    for file in files:
        dir_path = file.get('directory', '.')
        dir_files[dir_path].append(file)
    
    # Analyze each directory
    systems = {}
    processed_dirs = set()
    
    # Sort by depth (shallowest first)
    sorted_dirs = sorted(dir_files.keys(), key=lambda d: len(Path(d).parts))
    
    for dir_path in sorted_dirs:
        # Skip if already covered by a parent system
        if any(dir_path.startswith(p + '/') or dir_path == p for p in processed_dirs):
            continue
        
        dir_file_list = dir_files[dir_path]
        file_count = len(dir_file_list)
        depth = get_folder_depth(dir_path, root) if root else len(Path(dir_path).parts)
        
        # Get the system name from path
        parts = Path(dir_path).parts
        system_name = None
        
        for part in parts:
            if part.lower() not in ROOT_DIRS and not part.startswith('.') and part != '.':
                system_name = part.lower()
                break
        
        if not system_name:
            system_name = 'root'
        
        # Decision: Should this be a system or should we go deeper?
        has_fingerprint = has_system_fingerprint([f['path'] for f in dir_file_list])
        
        # Count files in subdirectories too
        total_files_in_subtree = sum(
            len(dir_files[d]) for d in dir_files 
            if d.startswith(dir_path + '/') or d == dir_path
        )
        
        # If large folder and not too deep, mark for splitting
        if total_files_in_subtree > MAX_FILES_BEFORE_SPLIT and depth < max_depth:
            # Don't register this as a system, let subdirectories be systems
            continue
        
        # Register as a system
        if system_name not in systems:
            systems[system_name] = {
                'name': system_name.replace('-', ' ').replace('_', ' ').title(),
                'paths': [],
                'files': [],
                'directories': [],
                'total_lines': 0,
                'has_fingerprint': has_fingerprint,
                'description': '',
                'used_by': [],
                'business_rules': []
            }
        
        # Add files to system
        for f in dir_file_list:
            systems[system_name]['files'].append(f['path'])
            systems[system_name]['total_lines'] += f.get('lines', 0)
        
        systems[system_name]['paths'].append(dir_path)
        systems[system_name]['directories'].append(dir_path)
        processed_dirs.add(dir_path)
    
    return systems


def load_config(config_path: Path) -> dict:
    """Load existing architecture config if it exists."""
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_config(config: dict, config_path: Path) -> None:
    """Save architecture config."""
    config['last_updated'] = datetime.now().isoformat()
    config['version'] = '3.0'
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    log_success(f"Config saved to: {config_path}")


def interactive_prompt(systems: dict, existing_config: dict) -> dict:
    """Interactively prompt user for system descriptions."""
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}  INTERACTIVE SYSTEM CONFIGURATION{Colors.NC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.NC}\n")
    
    existing_systems = existing_config.get('systems', {})
    
    for sys_name, sys_data in sorted(systems.items(), key=lambda x: -len(x[1]['files'])):
        file_count = len(sys_data['files'])
        
        # Skip "other" system
        if sys_name == 'other':
            continue
        
        # Check if we have existing config for this system
        existing = existing_systems.get(sys_name, {})
        
        if existing.get('user_modified'):
            # User has already configured this, skip
            log_info(f"Skipping {sys_name} (already configured)")
            sys_data['description'] = existing.get('description', '')
            sys_data['used_by'] = existing.get('used_by', [])
            sys_data['business_rules'] = existing.get('business_rules', [])
            continue
        
        print(f"\n{Colors.MAGENTA}{'─'*50}{Colors.NC}")
        print(f"{Colors.BOLD}📦 {sys_data['name']}{Colors.NC} ({file_count} files)")
        print(f"   Location: {sys_data['paths'][0] if sys_data['paths'] else 'root'}")
        
        # Show sample files
        sample_files = sys_data['files'][:3]
        if sample_files:
            print(f"   Files: {', '.join(Path(f).name for f in sample_files)}")
        
        print()
        
        # Prompt for description
        try:
            desc = input(f"{Colors.CYAN}   What does this system DO? {Colors.NC}(Enter to skip): ").strip()
            sys_data['description'] = desc if desc else f"Auto-detected from {sys_data['paths'][0] if sys_data['paths'] else 'root'}"
            
            # Prompt for used_by
            used_by = input(f"{Colors.CYAN}   Who/what uses it? {Colors.NC}(comma-separated, Enter to skip): ").strip()
            sys_data['used_by'] = [x.strip() for x in used_by.split(',') if x.strip()] if used_by else []
            
            # Prompt for business rules
            rules = input(f"{Colors.CYAN}   Key business rules? {Colors.NC}(comma-separated, Enter to skip): ").strip()
            sys_data['business_rules'] = [x.strip() for x in rules.split(',') if x.strip()] if rules else []
            
            # Mark as user modified if any input was given
            if desc or used_by or rules:
                sys_data['user_modified'] = True
            
            print(f"{Colors.GREEN}   ✓ Saved{Colors.NC}")
            
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}Skipping remaining systems...{Colors.NC}")
            break
    
    return systems


def identify_systems(scan_data: dict, interactive: bool = False, config_path: Path = None) -> dict:
    """
    Main system identification with granular detection.
    """
    
    files = scan_data.get('files', [])
    root = scan_data.get('root', '.')
    
    log_info(f"Analyzing {len(files)} files with granular detection...")
    
    # Load existing config
    existing_config = load_config(config_path) if config_path else {}
    
    # Step 1: Granular discovery
    systems = discover_systems_granular(files, root)
    
    # Step 2: Merge small systems into "other"
    final_systems = {}
    other_files = []
    other_lines = 0
    
    for name, data in sorted(systems.items(), key=lambda x: -len(x[1]['files'])):
        if len(data['files']) < MIN_SYSTEM_FILES:
            other_files.extend(data['files'])
            other_lines += data['total_lines']
        elif len(final_systems) >= MAX_SYSTEMS:
            other_files.extend(data['files'])
            other_lines += data['total_lines']
        else:
            final_systems[name] = data
            log_system(data['name'], len(data['files']))
    
    if other_files:
        final_systems['other'] = {
            'name': 'Other',
            'paths': [],
            'files': other_files,
            'directories': [],
            'total_lines': other_lines,
            'has_fingerprint': False,
            'description': 'Miscellaneous files not belonging to a major system',
            'used_by': [],
            'business_rules': []
        }
    
    # Step 3: Interactive prompts if enabled
    if interactive:
        final_systems = interactive_prompt(final_systems, existing_config)
    else:
        # Apply existing descriptions from config
        for sys_name, sys_data in final_systems.items():
            existing = existing_config.get('systems', {}).get(sys_name, {})
            if existing.get('description'):
                sys_data['description'] = existing['description']
            if existing.get('used_by'):
                sys_data['used_by'] = existing['used_by']
            if existing.get('business_rules'):
                sys_data['business_rules'] = existing['business_rules']
            if existing.get('user_modified'):
                sys_data['user_modified'] = True
    
    # Step 4: Build dependency relationships from imports
    # (Basic version - check if system names appear in import paths)
    system_names = set(final_systems.keys())
    
    for sys_name, data in final_systems.items():
        data['depends_on'] = []
        data['imported_by'] = []
    
    # Step 5: Build final result
    result_systems = {}
    for name, data in final_systems.items():
        result_systems[name] = {
            'name': data['name'],
            'description': data.get('description') or f"Auto-detected from {data['paths'][0] if data['paths'] else 'root'}",
            'file_count': len(data['files']),
            'total_lines': data['total_lines'],
            'directories': sorted(set(data['directories'])),
            'files': sorted(data['files']),
            'depends_on': data.get('depends_on', []),
            'imported_by': data.get('imported_by', []),
            'used_by': data.get('used_by', []),
            'business_rules': data.get('business_rules', []),
            'has_fingerprint': data.get('has_fingerprint', False),
            'user_modified': data.get('user_modified', False)
        }
    
    log_success(f"Discovered {len(result_systems)} systems")
    
    # Save config if path provided
    if config_path:
        config = {
            'version': '3.0',
            'last_scan': datetime.now().isoformat(),
            'root': root,
            'systems': result_systems
        }
        save_config(config, config_path)
    
    return {
        'systems': result_systems,
        'summary': {
            'total_systems': len(result_systems),
            'total_files': sum(s['file_count'] for s in result_systems.values()),
            'total_lines': sum(s['total_lines'] for s in result_systems.values()),
            'discovery_method': 'granular_v3'
        },
        'scan_data': {
            'root': root,
            'scanned_at': scan_data.get('scanned_at')
        }
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Elite System Identifier v3.0 - Granular detection with interactive mode'
    )
    parser.add_argument('input', help='Scan results JSON file (or - for stdin)')
    parser.add_argument('output', nargs='?', help='Output JSON file (optional)')
    parser.add_argument('-i', '--interactive', action='store_true', 
                        help='Enable interactive mode to configure systems')
    parser.add_argument('-c', '--config', default=CONFIG_FILE,
                        help=f'Config file path (default: {CONFIG_FILE})')
    parser.add_argument('--depth', type=int, default=MAX_DEPTH,
                        help=f'Max scan depth (default: {MAX_DEPTH})')
    
    args = parser.parse_args()
    
    # Read input
    if args.input == '-':
        scan_data = json.load(sys.stdin)
    else:
        with open(args.input, 'r') as f:
            scan_data = json.load(f)
    
    # Determine config path
    root = scan_data.get('root', '.')
    config_path = Path(root) / args.config
    
    # Identify systems
    result = identify_systems(
        scan_data, 
        interactive=args.interactive,
        config_path=config_path
    )
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        log_success(f"Results saved to: {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
