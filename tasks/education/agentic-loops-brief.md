# Agentic Loops: The Engine That Makes AI Feel Alive

**Workshop Section: "What Comes Next" — Final 30 Minutes**
**Duration:** 30 minutes of live presentation + 10 minutes Q&A
**Target Length:** 2,500-3,000 words
**Audience:** Technically curious newcomers who understand harnesses (OpenClaw, Claude Code, Hermes) but haven't seen the loop in action

---

## 1. The Core Loop: Perceive → Reason → Act → Observe → Repeat

### The Big Idea: An Agent Is Just a `while` Loop

Let's start with the simplest possible mental model: **an agent is a `while` loop whose body reads its own output.**

In traditional programming, you write:
```python
while not done:
    # do something
    # update state
    # check if done
```

In an agent loop, the "body" is a language model, and the "state" is the conversation history + tools + files. The loop terminates when the model decides it has an answer, when it hits a max-iteration limit, or when some external condition is met.

The loop has five distinct phases:

1. **Perceive** — The model reads what's in its context window: the user's original request, all previous tool calls and results, any memory files it's been told to consult.
2. **Reason** — The model thinks: "What do I know? What do I need? What tool should I call next? Or should I just give an answer?"
3. **Act** — The model emits a structured tool call (usually JSON): `{"tool": "search", "args": {"query": "flights to Tokyo"}}`.
4. **Observe** — The harness executes the tool, captures stdout/stderr, maybe runs a test, maybe reads a file back. This becomes the "observation" — the reality check on the model's action.
5. **Repeat** — The observation is appended to the context window, and the model sees it in the next iteration. It can now reason about what just happened.

### A Concrete Example: "Find Me Flights to Tokyo"

Let's walk through a realistic multi-turn interaction where a user asks: *"Find me the cheapest flight from San Francisco to Tokyo next week, economy class."*

**Iteration 0 (Initial State):**
- Context: Just the user's message
- Model's thought: "The user wants flights. I need to search. I have a `search_flights` tool."
- Model emits:
```json
{
  "tool": "search_flights",
  "args": {
    "origin": "SFO",
    "destination": "NRT",
    "departure_date": "2026-09-14",
    "return_date": "2026-09-21",
    "class": "economy"
  }
}
```
- Harness action: Calls an external API (maybe Google Flights, Skyscanner, or an internal database). Returns a JSON response with 3 options:
```json
{
  "flights": [
    {"price": 892, "airline": "United", "duration": "11h 30m", "stops": 1},
    {"price": 1047, "airline": "ANA", "duration": "10h 45m", "stops": 0},
    {"price": 756, "airline": "Jetstar", "duration": "14h 20m", "stops": 2}
  ]
}
```

**Iteration 1:**
- Context: User message + tool call + tool result (now ~400 tokens)
- Model's thought: "Got results. The cheapest is $756 with Jetstar but 2 stops. Should I present this, or search for more? Let me check if there's a better balance of price vs. convenience."
- Model emits:
```json
{
  "tool": "search_flights",
  "args": {
    "origin": "SFO",
    "destination": "NRT",
    "departure_date": "2026-09-14",
    "return_date": "2026-09-21",
    "class": "economy",
    "max_stops": 1
  }
}
```
- Harness action: Calls API again with modified params. Returns 2 options:
```json
{"flights": [{"price": 892, ...}, {"price": 934, ...}]}
```

**Iteration 2:**
- Context: ~600 tokens now (user + 2 tool calls + 2 results + initial message)
- Model's thought: "Okay, the best non-2-stop option is $892 United. That's a reasonable price. I should present this with the caveats."
- Model emits:
```json
{
  "tool": "present_result",
  "args": {
    "message": "Cheapest flight with ≤1 stop: United $892, 11h 30m, 1 stop. The absolute cheapest is Jetstar $756 with 2 stops. Which do you prefer?"
  }
}
```
- Harness action: Sends the message back to the user. The user might reply "United, book it" — which triggers a **new loop** with a fresh context window.

**Key Observation:** The model never "knows" the flight prices until the harness executes the tool. The model is guessing based on its training, but the observation is ground truth. The loop lets the model **update its mental model of reality** based on what actually happened.

### The Termination Condition: When Does the Loop Stop?

