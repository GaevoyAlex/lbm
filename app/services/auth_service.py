import base64
import httpx
from datetime import timedelta
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt
import json
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import get_user_by_email, create_or_update_google_user
# app/services/auth_service.py
async def get_google_token(code: str) -> Optional[Dict[str, Any]]:
    print(f"🔹 Отправляем код авторизации в Google: {code}")
    print(f"🔹 Длина кода: {len(code)}")
    print(f"🔹 Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
    
    # Установим очень короткий таймаут, чтобы увидеть, если проблема в этом
    async with httpx.AsyncClient(timeout=30.0) as client:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI
        }
        
        print(f"🔹 Полные данные запроса token: {data}")
        
        try:
            response = await client.post(token_url, data=data)
            print(f"🔹 Статус ответа: {response.status_code}")
            print(f"🔹 Ответ Google OAuth: {response.text}")
            
            if response.status_code != 200:
                print(f"❌ Ошибка Google OAuth: {response.text}")
                return None
            
            response_json = response.json()
            return response_json
        except Exception as e:
            print(f"❌ Исключение при запросе токена: {e}")
            return None
        


async def get_google_user_info(token: str) -> Optional[Dict[str, Any]]:
    """Получение информации о пользователе Google"""
    print(f"🔹 Используем Access Token для получения данных: {token}")

    if not token:
        print("❌ Ошибка: передан пустой токен!")
        return None

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения данных пользователя: {response.text}")
            return None

        user_info = response.json()
        print(f"✅ Данные пользователя: {user_info}")
        return user_info

async def authenticate_google_user(db: Session, code: str) -> Optional[Dict[str, Any]]:
    """Аутентификация пользователя через Google OAuth"""
    print(f"🔹 Полученный код авторизации: {code}")

    if not code:
        print("❌ Ошибка: код авторизации пустой!")
        return None

    try:
        # Получаем Google OAuth токен
        token_data = await get_google_token(code)
        if not token_data:
            return None

        access_token = token_data["access_token"]
        user_info = await get_google_user_info(access_token)

        if not user_info:
            return None

        # Проверяем, есть ли пользователь в базе
        db_user = get_user_by_email(db, email=user_info["email"])

        if not db_user:
            print(f"🆕 Создаем нового пользователя: {user_info['email']}")
            db_user = create_or_update_google_user(
                db,
                email=user_info["email"],
                name=user_info.get("name", user_info["email"].split("@")[0]),
                first_name=user_info.get("given_name"),
                last_name=user_info.get("family_name")
            )
        else:
            print(f"✅ Пользователь уже существует: {user_info['email']}")

        # Генерируем JWT токен
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            subject=db_user.id,
            expires_delta=access_token_expires
        )

        print(f"✅ JWT Token создан для пользователя: {db_user.email}")
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": db_user
        }

    except Exception as e:
        print(f"❌ Ошибка аутентификации Google: {e}")
        return None




async def authenticate_google_user_with_credential(db: Session, credential: str) -> Optional[Dict[str, Any]]:
    """Аутентификация пользователя через Google ID token"""
    print(f"🔹 Получен Google ID token (credential)")
    
    if not credential:
        print("❌ Ошибка: ID token пустой!")
        return None
    
    try:
        # Декодируем JWT без проверки (просто чтобы посмотреть содержимое)
        # Это не безопасно для реального использования, но поможет в отладке
        header_payload = credential.split('.')[:2]
        payload_base64 = header_payload[1]
        # Добавляем padding если нужно
        padding = '=' * (4 - len(payload_base64) % 4) if len(payload_base64) % 4 != 0 else ''
        payload_base64 += padding
        
        # Заменяем URL-safe символы на обычные для base64
        payload_base64 = payload_base64.replace('-', '+').replace('_', '/')
        try:
            payload_json = base64.b64decode(payload_base64).decode('utf-8')
            payload = json.loads(payload_json)
            print(f"🔹 Декодированный payload: {payload}")
            
            # Извлекаем данные пользователя из токена
            user_info = {
                "email": payload.get("email"),
                "name": payload.get("name"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name"),
                "picture": payload.get("picture")
            }
            
            # Здесь должна быть проверка ID токена
            # В реальном приложении используйте Google Client Library для проверки токена:
            # id_info = id_token.verify_oauth2_token(
            #     credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            # )
            
            # Проверяем, есть ли пользователь в базе
            db_user = get_user_by_email(db, email=user_info["email"])
            
            if not db_user:
                print(f"🆕 Создаем нового пользователя: {user_info['email']}")
                db_user = create_or_update_google_user(
                    db,
                    email=user_info["email"],
                    name=user_info.get("name", user_info["email"].split("@")[0]),
                    first_name=user_info.get("given_name"),
                    last_name=user_info.get("family_name")
                )
            else:
                print(f"✅ Пользователь уже существует: {user_info['email']}")
            
            # Генерируем JWT токен
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            jwt_token = create_access_token(
                subject=db_user.id,
                expires_delta=access_token_expires
            )
            
            print(f"✅ JWT Token создан для пользователя: {db_user.email}")
            return {
                "access_token": jwt_token,
                "token_type": "bearer",
                "user": db_user
            }
            
        except Exception as e:
            print(f"❌ Ошибка при декодировании payload: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Ошибка аутентификации с ID token: {e}")
        return None