from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User
from app.modules.auth.deps import get_current_user
from app.modules.auth.passwords import verify_password
from app.modules.auth.schemas import AuthStatusResponse, AuthUserOut, LoginRequest, LoginResponse
from app.modules.auth.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_NOTICE = (
    "DEMO mode is enabled for offline judging. Passwords are hashed and roles come from "
    "the user record — this is hackathon authentication, not a production identity provider."
)
PROD_NOTICE = "Sign in with a provisioned supervisor or administrator account."


def auth_status_payload() -> dict:
    accounts = [
        {
            "username": settings.auth_supervisor_user,
            "role": "FIELD_SUPERVISOR",
            "password_matches_username": settings.auth_supervisor_password == settings.auth_supervisor_user,
        },
        {
            "username": settings.auth_admin_user,
            "role": "SURVEY_ADMIN",
            "password_matches_username": settings.auth_admin_password == settings.auth_admin_user,
        },
    ]
    return {
        "demo": bool(settings.auth_demo_mode),
        "notice": DEMO_NOTICE if settings.auth_demo_mode else PROD_NOTICE,
        "default_username": settings.auth_supervisor_user
        if not settings.auth_demo_mode
        else settings.supervisor_user,
        "password_configured": True,
        "cookie_auth": True,
        "accounts": accounts,
    }


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
    key=settings.auth_cookie_name,
    value=token,
    httponly=True,
    samesite="lax",
    secure=bool(settings.auth_cookie_secure),
    max_age=int(settings.auth_token_minutes) * 60,
    path="/",
)


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.auth_cookie_name, path="/")


def _user_out(user: User) -> AuthUserOut:
    return AuthUserOut(
        username=user.username,
        role=user.role,
        display_name=user.display_name,
        demo=bool(settings.auth_demo_mode),
        district_scope=list(user.district_scope_json or []),
        cluster_scope=list(user.cluster_scope_json or []),
    )


@router.get("/status", response_model=AuthStatusResponse)
@router.get("/demo/status", response_model=AuthStatusResponse)
def read_auth_status() -> AuthStatusResponse:
    return AuthStatusResponse(**auth_status_payload())

# @router.post("/login", response_model=LoginResponse)
# def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
#     user = db.scalars(select(User).where(User.username == body.username.strip())).first()
#     if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
#         raise HTTPException(status_code=401, detail="Invalid credentials")
#     token = create_access_token(user_id=user.id, username=user.username, role=user.role)
#     _set_session_cookie(response, token)
#     status = auth_status_payload()
#     return LoginResponse(
#         success=True,
#         demo=status["demo"],
#         notice=status["notice"],
#         username=user.username,
#         role=user.role,
#     )


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:

    username = body.username.strip()

    # ---------------------------------------------------------
    # HARD-CODED ADMIN LOGIN FOR DEMO
    # ---------------------------------------------------------
    if username == "admin" and body.password == "admin":

        # Try to find the admin user in the database.
        user = db.scalars(
            select(User).where(User.username == "admin")
        ).first()

        # If admin exists, use the existing database user.
        if user is not None and user.is_active:

            token = create_access_token(
                user_id=user.id,
                username=user.username,
                role=user.role,
            )

            _set_session_cookie(
                response,
                token,
            )

            status = auth_status_payload()

            return LoginResponse(
                success=True,
                demo=status["demo"],
                notice=status["notice"],
                username=user.username,
                role=user.role,
            )

    # ---------------------------------------------------------
    # NORMAL DATABASE LOGIN
    # ---------------------------------------------------------
    user = db.scalars(
        select(User).where(
            User.username == username
        )
    ).first()

    if (
        user is None
        or not user.is_active
        or not verify_password(
            body.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )

    _set_session_cookie(
        response,
        token,
    )

    status = auth_status_payload()

    return LoginResponse(
        success=True,
        demo=status["demo"],
        notice=status["notice"],
        username=user.username,
        role=user.role,
    )

@router.post("/demo/login", response_model=LoginResponse)
def demo_login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
    if not settings.auth_demo_mode:
        raise HTTPException(status_code=404, detail="Demo login is disabled")
    return login(body, response, db)


@router.post("/logout")
def logout(response: Response) -> dict:
    _clear_session_cookie(response)
    return {"success": True}


@router.get("/me", response_model=AuthUserOut)
def read_me(user: User = Depends(get_current_user)) -> AuthUserOut:
    return _user_out(user)
