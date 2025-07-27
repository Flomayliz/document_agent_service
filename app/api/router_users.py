"""
User management API router for administrative use.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from app.models.user_models import User
from app.db.user_handler import get_user_service
from app.api.router_agent import get_current_user

router = APIRouter(prefix="/users", tags=["user-management"])
logger = logging.getLogger(__name__)


class CreateUserRequest(BaseModel):
    """Request model for creating a new user."""

    email: EmailStr
    name: str
    token_validity_hours: int = 24


class CreateUserResponse(BaseModel):
    """Response model for user creation."""

    user_id: str
    email: str
    name: str
    token: str
    expires_at: str
    message: str


class UpdateUserRequest(BaseModel):
    """Request model for updating user information."""

    name: Optional[str] = None


@router.post("/", response_model=CreateUserResponse)
async def create_user(request: CreateUserRequest):
    """Create a new user account."""
    try:
        user_service = get_user_service()

        # Check if user already exists
        existing_user = await user_service.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        # Create new user
        user = await user_service.create_user(
            email=request.email,
            name=request.name,
            token_validity_hours=request.token_validity_hours,
        )

        logger.info(f"Created new user: {user.email}")

        return CreateUserResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            token=user.access_token.token,
            expires_at=user.access_token.expires_at.isoformat(),
            message="User created successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.get("/me")
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile information."""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "token_valid": current_user.is_token_valid(),
        "token_expires": current_user.access_token.expires_at,
        "history_count": len(current_user.history),
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }


