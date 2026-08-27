from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api.routes import router
from app.api.store_routes import router as store_router
from app.config import settings
from app.db.channel_config import load_channel_config
from app.inventory_alert import check_inventory_and_alert

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    stored = load_channel_config()
    settings.apply_stored_channel_config(stored)
    storage = "Supabase" if settings.supabase_url and settings.supabase_key else settings.db_backend
    print(f"Starting {settings.store_name} support agent")
    print(f"  Platform: {settings.resolved_platform}")
    print(f"  Demo mode: {settings.demo_mode}")
    print(f"  Storage: {storage}")
    print(f"  Channel: {settings.channel}")
    print(f"  LLM: {settings.llm_provider} / {settings.llm_model}")
    scheduler.add_job(
        check_inventory_and_alert, "interval", hours=6,
        id="inventory_alert", replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Store Agent", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(store_router)

static_dir = Path("app/static")
store_html = static_dir / "store.html"
if store_html.is_file():
    @app.get("/store.html")
    async def storefront():
        return FileResponse(str(store_html))

    @app.get("/favicon.svg")
    async def favicon():
        return FileResponse(str(static_dir / "favicon.svg"))

    print(f"Serving storefront from {store_html}")

index_html = static_dir / "index.html"
if index_html.is_file():
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        static_root = static_dir.resolve()
        file = (static_dir / full_path).resolve()
        if full_path and file.is_file() and file.is_relative_to(static_root):
            return FileResponse(str(file))
        return FileResponse(str(index_html))

    print(f"Serving dashboard from {index_html}")
