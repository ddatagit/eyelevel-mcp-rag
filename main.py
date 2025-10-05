import contextlib
from fastapi import FastAPI
from server import mcp as mcp_server

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
  async with contextlib.AsyncExitStack() as stack:
    await stack.enter_async_context(mcp_server.session_manager.run())
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/mcp", mcp_server.streamable_http_app())

@app.get("/health")
async def health_check():
  return {"status": 200, "message": "service is up"}

if __name__ == "__main__":
  import uvicorn
  import os
  from dotenv import load_dotenv

  load_dotenv()
 
  PORT:int = int(os.getenv("PORT") or 8000)
  uvicorn.run(app, host="0.0.0.0", port=PORT)