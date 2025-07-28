from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User
from app.utils import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")





def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



db_dep = Annotated[Session, Depends(get_db)]
oauth2_dep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(db: db_dep, token: oauth2_dep):
    print("OAuth2 token extracted:", token)

    try:
        payload = jwt.decode(
            token=token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True},
        )

        print("Decoded payload:", payload)

        email: str = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError as err:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from err
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=401, detail="Refresh token has expired"
        ) from err


current_user_dep = Annotated[bool, Depends(get_current_user)]
