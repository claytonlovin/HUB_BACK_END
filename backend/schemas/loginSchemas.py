from pydantic import BaseModel

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserLogingoogleRequest(BaseModel):
    idToken: str

class UserLoginResponse(BaseModel):
    success: bool
    message: str
    token: str
    user_info: dict