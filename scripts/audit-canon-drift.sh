#!/bin/bash
# Canon Drift Audit Script
# Detects competing doctrine files in agent workspaces
# Usage: ./scripts/audit-canon-drift.sh [--verbose]

set -euo pipefail

CANON_ROOT="$HOME/.openclaw/workspace-elevate-flow"
MANIFEST="$CANON_ROOT/CANON-MANIFEST.md"
WORKSPACE_BASE="$HOME/.openclaw"

# Files that should NOT exist as standalone doctrine in workspaces
# (these should come from canon)
COMPETING_FILES=(
    "SOUL.md"
    "LANE.md"
    "ZERO-MISSION-CANON.md"
    "AGENTS.md"
    "RUNBOOK.md"
)

# Known stale files to check
STALE_PATTERNS=(
    "TASKS.md"
    "*-MISSION-*.md"
    "*-CANON.md"
)

VERBOSE=false
REPORT_ONLY=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose) VERBOSE=true; shift ;;
        --fix) REPORT_ONLY=false; shift ;;
        *) shift ;;
    esac
done

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

audit_workspace() {
    local workspace="$1"
    local workspace_path="$WORKSPACE_BASE/$workspace"
    
    echo "=== Checking $workspace ==="
    
    if [[ ! -d "$workspace_path" ]]; then
        echo "  [SKIP] Workspace not found: $workspace_path"
        return
    fi
    
    local drift_count=0
    
    # Check for competing doctrine files (non-canonical SOUL/LANE)
    for file in "${COMPETING_FILES[@]}"; do
        local file_path="$workspace_path/$file"
        
        if [[ -f "$file_path" ]]; then
            # Check if this file is managed by canon
            if grep -q "^.*|${workspace}|${file}$" "$MANIFEST" 2>/dev/null; then
                # This workspace should have this file - check if it matches canon
                local canon_path="$CANON_ROOT/$(grep "^.*|${workspace}|${file}$" "$MANIFEST" | cut -d'|' -f1)"
                
                if [[ -f "$canon_path" ]]; then
                    if diff -q "$file_path" "$canon_path" > /dev/null 2>&1; then
                        echo "  [OK] $file matches canon"
                    else
                        echo "  [DRIFT] $file differs from canon (run sync.sh)"
                        ((drift_count++))
                    fi
                fi
            else
                # This file is NOT supposed to be in this workspace
                echo "  [COMPETING] Unauthorized doctrine file: $file"
                ((drift_count++))
                
                if [[ "$REPORT_ONLY" == "false" ]]; then
                    local backup="$file_path.competing.$(date +%Y%m%d%H%M%S)"
                    mv "$file_path" "$backup"
                    echo "    -> Archived to: $backup"
                fi
            fi
        else
            # File missing - might need sync
            if grep -q "|$workspace/|" "$MANIFEST" 2>/dev/null; then
                local expected_from_manifest=$(grep "|${workspace}|" "$MANIFEST" | grep "/${file}$" | head -1)
                if [[ -n "$expected_from_manifest" ]]; then
                    echo "  [MISSING] $file (expected from canon, run sync.sh)"
                fi
            fi
        fi
    done
    
    # Check for stale task files
    for pattern in "${STALE_PATTERNS[@]}"; do
        local matches=($(find "$workspace_path" -maxdepth 2 -name "$pattern" -type f 2>/dev/null || true))
        
        if [[ ${#matches[@]} -gt 0 ]]; then
            for match in "${matches[@]}"; do
                local rel_path="${match#$workspace_path/}"
                # Skip if in canon directories
                if [[ "$rel_path" != agents/* ]] && [[ "$rel_path" != docs/* ]]; then
                    echo "  [STALE] $rel_path"
                    ((drift_count++))
                    
                    if [[ "$REPORT_ONLY" == "false" ]]; then
                        local backup="$match.stale.$(date +%Y%m%d%H%M%S)"
                        mv "$match" "$backup"
                        echo "    -> Archived to: $backup"
                    fi
                fi
            done
        fi
    done
    
    if [[ $drift_count -eq 0 ]]; then
        echo "  [CLEAN] No drift detected"
    else
        echo "  [TOTAL] $drift_count issue(s) found"
    fi
    
    echo ""
}

# Main audit logic
main() {
    echo "============================================"
    echo "Canon Drift Audit"
    echo "Canon Root: $CANON_ROOT"
    echo "Mode: $([ "$REPORT_ONLY" == "true" ] && echo "REPORT ONLY" || echo "FIX MODE")"
    echo "============================================"
    echo ""
    
    if [[ ! -f "$MANIFEST" ]]; then
        echo "ERROR: Manifest not found: $MANIFEST"
        exit 1
    fi
    
    # Audit each workspace
    for workspace in workspace-jj workspace-vlad workspace-pete workspace-ali workspace-coppa workspace-coach workspace-scout workspace-baby-vlad; do
        audit_workspace "$workspace"
    done
    
    echo "=== Audit Complete ==="
    echo "Run './scripts/sync.sh' to fix drift"
    echo "Run './scripts/audit-canon-drift.sh --fix' to auto-archive competing files"
}

main
