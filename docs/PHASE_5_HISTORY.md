# Phase 5 — Searchable scoring history

**Status:** Done · 32 API tests
**Certificate link:** AI101 (tables, filters, thinking in counts) + a real audit log

## What this phase adds

A `/history` page that is a **queryable audit trail**, not a dump of the last 20 rows.

```text
GET /api/v1/scores?risk_level=HIGH&merchant_category=crypto&page=1
        │
        ├─ analysts: WHERE scored_by_id = me
        ├─ admins + scope=all: every row (for review / compliance)
        ├─ filters applied in SQL (not in Python after fetch)
        └─ { items, total, page, page_size }

GET /api/v1/scores/{id}     404 if you shouldn't see it (no 403 leak)
GET /api/v1/scores/export   same filters, CSV, cap 10_000 rows
```

Filters sit in the **URL**, so a view can be bookmarked or pasted into Slack. CSV download goes through the Next.js server (`/history/export`) so the browser still never talks to FastAPI.

## Why these decisions

| Decision | Why |
|---|---|
| **Paginated envelope** `{items, total, page}` | A list of 10,000 scores would freeze the UI and the API |
| **SQL filters, not frontend filters** | The database should do the work; this is how you handle large data |
| **Analysts see only their rows** | Least privilege. Opening someone else's id returns **404**, not 403, so you cannot probe for ids |
| **Admin `scope=all`** | Compliance / model monitoring needs a cross-user view |
| **CSV through the BFF** | Same cookie/session as the page; no JWT in the browser |
| **Cache hits stay in the table** | "We served this decision" is the audit event, not "we computed it" |

## Try it yourself

1. Score grocery twice and crypto once, then open **History**.
2. Filter category = grocery. Total should be 2. Export CSV — only grocery rows.
3. Open one row. Log out, register a second user, paste the first row's URL. You should get a not-found page, not the score.
4. As admin, set **Whose scores = Everyone**.

## Known trade-offs

- No full-text search on payload JSON yet. Category / risk / cache cover the interview story.
- CSV is capped at 10,000 rows. A warehouse export would be a background job (Project 2).
