#!/usr/bin/env python3
"""
Project Status CLI - YuKyuDATA-app

Muestra el estado del proyecto en la consola.
Uso: python scripts/project-status.py

Opciones:
    --json          Salida en formato JSON
    --commits N     Mostrar N commits (default: 5)
    --no-color      Desactivar colores
"""

import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# Agregar directorio raiz al path para imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


# Disable colors if requested or not supported
NO_COLOR = '--no-color' in sys.argv or not sys.stdout.isatty()
if NO_COLOR:
    Colors.HEADER = Colors.BLUE = Colors.CYAN = ''
    Colors.GREEN = Colors.YELLOW = Colors.RED = ''
    Colors.BOLD = Colors.DIM = Colors.RESET = ''


def print_header(text: str):
    """Print a styled header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {text}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")


def print_section(text: str):
    """Print a section header"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}--- {text} ---{Colors.RESET}\n")


def print_kv(key: str, value: str, color: str = ''):
    """Print key-value pair"""
    print(f"  {Colors.DIM}{key}:{Colors.RESET} {color}{value}{Colors.RESET}")


def get_git_commits(limit: int = 5) -> list:
    """Get recent git commits"""
    try:
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--format=%H|%s|%an|%ad", "--date=iso"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0][:7],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3]
                        })
            return commits
    except Exception as e:
        print(f"{Colors.RED}Error getting commits: {e}{Colors.RESET}")
    return []


