# Dashboard (React + Vite)

Admin dashboard for the Shopify Support Agent — conversations, live analytics over WebSocket, email inbox, cart recovery, product-description generator, settings.

```bash
npm install
npm run dev      # http://localhost:5173 — proxies /api, /ws, /webhook, /health to the FastAPI backend on :8000
npm run build    # static build in dist/ (deploy to Vercel; vercel.json rewrites API routes to the backend)
```

See the root README for the full system.