The loop stops when:
- The model emits a "final answer" tool (like `present_result` or `write_file` with a note saying "done")
- The model's last message contains no tool calls (some harnesses treat this as "done")
- A max-iteration limit is hit (e.g., 20 iterations) — this is a **safety guard** to prevent infinite loops
- A timeout expires (e.g., 5 minutes) — prevents hanging forever
- A cost threshold is exceeded (e.g., $10 in API calls) — prevents bill blowups
- An external condition is met (e.g., a cron job wakes up and finds a new task)

In practice, **the model's own confidence** is the primary termination signal, but it's imperfect. That's why we need guards: if the model loops 20 times claiming "almost there," the harness should step in and say "okay, you're stuck, here's what you've tried."

---

## 2. Why the Loop Matters: From Stateless Function to Agent

### A Single Model Call Is Just a Function

Before the loop, a language model is a **stateless function**:
```python
def model(prompt):
    return response  # No memory of previous calls
```

If you call it twice with the same prompt, you get the same response. It doesn't know what you did last time. It doesn't remember your name. It doesn't know you asked it to "fix the bug" and it already tried once.

### The Loop + Context Window = State

The loop **adds state** by accumulating everything in the context window:
- User's original request
- All tool calls the model made
- All observations from the harness
- Any memory files it's been told to read
- Any intermediate conclusions it drew

This is why the **context window** is the agent's working memory. It's like RAM for a computer: fast, limited, and cleared when the session ends (unless you write to long-term memory files).

### Connecting to Harness Concepts They Already Know

They learned about:
- **Tools** — The `search_flights`, `git_diff`, `send_email` functions the model can call
- **Sessions** — The conversation history that persists across turns
- **Channels** — The input/output mechanism (webchat, iMessage, Discord)
- **Memory files** — Long-term storage like `memory/YYYY-MM-DD.md`, `SOUL.md`, `AGENTS.md`

The loop **ties all of these together**:
- Tools are called **inside** the loop
- Sessions are the **container** for the loop's history
- Channels are the **boundary** where user input enters and output exits
- Memory files are the **long-term store** that the loop can read/write to avoid filling the context window

**Analogy:** Think of the harness as a car, the context window as the dashboard, the tools as the steering wheel and pedals, and the loop as the driver. The driver (loop) reads the dashboard (context), presses the pedals (tools), sees where the car goes (observations), and keeps driving until it reaches the destination.

---

## 3. Loop Mechanics in Real Harnesses

### Tool-Call Parsing and Validation

Most harnesses use **structured output** (JSON Schema) to parse tool calls. The model emits:
```json
{
  "tool": "git_diff",
  "args": {"path": "src/"}
}
```

The harness:
1. Validates the JSON is well-formed
2. Validates the `tool` name exists in the registered tools
3. Validates the `args` match the tool's schema (e.g., `path` must be a string, not a number)
4. If validation fails, the harness sends an error back to the model: `"Error: tool 'git_diff' expects 'path' as a string, got number"`

This is critical: **the model is a probabilistic text generator, not a deterministic programmer.** It might emit:
```json
{"tool": "git_diff", "args": {}}  # missing required arg
{"tool": "nonexistent_tool", "args": {}}  # wrong tool name
{"tool": "git_diff", "args": {"path": 123}}  # wrong type
```

The harness must catch these and either:
- Send an error observation (model can try again with corrected args)
- Auto-correct (e.g., convert `"123"` to `123`)
- Fail fast (if the tool is critical)

### Tool Execution Sandboxing

Some harnesses (especially CLI tools like Claude Code) run tools in a **sandbox**:
- The `exec` tool runs `git diff src/` in a subprocess
- The `read_file` tool reads `/path/to/file.txt` with file permissions
- The `search_web` tool calls an external API with rate limits

Sandboxing prevents:
- **Infinite loops** — a tool that calls itself forever
- **File system damage** — `rm -rf /` (though most harnesses restrict to the workspace)
- **API abuse** — rate limits, billing overages
- **Side effects** — sending an email when the model meant to draft one

**Best practice:** Every tool should have a **dry-run mode** and a **confirmation step** for destructive actions.

### Retries and Error Feedback

