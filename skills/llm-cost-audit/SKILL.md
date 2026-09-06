---
name: llm-cost-audit
description: Audit and fix the code patterns that make AI/LLM API bills blow up: retries that loop or stack, no spending limit, no cap on output length, agent/tool loops that never stop, rate-limit pileups (429s), and re-sending the same big prompt without caching. Provider- and language-agnostic. Use whenever the user raises AI/LLM cost or a surprise bill: "my bill spiked", "AI costs out of control", "runaway spend", "retry storm", "getting 429s", "add a spend cap or token budget", "reduce AI API costs", "audit our AI integration", or when they just describe the symptom without naming the cause.
source: https://initialcommit.co/library/skills/llm-cost-audit
---

# LLM Cost Audit

You are auditing a codebase's AI/LLM integrations for the specific bugs that turn a normal month into a five-figure bill. LLM spend is dangerous in a way most cloud cost isn't: a single defect can run *unbounded* overnight. A retry loop on a `429` hammers the provider thousands of times; an agent with no iteration cap calls tools until it dies of old age; a model with no output cap falls into a repetition loop and bills to the context limit; one user who scripts your endpoint runs up the bill for everyone. None of these throw an error in code review — they just cost money.

The bar is **"would this surprise me on the invoice?"**, not "is this theoretically optimal." A weekend project calling OpenAI once per request doesn't need a distributed rate limiter. But *any* product that bills real money to an AI provider needs a ceiling on spend, a cap on output, and retries that can't turn into a storm. Match the bar of the surrounding code: don't demand a token-budget service in a 200-line side project, but do flag the side project that retries forever on a 500.

**Don't break working features.** Never propose a fix that breaks a working flow without flagging it. Prefer additions (add a limit, add a spending check) over changes that could make output worse or lock users out. Every finding flags what to watch when applying the fix.

The audit produces **one short report**, worst-first — the thing that can run up an unlimited bill comes before the thing that wastes 10%.

## Write it for a working developer

The person reading this is a good developer who has never tuned an AI integration for cost, doesn't know the jargon, and doesn't need to. Your job is to make them go "oh, I see it — and I know what to change."

- **Plain words, not insider terms.** Don't write "thundering herd," "backpressure," "idempotent," "poison job." Say the actual thing: "all the retries fire at the same instant and make the overload worse."
- **Short.** A couple of tight sentences per finding. Cut the warm-up, the hedging, and the repetition.
- **No made-up dollar figures.** Say plainly what has no limit and why ("nothing stops this from running all night").
- **Every finding ends with something to do.** The fix is the point — concrete enough to act on without more research.
- **Plain English for explanation, precise code for the fix.** Keep the explanation jargon-free, but make the fix technically exact: real parameter names, real retry/caching/job code, exact config keys, correct status codes.

## Mode and scope

- If `$ARGUMENTS` is a path, audit only that path. Otherwise audit the whole repo, excluding: `node_modules`, `.git`, `dist`, `build`, `out`, `.next`, `vendor`, `target`, `__pycache__`, `.venv`, lock files, minified assets, and anything in `.gitignore` that looks like build output.
- **Announce the scope before scanning** so the user can redirect you.
- **Detect the stack and the providers early.** Look at manifests (`package.json`, `requirements.txt`, `pyproject.toml`, `Gemfile`, `go.mod`, `Cargo.toml`, `composer.json`) for AI SDKs.

## Step 1 — Find every LLM call site

You cannot audit calls you haven't found. Search for the signatures of every major provider, gateway, and framework:

```bash
# OpenAI / Anthropic / common patterns
grep -rn "openai\.\|anthropic\.\|createCompletion\|createChatCompletion\|messages.create\|\.chat\.completions" --include="*.ts" --include="*.js" --include="*.py" --include="*.rb" --include="*.go" --include="*.rs" .

# AI SDKs and frameworks
grep -rn "from openai\|import openai\|from anthropic\|import anthropic\|langchain\|llama_index\|vercel.*ai\|@ai-sdk\|llm\.\|ai_client" --include="*.ts" --include="*.js" --include="*.py" --include="*.rb" --include="*.go" .

# Gateway / proxy patterns
grep -rn "openrouter\|litellm\|helicone\|portkey" --include="*.ts" --include="*.js" --include="*.py" .
```

Group by file:line, note which provider/framework each uses, and treat the output as your work-list.

If you find nothing but have reason to believe there are AI calls (e.g. an `OPENAI_API_KEY` in `.env`), the integration may be behind a gateway or a thin wrapper — grep for `api_key`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and for the project's own client wrapper.

Read the actual call sites. The bugs live in *how* each call is configured and *what surrounds it* (the retry wrapper, the job that enqueues it, the loop it sits in), not in the SDK import.

## Step 2 — Audit each finding two ways

Two passes, because the most expensive guardrails are **absences across the whole system**, not bugs at a single line.

1. **Per-call-site** — walk each call and check it against the checklist below.
2. **System-level** — ask whether each *capability* exists *anywhere*. Is there any global spend ceiling? Any per-user/per-tenant cap? Any client-side concurrency limit? Any usage logging? A missing system-wide ceiling is usually the single most important finding, and no individual call site reveals it.

Before flagging, confirm. If a call looks uncapped, check for a wrapper or middleware that caps it. If retries look infinite, check the SDK's defaults (most SDKs retry 2 times by default — your custom wrapper on *top* of that is the multiplicative bug). Speculation isn't a finding; a traced call path is.

---

## The checklist

### Critical — can cause unbounded or runaway spend

