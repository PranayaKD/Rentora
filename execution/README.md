# Execution

This directory houses deterministic Python scripts and utilities executed by the Agent.

**Purpose**:
- "Layer 3" execution space where scripts do exactly what they're told.
- By keeping code execution deterministic, the Agent avoids probabilistic drift/hallucinations across multi-step processes.

**Usage**:
- The Agent reads the `.md` from `directives/`, decides how to achieve it, and calls scripts mapped in `execution/` to actually process data, hit external APIs, or manage files.
