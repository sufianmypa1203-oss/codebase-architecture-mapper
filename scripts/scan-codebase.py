#!/usr/bin/env python3
"""
Codebase Scanner - Phase 1
Recursively scans a codebase and builds a complete file tree with metadata.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# ANSI Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def log_info(msg): print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}", file=sys.stderr)
def log_success(msg): print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}", file=sys.stderr)
def log_warn(msg): print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}", file=sys.stderr)
def log_error(msg): print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}", file=sys.stderr)

# Directories to skip
SKIP_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', '.nuxt',
    'coverage', '__pycache__', '.venv', 'venv', '.cache',
    '.turbo', '.vercel', '.output', 'out', '.svelte-kit'
}

# File extensions to analyze
CODE_EXTENSIONS = {
    '.ts', '.tsx', '.js', '.jsx', '.vue', '.svelte',
    '.py', '.go', '.java', '.rb', '.php',
    '.css', '.scss', '.less', '.sass',
    '.json', '.yaml', '.yml', '.toml',
    '.md', '.mdx'
}

def scan_directory(root_path: str) -> dict:
    """Scan a directory and return file tree with metadata."""
    
    root = Path(root_path).resolve()
    if not root.exists():
        log_error(f"Directory not found: {root_path}")
        sys.exit(1)
    
    log_info(f"Scanning: {root}")
    
    files = []
    directories = []
    total_lines = 0
    file_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip unwanted directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir != '.':
            directories.append(rel_dir)
        
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext not in CODE_EXTENSIONS:
                continue
            
            file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(file_path, root)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    total_lines += lines
                    
                    # Extract imports for later system detection
                    imports = extract_imports(content, ext)
                    
                    files.append({
                        'path': rel_path,
                        'name': filename,
                        'extension': ext,
                        'directory': os.path.dirname(rel_path) or '.',
                        'lines': lines,
                        'imports': imports
                    })
                    file_count += 1
                    
            except (UnicodeDecodeError, PermissionError):
                pass  # Skip binary or unreadable files
    
    log_success(f"Scanned {file_count} files, {len(directories)} directories")
    log_info(f"Total lines of code: {total_lines:,}")
    
    return {
        'root': str(root),
        'scanned_at': datetime.now().isoformat(),
        'summary': {
            'total_files': file_count,
            'total_directories': len(directories),
            'total_lines': total_lines
        },
        'files': files,
        'directories': sorted(set(directories))
    }

def extract_imports(content: str, ext: str) -> list:
    """Extract import statements from file content."""
    import re
    imports = []
    
    if ext in {'.ts', '.tsx', '.js', '.jsx'}:
        # ES6 imports
        patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s*\([\'"]([^\'"]+)[\'"]\)',
            r'require\([\'"]([^\'"]+)[\'"]\)'
        ]
        for pattern in patterns:
            imports.extend(re.findall(pattern, content))
    
    elif ext == '.vue':
        # Vue imports (same as JS/TS)
        patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s*\([\'"]([^\'"]+)[\'"]\)'
        ]
        for pattern in patterns:
            imports.extend(re.findall(pattern, content))
    
    elif ext == '.py':
        # Python imports
        patterns = [
            r'^import\s+(\S+)',
            r'^from\s+(\S+)\s+import'
        ]
        for pattern in patterns:
            imports.extend(re.findall(pattern, content, re.MULTILINE))
    
    return list(set(imports))

def main():
    if len(sys.argv) < 2:
        print("Usage: scan-codebase.py <directory> [output.json]")
        print("\nExample:")
        print("  scan-codebase.py /path/to/project")
        print("  scan-codebase.py . scan-results.json")
        sys.exit(1)
    
    directory = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = scan_directory(directory)
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        log_success(f"Results saved to: {output_file}")
    else:
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
