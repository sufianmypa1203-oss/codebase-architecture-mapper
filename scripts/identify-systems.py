#!/usr/bin/env python3
"""
Elite System Identifier v3.1 (Fixed)
- Granular Detection: Finds REAL subsystems within large folders
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

# === CONFIGURATION ===

# Directories to skip entirely
SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', '.next', '__pycache__', 'venv', '.venv'}

# Root directories to skip when naming
ROOT_DIRS = {'src', 'app', 'lib', 'packages', 'apps', 'modules', 'core', 'source', 'main', 'features', 'pages', 'components', 'views'}

# System fingerprint files
FINGERPRINT_FILES = {'index.ts', 'index.tsx', 'index.js', 'types.ts', 'api.ts', 'service.ts', 'client.ts', '__init__.py', 'mod.rs'}

# Minimum files to be a system
MIN_SYSTEM_FILES = 2

# Maximum systems before merging into "other"
MAX_SYSTEMS = 25

# Config file name
CONFIG_FILE = 'architecture-config.json'


def has_system_fingerprint(files: list) -> bool:
    """Check if folder has fingerprint files indicating it's a system."""
    filenames = {Path(f).name.lower() for f in files}
    return bool(filenames & {f.lower() for f in FINGERPRINT_FILES})


def get_meaningful_name(path: str) -> str:
    """
    Extract a meaningful system name from a path.
    
    Strategy: Find the deepest directory that isn't a generic container.
    For paths like:
      - src/pages/p2p/logic.ts → "p2p"
      - src/components/ui/Button.tsx → "ui" 
      - src/features/flinks/api.ts → "flinks"
      - src/utils/helpers.ts → "utils"
    """
    parts = Path(path).parts
    
    # Reverse to go deepest first
    meaningful = None
    for part in reversed(parts):
        p = part.lower()
        
        # Skip hidden directories
        if p.startswith('.'):
            continue
        
        # Skip generic containers - we want their children
        if p in ROOT_DIRS:
            # If we already found something meaningful, use it
            if meaningful:
                return meaningful
            # Otherwise keep looking
            continue
        
        # This is a meaningful name
        meaningful = p
    
    return meaningful or 'root'


def discover_systems_v31(files: list, root: str) -> dict:
    """
    V3.1 FIXED: Bottom-up discovery that correctly finds subsystems.
    
    Strategy:
    1. Group all files by their directory
    2. For each directory, determine if it's a "leaf system" (contains files directly)
    3. Group directories by their system name (extracted from path)
    4. Aggregate files with the same system name
    """
    
    # Step 1: Group files by their immediate directory
    dir_files = defaultdict(list)
    for file in files:
        dir_path = file.get('directory', '.')
        dir_files[dir_path].append(file)
    
    # Step 2: For each directory, extract the best system name
    system_candidates = defaultdict(lambda: {
        'files': [],
        'directories': set(),
        'total_lines': 0,
        'paths': set()
    })
    
    for dir_path, file_list in dir_files.items():
        # Get the system name for this directory
        system_name = get_meaningful_name(dir_path)
        
        # Add files to this system
        for f in file_list:
            system_candidates[system_name]['files'].append(f['path'])
            system_candidates[system_name]['total_lines'] += f.get('lines', 0)
        
        system_candidates[system_name]['directories'].add(dir_path)
        system_candidates[system_name]['paths'].add(dir_path)
    
    # Step 3: Check for fingerprints and build final systems
    systems = {}
    for name, data in system_candidates.items():
        has_fp = has_system_fingerprint(data['files'])
        
        systems[name] = {
            'name': name.replace('-', ' ').replace('_', ' ').title(),
            'paths': sorted(data['paths']),
            'files': data['files'],
            'directories': sorted(data['directories']),
            'total_lines': data['total_lines'],
            'has_fingerprint': has_fp,
            'description': '',
            'used_by': [],
            'business_rules': []
        }
    
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
    config['version'] = '3.1'
    
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
            log_info(f"Skipping {sys_name} (already configured)")
            sys_data['description'] = existing.get('description', '')
            sys_data['used_by'] = existing.get('used_by', [])
            sys_data['business_rules'] = existing.get('business_rules', [])
            continue
        
        print(f"\n{Colors.MAGENTA}{'─'*50}{Colors.NC}")
        print(f"{Colors.BOLD}📦 {sys_data['name']}{Colors.NC} ({file_count} files)")
        print(f"   Location: {sys_data['paths'][0] if sys_data['paths'] else 'root'}")
        
        sample_files = sys_data['files'][:3]
        if sample_files:
            print(f"   Files: {', '.join(Path(f).name for f in sample_files)}")
        
        print()
        
        try:
            desc = input(f"{Colors.CYAN}   What does this system DO? {Colors.NC}(Enter to skip): ").strip()
            sys_data['description'] = desc if desc else f"Auto-detected from {sys_data['paths'][0] if sys_data['paths'] else 'root'}"
            
            used_by = input(f"{Colors.CYAN}   Who/what uses it? {Colors.NC}(comma-separated, Enter to skip): ").strip()
            sys_data['used_by'] = [x.strip() for x in used_by.split(',') if x.strip()] if used_by else []
            
            rules = input(f"{Colors.CYAN}   Key business rules? {Colors.NC}(comma-separated, Enter to skip): ").strip()
            sys_data['business_rules'] = [x.strip() for x in rules.split(',') if x.strip()] if rules else []
            
            if desc or used_by or rules:
                sys_data['user_modified'] = True
            
            print(f"{Colors.GREEN}   ✓ Saved{Colors.NC}")
            
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}Skipping remaining systems...{Colors.NC}")
            break
    
    return systems


def identify_systems(scan_data: dict, interactive: bool = False, config_path: Path = None) -> dict:
    """Main system identification with v3.1 fixed granular detection."""
    
    files = scan_data.get('files', [])
    root = scan_data.get('root', '.')
    
    log_info(f"Analyzing {len(files)} files with v3.1 granular detection...")
    
    # Load existing config
    existing_config = load_config(config_path) if config_path else {}
    
    # Step 1: Granular discovery (FIXED)
    systems = discover_systems_v31(files, root)
    
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
    
    # Step 4: Build final result
    result_systems = {}
    for name, data in final_systems.items():
        result_systems[name] = {
            'name': data['name'],
            'description': data.get('description') or f"Auto-detected from {data['paths'][0] if data['paths'] else 'root'}",
            'file_count': len(data['files']),
            'total_lines': data['total_lines'],
            'directories': sorted(set(data['directories'])) if data.get('directories') else [],
            'files': sorted(data['files']),
            'depends_on': [],
            'imported_by': [],
            'used_by': data.get('used_by', []),
            'business_rules': data.get('business_rules', []),
            'has_fingerprint': data.get('has_fingerprint', False),
            'user_modified': data.get('user_modified', False)
        }
    
    log_success(f"Discovered {len(result_systems)} systems")
    
    # Save config if path provided
    if config_path:
        config = {
            'version': '3.1',
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
            'discovery_method': 'granular_v3.1_fixed'
        },
        'scan_data': {
            'root': root,
            'scanned_at': scan_data.get('scanned_at')
        }
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Elite System Identifier v3.1 - Fixed granular detection'
    )
    parser.add_argument('input', help='Scan results JSON file (or - for stdin)')
    parser.add_argument('output', nargs='?', help='Output JSON file (optional)')
    parser.add_argument('-i', '--interactive', action='store_true', 
                        help='Enable interactive mode to configure systems')
    parser.add_argument('-c', '--config', default=CONFIG_FILE,
                        help=f'Config file path (default: {CONFIG_FILE})')
    
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
