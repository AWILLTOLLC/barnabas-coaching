---
source: https://barnabas.coach/agent-foundations-workshop.html
fetched: 2026-09-11
type: website
---

<<<EXTERNAL_UNTRUSTED_CONTENT id="4969eb3debacb6cd">>>
Source: Web Fetch
---
Working session
# Agents, harnesses,
and how to actually run them
 What the pieces are, which ones matter, and what to do first.
 Who's talking
## Aaron Williams
 Seattle. Two hats, and the deck sits under the second one.
 Merkle & Bloom · the day job
### Embedded IT ownership for laboratories
Principal Consultant. Senior technical leadership working on site inside biotech and other GxP environments, accountable for the whole picture rather than a ticket queue or a project brief. One client grew from 6 people to 60 with that environment underneath them.
Local and private AI is part of the same job: fully local LLM infrastructure with tight guardrails, a complete audit trail of what every agent did, and graph engineering across large existing data repositories.
[aaron@merkleandbloom.com](mailto:aaron@merkleandbloom.com)
 Barnabas Coaching · why this deck exists
### The same work, scaled down
Individuals and small businesses who want their agents to earn their keep. That runs from writing better prompts all the way to a full layer 4 agent and harness taking the tedious parts of a business off your hands.
If "layer 4 agent" means nothing to you yet, the next slide explains it, and the rest of the deck is how you get one running.
[aaron@barnabas.coach](mailto:aaron@barnabas.coach)
### The standard this deck holds itself to
Every number here is measured on my own hardware or taken from a vendor's own documentation. The agent used as the worked example is mine and it has been running 200 days. Where something isn't verified, the slide says so.
 How this works
## Seven blocks, and you interrupt whenever
 A
### The stack
Model, chatbot, agent, harness, session. What the words mean.
 B
### What it costs
Context windows, why long chats get expensive, what $20 buys.
 C
### The options
What is out there and where each one actually fits.
 D
### Channels
How you reach an agent, and why that quietly shapes it.
 E
### Memory
Why it decides whether any of this holds up over months.
 F
### Orchestration
One front door or ten agents. Delegating without it running away.
 G
### Behaviour
Skills, identity files, and rules an agent cannot break.
 Rule
### Stop me
If something sounds like magic, say so. All of it is mechanism.
 What do you want to hand off in 90 days that you do by hand today?
 Block A
## Four layers, and only one is unfamiliar
 Layer 1The modelA text predictor. GPT, Claude, Grok, Llama, Qwen. Raw capability, zero ability to do anything.
 Layer 2The chatbotChatbot = Model + Textbox. A model plus a text box. You type, it answers, it forgets. Nothing persists.
 Layer 3The harnessTriggers, tools, memory, scheduler, identity, guardrails, logs. The part that turns a predictor into a worker.
 Layer 4The agentAgent = Model + Harness. One job, one identity, running on your accounts, without you.
 Two years of headlines went to layer 1 getting better. Almost everything that changed what's possible in a business happened at layer 3.
### The question that sorts people instantly
Plenty of people describe ChatGPT as "their agent." If someone tells you about their agent, ask which harness they run. If they don't know what that means, they are describing layer 2, not layer 4.
 Block A · vocabulary
## The words, so nothing later is a guess
 The terms we all use, explained correctly. Clarity of language drives clarity of design, and a clean design is why your agent keeps working when someone else's falls over.
### Token
The unit everything is counted in. Roughly three quarters of a word. "Mukilteo" is about four. A page of prose is around 700.
### Turn
One exchange. You ask, it answers. That pair is a turn.
### Prompt
Everything handed to the model to produce one answer. Not just what you typed. Your question plus the instructions plus the history plus every tool it can reach.
### Conversation
What you see in the app. The thread of turns.
### Session
The live thread plus everything the model receives with it. In a chat app the conversation and the session are the same thing. In a harness a session can span channels, run in the background, and outlive the window it started in.
### Context window
How much fits in front of the model at one time. A capacity, fixed by the model.
### Compaction
What happens when the window fills. The system summarises the older middle of the conversation and drops the detail to make room.
### Reasoning (or effort)
The model thinking before it answers. Real work, charged like output. Turning it up can multiply what an answer costs several times over.
 Which of those did you think meant something different?
 Layer 1
## What the model actually does
 It predicts the next chunk of text. Sounds simple. It turns out to be incredibly useful.
