<div align="center">


  <h1>Store Agent</h1>

  <p>
    AI customer support for online stores that do not have a support team.<br>
    It answers order, return, product and policy questions from live store data.<br>
    One agent that works across web chat, WhatsApp, Telegram and email.
  </p>

  <p>
    <a href="https://store-agent-app.onrender.com/store.html"><strong>View the live demo</strong></a>
  </p>

  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/LangGraph-1C3C3C?logo=langchain&logoColor=white" alt="LangGraph">
  <img src="https://img.shields.io/badge/React-20232a?logo=react&logoColor=61DAFB" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Groq-F55036?logo=groq&logoColor=white" alt="Groq">

</div>

---

## What it does

Store Agent answers the questions that make up most of a store's day to day support: where is my order, can I return this, do you stock it in blue, what is your policy, and I need a human. It reads from the store's real data instead of guessing, and it hands anything uncertain to the store owner with the full conversation attached.

The storefront is a plugin. `CommerceProvider` defines the interface, and Shopify ships as the reference adapter. Any other platform, such as WooCommerce, Medusa or a custom backend, connects by implementing that one interface.

It runs on four channels at once: web chat, WhatsApp, Telegram and email. The owner dashboard shows the conversations, order data, analytics, abandoned carts and incoming email in one place.

## Screenshots

The customer storefront, running against the live demo:

<div align="center">
  <img src="assets/storefront.png" alt="Northlane customer storefront" width="90%">
</div>

The product page with the chat widget:

<div align="center">
  <img src="assets/storefront-product.png" alt="Northlane product page with chat widget" width="90%">
</div>

The owner dashboard views:

<div align="center">
  <img src="assets/conversations.png" alt="Conversations view" width="32%">
  <img src="assets/orders.png" alt="Orders view" width="32%">
  <img src="assets/analytics.png" alt="Analytics view" width="32%">
</div>

<div align="center">
  <img src="assets/cart-recovery.png" alt="Cart recovery view" width="32%">
  <img src="assets/email-inbox.png" alt="Email inbox view" width="32%">
  <img src="assets/descriptions.png" alt="Product descriptions view" width="32%">
</div>

<div align="center">
  <img src="assets/settings.png" alt="Settings view" width="90%">
</div>

## Features

- Answers from real store data with six tools: orders, returns, products, fulfillment, policies and escalation
- Escalates instead of guessing: uncertain questions go to the owner with the full context
- Multi channel: web chat, WhatsApp, Telegram and email from one agent and the same tools
- Pluggable storefronts: a `CommerceProvider` interface that swaps Shopify for any platform
- Owner dashboard: conversations, analytics, orders, email inbox, cart recovery and product descriptions
- Sentiment tagging: every message is tagged positive, neutral or negative
- Cart recovery: drafts a personalised win back message for each abandoned cart
- Demo mode: `PLATFORM=mock` runs with sample data, no store connected

## Getting started

### Prerequisites