def get_commits_per_day(days: int = 7) -> dict:
    """Get commit count per day"""
    try:
        result = subprocess.run(
            ["git", "log", f"--since={days} days ago", "--format=%ad", "--date=short"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            dates = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            counts = Counter(dates)
            today = datetime.now().date()
            result_dict = {}
            for i in range(days - 1, -1, -1):
                day = (today - timedelta(days=i)).isoformat()
                result_dict[day] = counts.get(day, 0)
            return result_dict
    except Exception:
        pass
    return {}


def get_git_branch() -> str:
    """Get current git branch"""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def load_memory_store() -> dict:
    """Load memory_store.json"""
    memory_path = ROOT_DIR / "agents" / "memory_store.json"
    if memory_path.exists():
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_database_status() -> dict:
    """Get database counts - tries direct SQLite query if module import fails"""
    # First try direct SQLite query (faster and avoids import issues)
    db_path = ROOT_DIR / "yukyu.db"
    if db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            tables = {
                "employees": "SELECT COUNT(*) FROM employees",
                "genzai": "SELECT COUNT(*) FROM genzai",
                "ukeoi": "SELECT COUNT(*) FROM ukeoi",
                "staff": "SELECT COUNT(*) FROM staff",
                "leave_requests": "SELECT COUNT(*) FROM leave_requests",
                "usage_details": "SELECT COUNT(*) FROM yukyu_usage_details"
            }

            counts = {}
            for table, query in tables.items():
                try:
                    cursor.execute(query)
                    counts[table] = cursor.fetchone()[0]
                except:
                    counts[table] = 0

            conn.close()
            return counts
        except Exception as e:
            pass

    # Database not found or accessible
    return {"error": "Database file not found (yukyu.db)"}


def get_system_info() -> dict:
    """Get system resource info"""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": round(disk.percent, 1),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2)
        }
    except ImportError:
        return {"error": "psutil not installed"}
    except Exception as e:
        return {"error": str(e)}


def draw_bar(percent: float, width: int = 20, fill_char: str = '█', empty_char: str = '░') -> str:
    """Draw a progress bar"""
    filled = int(width * percent / 100)
    return fill_char * filled + empty_char * (width - filled)


def get_bar_color(percent: float) -> str:
    """Get color based on percentage"""
    if percent > 90:
        return Colors.RED
    elif percent > 70:
        return Colors.YELLOW
    else:
        return Colors.GREEN


def print_progress_bar(label: str, value: float, total: float, percent: float):
    """Print a labeled progress bar"""
    bar = draw_bar(percent)
    color = get_bar_color(percent)
    print(f"  {label:12} {color}{bar}{Colors.RESET} {value:.1f}/{total:.1f} GB ({percent:.0f}%)")


def main():
    # Parse arguments
    output_json = '--json' in sys.argv
    commits_limit = 5
    for i, arg in enumerate(sys.argv):
        if arg == '--commits' and i + 1 < len(sys.argv):
            try:
                commits_limit = int(sys.argv[i + 1])
            except ValueError:
                pass

    # Collect all data
    memory = load_memory_store()
    db_status = get_database_status()
    system_info = get_system_info()
    commits = get_git_commits(commits_limit)
    commits_per_day = get_commits_per_day(7)
    branch = get_git_branch()

    # Extract TODOs
    todos = []
    if memory.get("todos"):
        for todo_id, todo in memory["todos"].items():
            if not todo.get("completed"):
                todos.append({
                    "title": todo.get("title", ""),
                    "priority": todo.get("priority", "medium"),
                    "category": todo.get("category", "general")
                })

    # Extract features
    features = memory.get("features", [])

    # Extract errors
    errors = []
    if memory.get("errors"):
        for err_id, err in memory["errors"].items():
            if not err.get("verified"):
                errors.append({
                    "pattern": err.get("error_pattern", ""),
                    "solution": err.get("solution", "")
                })

    # JSON output
    if output_json:
        output = {
            "timestamp": datetime.now().isoformat(),
            "project": {
                "name": "YuKyuDATA-app",
                "version": "2.1.0",
                "branch": branch
            },
            "git": {
                "recent_commits": commits,
                "commits_per_day": commits_per_day
            },
            "database": db_status,
            "todos": todos,
            "features": features,
            "errors": errors,
            "system": system_info
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Console output
    print_header("YuKyuDATA Project Status")

    # Project info
    print_section("Project Info")
    print_kv("Name", "YuKyuDATA-app", Colors.CYAN)
    print_kv("Version", "2.1.0", Colors.GREEN)
    print_kv("Branch", branch, Colors.BLUE)
    print_kv("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Database status
    print_section("Database Status")
    if "error" in db_status:
        print_kv("Error", db_status["error"], Colors.RED)
    else:
        total = sum(db_status.values())
        print_kv("employees", str(db_status.get("employees", 0)))
        print_kv("genzai", str(db_status.get("genzai", 0)))
        print_kv("ukeoi", str(db_status.get("ukeoi", 0)))
        print_kv("staff", str(db_status.get("staff", 0)))
        print_kv("leave_requests", str(db_status.get("leave_requests", 0)))
        print_kv("usage_details", str(db_status.get("usage_details", 0)))
        print(f"\n  {Colors.BOLD}Total Records:{Colors.RESET} {Colors.CYAN}{total:,}{Colors.RESET}")

    # System info
    print_section("System Resources")
    if "error" in system_info:
        print_kv("Error", system_info["error"], Colors.RED)
    else:
        cpu = system_info.get("cpu_percent", 0)
        mem_pct = system_info.get("memory_percent", 0)
        disk_pct = system_info.get("disk_percent", 0)

        print(f"  {'CPU':12} {get_bar_color(cpu)}{draw_bar(cpu)}{Colors.RESET} {cpu:.0f}%")
        print_progress_bar("Memory",
                          system_info.get("memory_used_gb", 0),
                          system_info.get("memory_total_gb", 0),
                          mem_pct)
        print_progress_bar("Disk",
                          system_info.get("disk_used_gb", 0),
                          system_info.get("disk_total_gb", 0),
                          disk_pct)

    # Commits activity (ASCII chart)
    print_section("Commits Activity (Last 7 Days)")
    if commits_per_day:
        max_commits = max(commits_per_day.values()) if commits_per_day.values() else 1
        for date, count in commits_per_day.items():
            day_name = datetime.fromisoformat(date).strftime("%a %m/%d")
            bar_len = int(count / max_commits * 30) if max_commits > 0 else 0
            bar = '█' * bar_len
            color = Colors.CYAN if count > 0 else Colors.DIM
            print(f"  {day_name}  {color}{bar or '·'} {count}{Colors.RESET}")
    else:
        print(f"  {Colors.DIM}No commit data available{Colors.RESET}")

    # Recent commits
    print_section(f"Recent Commits ({len(commits)})")
    if commits:
        for commit in commits:
            hash_str = f"{Colors.YELLOW}{commit['hash']}{Colors.RESET}"
            msg = commit['message'][:50] + ('...' if len(commit['message']) > 50 else '')
            print(f"  {hash_str} {msg}")
            print(f"       {Colors.DIM}{commit['author']} - {commit['date'][:10]}{Colors.RESET}")
    else:
        print(f"  {Colors.DIM}No commits found{Colors.RESET}")

    # Pending TODOs
    print_section(f"Pending TODOs ({len(todos)})")
    if todos:
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        todos.sort(key=lambda t: priority_order.get(t["priority"], 1))

        for todo in todos:
            priority = todo['priority']
            if priority == 'high':
                prio_color = Colors.RED
                prio_icon = '!!!'
            elif priority == 'medium':
                prio_color = Colors.YELLOW
                prio_icon = '!!'
            else:
                prio_color = Colors.GREEN
                prio_icon = '!'

            print(f"  {prio_color}[{prio_icon}]{Colors.RESET} {todo['title']}")
            print(f"       {Colors.DIM}Category: {todo['category']}{Colors.RESET}")
    else:
        print(f"  {Colors.GREEN}All tasks completed!{Colors.RESET}")

    # Implemented Features
    print_section(f"Implemented Features ({len(features)})")
    if features:
        for feat in features:
            status_icon = f"{Colors.GREEN}✓{Colors.RESET}" if feat.get("status") == "completed" else f"{Colors.YELLOW}○{Colors.RESET}"
            print(f"  {status_icon} {feat.get('feature_name', 'Unknown')} {Colors.DIM}v{feat.get('version', '?')}{Colors.RESET}")
    else:
        print(f"  {Colors.DIM}No features tracked{Colors.RESET}")

    # Known Errors
    print_section(f"Unresolved Issues ({len(errors)})")
    if errors:
        for err in errors:
            print(f"  {Colors.RED}●{Colors.RESET} {err['pattern']}")
            print(f"    {Colors.DIM}Solution: {err['solution']}{Colors.RESET}")
    else:
        print(f"  {Colors.GREEN}No unresolved issues!{Colors.RESET}")

    # Footer
    print(f"\n{Colors.DIM}{'─' * 60}{Colors.RESET}")
    print(f"{Colors.DIM}Web Dashboard: http://localhost:8000/status{Colors.RESET}")
    print(f"{Colors.DIM}API Endpoint:  http://localhost:8000/api/project-status{Colors.RESET}")
    print()


if __name__ == "__main__":
    main()