### No memory
Close the tab and it's gone. Every conversation starts from zero.
### No hands
It can describe sending an email perfectly. It cannot send one.
### No clock, no trigger
It does nothing until a human types. It has no idea what time it is.
 It makes things up with total confidence because plausible-sounding is the only target it was ever given. Nothing inside it checks. A better model just misses less often (and misses more convincingly). Catching it is layer 3's job.
 Block A · the distinction that matters
## A chatbot "agent" and a harness agent are different animals
 Chatbot with agent featuresAgent in a harness
 Who starts itYou. Always.An event, a schedule, an inbound message
 Exists when you're awaynoyes, it's a running process
 IdentityA prompt you paste inFiles on disk. Name, values, rules, memory.
 MemoryThis conversationPersistent, searchable, accrues over months
 ReachableIn one appTelegram, Slack, Discord, email, webhook
 ToolsWhat the vendor shippedWhatever you give it, scoped per agent
 FailureBad answer, you ignore itBad action, already happened, in the log
 The testCan it act when nobody is typing? If no, it's layer 2 with a costume.
 Which AI tools you're paying for right now would pass that test?
 Block A · layer 3
## What's actually in a harness
 01
### Trigger
What wakes it. A message, a schedule, a webhook, another agent.
 02
### Tools
What it can do. Read a calendar, send a message, hit an API, run a script.
 03
### Memory
What survives the session. Facts, procedures, transcripts, search over all of it.
 04
### Identity
Who it is. Name, voice, values, standing instructions. Files, not vibes.
 05
### Guardrails
What it cannot do, enforced outside the model's judgment.
 06
### Logs
Every action, timestamped, readable later. Without this you have a rumor.
 Same model in two harnesses, wildly different outcomes. Which is why we're all sitting here.
 Block A · the unit of work
## What a session is, and why old ones are worth protecting
 A session is one continuous thread with its own running history. Everything said in it is available to the agent without being looked up.
 A new session is only a stranger if you let it be. A well-built harness starts one already holding its identity, its long-term memory of its own work, and a map of its environment. What it loses is the short-term stuff nobody wrote down. That difference is most of what block E is about.
 Why long is better
### You stop re-briefing
A months-old session knows the project, the constraints, what you already tried and rejected, and how you like things phrased. None of that has to be retrieved because it's simply present.
 Why it's hard
### Compaction is lossy and quiet
A session fills up. The harness then summarizes the middle to make room. Detail goes. You aren't told what went, and the agent doesn't know either. Enough rounds of that and the thread is a shadow of itself.
 The usual outcome
### People start over
The session gets vague, so you open a fresh one and re-explain everything. Most people live in that loop. It's why agents feel like they never quite learn you.
 Keeping a session alive takes three things: keep the always-loaded context small so you compact less often, write anything durable to disk the moment you learn it with a scheduled sweep behind it for whatever slipped, and keep it all searchable so what compaction drops is still recoverable. Hold onto those three. The next block is about what they cost you when you don't.
 Block B · the constraint
## A context window is a desk, not an inbox
 Everything the model needs has to fit on the desk at once. The system prompt, the tools it can use, everything said so far, your question, and the answer it's in the middle of writing.
### What's on the desk
System prompt and tool definitions. The whole conversation to date. Your new question. The reply being written. All of it, every turn.
### A capacity, not a budget
Fixed by the model. It doesn't grow because your conversation did. Claude's current top three hold about a million tokens. Qwen3.8 holds 256,000. GLM 5.3 Flash holds a million.
### Why long sessions go shallow
Long before anything errors, the history has crowded the desk enough that there's little room left to write. Answers get shorter and thinner and nobody can quite say why.
 Block B · the constraint
## Why the same question costs more later
 The model remembers nothing between turns. Every time you ask something, the whole conversation is sent again from the top.
 ~10k
Turn 10. Tokens sent to ask one question.
 ~50k
Turn 50. Same question, five times the freight.
 ~100k
Turn 100. "What did we decide about Tuesday" now costs ten times what it did at turn 10.
### Every turn pays for every turn before it
Nothing is remembered, so everything is re-read. To the model the conversation doesn't grow. It gets re-delivered in full, from scratch, every time.
### Tool results are the accelerant
One document read, one search, one database query can drop eight thousand tokens into the transcript. It stays there, re-sent on every turn after, long after it stopped being relevant.
 This is why a long chat feels sluggish and expensive even when you're asking easy things. You're not paying for the question. You're paying for the archive it's attached to.
 Block B · what it costs
## Four ways to pay for the same work
 Neither big vendor sells you tokens on a consumer plan. They sell messages, and how many you get depends on how heavy each one is.
 $20 · entry
