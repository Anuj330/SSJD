from pydantic import BaseModel


class MemberRegisterRequest(BaseModel):
    member_id: int
    username: str
    password: str


class MemberLoginRequest(BaseModel):
    username: str
    password: str


class MemberTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
