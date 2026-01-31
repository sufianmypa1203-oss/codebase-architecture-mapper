#!/usr/bin/env python3
"""
System Identifier - Phase 1
Groups files into logical systems based on patterns, directories, and imports.
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
def log_system(name): print(f"{Colors.MAGENTA}[SYSTEM]{Colors.NC} Found: {name}", file=sys.stderr)

# System detection patterns
# Format: { system_name: { 'dirs': [...], 'files': [...], 'imports': [...] } }
SYSTEM_PATTERNS = {
    'flinks': {
        'dirs': ['flinks', 'flink'],
        'files': ['flinks', 'bank-connect', 'account-sync'],
        'imports': ['flinks', '@flinks'],
        'description': 'Bank account integration via Flinks API'
    },
    'supabase': {
        'dirs': ['supabase', 'database', 'db'],
        'files': ['supabase', 'createClient', 'useSupabase'],
        'imports': ['@supabase', 'supabase-js', 'supabase'],
        'description': 'Database and authentication layer'
    },
    'p2p': {
        'dirs': ['p2p', 'peer-to-peer', 'loans'],
        'files': ['p2p', 'loan', 'person', 'lend', 'borrow'],
        'imports': ['p2p', 'loans'],
        'description': 'Peer-to-peer lending system'
    },
    'classifications': {
        'dirs': ['classifications', 'categories', 'classify'],
        'files': ['classification', 'category', 'classify', 'categorize'],
        'imports': ['classifications', 'categories'],
        'description': 'Transaction classification and categorization'
    },
    'auth': {
        'dirs': ['auth', 'authentication', 'login'],
        'files': ['auth', 'login', 'signup', 'session', 'token'],
        'imports': ['auth', 'next-auth', '@auth'],
        'description': 'User authentication and session management'
    },
    'dashboard': {
        'dirs': ['dashboard', 'home', 'main'],
        'files': ['dashboard', 'widget', 'overview'],
        'imports': ['dashboard'],
        'description': 'Main dashboard and overview UI'
    },
    'debts': {
        'dirs': ['debts', 'credit', 'loans'],
        'files': ['debt', 'credit-card', 'auto-loan', 'mortgage'],
        'imports': ['debts'],
        'description': 'Debt tracking and management'
    },
    'income': {
        'dirs': ['income', 'earnings', 'salary'],
        'files': ['income', 'salary', 'paycheck', 'earnings'],
        'imports': ['income'],
        'description': 'Income tracking and analysis'
    },
    'api': {
        'dirs': ['api', 'routes', 'endpoints'],
        'files': ['route', 'endpoint', 'handler'],
        'imports': ['api'],
        'description': 'API routes and handlers'
    },
    'ui': {
        'dirs': ['components', 'ui', 'shared'],
        'files': ['button', 'modal', 'card', 'input', 'form'],
        'imports': ['@/components', '@/ui'],
        'description': 'Shared UI components'
    },
    'utils': {
        'dirs': ['utils', 'helpers', 'lib'],
        'files': ['utils', 'helpers', 'format', 'parse'],
        'imports': ['@/utils', '@/lib'],
        'description': 'Utility functions and helpers'
    }
}

def identify_systems(scan_data: dict) -> dict:
    """Identify systems from scanned codebase data."""
    
    files = scan_data.get('files', [])
    systems = defaultdict(lambda: {
        'files': [],
        'file_count': 0,
        'total_lines': 0,
        'directories': set(),
        'imports_from': set(),
        'imported_by': set()
    })
    
    log_info(f"Analyzing {len(files)} files for system patterns...")
    
    # First pass: assign files to systems
    for file in files:
        path = file['path'].lower()
        directory = file['directory'].lower()
        name = file['name'].lower()
        imports = [i.lower() for i in file.get('imports', [])]
        
        assigned_systems = set()
        
        for system_name, patterns in SYSTEM_PATTERNS.items():
            score = 0
            
            # Check directory patterns
            for dir_pattern in patterns['dirs']:
                if dir_pattern in directory:
                    score += 3  # Strong signal
            
            # Check filename patterns
            for file_pattern in patterns['files']:
                if file_pattern in name:
                    score += 2
            
            # Check import patterns
            for import_pattern in patterns['imports']:
                for imp in imports:
                    if import_pattern in imp:
                        score += 1
            
            if score >= 2:  # Threshold for assignment
                assigned_systems.add(system_name)
        
        # Default to 'other' if no system matched
        if not assigned_systems:
            assigned_systems.add('other')
        
        # Assign file to all matched systems
        for system in assigned_systems:
            systems[system]['files'].append(file['path'])
            systems[system]['file_count'] += 1
            systems[system]['total_lines'] += file.get('lines', 0)
            systems[system]['directories'].add(file['directory'])
            
            # Track imports for dependency mapping
            for imp in file.get('imports', []):
                systems[system]['imports_from'].add(imp)
    
    # Second pass: map system relationships
    log_info("Mapping system relationships...")
    system_names = list(systems.keys())
    
    for system_name, system_data in systems.items():
        for imp in system_data['imports_from']:
            imp_lower = imp.lower()
            for other_system in system_names:
                if other_system != system_name:
                    patterns = SYSTEM_PATTERNS.get(other_system, {})
                    for pattern in patterns.get('dirs', []) + patterns.get('imports', []):
                        if pattern in imp_lower:
                            system_data['imported_by'].add(other_system)
    
    # Convert sets to lists and add descriptions
    result = {}
    for system_name, data in systems.items():
        if data['file_count'] > 0:
            log_system(f"{system_name} ({data['file_count']} files)")
            result[system_name] = {
                'name': system_name.title().replace('_', ' '),
                'description': SYSTEM_PATTERNS.get(system_name, {}).get('description', 'Custom system'),
                'file_count': data['file_count'],
                'total_lines': data['total_lines'],
                'directories': sorted(data['directories']),
                'files': sorted(data['files']),
                'depends_on': sorted(data['imported_by']),
                'imported_by': []  # Will be filled in cross-reference
            }
    
    # Cross-reference: fill in imported_by
    for system_name, data in result.items():
        for dep in data['depends_on']:
            if dep in result:
                result[dep]['imported_by'].append(system_name)
    
    log_success(f"Identified {len(result)} systems")
    
    return {
        'systems': result,
        'summary': {
            'total_systems': len(result),
            'total_files': sum(s['file_count'] for s in result.values()),
            'total_lines': sum(s['total_lines'] for s in result.values())
        },
        'scan_data': {
            'root': scan_data.get('root'),
            'scanned_at': scan_data.get('scanned_at')
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: identify-systems.py <scan-results.json> [output.json]")
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