### Fine for one agent
Claude Pro resets every five hours with a weekly cap on top, published as a multiplier rather than a number. ChatGPT Plus publishes no limit at all. Run three to five domain owners against it all day and you spend more time throttled than working.
 $100 · where businesses land
### The realistic tier
Claude Max 5x publishes at least 225 messages per five hours. ChatGPT's $100 tier is 5x Plus, with 50 premium-reasoning messages a week. Budget for this one if agents work on your behalf every day.
 OpenRouter · credits
### Pay per token, no caps
Prepaid credits, no subscription. No markup on inference, so you pay the provider's own rate; the fee is 5.5% on topping up. No message cap and no five-hour window. You pick the model per request, so a routine domain owner sits on GLM Flash while a hard one calls Fable.
 Local
### No allowance at all
No limit, no window, no throttle. You pay in electricity and hardware you already own. Nothing to run out of at 4pm on a Friday.
 Hybrid · what I run
### Both, on purpose
A fast cheap cloud model answers by default and delegates to a domain owner where one fits. Anything it must do itself goes to a local subagent. Cloud speed on hard thinking, near-zero cost on the narrow jobs.
### A plan stops you. Credits don't.
That cuts both ways. A subscription caps spend by capping your work. Credits never interrupt you, so a misbehaving agent can spend real money unwatched.
Cap it yourself: OpenRouter takes a per-key spending limit that resets daily, weekly or monthly, and auto top-up is optional. Its API reports usage and remaining budget, so a scheduled task checking every fifteen minutes warns you before the invoice does.
### Availability is not inclusion
Claude Pro shows Fable in the picker but doesn't count it against the plan allowance, so choosing it spends credits bought separately. Max includes it up to half your weekly limit. Whatever you are on, find out before it finds you.
 Block B · what it costs
## Same job, eight prices
 A task uses roughly the same tokens whichever model you point at it. Only the rate changes.
 ModelEmail
~500 tok506 4th St
~40,000 tokCompetitor study
~500,000 tok
 GPT-6 Astra$0.0170$0.6000$14.4000
 Claude Fable 5.1$0.0170$0.6000$8.2000
 GPT-5.6 Sol$0.0068$0.2400$5.7600
 Claude Opus 5$0.0085$0.3000$4.1000
 Claude Sonnet 5$0.0034$0.1200$1.6400
 GPT-5.6 Luna$0.0004$0.0130$0.3120
 GLM 5.3 Flash$0.0001$0.0039$0.0515
 Qwen3.8 27B, local$0.0000$0.0000$0.0000
### Cheaper is not equal
Sonnet reads the same 420,000 tokens for a fifth of the price, and on a job that suits it the answer is just as good. On hard reasoning Fable is meaningfully better and worth it. Pick the model the job needs.
### Local isn't the slow option
M5 Max, Qwen3.8 27B under Ollama: 90.4 tokens a second. Cloud-based Sonnet 5 and GLM 5.3 Flash benchmark around 62 to 63. OpenAI doubles input pricing above ~270,000 tokens, which is why Astra's heavy job is $14.40 and not $8.20. Anthropic and GLM charge no premium.
 Models differ in kind too. Some are text only, some read images and audio, some make pictures or video. OpenRouter reaches nearly all of them on one key and one balance, and both harnesses support it directly, so routing each task to the right model is a config line. That is the argument against a one-model setup.
 Block B · what it costs
## Two ways this bites, one fix
### The wall
You fill the window and something visibly breaks. The session compacts, goes vague, or refuses outright. At least you notice.
### The ceiling
Nothing breaks at all. Every message works. You burn a five-hour allowance in ninety minutes and get told to come back later, usually mid-thought on the thing you cared about.
### Same root, same fix
Both come from carrying too much in the window on every turn. Keep the always-loaded part small and you sit lower in the window, so you compact less often and each message costs less of your allowance.
 Which is the whole argument for a memory system. The point is carrying less. Keep the desk clear, write the durable things down, and pull them back only when they're needed.
 Block C
## Three different products get called the same thing
 Category 1
### Custom agent harnesses
OpenClaw, Hermes
You run them, on your hardware. Always listening, own their memory and identity, reachable on any channel, any model including ones running on your own machine.
 Category 2
### Assistant apps growing agent features
Claude Desktop, Codex, Grok Bot
Someone else runs them. Scheduled tasks, memory, connectors. Capable and improving fast, but you're a tenant.
 Category 3
### Rented vertical agents
CloseBot, Meta's Business AI
An agent built for one industry job, sold as a subscription. It lives entirely inside its provider's walled garden: their channels, their model, their logs. Purpose-built for the narrow thing. It extends only as far as the webhooks and integrations that vendor chose to offer.
 Most people who run agents seriously end up with all three: a rented one for the high-volume job, an assistant app for daily work, and a harness for anything they want to own.
 Where does the thing you named at the start actually live?
 Block C