* Python 3.10+
* Node.js 18+
* A [Groq](https://groq.com) API key. The free tier works and the demo deploy uses it.

### Install

1. Clone the repository
   ```sh
   git clone https://github.com/coder-red/store-agent.git
   ```
2. Install the backend dependencies
   ```sh
   pip install -r requirements.txt
   ```
3. Copy the example environment file
   ```sh
   cp .env.example .env
   ```
4. Start the backend
   ```sh
   uvicorn app.main:app --reload --port 8000
   ```
5. Start the dashboard
   ```sh
   cd frontend && npm install && npm run dev
   ```
6. Open the dashboard in your browser

The environment file `.env.example` lists every variable and what it does. The demo runs out of the box with `PLATFORM=mock`, no store credentials needed.

## Usage

Send a test message to the local backend:

```sh
curl -X POST localhost:8000/webhook/test \
  -H 'content-type: application/json' \
  -d '{"customer_identifier":"demo","message":"Where is my order #1006?"}'
```

Connect a real store in one of two ways:

- Run with `PLATFORM=shopify` and set the `SHOPIFY_*` variables in `.env`.
- Or enter the credentials in the dashboard Settings screen and select the channel there. This is the right option for a deployed app, because the channels are stored in the database.

You can use a custom adapter by pointing `PLATFORM` at it, for example `PLATFORM=my_pkg.adapters:WooAdapter`. See the section on [adding a storefront platform](#adding-a-storefront-platform).

Switch the channel with `CHANNEL` set to `webchat`, `whatsapp`, `telegram` or `email`. WhatsApp uses Twilio, Telegram uses the Bot API, and email uses Resend.

## Architecture

```mermaid
flowchart TB
    subgraph Channels
        WC[Web chat / WS]
        WA[WhatsApp / Twilio]
        TG[Telegram / Bot API]
        EM[Email / inbound webhook]
    end
    subgraph FastAPI
        API[/webhook and /api routes/]
    end
    subgraph Agents
        SUP[Supervisor LLM router]
        OA[Orders agent]
        RA[Returns agent]
        PA[Products agent]
        GA[General agent]
    end
    subgraph Platform
        CP[CommerceProvider]
        MOCK[Mock adapter]
        SHOP[Shopify adapter]
    end
    WC --> API
    WA --> API
    TG --> API
    EM --> API
    API --> SUP
    SUP --> OA
    SUP --> RA
    SUP --> PA
    SUP --> GA
    OA --> CP
    RA --> CP
    PA --> CP
    GA --> CP
    CP --> MOCK
    CP --> SHOP
```

A message enters through a channel, hits the FastAPI route, and the supervisor routes it to one of four specialist agents. Each specialist is a LangGraph ReAct agent that only has the tools it needs, and every tool call goes through `CommerceProvider`. Conversations, escalations and analytics persist to SQLite by default.

The agent has six tools, each returning from the store and never from memory: `get_order_status`, `check_return_eligibility`, `get_product_info`, `check_fulfillment_status`, `query_store_policies`, `escalate_to_human`. A single supervisor call picks the specialist, and the dashboard shows which one answered. Web chat streams tokens over WebSocket, and the dashboard subscribes to the same stream.

## Adding a storefront platform

Subclass `CommerceProvider` and implement the seven required async methods:

```python
from app.commerce.base import CommerceProvider

class MyPlatformAdapter(CommerceProvider):
    platform_name = "myplatform"
    # get_order_by_number, get_order_by_email, search_products,
    # get_fulfillments, get_all_products, get_all_orders, check_inventory
```

Three optional methods default to a safe no-op so every store works out of the box: `get_order` looks up a single order, and the cart recovery trio (`get_abandoned_carts`, `attempt_cart_recovery`, `mark_cart_recovered`) reads and updates abandoned carts. Override them when your platform supports cart recovery.

Then set:

```sh
PLATFORM=my_store.adapter:MyPlatformAdapter
```

Built in options: `PLATFORM=mock` for the demo store and `PLATFORM=shopify` for the reference adapter, which uses the `SHOPIFY_*` credentials.

## API

| Route | Purpose |
|---|---|
| `POST /webhook/test` | Send a message as a customer, get the agent's reply |
| `POST /webhook/whatsapp` | Inbound WhatsApp webhook |
| `POST /webhook/telegram` | Inbound Telegram update |
| `POST /webhook/email` | Inbound email webhook |
| `WS /ws/chat` | Streaming web chat and dashboard live events |
| `GET /api/conversations`, `GET /api/conversations/{id}` | Transcripts |
| `GET /api/orders`, `GET /api/orders/{id}` | Owner order ledger and per order detail with line items |
| `GET /api/escalations`, `GET /api/analytics` | Owner views |
| `GET /api/emails` | Email inbox |
| `GET /api/products` | Product catalogue with images |
| `POST /api/generate-descriptions` | Product description generator |
| `GET /api/settings`, `PUT /api/settings` | Read and update store settings |
| `GET /api/channels`, `PUT /api/channels` | Read and update channel credentials |
| `GET /store/carts/abandoned` | Abandoned carts |
| `POST /store/carts/{id}/recover` | Draft a recovery message for one cart |
| `POST /store/carts/auto-recover` | Draft recovery messages for all carts |
| `GET /store/carts/recovery-stats` | Cart recovery summary |
| `GET /store/products` | Customer facing product list |
| `POST /store/orders` | Place an order against the demo store |
| `GET /store/track` | Customer order lookup. Requires both the order number and the checkout email |
| `GET /health` | Mode, platform, channel and model |

## Deployment

`render.yaml` deploys the API. The dashboard builds to static files, and `frontend/vercel.json` rewrites the API, WebSocket and webhook routes to the backend URL. The repository deploys automatically to Render on every push to `main`.

## License

This project does not currently include a license file. Until one is added, the default copyright applies, so you need permission from the author before copying, modifying or reusing the code.
