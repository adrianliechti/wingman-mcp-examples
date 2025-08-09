import uvicorn
from pathlib import Path
from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

mcp = FastMCP.as_proxy(
    ProxyClient("http://127.0.0.1:8000/mcp"),
    name="Wingman Bridge",
)

mcp_app = mcp.http_app(transport="sse")

async def wingman_endpoint(request: Request) -> JSONResponse:
    data = {
        "name": "wingman",
    }
    
    # Read instructions from file dynamically
    instructions_file = Path(__file__).parent.parent / "instructions.md"
    if instructions_file.exists():
        try:
            with open(instructions_file, 'r', encoding='utf-8') as f:
                instructions = f.read().strip()
                if instructions:
                    data["instructions"] = instructions
        except Exception as e:
            # If there's an error reading the file, we'll just skip adding instructions
            pass
    
    return JSONResponse(data)

app = Starlette(
    routes=[
        Route("/.well-known/wingman", wingman_endpoint, methods=["GET"]),
        Mount("/", app=mcp_app),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=4200)