## The five, side by side
 Who runs itModelsAlways listeningThe real tradeoff
 OpenClaw 2.0YouAny, incl. localyes, widest channel supportLargest ecosystem, strongest scheduler. Runs any skill or tool you can install, including things that need local files, local networks and hardware. More configuration surface, which is both the power and the work.
 HermesYouAny, incl. localyes, many channelsFewer moving parts, tight and opinionated by design. Same open tool surface as OpenClaw. Younger, so fewer people to ask.
 Grok BotxAIGrok onlyScheduled, not inboundSlickest onboarding. One vendor for model and runtime. ~$200/mo, early beta.
 Claude DesktopAnthropicClaude onlyCloud schedules, no inboundScheduled tasks run with your machine off. Real memory and connectors. No agent you can message.
 CodexOpenAIOpenAI onlyScheduled + event triggersStrong at code in isolated cloud containers. Nothing persists between runs. No access to your machine.
 Column three decides it for most people. The rest is taste.
 Both self-hosted options hand you the security posture. Same deal either way. Owning it means owning that.
 Block C
## What the cloud assistants give you, and where they stop
 Capable, improving quickly, and the right starting point for most people. The ceiling is a different shape than most expect.
### What they do well
- Scheduled tasks that run on the vendor's infrastructure, laptop asleep and app closed
- Memory that persists across sessions
- Connectors, skills and plugins, installed in a click
- Work triggered by Gmail, Slack and GitHub events
- Nothing to maintain, patch or secure
### Where they stop
- Nothing can message them. No inbound anything. Pull and schedule only.
- No local models, ever. Every request leaves your building.
- Whatever tools the vendor exposes, and nothing else. No local files beyond a granted folder, no local network, nothing you install yourself.
- One assistant, not a set of agents that own areas of your work
### The honest summary
The gap is scope. Memory you design, tools you write, agents that own a domain and hand work to each other, rules enforced outside the model's judgment: those are the next three blocks of this deck, and none of them are things these products are trying to do. Start here, and know what you'll want next.
Worth knowing too: a documented, reproducible bug stops cloud scheduled tasks reaching their connectors when they start on their own. One message into the same session and it works.
 Block C
## Where a rented vertical agent fits
### What you get
One job done properly on day one. No infrastructure, no model selection, no security posture to maintain, and someone else's phone rings at 2am. For a single high-volume job with a clear shape, this is usually the right call.
### What you give up
You configure inside their box. Their channels, their logging, their model, their roadmap. Nothing you learn transfers out, and when the second job comes along you rent again.
### Most of them can hand off
Most vertical agents can fire a webhook out when something happens. CloseBot and Meta's Business Agent both do. That means the rented agent doesn't have to be a dead end: it works the narrow job inside its walled garden, then hands the result to an agent you own, which can do everything the rented one can't.
Booked call goes out as a webhook, your agent picks it up, updates your records, preps the brief, tells you what it knows about them. The two categories work together rather than replacing each other.
### The pattern that works
Rent the vertical agent for the one job that pays for itself immediately. Build in a harness for work that's specific to you, changes often, or touches things you'd rather not put in someone else's system. Wire the first into the second.
 Block D
## The channel is an architecture decision
 How you reach your agent determines what it can be. Most people pick by habit and then spend a year working around it.
### Threading
Can it hold several parallel workstreams without them bleeding together?
### Privacy
Who else can read the transcript. Your agent's log is a record of your business.
### Reliability
Some channels go quiet and stay quiet. You won't get an alert.
### Reach
Files, voice, images, groups. Not every channel carries everything.
 Block D
## What each channel actually gives you
 ChannelThreadsFilesPrivacySetupNotes
 TelegramyesyesNot end-to-end~5 minThe consensus starting point. Works from a home server with no public IP. Voice included.
 DiscordnativeyesServer-visible~30 minBest structure for multiple agents. Buttons, forms, voice, presence.
 SlackyesyesWorkspace-visibleMediumThreading plus a built-in audit trail. Right answer if the team already lives there.
 Signalnoyesend-to-endHardPrivate by default. Painful setup, weak voice.
 iMessagenoyesend-to-endMediumEncrypted Apple device to Apple device. The bridge runs on your Mac, so that Mac is the trust boundary, not Apple.
 WhatsAppnoyesMetaHardReverse-engineered. Breaks when Meta changes things. Account-ban risk.
 MS Teamsyesno filesTenantMediumThreads but won't carry attachments. Surprising and annoying.
 SMSnonoCarrierMediumMaximum reach, minimum capability.
 EmailyesyesProvider reads itEasyUnderrated for anything that isn't urgent. Not private: most providers openly scan inboxes for ad targeting and training unless you self-host or pay for one that doesn't.
 Block D
