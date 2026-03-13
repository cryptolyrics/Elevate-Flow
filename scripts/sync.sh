#!/bin/bash
# Canon Sync Script
# Syncs canon doctrine from workspace-elevate-flow to agent workspaces
# Usage: ./scripts/sync.sh [--dry-run] [--verbose]

set -euo pipefail

CANON_ROOT="$HOME/.openclaw/workspace-elevate-flow"
MANIFEST="$CANON_ROOT/CANON-MANIFEST.md"
WORKSPACE_BASE="$HOME/.openclaw"
LOG_FILE="$CANON_ROOT/logs/sync-$(date +%Y%m%d-%H%M%S).log"

DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

sync_file() {
    local source="$1"
    local target_workspace="$2"
    local target_path="$3"
    
    local source_file="$CANON_ROOT/$source"
    local target_dir="$WORKSPACE_BASE/$target_workspace"
    local target_file="$target_dir/$target_path"
    
    if [[ ! -f "$source_file" ]]; then
        log "ERROR: Source file not found: $source_file"
        return 1
    fi
    
    # Create target directory if needed
    if [[ ! -d "$(dirname "$target_file")" ]]; then
        mkdir -p "$(dirname "$target_file")"
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would sync: $source -> $target_workspace/$target_path"
        return 0
    fi
    
    # Check if target exists and is different
    if [[ -f "$target_file" ]]; then
        if ! diff -q "$source_file" "$target_file" > /dev/null 2>&1; then
            # Backup existing file
            local backup="$target_file.backup.$(date +%Y%m%d%H%M%S)"
            cp "$target_file" "$backup"
            log "Backed up: $target_workspace/$target_path -> $backup"
        fi
    fi
    
    # Copy the file
    cp "$source_file" "$target_file"
    log "Synced: $source -> $target_workspace/$target_path"
}

# Main sync logic
main() {
    log "=== Canon Sync Started ==="
    log "Canon root: $CANON_ROOT"
    log "Manifest: $MANIFEST"
    
    if [[ ! -f "$MANIFEST" ]]; then
        log "ERROR: Manifest not found: $MANIFEST"
        exit 1
    fi
    
    # Create logs directory
    mkdir -p "$CANON_ROOT/logs"
    
    local sync_count=0
    local error_count=0
    
    # Read manifest (skip comments and empty lines)
    while IFS='|' read -r source target _; do
        # Skip comments and empty lines
        [[ "$source" =~ ^# ]] && continue
        [[ -z "$source" ]] && continue
        
        # Handle ALL - sync to all workspaces
        if [[ "$target" == "ALL" ]]; then
            for workspace in workspace-jj workspace-vlad workspace-pete workspace-ali workspace-coppa workspace-coach workspace-scout workspace-baby-vlad; do
                if sync_file "$source" "$workspace" "$(basename "$source")"; then
                    ((sync_count++))
                else
                    ((error_count++))
                fi
            done
        else
            if sync_file "$source" "$target" "$(basename "$source")"; then
                ((sync_count++))
            else
                ((error_count++))
            fi
        fi
    done < <(grep -v '^#' "$MANIFEST" | grep -v '^$')
    
    log "=== Canon Sync Complete ==="
    log "Files synced: $sync_count"
    log "Errors: $error_count"
    
    if [[ $error_count -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
