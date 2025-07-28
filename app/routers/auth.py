from fastapi import APIRouter, HTTPException
from jose import JWTError, jwt

from app.dependencies import db_dep, current_user_dep
from app.models.models import User
from app.schemas.schemas import TokenIn, UserRegisterIn, UserOut
from app.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    FRONTEND_URL,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
)
from app.tasks import send_email
from app.utils import (
    create_jwt_token,
    generate_confirmation_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/")
async def register_user(db: db_dep, register_data: UserRegisterIn):
    is_user_exists = db.query(User).filter(User.email == register_data.email).first()

    if is_user_exists:
        raise HTTPException(status_code=400, detail="User already exists")

    is_first_user = db.query(User).count() == 0

    if is_first_user:
        user = User(
            username=register_data.username,
            email=register_data.email,
            hashed_password=hash_password(register_data.password),
            is_admin=True,
            is_verified=False,  # not confirmed yet
        )
    else:
        user = User(
            username=register_data.username,
            email=register_data.email,
            hashed_password=hash_password(register_data.password),
            is_admin=False,
            is_verified=False,  # not confirmed yet
        )

    db.add(user)
    db.commit()
    db.refresh(user)

    # send confirmation email
    token = generate_confirmation_token(email=user.email)

    send_email.delay(
        to_email=user.email,
        subject="Confirm your registration to Bookla",
        body=f"You can click the link to confirm your email: {FRONTEND_URL}/auth/confirm/{token}/",
    )

    return {
        "detail": f"Confirmation email sent to {user.email}. Please confirm to finalize your registration.",
    }


@router.post("/login/")
async def login_user(db: db_dep, login_data: UserRegisterIn):
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="User not found or you entered wrong credentials."
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Please confirm your email before logging in. Check your inbox for the confirmation link.",
        )
    login_dict = {"email": user.email, "is_admin": user.is_admin}

    access_token = create_jwt_token(
        data=login_dict, expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    refresh_token = create_jwt_token(
        data=login_dict, expires_delta=REFRESH_TOKEN_EXPIRE_MINUTES
    )

    response = {"access_token": access_token, "refresh_token": refresh_token}

    return response


@router.post("/refresh/")
async def get_access_token(db: db_dep, token_data: TokenIn):
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


@router.get("/verify-email/{token}/")
async def verify_email(db: db_dep, token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload["email"]

        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        if user.is_active:
            raise HTTPException(status_code=400, detail="User already confirmed")

        user.is_verified = True
        db.commit()
        db.refresh(user)

        return {"message": "Email confirmed successfully"}

    except jwt.ExpiredSignatureError as err:
        raise HTTPException(status_code=400, detail="Token has expired") from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=400, detail="Invalid token") from err

@router.get("/me", response_model=UserOut)
async def get_me(current_user: current_user_dep, db: db_dep):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user