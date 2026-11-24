import os
import secrets
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials

load_dotenv()
API_KEY = os.getenv("ONEXAI_API_KEY")
TEST_USERNAME = os.getenv("TEST_USERNAME")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")
if not API_KEY:
    raise RuntimeError("Set ONEXAI_API_KEY in the environment.")
if not TEST_USERNAME or not TEST_PASSWORD:
    raise RuntimeError("Set TEST_USERNAME and TEST_PASSWORD to protect the test page.")

app = FastAPI(title="Persian Academy Realtime Test")
security = HTTPBasic()

def require_test_login(credentials: HTTPBasicCredentials = Depends(security)):
    user_ok = secrets.compare_digest(credentials.username, TEST_USERNAME)
    pass_ok = secrets.compare_digest(credentials.password, TEST_PASSWORD)
    if not (user_ok and pass_ok):
        from fastapi import status
        from fastapi.responses import JSONResponse
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/")
async def home(_user: str = Depends(require_test_login)):
    return FileResponse("static/index.html")

@app.post("/voice-token")
async def voice_token(_user: str = Depends(require_test_login)):
    # Long-lived key stays on this server; browser receives only a short-lived secret.
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://1xai.ir/v1/realtime/client_secret",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={"model": "gpt-realtime-mini"},
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"1xAI returned {exc.response.status_code}: {exc.response.text[:400]}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach 1xAI: {str(exc)}")
