from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any

class ThirdPartyOauthDataResponse(BaseModel):
    clientId: str
    redirectUri: str
    codeChallenge: str
    state: str
    scopes: str
    codeChallengeMethod: str
    responseType: str
    oauthConnectUrl: str

class ThirdPartyOauthResponse(BaseModel):
    status_code: int
    success: bool
    access_token: str
    refresh_token: str
    expires_in: int
    message: str

class EtsyConnectionStatus(BaseModel):
    connected: bool
    message: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None
    shop_info: Optional[Dict[str, Any]] = None
    expires_at: Optional[int] = None

class EtsyDisconnectResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None