| Issue | Detection hint | Why it costs / Bad → Good |
|---|---|---|
| **No ceiling on total spend anywhere** | Search for any budget/quota/spend gate: `budget`, `quota`, `spend`, `cost_limit`, `usage_limit`, `credits`, a daily/monthly counter checked before calls. | One scripted user, one runaway loop, or one viral day bills with no upper bound. → A budget check before the call (per-user *and* global) that refuses or queues once a ceiling is hit, plus an alert. |
| **Retrying errors that can never succeed** | Does retry code retry on *every* error, or only the ones worth retrying (`429` rate-limit, `500`/`503` server errors, timeouts)? Retrying a `400 bad request` or `401 unauthorized` will fail every time. | Every retry of a broken request still costs money and still fails. A bad prompt retried 5 times = 5× the cost for zero result. → Retry only rate-limit, server, and timeout errors; for the rest, fail right away. |
| **Retries that fire too fast and all at once** | Look for `for`/`while` retry loops, `sleep(constant)`, or retry libs set to a fixed delay. | A `429` error means "you're sending too fast." Retrying immediately, or on a fixed timer from many workers, means all the retries hit at the same instant — which makes the overload worse. → Wait longer after each failed try plus a little randomness so they don't all retry in sync, and stop after a few tries. |
| **Retries piled on top of retries** | Your own retry code *plus* the SDK's built-in retries *plus* the job queue's retries (Sidekiq/Celery/BullMQ). These multiply together. | 3 layers of 3 retries each = up to 27 paid attempts for one call. → Keep *one* layer of retries and turn the others off. Usually let the SDK handle the quick retries and the job queue handle the give-up case, and delete your own retry loop. |
| **A background job that fails and re-runs itself forever** | Find background jobs that call the AI. When one fails, does it retry with no limit on attempts? Does it re-run even when the thing it's working on was deleted? | A job that always fails re-runs every time the queue comes around, forever — and every attempt is a paid AI call. → Limit the number of attempts, give up after that, and skip the job entirely when the record it needs is gone. |
| **No cap on output tokens** | Check each call for `max_tokens` / `max_output_tokens` / `maxOutputTokens` / `max_completion_tokens` / `maxTokens` (names vary by provider). Flag calls that omit it. | Output tokens are the expensive ones (often 3–5× input). With no cap, a model that falls into a repetition loop generates until it hits the context window, and you pay for every token. → Always set an explicit output cap sized to the feature. |
| **An AI loop that can run forever** | Find `while`/`for` loops that call the model, add the tool result, and call again. Is there a cap on iterations, a time limit, and a deadline? | A model that keeps calling one more tool loops until something else breaks — and each turn re-sends the whole growing conversation, so the cost climbs faster and faster. → Cap the number of loops, set a time limit, and set a total spending limit for the whole run. |
| **Model returns empty or junk output and the code just retries it** | For generation/structured-output calls, is there any check for the model returning nothing, getting cut off, or repeating itself before retrying? | A bad response counts as a failure and you pay to run it again, over and over, often without recording it. → Detect the bad response (empty, cut off, or repeating), limit how many times you re-run it, and record every attempt so the cost is visible. |

### Important — wastes money consistently

| Issue | Detection hint | Why it costs / Bad → Good |
|---|---|---|
| **Re-sending the same prompt without caching** | Look for repeated calls with deterministic inputs: system prompts, few-shot examples, document chunks that don't change between requests. Is there any caching layer? | A long system prompt sent with every user message costs money every time. → Cache identical prefixes (most providers support prompt caching automatically for repeated prefixes — just keep the static part unchanged between calls). |
| **Sending more context than needed** | Does the code send full conversation history, entire documents, or large codebases when a smaller slice would work? | Context tokens are cheaper than output but still add up fast at scale. → Trim context to what the task needs: limit conversation history, chunk documents, use RAG instead of stuffing everything in. |
| **Using a bigger model than the task needs** | Is the task using GPT-4 or Claude Opus for classification, extraction, or summarization that a smaller model handles just as well? | Small/fast models are 10–50× cheaper. → Tier tasks: use the big model for hard reasoning, the small model for classification, extraction, rewrites. |

### Worth checking

| Issue | Detection hint | Why it costs / Bad → Good |
|---|---|---|
| **No usage logging or monitoring** | Is there any logging of token counts, cost, or request volume per user/endpoint? | You can't fix what you can't see. → Log token usage and estimated cost per call, with a dashboard or alert on anomalies. |
| **Rate limiting missing or too generous** | Is there any per-user or per-IP rate limit? Can one user burn the whole budget? | One heavy user (or a script) consumes the budget meant for everyone. → Per-user rate limits and concurrency caps. |
| **Streaming not used where it helps** | Long generations without streaming — user waits, and if they cancel, you still pay for the full generation. | Streaming lets you stop early when the user bails. → Use streaming for chat/real-time use cases. |

## Output format

```markdown
## LLM Cost Audit

**Scope:** [repo path or specific directory]
**Providers detected:** [list]
**Call sites found:** [count]

### Findings — ranked by severity

**1. [Finding title]**
**Severity:** [critical | important | worth-checking]
**Location:** `path/to/file:line`
**What:** [concrete description of the cost bug]
**Fix:** [specific, actionable fix with exact parameter names/config keys]
**Watch when applying:** [any risk to functionality]

### Summary
[X findings total: Y critical, Z important, N worth-checking]

### System-level gaps
[Any missing global guards: spend ceiling, per-user caps, usage monitoring, rate limiting]
```