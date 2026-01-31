#!/usr/bin/env python3
"""
Universal System Identifier v2.0
Groups files into logical systems using AUTO-DISCOVERY - no hardcoded patterns.
Works on ANY codebase: React, Vue, Python, Go, anything.
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict

# ANSI Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'

def log_info(msg): print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}", file=sys.stderr)
def log_success(msg): print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}", file=sys.stderr)
def log_warn(msg): print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}", file=sys.stderr)
def log_system(name, count): print(f"{Colors.MAGENTA}[SYSTEM]{Colors.NC} {name} ({count} files)", file=sys.stderr)

# Common root directories to skip when determining system names
ROOT_DIRS = {'src', 'app', 'lib', 'packages', 'apps', 'modules', 'core', 'source', 'main'}

# Directories that should be grouped as "utils" or "shared"
UTILITY_DIRS = {'utils', 'helpers', 'lib', 'common', 'shared', 'utilities'}

# Directories that should be grouped as "ui" or "components"
UI_DIRS = {'components', 'ui', 'views', 'widgets', 'elements'}

# Minimum files to be considered a "real" system
MIN_SYSTEM_FILES = 2

# Maximum systems before merging smallest into "other"
MAX_SYSTEMS = 12


def get_system_name(file_path: str) -> str:
    """
    Extract a meaningful system name from a file path.
    
    Examples:
        src/auth/login.ts → "auth"
        src/features/dashboard/index.tsx → "dashboard"
        packages/web/src/components/Button.tsx → "components"
        app/(dashboard)/page.tsx → "dashboard"
        components/ui/Button.tsx → "ui"
    """
    parts = Path(file_path).parts
    
    if len(parts) <= 1:
        return "root"
    
    # Find the first meaningful directory
    for i, part in enumerate(parts):
        # Skip root directories
        if part.lower() in ROOT_DIRS:
            continue
        
        # Skip hidden directories
        if part.startswith('.'):
            continue
        
        # Handle Next.js route groups: (dashboard) → dashboard
        if part.startswith('(') and part.endswith(')'):
            return part[1:-1].lower()
        
        # Skip __tests__, __mocks__, etc.
        if part.startswith('__') and part.endswith('__'):
            continue
        
        # Found a meaningful directory
        return part.lower()
    
    # Fallback to first non-root directory or filename prefix
    if len(parts) >= 2:
        return parts[0].lower()
    
    return "root"


def normalize_system_name(name: str) -> str:
    """Normalize system names for consistency."""
    name = name.lower().strip()
    
    # Map common variations to standard names
    if name in UTILITY_DIRS:
        return "utils"
    if name in UI_DIRS:
        return "components"
    if name in {'api', 'routes', 'endpoints', 'handlers'}:
        return "api"
    if name in {'tests', 'test', '__tests__', 'spec', 'specs'}:
        return "tests"
    if name in {'types', 'interfaces', 'models', 'schemas'}:
        return "types"
    if name in {'config', 'configs', 'configuration', 'settings'}:
        return "config"
    if name in {'assets', 'static', 'public', 'images'}:
        return "assets"
    if name in {'styles', 'css', 'scss', 'stylesheets'}:
        return "styles"
    
    return name


def generate_description(system_name: str, file_count: int, directories: list) -> str:
    """Generate a human-readable description for a system."""
    
    # Get the most common directory
    if directories:
        main_dir = max(set(directories), key=directories.count)
    else:
        main_dir = system_name
    
    # Generate description based on name patterns
    descriptions = {
        'api': 'API routes and request handlers',
        'auth': 'Authentication and authorization',
        'components': 'Reusable UI components',
        'utils': 'Utility functions and helpers',
        'config': 'Configuration and environment settings',
        'types': 'Type definitions and interfaces',
        'tests': 'Test files and fixtures',
        'styles': 'Stylesheets and CSS modules',
        'assets': 'Static assets and media files',
        'root': 'Root-level project files',
    }
    
    if system_name in descriptions:
        return descriptions[system_name]
    
    return f"Auto-detected from /{main_dir}/ ({file_count} files)"


def identify_systems(scan_data: dict) -> dict:
    """
    Identify systems from scanned codebase using AUTO-DISCOVERY.
    No hardcoded patterns - works on any codebase.
    """
    
    files = scan_data.get('files', [])
    log_info(f"Analyzing {len(files)} files for system patterns...")
    
    # Step 1: Group files by auto-detected system name
    raw_systems = defaultdict(lambda: {
        'files': [],
        'directories': [],
        'total_lines': 0,
        'imports_from': set()
    })
    
    for file in files:
        path = file['path']
        system_name = get_system_name(path)
        system_name = normalize_system_name(system_name)
        
        raw_systems[system_name]['files'].append(path)
        raw_systems[system_name]['directories'].append(file.get('directory', '.'))
        raw_systems[system_name]['total_lines'] += file.get('lines', 0)
        
        # Track imports for relationship mapping
        for imp in file.get('imports', []):
            raw_systems[system_name]['imports_from'].add(imp)
    
    # Step 2: Merge small systems into "other"
    systems = {}
    other_files = []
    other_lines = 0
    other_dirs = []
    
    for name, data in sorted(raw_systems.items(), key=lambda x: -len(x[1]['files'])):
        if len(data['files']) < MIN_SYSTEM_FILES:
            other_files.extend(data['files'])
            other_lines += data['total_lines']
            other_dirs.extend(data['directories'])
        elif len(systems) >= MAX_SYSTEMS:
            other_files.extend(data['files'])
            other_lines += data['total_lines']
            other_dirs.extend(data['directories'])
        else:
            systems[name] = data
    
    # Add "other" system if there are orphan files
    if other_files:
        systems['other'] = {
            'files': other_files,
            'directories': other_dirs,
            'total_lines': other_lines,
            'imports_from': set()
        }
    
    # Step 3: Build relationship map from imports
    system_names = set(systems.keys())
    
    for sys_name, data in systems.items():
        data['depends_on'] = set()
        for imp in data['imports_from']:
            imp_lower = imp.lower()
            for other_sys in system_names:
                if other_sys != sys_name and other_sys in imp_lower:
                    data['depends_on'].add(other_sys)
    
    # Step 4: Build final result with metadata
    result = {}
    for name, data in systems.items():
        file_count = len(data['files'])
        log_system(name.title(), file_count)
        
        result[name] = {
            'name': name.title().replace('_', ' '),
            'description': generate_description(name, file_count, data['directories']),
            'file_count': file_count,
            'total_lines': data['total_lines'],
            'directories': sorted(set(data['directories'])),
            'files': sorted(data['files']),
            'depends_on': sorted(data.get('depends_on', set())),
            'imported_by': []
        }
    
    # Step 5: Cross-reference imported_by
    for sys_name, data in result.items():
        for dep in data['depends_on']:
            if dep in result:
                result[dep]['imported_by'].append(sys_name)
    
    log_success(f"Discovered {len(result)} systems automatically")
    
    return {
        'systems': result,
        'summary': {
            'total_systems': len(result),
            'total_files': sum(s['file_count'] for s in result.values()),
            'total_lines': sum(s['total_lines'] for s in result.values()),
            'discovery_method': 'auto'
        },
        'scan_data': {
            'root': scan_data.get('root'),
            'scanned_at': scan_data.get('scanned_at')
        }
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: identify-systems.py <scan-results.json> [output.json]")
        print("\nUniversal System Discovery - works on ANY codebase!")
        print("\nExample:")
        print("  python scan-codebase.py /path/to/project | python identify-systems.py -")
        print("  python identify-systems.py scan-results.json systems.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Read input
    if input_file == '-':
        scan_data = json.load(sys.stdin)
    else:
        with open(input_file, 'r') as f:
            scan_data = json.load(f)
    
    # Identify systems
    result = identify_systems(scan_data)
    
    # Output
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        log_success(f"Results saved to: {output_file}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