When a tool fails (e.g., API returns 500, file not found), the harness can:
- **Retry** — automatically retry with exponential backoff (e.g., wait 1s, 2s, 4s, 8s)
- **Fail fast** — return the error to the model immediately
- **Transform the error** — convert a raw API error into a model-friendly message: `"Search API returned 500: trying with a different provider..."`

The model sees the error in the observation and can:
- Try a different tool
- Adjust its args
- Give up and report failure
- Ask the user for clarification

### Max-Iteration, Timeout, and Cost Guards

Real-world harnesses have **hard limits** to prevent runaway agents:

| Guard | Typical Value | Purpose |
|-------|---------------|---------|
| Max iterations | 10-50 | Prevent infinite loops |
| Timeout | 1-10 minutes | Prevent hanging forever |
| Cost cap | $1-$10 | Prevent API bill blowups |
| Token limit | 128K-200K context window | Prevent OOM |

These guards are **safety nets**, not features. If the agent hits the max-iteration limit, it means the loop control is broken. The harness should:
- Log the full conversation
- Report to the user: "Agent ran for 20 iterations without finishing. Here's what it tried: [summary]"
- Optionally, **summarize** the conversation and ask the user if they want to continue

### Streaming vs. Blocking

There are two architectures for tool execution:

**Blocking (synchronous):**
- Model emits tool call
- Harness waits for tool to finish
- Observation is appended
- Next iteration begins
- **Pros:** Simple, deterministic, easy to debug
- **Cons:** Slow, blocks the user, tool errors halt the entire loop

**Streaming (asynchronous):**
- Model emits tool call
- Harness fires and continues to next iteration
- Tool results arrive later and are appended when ready
- **Pros:** Faster, non-blocking, tools can run in parallel
- **Cons:** Complex, race conditions, harder to debug

Most current harnesses (OpenClaw, Claude Code) use **blocking** for simplicity. Streaming is the next evolution.

---

## 4. Context Window as the Loop's Working Memory

### What Accumulates Each Iteration

Each iteration adds:
- The model's tool call (10-100 tokens)
- The observation (50-500 tokens, depending on tool)
- Sometimes intermediate reasoning (if the harness logs it)

After 10 iterations, you might have:
- User message: 50 tokens
- 10 tool calls: ~500 tokens
- 10 observations: ~2000 tokens
- Total: ~2550 tokens

This is tiny compared to a 128K context window, but it **adds up**. After 50 iterations, you're at ~12K tokens. After 100 iterations, ~25K. After 200 iterations, ~50K. You start eating into your context budget.

### Token Growth Per Turn

**Rule of thumb:** Each iteration adds 100-500 tokens (tool call + observation). The exact amount depends on:
- Tool complexity (simple `echo` vs. `search_web` with 10 results)
- Observation verbosity (raw API response vs. summarized)
- Whether the harness logs intermediate reasoning

**Optimization:** Summarize old observations. After iteration 10, the harness can compress iterations 1-5 into a summary: "Tried searching flights with 3 different params, got 5 options, cheapest was $756."

### Compaction and Summarization

Some advanced harnesses use **context compaction**:
- After every N iterations, summarize the last M iterations
- Replace the raw tool calls/observations with a paragraph
- Keep only the most recent N iterations in full

This is like **garbage collection** for AI agents. It prevents context overflow but loses some detail.

**Trade-off:** Summarization saves tokens but might lose edge cases. If the model needs to debug a specific tool failure, it might need the raw observation, not a summary.

### Memory Files as Long-Term Store

This is where **memory files** (like `memory/YYYY-MM-DD.md`, `SOUL.md`, `AGENTS.md`) come in. The loop can:
- **Read** memory files at the start of each iteration (e.g., "what did I learn yesterday?")
- **Write** memory files at the end of each iteration (e.g., "here's what I did today")
- **Query** memory files with semantic search (e.g., "find all instances where I searched for flights")

**Retrieval vs. Stuffing:**
- **Stuffing** — Read the entire memory file and append it to the context window. Simple but wasteful.
- **Retrieval** — Use semantic search to find relevant chunks (e.g., "find memories about flights") and only include those chunks. More complex but efficient.

**Best practice:** Use retrieval for large memory files (e.g., 100+ pages of daily notes). Stuffing is fine for small files (<10 pages).

---

## 5. Classic Patterns and Named Techniques

### ReAct: Reason + Act Interleaved

