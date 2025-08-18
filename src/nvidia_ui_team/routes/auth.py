from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from nvidia_ui_team.utils.consts import Routes
from nvidia_ui_team.models.outbound.auth import OutboundUser
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel
import jwt

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# דוגמה ל-Fake Users עם סיסמאות
fake_users = [
    {
        "user_uuid": uuid4(),
        "username": "alice",
        "email": "alice@example.com",
        "full_name": "Alice Wonderland",
        "is_active": True,
        "password": "alice123"
    },
    {
        "user_uuid": uuid4(),
        "username": "bob",
        "email": "bob@example.com",
        "full_name": "Bob Builder",
        "is_active": True,
        "password": "bob123"
    }
]

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str | None = None

class UsersRouter:
    def __init__(self):
        self.router = APIRouter(prefix=Routes.AUTH)

    def build(self):
        self.router.add_api_route("/{user_uuid}",
                                  self.get_user, methods=["GET"], response_model=OutboundUser)
        self.router.add_api_route("/login",
                                  self.login, methods=["POST"])
        self.router.add_api_route("/signup",
                                  self.signup, methods=["POST"])
        return self.router

    @staticmethod
    async def get_user(user_uuid: UUID):
        for user in fake_users:
            if user["user_uuid"] == user_uuid:
                return user
        raise HTTPException(status_code=404, detail="User not found")

    @staticmethod
    async def login(form_data: OAuth2PasswordRequestForm = Depends()):
        for user in fake_users:
            if user["username"] == form_data.username and user["password"] == form_data.password:
                token = create_access_token({"sub": user["username"]})
                return {"access_token": token, "token_type": "bearer"}
        raise HTTPException(status_code=401, detail="Invalid username or password")

    @staticmethod
    async def signup(signup_data: SignupRequest):
        # בדיקה אם המשתמש כבר קיים
        for user in fake_users:
            if user["username"] == signup_data.username or user["email"] == signup_data.email:
                raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # יצירת משתמש חדש
        new_user = {
            "user_uuid": uuid4(),
            "username": signup_data.username,
            "email": signup_data.email,
            "full_name": signup_data.full_name,
            "is_active": True,
            "password": signup_data.password
        }
        fake_users.append(new_user)
        token = create_access_token({"sub": new_user["username"]})
        return {"access_token": token, "token_type": "bearer", "user_uuid": new_user["user_uuid"]}
