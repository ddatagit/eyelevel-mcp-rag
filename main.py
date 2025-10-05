import contextlib
from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from server import mcp as mcp_server

limiter = Limiter(key_func=get_remote_address)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
  async with contextlib.AsyncExitStack() as stack:
    await stack.enter_async_context(mcp_server.session_manager.run())
    yield

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter

# Apply rate limiting to /server endpoint
server_app = mcp_server.streamable_http_app()
server_app.state.limiter = limiter

# Wrap the server app with rate limiting middleware
from slowapi.middleware import SlowAPIMiddleware
server_app.add_middleware(SlowAPIMiddleware)

app.mount("/server", server_app)

@app.get("/render-health-check")
async def health_check():
  return {"status": 200, "message": "service is up"}

if __name__ == "__main__":
  import uvicorn
  import os
  from dotenv import load_dotenv

  load_dotenv()
 
  PORT:int = int(os.getenv("PORT") or 8000)
  uvicorn.run(app, host="0.0.0.0", port=PORT)