**ReAct** (Reason + Act) is the foundational pattern for agentic loops. It was introduced in the paper *"ReAct: Synergizing Reasoning and Acting in Language Models"* (Yao et al., 2022).

The pattern interleaves reasoning and action:
```
Thought: What do I know? What do I need?
Action: [tool call]
Observation: [result]
Thought: What does this mean?
Action: [next tool call]
...
Final Answer: [conclusion]
```

**Why it works:** The model doesn't just act blindly. It reasons about what it knows, then acts, then reasons about the result, then acts again. This is more robust than "act first, reason later."

**Example:**
```
Thought: The user wants flights. I have a search_flights tool.
Action: {"tool": "search_flights", "args": {"origin": "SFO", ...}}
Observation: {"flights": [...]}
Thought: Got results. The cheapest is $756. Should I present this or refine?
Action: {"tool": "search_flights", "args": {"origin": "SFO", "max_stops": 1}}
Observation: {"flights": [...]}
Thought: Best non-2-stop option is $892. I'll present this.
Final Answer: "Cheapest flight with ≤1 stop: United $892..."
```

### Plan-Then-Execute vs. Interleaved

There are two main strategies:

**Plan-Then-Execute (PTE):**
- First iteration: model writes a plan (e.g., "Step 1: search flights, Step 2: compare prices, Step 3: present results")
- Subsequent iterations: execute each step in order
- **Pros:** Structured, predictable, easy to debug
- **Cons:** Inflexible, model might realize the plan is wrong mid-execution

**Interleaved (ReAct):**
- Model reasons and acts in the same iteration
- **Pros:** Flexible, adaptive, can change direction mid-stream
- **Cons:** Harder to debug, might loop unnecessarily

**Hybrid approach:** Start with a plan, but allow the model to revise it mid-execution. This is what most advanced agents do.

### Reflection / Self-Critique Passes

After a few iterations, the model can **reflect** on its own work:
```
Thought: I've tried 3 search strategies. Let me review what worked and what didn't.
Action: {"tool": "reflect", "args": {"summary": "Search 1: no stops, got 2 results. Search 2: max 1 stop, got 3 results. Search 3: max 2 stops, got 5 results. Cheapest was $756 with 2 stops."}}
Observation: [reflection output]
Thought: Okay, the cheapest option is $756 but with 2 stops. Should I present this or search for a better balance?
Action: {"tool": "search_flights", "args": {"max_stops": 1}}
```

This is like a **code review** for the agent's own reasoning. It helps catch errors and improve decisions.

### Subagent Delegation and Fan-Out / Fan-In

**Subagent delegation:**
- Main agent spawns a subagent for a specific task (e.g., "search flights")
- Subagent runs its own loop, returns a result
- Main agent continues with the result

**Fan-out / Fan-in:**
- Main agent spawns N subagents in parallel (e.g., "search flights on 3 different APIs")
- Subagents run concurrently
- Main agent aggregates results (fan-in)

This is **parallelism** for agents. It's useful when:
- Tasks are independent (e.g., search 3 APIs)
- You want to avoid blocking (e.g., run 10 tools in parallel)
- You want to scale (e.g., 100 subagents for 100 users)

**Example:**
```
Main agent: "I need to find flights. Let me ask 3 subagents to search 3 different APIs."
Subagent 1: [searches Skyscanner]
Subagent 2: [searches Google Flights]
Subagent 3: [searches Kayak]
Main agent: "Got 3 results. Let me compare them and present the best option."
```

### Watchdogs and Wake Conditions

**Watchdogs** are external monitors that:
- Watch for a condition (e.g., "new email arrived")
- Wake up the agent when the condition is met
- Optionally, trigger a specific task

**Wake conditions** include:
- **Cron** — Run at 9am every day
- **Event-driven** — New email, new file in a folder, new GitHub issue
- **Manual** — User sends a message
- **Health check** — Agent is stuck, watchdog wakes it up and resets it

This is how agents become **persistent** rather than ephemeral. They don't just run once and die; they keep running, waiting for the next trigger.

---

## 6. Failure Modes the Audience Will Hit

### Infinite Loops / Stuck Retries

**What happens:**
- Model keeps calling the same tool with the same args
- Tool keeps returning the same result
- Model thinks it's "almost there" but never finishes

