"""
GitHub Integration Routes
Endpoints de integracion con GitHub Issues
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import os

from .dependencies import (
    get_current_user,
    get_admin_user,
    CurrentUser,
    logger,
)

router = APIRouter(prefix="/api/github", tags=["GitHub"])


# ============================================
# PYDANTIC MODELS
# ============================================

class CreateIssueRequest(BaseModel):
    """Model for creating a GitHub issue."""
    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(..., min_length=1)
    labels: Optional[list] = None


class CommentRequest(BaseModel):
    """Model for adding a comment to an issue."""
    body: str = Field(..., min_length=1)


# ============================================
# GITHUB ENDPOINTS
# ============================================

@router.get("/issues")
async def list_github_issues(
    state: str = "open",
    labels: Optional[str] = None,
    per_page: int = 30,
    page: int = 1,
    user: CurrentUser = Depends(get_current_user)
):
    """
    List GitHub issues.
    Lista issues de GitHub.
    """
    try:
        from scripts.github_issues import GitHubIssues, GitHubAuthError, GitHubAPIError

        gh = GitHubIssues()
        issues = gh.list_issues(
            state=state,
            labels=labels,
            per_page=per_page,
            page=page
        )

        return {
            "status": "success",
            "count": len(issues),
            "page": page,
            "per_page": per_page,
            "issues": issues
        }
    except GitHubAuthError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "github_auth_error",
                "message": "GitHub token not configured or invalid"
            }
        )
    except GitHubAPIError as e:
        logger.error(f"GitHub API error: {e}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "github_api_error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error listing GitHub issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/issues")
async def create_github_issue(
    issue_data: CreateIssueRequest,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new GitHub issue.
    Crea un nuevo issue en GitHub.
    """
    try:
        from scripts.github_issues import GitHubIssues, GitHubAuthError, GitHubAPIError

        gh = GitHubIssues()
        issue = gh.create_issue(
            title=issue_data.title,
            body=issue_data.body,
            labels=issue_data.labels
        )

        logger.info(f"GitHub issue created by {user.username}: #{issue.get('number')}")

        return {
            "status": "success",
            "message": "Issue created successfully",
            "issue": issue
        }
    except GitHubAuthError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "github_auth_error",
                "message": "GitHub token not configured or invalid"
            }
        )
    except GitHubAPIError as e:
        logger.error(f"GitHub API error creating issue: {e}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "github_api_error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error creating GitHub issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues/{issue_number}")
async def get_github_issue(
    issue_number: int,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get a specific GitHub issue.
    Obtiene un issue especifico de GitHub.
    """
    try:
        from scripts.github_issues import GitHubIssues, GitHubAuthError, GitHubAPIError

        gh = GitHubIssues()
        issue = gh.get_issue(issue_number)

        return {
            "status": "success",
            "issue": issue
        }
    except GitHubAuthError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "github_auth_error",
                "message": "GitHub token not configured or invalid"
            }
        )
    except GitHubAPIError as e:
        logger.error(f"GitHub API error getting issue: {e}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "github_api_error",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/issues/{issue_number}/close")
async def close_github_issue(
    issue_number: int,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Close a GitHub issue.
    Cierra un issue de GitHub.
    """
    try:
        from scripts.github_issues import GitHubIssues, GitHubAuthError, GitHubAPIError

        gh = GitHubIssues()
        issue = gh.close_issue(issue_number)

        logger.info(f"GitHub issue #{issue_number} closed by {user.username}")

        return {
            "status": "success",
            "message": f"Issue #{issue_number} closed",
            "issue": issue
        }
    except GitHubAuthError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "github_auth_error",
                "message": "GitHub token not configured or invalid"
            }
        )
    except GitHubAPIError as e:
        logger.error(f"GitHub API error closing issue: {e}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "github_api_error",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/issues/{issue_number}/comments")
async def add_github_comment(
    issue_number: int,
    comment_data: CommentRequest,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Add a comment to a GitHub issue.
    Agrega un comentario a un issue de GitHub.
    """
    try:
        from scripts.github_issues import GitHubIssues, GitHubAuthError, GitHubAPIError

        gh = GitHubIssues()
        comment = gh.add_comment(issue_number, comment_data.body)

        logger.info(f"Comment added to issue #{issue_number} by {user.username}")

        return {
            "status": "success",
            "message": "Comment added successfully",
            "comment": comment
        }
    except GitHubAuthError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "github_auth_error",
                "message": "GitHub token not configured or invalid"
            }
        )
    except GitHubAPIError as e:
        logger.error(f"GitHub API error adding comment: {e}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "github_api_error",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-todos")
async def sync_todos_to_github(user: CurrentUser = Depends(get_admin_user)):
    """
    Sync TODOs from memory store to GitHub issues.
    Sincroniza TODOs del memory store a GitHub issues.

    Requires admin authentication.
    """
    try:
        from scripts.github_issues import GitHubIssues, GitHubAuthError, GitHubAPIError
        from pathlib import Path
        import json

        memory_path = Path(__file__).parent.parent / "agents" / "memory_store.json"
        if not memory_path.exists():
            return {
                "status": "success",
                "message": "No memory store found",
                "synced": 0
            }

        with open(memory_path, 'r', encoding='utf-8') as f:
            memory = json.load(f)

        todos = memory.get("todos", {})
        if not todos:
            return {
                "status": "success",
                "message": "No TODOs to sync",
                "synced": 0
            }

        gh = GitHubIssues()
        synced = 0
        errors = []

        for todo_id, todo in todos.items():
            if todo.get("completed"):
                continue

            try:
                title = f"[TODO] {todo.get('title', 'Untitled')}"
                body = f"""
## Description
{todo.get('description', 'No description')}

## Details
- **Priority**: {todo.get('priority', 'medium')}
- **Category**: {todo.get('category', 'general')}
- **Created**: {todo.get('created_at', 'Unknown')}
- **TODO ID**: {todo_id}

---
*Synced from YuKyuDATA memory store*
"""
                labels = [todo.get('category', 'general'), f"priority:{todo.get('priority', 'medium')}"]

                gh.create_issue(title=title, body=body, labels=labels)
                synced += 1
            except Exception as e:
                errors.append(f"{todo_id}: {str(e)}")

        logger.info(f"GitHub sync by {user.username}: {synced} issues created")

        return {
            "status": "success",
            "message": f"Synced {synced} TODOs to GitHub",
            "synced": synced,
            "errors": errors if errors else None
        }
    except GitHubAuthError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "github_auth_error",
                "message": "GitHub token not configured or invalid"
            }
        )
    except GitHubAPIError as e:
        logger.error(f"GitHub API error during sync: {e}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "github_api_error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during GitHub sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def github_integration_status():
    """
    Check GitHub integration status.
    Verifica el estado de la integracion con GitHub.
    """
    token_configured = bool(os.getenv("GITHUB_TOKEN"))
    repo_configured = os.getenv("GITHUB_REPO", "jokken79/YuKyuDATA-app1.0v")

    result = {
        "status": "configured" if token_configured else "not_configured",
        "token_configured": token_configured,
        "repository": repo_configured,
        "connection_test": None
    }

    if token_configured:
        try:
            from scripts.github_issues import GitHubIssues, GitHubAuthError, GitHubAPIError

            gh = GitHubIssues()
            gh.list_issues(per_page=1)
            result["connection_test"] = "success"
        except GitHubAuthError:
            result["connection_test"] = "auth_failed"
        except GitHubAPIError as e:
            result["connection_test"] = f"api_error: {str(e)}"
        except Exception as e:
            result["connection_test"] = f"error: {str(e)}"

    return result
