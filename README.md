# 🏗️ Codebase Architecture Mapper

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Quality](https://img.shields.io/badge/quality-Elite%20Grade-gold.svg)]()

**An elite AI skill that scans codebases, identifies systems, and generates architecture documentation.**

> 🏆 Built by [The Premiere Skill Factory](https://github.com/sufianmypa1203-oss)

## What This Does

- ✅ **Scans entire codebase** - Recursively analyzes all files
- ✅ **Identifies systems** - Groups files into logical systems (Flinks, Supabase, P2P, etc.)
- ✅ **Maps relationships** - Shows which systems depend on each other
- ✅ **Generates docs** - Creates organized `docs/architecture/` folder
- ✅ **Creates diagrams** - Mermaid visualizations of system relationships

## Quick Start

### Prerequisites

- Python 3.8+
- A git-based project to scan

### Installation

```bash
# Clone or copy to your skills directory
cp -r codebase-architecture-mapper ~/.claude/skills/
```

### Usage

```bash
# Navigate to your project
cd /path/to/your/project

# Run the full pipeline
python ~/.claude/skills/codebase-architecture-mapper/scripts/scan-codebase.py . > /tmp/scan.json
python ~/.claude/skills/codebase-architecture-mapper/scripts/identify-systems.py /tmp/scan.json > /tmp/systems.json
python ~/.claude/skills/codebase-architecture-mapper/scripts/generate-docs.py /tmp/systems.json docs/architecture
python ~/.claude/skills/codebase-architecture-mapper/scripts/generate-diagrams.py /tmp/systems.json docs/architecture/diagrams
```

**Or with Claude/Antigravity:**
```
You: "/map-architecture"
AI: *Scans codebase, identifies systems, generates docs*
```

## Output Structure

```
your-project/
└── docs/
    └── architecture/
        ├── OVERVIEW.md              # High-level system map
        ├── systems/
        │   ├── flinks.md            # Flinks documentation
        │   ├── supabase.md          # Database layer
        │   ├── p2p.md               # P2P loans
        │   ├── classifications.md   # Categories
        │   └── ...
        └── diagrams/
            ├── system-overview.mmd  # All systems
            ├── data-flow.mmd        # Data movement
            └── dependency-map.mmd   # Dependencies
```

## Systems It Detects

| System | Detection Pattern |
|--------|-------------------|
| Flinks | `/flinks/`, `FlinksConnect` |
| Supabase | `/supabase/`, `createClient` |
| P2P | `/p2p/`, `loan`, `person` |
| Classifications | `classification`, `category` |
| Auth | `/auth/`, `login`, `session` |
| Dashboard | `/dashboard/`, `widget` |
| Debts | `/debts/`, `credit-card` |
| Income | `/income/`, `salary` |
| API | `/api/`, `route` |
| UI | `/components/`, `button` |

## Scripts

| Script | Purpose |
|--------|---------|
| `scan-codebase.py` | Recursively scan files, extract imports |
| `identify-systems.py` | Group files into systems by patterns |
| `generate-docs.py` | Create markdown documentation |
| `generate-diagrams.py` | Generate Mermaid diagrams |

## Example Output

### OVERVIEW.md

```markdown
# Architecture Overview

## System Map
[Mermaid diagram showing all systems]

## Summary
| Total Systems | 8 |
| Total Files | 156 |
| Total Lines | 12,340 |

## Quick Links
- [Flinks](systems/flinks.md)
- [Supabase](systems/supabase.md)
- [P2P](systems/p2p.md)
```

### System Doc (p2p.md)

```markdown
# P2P System

## Overview
Peer-to-peer lending system

## Statistics
| Files | 18 |
| Lines | 2,340 |

## Dependencies
**Depends On:** Supabase, Auth
**Used By:** Dashboard
```

## License

MIT License - Free to use and modify!

---

**Ready to map your architecture? Run `/map-architecture`!** 🚀