**Why it happens:**
- Model is overconfident ("I'm 99% done, just one more check")
- Tool is flaky (returns different results each time)
- Model doesn't understand the observation (e.g., "API returned 500" but model thinks it's a success)

**How to fix:**
- **Max-iteration guard** — Stop after N iterations
- **Change detection** — If the last M observations are identical, break the loop
- **Exponential backoff** — Wait longer between retries
- **User intervention** — Ask the user: "Agent is stuck. Do you want to continue or cancel?"

### Context Overflow

**What happens:**
- Context window fills up
- New observations are truncated or dropped
- Model loses earlier context (e.g., "what was the user's original request?")

**Why it happens:**
- Too many iterations
- Large observations (e.g., 10KB API responses)
- No compaction or summarization

**How to fix:**
- **Context compaction** — Summarize old iterations
- **Memory files** — Offload to long-term storage
- **Token budget** — Stop when you hit 80% of the context window
- **Sliding window** — Keep only the last M iterations

### Tool Errors Compounding

**What happens:**
- Tool 1 fails, model tries to recover
- Tool 2 fails, model tries to recover
- Model gets confused, makes wrong decisions

**Why it happens:**
- Model assumes tools always work
- Model doesn't handle errors gracefully
- Harness doesn't provide clear error messages

**How to fix:**
- **Error transformation** — Convert raw errors into model-friendly messages
- **Retry with backoff** — Automatically retry failed tools
- **Fallback tools** — Have a backup tool if the primary fails
- **Error logging** — Log all errors for debugging

### Model Claims Success Without Verification

**What happens:**
- Model says "Done!" but the file is empty
- Model says "Email sent!" but the API returned 500
- Model says "Bug fixed!" but the tests still fail

**Why it happens:**
- Model is overconfident
- Model doesn't verify the result
- Harness doesn't require verification

**How to fix:**
- **Verification tools** — Require the model to run tests or read back the file
- **Assertion checks** — After a tool call, check if the result matches expectations
- **Read-back checks** — After writing a file, read it back and compare
- **Human-in-the-loop** — Ask the user to confirm before marking "done"

### Hallucinated Tool Calls

**What happens:**
- Model calls a tool that doesn't exist
- Model calls a tool with wrong args
- Model calls a tool and claims it worked, but the harness never executed it

**Why it happens:**
- Model is hallucinating (probabilistic text generation)
- Model doesn't know the tool schema
- Model is overconfident

**How to fix:**
- **Tool validation** — Validate tool name and args before execution
- **Schema enforcement** — Require JSON Schema for tool args
- **Error feedback** — Send the error back to the model so it can correct
- **Tool registry** — Maintain a list of available tools and let the model query it

---

## 7. A Worked "Day in the Life" Trace

Let's trace a **multi-step task end-to-end** with 7 loop iterations.

**User Request:** "Fix the bug in src/login.py where the password hash is too short."

**Iteration 0:**
- Context: User message
- Model thought: "Need to read the file first. I have a `read_file` tool."
- Model action: `{"tool": "read_file", "args": {"path": "src/login.py"}}`
- Observation: File content (200 lines, including the bug)

**Iteration 1:**
- Context: User message + tool call + file content
- Model thought: "Found the bug. Line 45: `hash = sha256(password[:8])`. Should be `sha256(password)`. Let me read the tests first to make sure I don't break them."
- Model action: `{"tool": "read_file", "args": {"path": "tests/test_login.py"}}`
- Observation: Test file (50 lines)

**Iteration 2:**
- Context: ~3KB tokens
- Model thought: "Tests look simple. Let me fix the bug and run the tests."
- Model action: `{"tool": "edit_file", "args": {"path": "src/login.py", "edits": [{"old_text": "sha256(password[:8])", "new_text": "sha256(password)"}]}}`
- Observation: "File edited successfully"

**Iteration 3:**
- Context: ~3.5KB tokens
- Model thought: "File edited. Now run the tests to verify."
- Model action: `{"tool": "exec", "args": {"command": "pytest tests/test_login.py"}}`
- Observation: "PASSED (2 tests)"

**Iteration 4:**
- Context: ~4KB tokens
- Model thought: "Tests passed. Let me also run the full test suite to make sure I didn't break anything else."
- Model action: `{"tool": "exec", "args": {"command": "pytest"}}`
- Observation: "PASSED (150 tests)"

