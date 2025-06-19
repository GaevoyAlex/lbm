from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.crud.user import authenticate_user, create_user, get_user_by_email, get_user_by_name
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserResponse, GoogleAuthRequest
from app.core.security import create_access_token
from app.services.auth_service import authenticate_google_user, authenticate_google_user_with_credential

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя
    """
     
    if get_user_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )
    
     
    if get_user_by_name(db, name=user_in.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует",
        )
     
    user = create_user(db, user_in=user_in)
    return user

@router.post("/login", response_model=Token)
def login_for_access_token(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Аутентификация пользователя и получение JWT токена
    """
    user = authenticate_user(db, email=user_in.email, password=user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
 
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/google/login")
def login_google():
    """
    Перенаправление на страницу аутентификации Google
    """
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
    )
    return RedirectResponse(google_auth_url)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Callback для обработки ответа от Google OAuth
    """
 
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Отсутствует код авторизации",
        )
    
 
    auth_result = await authenticate_google_user(db, code)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка аутентификации через Google",
        )
    
    # Здесь можно добавить перенаправление на фронтенд с токеном
    # Или вернуть токен в ответе
    return {
        "access_token": auth_result["access_token"],
        "token_type": "bearer",
        "user": auth_result["user"]
    }

@router.post("/google/auth", response_model=Token)
async def auth_google(google_auth: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Аутентификация через Google OAuth для API
    """
    print(f"🔹 Получен запрос на аутентификацию Google: {google_auth}")
    
    if google_auth.credential:
        print("🔹 Используем credential (ID token) для аутентификации")
        auth_result = await authenticate_google_user_with_credential(db, google_auth.credential)
    elif google_auth.code:
        print("🔹 Используем code для аутентификации")
        auth_result = await authenticate_google_user(db, google_auth.code)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Требуется код авторизации или credential",
        )
    
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка аутентификации через Google",
        )
    
    return {
        "access_token": auth_result["access_token"],
        "token_type": "bearer"
    }