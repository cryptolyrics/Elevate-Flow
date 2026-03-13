#!/usr/bin/env python3
"""Canon Task Resolver - Single source of truth for tasks.

This module provides a canonical interface for reading task state.
ALL task operations must go through this resolver.

Usage:
    from canon_tasks import get_task, list_tasks, get_task_state
    
    task = get_task("task-id")
    tasks = list_tasks(status="OPEN")
    state = get_task_state("task-id")
"""

import json
from pathlib import Path
from typing import Literal

# Canonical task root - MUST use this
CANON_TASK_ROOT = Path.home() / ".openclaw" / "workspace-elevate-flow" / "tasks"

TaskStatus = Literal["QUEUED", "OPEN", "IN_PROGRESS", "REVIEW", "DONE", "CLOSED"]


def _load_task(task_id: str) -> dict | None:
    """Load a single task by ID."""
    task_file = CANON_TASK_ROOT / "open" / f"{task_id}.json"
    if not task_file.exists():
        # Try closed
        task_file = CANON_TASK_ROOT / "closed" / f"{task_id}.json"
    if not task_file.exists():
        return None
    return json.loads(task_file.read_text())


def get_task(task_id: str) -> dict:
    """Get a single task by ID.
    
    Returns task dict or raises FileNotFoundError if not found.
    """
    task = _load_task(task_id)
    if task is None:
        raise FileNotFoundError(f"Task not found: {task_id}")
    return task


def list_tasks(status: TaskStatus | None = None) -> list[dict]:
    """List all tasks, optionally filtered by status.
    
    Args:
        status: Optional filter by status (QUEUED, OPEN, IN_PROGRESS, etc.)
    
    Returns:
        List of task dicts
    """
    tasks = []
    
    # Check open tasks
    open_dir = CANON_TASK_ROOT / "open"
    if open_dir.exists():
        for f in open_dir.glob("*.json"):
            task = json.loads(f.read_text())
            if status is None or task.get("status") == status:
                tasks.append(task)
    
    # Check closed tasks
    closed_dir = CANON_TASK_ROOT / "closed"
    if closed_dir.exists():
        for f in closed_dir.glob("*.json"):
            task = json.loads(f.read_text())
            if status is None or task.get("status") == status:
                tasks.append(task)
    
    return tasks


def get_task_state(task_id: str) -> dict:
    """Get essential state for a task (id, status, owner, reviewer).
    
    Returns minimal dict for quick status checks.
    Raises FileNotFoundError if task not found.
    """
    task = get_task(task_id)
    return {
        "task_id": task.get("task_id"),
        "status": task.get("status"),
        "owner_agent": task.get("owner_agent"),
        "reviewer_agent": task.get("reviewer_agent"),
        "title": task.get("title"),
    }


def validate_canon_tasks() -> dict:
    """Validate canonical task root is accessible.
    
    Returns dict with validation result.
    """
    if not CANON_TASK_ROOT.exists():
        return {
            "valid": False,
            "error": f"Canon task root not found: {CANON_TASK_ROOT}",
            "canonical_root": str(CANON_TASK_ROOT),
        }
    
    if not (CANON_TASK_ROOT / "open").exists():
        return {
            "valid": False,
            "error": "Canon tasks/open directory missing",
            "canonical_root": str(CANON_TASK_ROOT),
        }
    
    return {
        "valid": True,
        "canonical_root": str(CANON_TASK_ROOT),
        "task_count": len(list_tasks()),
    }


# Default: fail if canonical tasks unavailable
if not CANON_TASK_ROOT.exists():
    raise RuntimeError(
        f"CRITICAL: Canon task root not accessible: {CANON_TASK_ROOT}. "
        "Task operations cannot proceed."
    )
