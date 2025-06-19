# Обновите GoogleAuthRequest в schemas/user.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    creation_date: datetime

    class Config:
        orm_mode = True

class GoogleAuthRequest(BaseModel):
    code: Optional[str] = None
    credential: Optional[str] = None
    
    @validator('code', 'credential')
    def check_at_least_one_field(cls, v, values):
        if not v and not values.get('code') and not values.get('credential'):
            raise ValueError('Должен быть предоставлен либо code, либо credential')
        return v