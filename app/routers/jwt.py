import os

from fastapi import APIRouter, HTTPException
from jose import JWTError, jwt

from app.dependencies import db_dep, current_user_dep
from app.models import User
from app.schemas.schemas import JWTRefreshIn, TokenResponse, UserJWTLogin, UserRegister

ACCESS_TOKEN_EXPIRE_MINUTES=os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
ALGORITHM=os.getenv("ALGORITHM")
FRONTEND_URL=os.getenv("FRONEND_URL")
REFRESH_TOKEN_EXPIRE_MINUTES=os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")
SECRET_KEY=os.getenv("SECRET_KEY")

from app.tasks import send_email

from app.utils import (
    create_jwt_token,
    generate_confirmation_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register_user(db: db_dep, register_data: UserRegister):
    if db.query(User).filter(User.email == register_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=register_data.username,
        email=register_data.email,
        password_hash=hash_password(register_data.password),
        is_active=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = generate_confirmation_token(email=user.email)

    try:
        send_email.delay(
            to_email=user.email,
            subject="Confirm your registration to Bookla",
            body=f"You can click the link to confirm your email: {FRONTEND_URL}/auth/confirm/{token}/",
        )
    except Exception as e:
        print("❗ Celery task failed:", e)

    return {
        "detail": f"Confirmation email sent to {user.email}. Please confirm to finalize your registration.",
    }

@router.post("/jwt/me", response_model=TokenResponse)
async def jwt_me(current_user: current_user_dep):
    return current_user

@router.post("/login")
async def login_user(db: db_dep, login_data: UserJWTLogin):
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=400, detail="User not found or you entered wrong credentials."
        )

    login_dict = {"email": user.email}

    access_token = create_jwt_token(
        data=login_dict, expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    refresh_token = create_jwt_token(
        data=login_dict, expires_delta=REFRESH_TOKEN_EXPIRE_MINUTES
    )

    response = {"access_token": access_token, "refresh_token": refresh_token}

    return response


@router.post("/refresh/")
async def get_access_token(db: db_dep, token_data: JWTRefreshIn):
    try:
        payload = jwt.decode(
            token_data.refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True},
        )
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = create_jwt_token(
            data={"email": email}, expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES
        )

        response = {
            "access_token": new_access_token,
            "refresh_token": token_data.refresh_token,
            "token_type": "bearer",
        }

        return response

    except JWTError as err:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from err
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=401, detail="Refresh token has expired"
        ) from err
    except Exception as err:
        raise HTTPException(
            status_code=400, detail="Something went wrong. Please try again later."
        ) from err


@router.get("/auth/verify-email/{token}")
async def confirm_email(db: db_dep, token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload["email"]

        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        if user.is_active:
            raise HTTPException(status_code=400, detail="User already confirmed")

        user.is_active = True
        db.commit()
        db.refresh(user)

        return {"message": "Email confirmed successfully"}

    except jwt.ExpiredSignatureError as err:
        raise HTTPException(status_code=400, detail="Token has expired") from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=400, detail="Invalid token") from err