**Iteration 5:**
- Context: ~4.5KB tokens
- Model thought: "All tests passed. Let me check the git diff to see what changed."
- Model action: `{"tool": "exec", "args": {"command": "git diff src/login.py"}}`
- Observation: "Diff shows 1 line changed"

**Iteration 6:**
- Context: ~5KB tokens
- Model thought: "Bug fixed, tests pass, diff looks correct. Time to present the result."
- Model action: `{"tool": "present_result", "args": {"message": "Bug fixed in src/login.py. Changed line 45 from `sha256(password[:8])` to `sha256(password)`. All 150 tests pass. Git diff: [show diff]"}}`
- Observation: User sees the result

**Total:** 7 iterations, ~5KB context, 5 tool calls, 2 user interactions (initial request + final result)

**Key Observation:** The agent didn't just "fix the bug" in one shot. It **reasoned**, **acted**, **observed**, and **repeated** until it was confident. The loop gave it the flexibility to adapt (e.g., "let me run the full test suite first") and the safety to verify (e.g., "tests passed, so I'm done").

---

## 8. What to Learn Next

### Recommended Resources

**Papers:**
- **"ReAct: Synergizing Reasoning and Acting in Language Models"** (Yao et al., 2022) — The foundational paper for interleaved reasoning + action
- **"Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"** (Wei et al., 2022) — How to make models reason step-by-step
- **"Toolformer: Language Models That Teach Themselves to Use Tools"** (Schick et al., 2023) — How models learn to call tools

**Harness Docs:**
- **OpenClaw** — https://github.com/openclaw/openclaw (CLI harness with sessions, channels, memory files)
- **Claude Code** — https://github.com/anthropics/anthropic-quickstarts/tree/main/claude-code (CLI tool for Anthropic models)
- **Hermes** — https://github.com/hermes/hermes (multi-agent orchestration)
- **LangChain** — https://python.langchain.com (Python framework for agents)
- **LlamaIndex** — https://docs.llamaindex.ai (RAG + agents)

**Tool Ecosystem Layer:**
- **MCP (Model Context Protocol)** — https://modelcontextprotocol.io (standardized tool interface for agents)
- **Function calling docs** — OpenAI, Anthropic, Google all have their own function calling schemas

### Concrete Next Steps

1. **Read the ReAct paper** — Understand the core pattern that powers most agents
2. **Play with a CLI harness** — Install OpenClaw or Claude Code and run a few tasks
3. **Build a simple agent** — Start with a `while` loop that calls one tool and prints the result
4. **Add memory** — Write to `memory/YYYY-MM-DD.md` after each iteration
5. **Add a watchdog** — Use cron to wake up your agent every hour

---

## Discussion Questions for Closing Slide

1. **"If an agent is just a `while` loop, what makes it feel 'alive' to users?"** — Encourage discussion about the perception of agency vs. the reality of a simple loop.

2. **"What's the hardest failure mode to debug: infinite loops, context overflow, or tool errors? Why?"** — Prompt debate about trade-offs and which guardrails matter most.

3. **"If you could add one new tool to your agent's toolbox, what would it be and why?"** — Creative thinking about what capabilities agents are missing today.

---

## Appendix: Analogy Cheat Sheet

**OODA Loop (Military):** Observe → Orient → Decide → Act. The agent loop is basically OODA with a language model doing the "Orient" and "Decide" steps.

**While Loop with Self-Output:** In traditional programming, you read input from a file or user. In an agent loop, you read your own previous output as the new input.

**Driver and Dashboard:** The harness is the car, the context window is the dashboard, the tools are the steering wheel and pedals, and the loop is the driver. The driver (loop) reads the dashboard (context), presses the pedals (tools), sees where the car goes (observations), and keeps driving until it reaches the destination.

**Recursive Function:** Like a recursive function that calls itself with modified arguments, but the "arguments" are the conversation history + tool results.

**Scientific Method:** Hypothesize (reason) → Experiment (act) → Observe results → Revise hypothesis (repeat).

---

**Word Count:** ~3,200 words
**Format:** Markdown with clear headings for slide carving
**Tone:** Technical but accessible, pedagogical, analogy-rich
