# AI layer

```
browser ─▶ /api/ai/*  ─▶  app/ai/assistant.py ─▶ Claude (Messages API, tool use)
                              │                        │
                              └──── app/ai/tools.py ◀──┘   read-only, role-scoped queries on the same services
```

## Configuration

| Variable | Meaning |
| --- | --- |
| `AI_PROVIDER` | `auto` (default: Anthropic if its key is set, else Gemini), `anthropic` or `gemini`. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Google Gemini key (server only) and model, default `gemini-3.8-flash`. Get a key at aistudio.google.com. |
| `ANTHROPIC_API_KEY` | Your key. Server only. Empty = AI chat and drafting disabled (everything else works). |
| `AI_MODEL` | Model id, default `claude-sonnet-5-5`. |
| `AI_COMPANY` | Optional sentence about the business, added to the prompts. |
| `AI_RATE_PER_10MIN` | Requests per user to the model in 10 minutes (default 40). |

The key is read from the environment by `app/core/config.py`, used only in `app/ai/client.py`, and is never logged,
stored or returned by any endpoint (`GET /api/ai/status` only says whether AI is on).

## Endpoints

| Endpoint | What it does | Needs the key |
| --- | --- | --- |
| `GET /api/ai/status` | `{enabled, model}` | no |
| `GET /api/ai/insights?lang=` | rule-based signals for the user's role | no |
| `GET /api/ai/brief?mode=daily\|finance&lang=` | short briefing; the model explains computed numbers, falls back to the signal list | optional |
| `POST /api/ai/chat` | `{messages, mode: assistant\|finance\|analyst, lang}` → `{reply, tools}` | yes |
| `POST /api/ai/draft` | `{text?, image?: {media_type, data(base64)}, lang}` → draft document | yes |
| `POST /api/ai/draft/commit` | posts a reviewed draft (receipt, delivery note, order, production) → `{kind, id, number}` | no |

## How it stays safe

- **Read-only.** No tool changes data. The model cannot post a document; a draft is returned to the browser and opens
  in the ordinary form, where the user checks it and presses Post (all normal rules apply then).
- **Role-scoped.** `app/ai/tools.py` offers the model only the tools the user's role may use and re-checks every call.
  A sales manager's assistant cannot read cash balances or supplier debts, even if asked.
- **Numbers come from tools.** The prompt tells the model to take every figure from tool results; the briefing sends it
  precomputed JSON. Signals (`app/ai/insights.py`) are plain code, so they are reproducible and testable.
- **Prompt injection.** Tool results and pasted/photographed text are marked as data, not instructions; tools are
  read-only so the worst a hostile document can do is produce a wrong draft that the user reviews.
- **Cost control.** Per-user rate limit, at most 6 tool rounds per question, 16 messages of history, briefing cache
  (keyed by the data, 30 minutes), photos downscaled to 1600 px in the browser and limited to 5 MB.

## Entering documents with AI

`POST /ai/draft` reads free text or a photo and returns a **draft**; nothing is saved. Kinds: purchase receipt, delivery note, customer order,
production (finished products made at a plant) and payments. `POST /ai/draft/commit` posts a reviewed draft (receipt, delivery note, order,
production) through the same services and role checks as the normal screens; a new partner can be created with `new_party`.

Names are matched by `app/ai/matching.py`, which is tolerant on purpose: Latin and Cyrillic are folded to one sound form (`sement` = `цемент`),
typos and doubled letters are forgiven, numbers are compared apart from words (`66x12` = `66*12`). Near-equal candidates are not guessed:
the row is marked ambiguous and the user picks. Tonnes are converted to kilograms (and back) when the catalogue unit differs, with a notice.

## Resetting the data

`python -m app.tools.reset_data --yes` (Docker: `docker compose exec api python -m app.tools.reset_data --yes`) deletes all documents, partners,
stock and money movements, **every product, material and norm, and every warehouse and plant**, and zeroes the account opening balances.
Only users, units and money accounts stay. Options: `--keep-stores` keeps warehouses and plants, `--keep-catalogue` keeps products and materials.
A fresh installation starts empty too; create your plants, warehouses, materials and products in the app
(Settings > Warehouses has a *Type* choice: Warehouse or Plant). For a sample catalogue set `SEED_CATALOGUE=true` before the first start.

## Privacy

When AI is on, the questions, the tool results needed to answer them (stock, partner names, amounts) and uploaded
photos are sent to Anthropic's API. Leave `ANTHROPIC_API_KEY` empty if that is not acceptable; nothing is sent then.

## Signals (`app/ai/insights.py`)

Stock-out forecast (stock ÷ average daily use over 30 days, warning under 14 days), below-minimum stock, slow movers
(in stock, no shipment for 60 days), sales trend (30 days vs the previous 30, ±20%), overdue customers (debt and no
payment for 30 days), 30-day cash forecast from the 60-day average, payables above available money, unusual
delivery-note prices (±40% from the item's median) and unusually large payments (> 3× the article's median).
Thresholds are constants at the top of each function.

## Testing without a key

`tests/test_ai.py` drives the real endpoints with a scripted fake model (`client.set_llm`) and checks the tool loop,
role scoping, caching, drafts, image validation and the rate limit. `e2e/reset_ai.sh` starts the app against a tiny
fake Messages API so the browser flow can be tested end to end. The real Claude call itself (`AnthropicClient`) is
only a plain HTTPS POST; try it once with your key via the *AI assistant* page.

## Adding a tool

Append a tuple to `TOOLS` in `app/ai/tools.py` (name, description, JSON-schema properties, required, function,
required sections). The function gets a `Ctx` (db, levels, lang) and returns JSON-able data; add a test that a role
without the section gets `forbidden`.
