from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_required(cls, value: str) -> str:
        cleaned = value.strip() if isinstance(value, str) else ""
        if not cleaned:
            raise ValueError("username is required")
        return cleaned

    @field_validator("password")
    @classmethod
    def password_required(cls, value: str) -> str:
        if not isinstance(value, str) or value == "":
            raise ValueError("password is required")
        return value


class AuthUserOut(BaseModel):
    username: str
    role: str
    display_name: str = ""
    demo: bool = False
    district_scope: list[str] = Field(default_factory=list)
    cluster_scope: list[str] = Field(default_factory=list)


class LoginResponse(BaseModel):
    success: bool
    demo: bool
    notice: str
    username: str
    role: str


class AuthStatusResponse(BaseModel):
    demo: bool
    notice: str
    default_username: str
    password_configured: bool
    cookie_auth: bool = True
    accounts: list[dict] = Field(default_factory=list)