## Threading matters less than you'd think
 One agent juggling three jobs needs threads to keep them apart. A coordinator with domain owners doesn't, because the agents already are apart.
### With one agent
Everything you say lands in one context. Ask about the listing and the ad account in the same stream and they blur together. Threads are the fix, so the channel choice is load-bearing.
### With domain owners
Your Leads agent and your Ads agent already have separate sessions, memory and credentials. Asking about both on a single unthreaded channel doesn't mix them, because they were never in the same place.
The architecture absorbs the job threading was doing.
### What threads still buy
Seeing several delegated jobs in flight at once, and keeping your own separate conversations with the coordinator from running together. Real, and a convenience rather than a requirement.
### The interface people forget
Both harnesses ship a browser interface, and it's where most heavy work happens: long pastes, file drops, editing config, reading back a transcript, several sessions side by side. Chat apps are for reaching the agent from your pocket.
 Block E · memory
## Two philosophies, neither one wrong
 The take going around is that Hermes has weak memory and OpenClaw's tiers run away with it over time. Both halves of that are wrong. They're multi-tiered systems that made opposite bets.
### Hermes bets on constraint
- Small always-loaded tier, enforced by hard character caps
- Over the cap, a write is refused until the agent consolidates
- Unlimited searchable session archive underneath it
- Skills the agent writes for itself act as procedural memory
- Eight pluggable memory backends, several of them free and self-hostable
### OpenClaw bets on capture
- Hybrid keyword and vector search across everything
- A nightly consolidation pass promotes notes into long-term memory. They call it dreaming.
- Daily working notes, indexed automatically
- Origin tracking on every chunk
- Same pluggable backends available
### Which is better depends entirely on you
Constraint means the system tells you no and makes you tidy up. Capture means it keeps everything and trusts retrieval to sort it out. Neither recalls reliably across many months on built-in memory alone, and both fix that the same way: bolt on a stronger memory backend. Those are not necessarily paid services. Supermemory, for one, is MIT-licensed and self-hosts from a single binary, and plenty of people simply build their own out of files and skills.
If you'd rather be forced to prune, Hermes. If you'd rather keep everything and sort through noise, OpenClaw. Pick the one that matches how you work.
 Block E
## Two things none of them do out of the box
 Gap 1
### Checking is a habit, not a mechanism
Ask it about a decision you made in April. The notes are on disk, the index is fine, and there's a written rule saying it must search before answering questions about past work.
That rule is enforced by the agent itself. Nothing in the pipeline stops it answering from whatever is in front of it. In one real incident mine searched, the right answer appeared in the results, and it asked me the question anyway. When the discipline slips it feels exactly like forgetting, because to you it is.
 Gap 2
### It never writes down how it did
It will faithfully remember that you prefer short emails. Nothing records that its last three drafts got rewritten, that you asked the same question four ways before giving up, or that delegating that job was a mistake.
Perfect recall of your preferences. No record at all of its own performance. It will make the same mistake next month, and the month after.
### The fix for gap 1 is architectural, not disciplinary
Sharpening the instruction helps a little and is still self-enforced. Runtime hooks would actually force it, and nobody has built that yet. What works today is grounding by construction: anything living in always-loaded context cannot be forgotten. So the fix for any recurring miss is to move that fact up a tier rather than to ask the agent to try harder.
 Not a knock on self-hosted. Both gaps are just as true of the cloud assistants, and there you have less room to do anything about them.
 Block E · what I actually run
## The layer I built on top
 Every session starts from zero, so nothing lives in the model's head and everything lives in files. The agent is 200 days old. The session isn't, I reset that constantly. Continuity lives in the files, not the thread.
 Tier 0 · always loaded
### Who and how
- SOUL.md persona, tone, when to act versus ask
- USER.md everything about the person. One place, sacred.
- AGENTS.md the operating manual
 Tier 1 · the index
### See it before you search for it
- MEMORY-L0.md one line per topic, ~20 lines
- A Right now header: current focus, refreshed in session and nightly
- MEMORY.md operational facts. Where credentials live, never what they are.
 Tier 2 · on demand
