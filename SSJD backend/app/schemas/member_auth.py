from pydantic import BaseModel


class MemberLoginRequest(BaseModel):
    username: str
    password: str


class MemberTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
