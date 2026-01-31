# 🏗️ Codebase Architecture Mapper

[![Version](https://img.shields.io/badge/version-3.3.0-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Quality](https://img.shields.io/badge/quality-Elite%20Grade-gold.svg)]()

**An elite AI skill that scans codebases, identifies systems, and generates architecture documentation.**

> 🏆 Built by [The Premiere Skill Factory](https://github.com/sufianmypa1203-oss)

## What This Does

- ✅ **Granular Detection** - Bottom-up discovery finds REAL subsystems in deep folders
- ✅ **Interactive Mode** - Asks you for descriptions and business rules
- ✅ **Persistent Config** - Saves your answers to `architecture-config.json`
- ✅ **Auto-discovery** - Works on ANY codebase without configuration
- ✅ **Mermaid Diagrams** - Visual system maps, data flow, dependencies
- ✅ **Elite Synergy** - Integrates with [Smart PR Docs](https://github.com/sufianmypa1203-oss/smart-pr-docs) for system-aware PRs

## Quick Start

### Prerequisites

- Python 3.8+
- A git-based project to scan

### Interactive Mode (Recommended)

```bash
# Scan your project with interactive prompts
python scan-codebase.py /path/to/project > scan.json
python identify-systems.py scan.json --interactive
```

This will ask you for each system:
- What does it do?
- Who uses it?
- Key business rules?

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

## How It Works - Universal Auto-Discovery

**No configuration needed!** The tool automatically discovers systems from your actual codebase structure.

### Detection Logic

1. **Directory-Based**: Files in `src/auth/` → "Auth" system
2. **Next.js Groups**: Files in `app/(dashboard)/` → "Dashboard" system  
3. **Monorepo Support**: Files in `packages/web/` → "Web" system
4. **Smart Merging**: Small folders (<2 files) merge into "Other"

### Example Discovery

```
Your Project:
src/
├── auth/           → "Auth" system (8 files)
├── payments/       → "Payments" system (12 files)
├── components/     → "Components" system (45 files)
└── utils/          → "Utils" system (15 files)
```

**Works on ANY codebase**: React, Vue, Angular, Python, Go, Rust, anything!

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

## 🤝 Elite Synergy: Architecture + PRs

This skill is designed to work in perfect harmony with **[Smart PR Docs](https://github.com/sufianmypa1203-oss/smart-pr-docs)**.

When both are installed:
1. **Mapper** provides the "Global Vision" (Systems & Business Rules).
2. **PR Docs** reads that vision and automatically enriches your PR reports with architectural context.

**The result?** Your PRs don't just show code—they show **systemic impact**.

## License

MIT License - Free to use and modify!

---

**Ready to map your architecture? Run `/map-architecture`!** 🚀