@router.put("/me")
async def update_current_user(
    request: UpdateUserRequest, current_user: User = Depends(get_current_user)
):
    """Update current user's profile information."""
    try:
        user_service = get_user_service()

        updated_user = await user_service.update_user_info(
            user_id=current_user.id, name=request.name
        )

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Updated user profile: {updated_user.email}")

        return {
            "message": "Profile updated successfully",
            "user": {
                "user_id": updated_user.id,
                "email": updated_user.email,
                "name": updated_user.name,
                "updated_at": updated_user.updated_at,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


@router.get("/me/history")
async def get_current_user_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(30, ge=1, le=30, description="Number of recent Q/A pairs to return"),
):
    """Get current user's Q/A history."""
    try:
        user_service = get_user_service()
        history = await user_service.get_user_history(current_user.id)

        if history is None:
            raise HTTPException(status_code=404, detail="User history not found")

        # Return the most recent 'limit' items
        recent_history = history[-limit:] if len(history) > limit else history

        return {
            "history": [
                {
                    "id": qa.id,
                    "question": qa.question,
                    "answer": qa.answer,
                    "timestamp": qa.timestamp,
                }
                for qa in recent_history
            ],
            "total_count": len(history),
            "returned_count": len(recent_history),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user history: {str(e)}")


@router.post("/me/refresh-token")
async def refresh_current_user_token(
    current_user: User = Depends(get_current_user),
    token_validity_hours: int = Query(
        24, ge=1, le=168, description="Token validity in hours (max 7 days)"
    ),
):
    """Refresh current user's access token."""
    try:
        user_service = get_user_service()
        updated_user = await user_service.refresh_token(current_user.id, token_validity_hours)

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Refreshed token for user: {updated_user.email}")

        return {
            "message": "Token refreshed successfully",
            "new_token": updated_user.access_token.token,
            "expires_at": updated_user.access_token.expires_at,
            "valid_for_hours": token_validity_hours,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error refreshing token: {str(e)}")


@router.delete("/me")
async def delete_current_user(current_user: User = Depends(get_current_user)):
    """Delete current user's account."""
    try:
        user_service = get_user_service()
        deleted = await user_service.delete_user(current_user.id)

        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Deleted user account: {current_user.email}")

        return {"message": "User account deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


@router.post("/validate-token")
async def validate_token(current_user: User = Depends(get_current_user)):
    """Validate the provided token and return user information."""
    return {
        "valid": True,
        "user": {
            "user_id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "token_expires": current_user.access_token.expires_at,
        },
        "message": "Token is valid",
    }


# Admin-only endpoints (no authentication required since this is on admin server)


@router.get("/list")
async def list_all_users(
    limit: int = Query(50, ge=1, le=100, description="Number of users to return"),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
):
    """List all users (admin only endpoint)."""
    try:
        user_service = get_user_service()
        users = await user_service.list_users(limit=limit, skip=skip)

        logger.info(f"Admin requested user list: returned {len(users)} users")

        return {
            "users": [
                {
                    "user_id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "token_valid": user.is_token_valid(),
                    "token_expires": user.access_token.expires_at,
                    "history_count": len(user.history),
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                }
                for user in users
            ],
            "count": len(users),
            "limit": limit,
            "skip": skip,
        }

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")


@router.get("/{user_id}")
async def get_user_by_id_admin(user_id: str):
    """Get any user by ID (admin only)."""
    try:
        user_service = get_user_service()
        user = await user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Admin accessed user: {user.email}")

        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "token_valid": user.is_token_valid(),
            "token_expires": user.access_token.expires_at,
            "history_count": len(user.history),
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")


@router.get("/{user_id}/history")
async def get_user_history_admin(
    user_id: str,
    limit: int = Query(30, ge=1, le=100, description="Number of recent Q/A pairs to return"),
):
    """Get any user's Q/A history (admin only)."""
    try:
        user_service = get_user_service()
        history = await user_service.get_user_history(user_id)

        if history is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Return the most recent 'limit' items
        recent_history = history[-limit:] if len(history) > limit else history

        logger.info(f"Admin accessed history for user {user_id}: {len(recent_history)} items")

        return {
            "user_id": user_id,
            "history": [
                {
                    "id": qa.id,
                    "question": qa.question,
                    "answer": qa.answer,
                    "timestamp": qa.timestamp,
                }
                for qa in recent_history
            ],
            "total_count": len(history),
            "returned_count": len(recent_history),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user history {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user history: {str(e)}")


@router.delete("/{user_id}")
async def delete_user_admin(user_id: str):
    """Delete any user account (admin only)."""
    try:
        user_service = get_user_service()

        # Get user info for logging before deletion
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete the user
        deleted = await user_service.delete_user(user_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")

        logger.warning(f"Admin deleted user account: {user.email} (ID: {user_id})")

        return {
            "message": "User account deleted successfully",
            "deleted_user": {"user_id": user_id, "email": user.email, "name": user.name},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


@router.post("/{user_id}/refresh-token")
async def refresh_user_token_admin(
    user_id: str,
    token_validity_hours: int = Query(
        24, ge=1, le=168, description="Token validity in hours (max 7 days)"
    ),
):
    """Refresh any user's access token (admin only)."""
    try:
        user_service = get_user_service()
        updated_user = await user_service.refresh_token(user_id, token_validity_hours)

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Admin refreshed token for user: {updated_user.email}")

        return {
            "message": "Token refreshed successfully",
            "user_id": user_id,
            "email": updated_user.email,
            "new_token": updated_user.access_token.token,
            "expires_at": updated_user.access_token.expires_at,
            "valid_for_hours": token_validity_hours,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error refreshing token: {str(e)}")


@router.get("/by-email/{email}")
async def get_user_by_email_admin(email: str):
    """Get any user by email (admin only)."""
    try:
        user_service = get_user_service()
        user = await user_service.get_user_by_email(email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Admin accessed user by email: {user.email}")

        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "token_valid": user.is_token_valid(),
            "token_expires": user.access_token.expires_at,
            "history_count": len(user.history),
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")


class AddQARequest(BaseModel):
    """Request model for adding Q/A to user history."""

    question: str
    answer: str


@router.post("/{user_id}/add-qa")
async def add_qa_to_user_admin(user_id: str, request: AddQARequest):
    """Add Q/A to any user's history (admin only)."""
    try:
        user_service = get_user_service()
        user = await user_service.add_qa_to_history(user_id, request.question, request.answer)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Admin added Q/A to user {user_id}: {len(user.history)} total items")

        return {
            "message": "Q/A added to user history successfully",
            "user_id": user_id,
            "total_history_items": len(user.history),
            "added_qa": {"question": request.question, "answer": request.answer},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding Q/A to user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding Q/A: {str(e)}")


@router.get("/stats/overview")
async def get_system_stats():
    """Get system statistics (admin only)."""
    try:
        # This would require implementing stats methods in the service
        logger.info("Admin requested system statistics")

        return {
            "message": "System stats endpoint - implementation needed",
            "note": "This endpoint requires implementing stats methods in UserDbHandler",
            "suggested_stats": [
                "total_users",
                "active_users_24h",
                "total_qa_interactions",
                "users_by_creation_date",
                "token_expiry_summary",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting system stats: {str(e)}")