### Detail only when relevant
- memory/topics/*.md full context per subject
- Daily logs, DECISIONS.md, ERRORS.md, instincts.md
- Search runs on a small local embedding model. Nothing leaves the building.
 Everything is plain markdown. Greppable, diffable, no proprietary store. The search index is a convenience layer over the files and never the source of truth.
 Block E · the lesson
## Memory is a liability as much as an asset
 The classic failure isn't forgetting. It's remembering something that stopped being true, with total confidence, and never flagging it.
### The supersede rule
When something replaces an existing entry, the old entry gets edited rather than deleted. A line goes on top of it:
> superseded 2026-09-08 by: <new fact>The old fact stays visible with its replacement named. Stale and current never sit side by side looking equally true.
### Forgetting as a real operation
- Instincts start at low confidence and get deleted when they turn out wrong
- Promotion is gated: two separate sessions with citable evidence, never the same night a pattern is first seen
- Errors carry a prevention rule, so the same mistake changes the protocol rather than repeating
Most systems treat writing as the feature and never build the other half.
### What this doesn't solve yet
Supersede handles old versus new. It does nothing about two sources that disagree right now: a topic file and a wiki, a database and an imported archive. Today whichever the search ranks highest wins, and ranking is about phrasing, so the stalest thing in the pile can win by using your exact words.
Scoring each source by how much you trust it helps and doesn't settle it. Ranking which answer looks most relevant and deciding which source wins are two different jobs, and most systems only do the first.
 What does your agent still believe about you that stopped being true months ago?
 Block F
## You will end up with more than one agent
 Then the question stops being "can it do the task" and becomes "who's in charge."
 Option A
### Talk to all of them
You're the router. You remember which agent does what, which has the calendar, which one you told about the thing last week.
 Option B
### One Chief of Staff
You talk to one. It knows the others, holds the context, and routes. You stop being the switchboard.
 Option C
### Chief of Staff spawns whatever
No standing agents. The orchestrator creates helpers on demand, they work, they disappear.
 How many agents do you each have, and how do you decide which one to talk to?
 Block F
## Why a Chief of Staff beats ten solo agents
### What ten separate agents cost you
- You hold the routing table in your head
- Context splits ten ways and none has the whole picture
- You repeat yourself constantly
- You forget which one you told
- Each needs its own attention to stay useful
### What one front door buys
- One place to talk, from one channel
- Context accrues somewhere singular
- It knows what the others are for and when to involve them
- You describe outcomes instead of choosing tools
- One relationship to maintain instead of ten
 The real win is where things land. Everything you say goes into one memory instead of scattering across ten.
 Block F
## Who decides where a request goes?
### Config decides
You write down that messages from this channel go to that agent. Most specific rule wins. Same result every time, costs nothing.
Cannot mis-route.
### A model decides
The orchestrator reads the request and picks a specialist. Flexible, handles things you didn't anticipate.
Adds a guess and a token charge to every request, and it will occasionally pick wrong.
 Most people build the second because it feels smarter. The harnesses that have been around longest default to the first, and let the model decide only when config runs out.
 Block F
## Why you build a domain owner on purpose
 A standing agent that owns one area of your work, with its own identity, memory, credentials and history.
 01
### Learning compounds
A spawned helper does the job and evaporates. Everything it worked out is gone. A standing agent gets better at its domain every week.
 02
### Credentials stay scoped
Your Leads agent has the inbox. Your Ads agent has the ad account. Neither has the other. A spawned helper inherits whatever its parent had.
 03
### Cost is knowable
Five agents is five. Unbounded spawning is unbounded until someone caps it.
 04
### You can debug it
Open its history and read what it did. Spawned children are harder to find and sometimes still running.
 05
### It has a voice
A standing agent develops a way of working you come to trust. It's how you notice when something's off.
 The cost
### Memory has to be managed
Persistent state needs looking after, and memory that sticks around can be fed something wrong and keep it. That's one maintenance job with known fixes, the same ones from block B: provenance on every entry, scheduled review, and confidence that can be demoted. It's a maintenance job, and one you already know how to do.
 Block F
## Delegation is good. Unbounded delegation is the problem.
### What spawning buys you
Two real wins. You get parallel work, so five things get researched at once instead of in sequence. And a messy subtask runs in its own context, so a thousand lines of noisy output never lands in the conversation you care about.
Delegation earns its place. The shape of it is the whole question.
### What goes wrong without limits
Nothing tells a helper it can't create its own helpers. Two becomes six becomes twenty, each one paying for its own context. Work runs that you can't see, can't stop, and find out about on the bill.
It leaks instead of crashing. Nobody notices until the bill.
### How we know this is real
Claude Code shipped three separate limits in a single week last July: how many helpers at once, how many per session, and how deep the nesting can go. Nesting was switched off entirely for four days before coming back capped. OpenClaw ships its own depth and per-agent child limits. Those caps exist because the behavior wasn't bounded and it cost people money.
### The setup that keeps the upside
Let your domain owners delegate, and put a ceiling on it: two or three helpers at a time, one level deep, helpers cannot create helpers, and every run has a timeout. You keep the parallel work and the clean context, and you lose the runaway.
 Block F
## Where people land
### The shape that holds up
- One persistent coordinator holding memory and routing
- A small number of persistent domain owners, each with scoped credentials
- Each domain owner can spin up two or three helpers for parallel work in its own area
- Helpers can't create helpers. One level, always.
- Cheap model for routing, expensive model for thinking
### How they coordinate
Through a shared work queue rather than agents talking to each other. Both harnesses ship one now. Hermes calls it Kanban, OpenClaw calls it Workboard. Cards hold the work, workers claim them, and every handoff is a row a human can read.
At small scale a few shared files do the same job: a goal, a plan, a status, and an append-only log. Either way that log is your audit trail, and it's what makes the arrangement debuggable instead of mysterious.
 Capped delegation from a standing owner is the sweet spot. The owner keeps the memory and the keys, and borrows hands when it needs them.
 If you built three domain owners this month, what would they own?
 Block G
## Skills: capability without bloat
 A skill is a folder with instructions in it. The agent sees a one-line description of every skill it has, and reads the full thing only when it's relevant.
 Tier 1
### The list
Every skill's name and one-line description. Always loaded, costs almost nothing.
 Tier 2
### The instructions
Loaded only when the agent decides the skill applies.
 Tier 3
### The references
Deeper files, pulled in only if the instructions call for them.
 Fifty skills can sit installed and cost you almost nothing until one is needed. It's also why a skill's description matters more than its contents: the description is the only part that decides whether it ever gets opened.
 Block G
## Humanizer
 Strips the tells out of AI-written text. Roughly thirty patterns: inflated significance, vague attribution, hedging, the rule-of-three rhythm, "I hope this helps."
### Why it's on every essentials list
Your agents draft most of what goes out under your name, and the default register is recognizable at a glance. It needs no API key and no account, so there's no reason not to run it.
Hermes ships one in the default bundle, which tells you how settled the question is.
### Two honest caveats
There are several credible versions and no canonical one, so "install humanizer" is ambiguous advice. Pick one and stick with it.
None of them claim to beat AI detectors and there's no evidence they do. They fix how it reads, not whether a classifier flags it.
 Block G
## Ponytail
 Stops an agent overbuilding. Left alone, agents write far more than the job needs, because more code looks like more effort.
### What it does
Makes the agent walk a ladder before writing anything, and stop at the first rung that works.
- Does this need to exist at all?
- Is it in the standard library?
- Is it already a built-in feature?
- Is it in something you already installed?
- Is it a one-liner?
- Only then, write something new.
### Why you want it
Less code to read and less to pay for. The demo everyone quotes is an agent knocking out four hundred lines of custom date picker when browsers have shipped one for a decade.
It carves out safety, validation and anything you explicitly asked for, so it won't quietly simplify away something that mattered.
 Invoke it. Say "ponytail" or "give me the simplest thing that works." Installing a behavioral skill and never mentioning it usually means it just sits there.
 Block G
## Where the agent's personality lives
 FileAnswersScopeWhat goes in
 SOUL.mdWho is talking?Global, alwaysValues, tone, boundaries, how it handles being wrong. Two or three hundred words.
 IDENTITY.mdWhat do people see?GlobalName, avatar, how it presents itself externally.
 AGENTS.mdHow does work get done?Per projectProcedures, commands, output format, hard rules for this context.
 USER.mdWho am I?GlobalDurable facts about you it shouldn't need told twice.
 TOOLS.mdWhat may it use?GlobalTool policy, what needs approval, cost and frequency limits.
 MEMORY.mdWhat has it learned?GlobalFacts that accrued. Usually written by the agent, not you.
 The standard mistake is workflow steps in SOUL and personal preferences in AGENTS. Identity travels everywhere. Rules are scoped to where the work is.
### Don't write these from a blank page
I built a free tool for exactly this. It walks you through the questions and hands you the files.
[barnabas.coach → AI Agent Builder](http://barnabas.coach/agent-configurator.html)
 Block G
## Shorter files work better
 Anthropic's own guidance is blunt about it: a bloated instruction file causes the model to ignore the instructions you actually care about. They compete for attention with everything else in the window.
### The test for every line
Would removing this cause a mistake? If not, cut it.
No word count, on purpose. A target invites padding up to reach it, and the goal was never a number.
### Two diagnostics worth memorizing
It keeps breaking a rule you wrote? The file is too long and the rule is getting lost in it.
It asks things the file already answers? The wording is ambiguous, not missing.
### What not to put in
- Anything it could work out by looking
- Standard conventions it already follows
- Anything that changes often
- "Write clean code"
- Someone else's file, unedited
 Block G
## A rule it follows, and a rule it can't break
 There's no RULES file. People go looking for one. Hard constraints don't live in markdown, and understanding why is the difference between an agent you trust and one you hope about.
 Layer 1Instruction filesSOUL, AGENTS, TOOLS. Advisory. Competes for attention with everything else. Buried rules get deprioritized as context fills.
 Layer 2Tool gates & hooksDeterministic. Code that runs before the tool does and can cancel it. The model never gets a chance to reason around it.
 Layer 3Harness & sandboxHardest. Permission modes, allow-lists, filesystem and network isolation. The check happens outside the agent entirely.
 Layer 4GovernancePolicy, human checkpoints, audit. More a discipline than a product, and the weakest layer in practice.
 Block G · the proof
## The same agent, twice
 Someone gave an agent three rules it must not break, put them in the instruction file, and tested it.
### Rules written as instructions
2 of 3 broken
It confirmed a booking with no payment verified, and accepted fifteen guests against a stated maximum of ten. The rules were right there in the file. It read them and did it anyway.
### Same rules as a gate
3 of 3 held
No false alarms. A gate is a small piece of code that runs before the action does. It sees what the agent is about to do, decides no, and hands back a refusal. The model never gets the chance to talk itself into it.
 Every harness has somewhere to put one. The names differ and the idea doesn't: a check that lives outside the agent's judgment.
 Instruction files are for preferences. The harness is for rules. Writing something you truly cannot allow into a markdown file and trusting it is the most common way people get surprised.
 Block G · from 200 days of running one
## Five things that took me months to learn
 01
### Two channels, two permission levels
My main session runs in the web interface with elevated rights. iMessage gets its own sessions with reduced ones, so nobody holding my phone can do damage.
It doubles as a live memory test. The channels share nothing except what got written to disk, so if I tell Main something and iMessage hasn't heard, my memory system just failed in front of me.
 02
### Vague guidance, vague behaviour
I told mine it could handle "very tiny" tasks inline. Very tiny to me and very tiny to it were different things, and it worked inline 80% of the time when I wanted a subagent.
Numeric criteria beat adjectives every time. A counter it can read beats a word it has to interpret.
 03
### Let it finish, then ask why
When it does something wrong I don't interrupt. It completes the task, then I ask it to work out what caused the error.
The wording matters: this isn't a knock on you, we need to know why it happened so future sessions remember. That usually ends as an entry in DECISIONS or a change to the nightly pass.
 04
### "You're right, I'll fix that" means nothing
Correct an agent and it will agree warmly and promise to do better. There is no mechanism behind that promise, and it usually doesn't.
Point at the rules instead of the agent. The failure happened because the rule wasn't clear enough, and the rule is the thing you can actually change. Two or three rounds sometimes.
 05
### Use the secrets store
Both harnesses ship one. It's the right thing for security, and it also means a fresh session finds the credential it needs instead of stopping to ask you where it lives.
 The thread
### Never ask the model that failed to catch its own failure
Every fix above moves the check outside the agent's judgment: a second channel, a number instead of a word, a nightly pass, a log line the session can't skip.
 Close
## One thing each, this week
### New to this
One agent, one channel, one job you can check on in a week. Something low stakes, and something you would notice if it went wrong.
### Already running one
Pick one: a stronger memory backend, moving routing from judgment to config, or turning a standing instruction into an actual gate.
### Everyone
Move one fact you keep re-typing into always-loaded context. Smallest possible version of the whole idea.
 The trap right now is designing a nine-agent system before running one. Run one badly first. You will learn more in a week of that than from another afternoon like this.
 Barnabas Coaching · Seattle
# Want one of these
built for you?
 Happy to talk it through, whether you want help standing one up or just a second opinion on what you have.
### Free call, no pitch
[aaron@barnabas.coach](mailto:aaron@barnabas.coach)
[barnabas.coach](http://barnabas.coach)
 0:00
 notes
 theme
<<<END_EXTERNAL_UNTRUSTED_CONTENT id="4969eb3debacb6cd">>>
