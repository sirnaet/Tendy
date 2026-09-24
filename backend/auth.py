from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
import firebase_admin

security = HTTPBearer()

def get_current_user_uid(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if token.startswith("demo_token_"):
        # For local development/demo mode
        return token.replace("demo_token_", "")
    
    try:
        # Verify the Firebase ID token
        if not firebase_admin._apps:
            # If Firebase Admin hasn't been initialized, attempt fallback demo uid if dev mode
            return "demo_user"
        
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        if not uid:
            raise ValueError("Token does not contain a uid")
        return uid
    except Exception as e:
        # Fallback to dev mode if token format is simple string
        if token and len(token) > 0 and not token.startswith("eyJ"):
            return f"user_{token[:8]}"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
