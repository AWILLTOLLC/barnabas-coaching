---
source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
fetched: 2026-09-11
type: website
---

<<<EXTERNAL_UNTRUSTED_CONTENT id="b970f6dcfab51a04">>>
Source: Web Fetch
---
[Skip to content](#start-of-content)
 [All gists](/discover)
 [Back to GitHub](https://github.com)
 [Sign in](https://gist.github.com/auth/github?return_to=https%3A%2F%2Fgist.github.com%2Fkarpathy%2F442a6bf555914893e9891c11519de94f)
 [Sign up](/join?return_to=https%3A%2F%2Fgist.github.com%2Fkarpathy%2F442a6bf555914893e9891c11519de94f&source=header-gist)
 /
 [Sign in](https://gist.github.com/auth/github?return_to=https%3A%2F%2Fgist.github.com%2Fkarpathy%2F442a6bf555914893e9891c11519de94f) [Sign up](/join?return_to=https%3A%2F%2Fgist.github.com%2Fkarpathy%2F442a6bf555914893e9891c11519de94f&source=header-gist)
 Instantly share code, notes, and snippets.
# [karpathy](/karpathy)/[llm-wiki.md](/karpathy/442a6bf555914893e9891c11519de94f)
 Created
 April 4, 2026 16:25
- [Download ZIP](/karpathy/442a6bf555914893e9891c11519de94f/archive/ac46de1ad27f92b28ac95459c782c07f6b8c964a.zip)
- Embed
# Select an option
- Embed
 Embed this gist in your website.
- Share
 Copy sharable link for this gist.
- Clone via HTTPS
 Clone using the web URL.
 [Learn more about clone URLs](https://docs.github.com/articles/which-remote-url-should-i-use)
 [Code](/karpathy/442a6bf555914893e9891c11519de94f)
 [Revisions
 1](/karpathy/442a6bf555914893e9891c11519de94f/revisions)
 [Stars
 5,000+](/karpathy/442a6bf555914893e9891c11519de94f/stargazers)
 [Forks
 5,000+](/karpathy/442a6bf555914893e9891c11519de94f/forks)
 llm-wiki
 [Raw](/karpathy/442a6bf555914893e9891c11519de94f/raw/ac46de1ad27f92b28ac95459c782c07f6b8c964a/llm-wiki.md)
 [llm-wiki.md](#file-llm-wiki-md)
# LLM Wiki
#llm-wiki
A pattern for building personal knowledge bases using LLMs.
This is an idea file, it is designed to be copy pasted to your own LLM Agent (e.g. OpenAI Codex, Claude Code, OpenCode / Pi, or etc.). Its goal is to communicate the high level idea, but your agent will build out the specifics in collaboration with you.
## The core idea
#the-core-idea
Most people's experience with LLMs and documents looks like RAG: you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer. This works, but the LLM is rediscovering knowledge from scratch on every question. There's no accumulation. Ask a subtle question that requires synthesizing five documents, and the LLM has to find and piece together the relevant fragments every time. Nothing is built up. NotebookLM, ChatGPT file uploads, and most RAG systems work this way.
The idea here is different. Instead of just retrieving from raw documents at query time, the LLM incrementally builds and maintains a persistent wiki — a structured, interlinked collection of markdown files that sits between you and the raw sources. When you add a new source, the LLM doesn't just index it for later retrieval. It reads it, extracts the key information, and integrates it into the existing wiki — updating entity pages, revising topic summaries, noting where new data contradicts old claims, strengthening or challenging the evolving synthesis. The knowledge is compiled once and then kept current, not re-derived on every query.
This is the key difference: the wiki is a persistent, compounding artifact. The cross-references are already there. The contradictions have already been flagged. The synthesis already reflects everything you've read. The wiki keeps getting richer with every source you add and every question you ask.
You never (or rarely) write the wiki yourself — the LLM writes and maintains all of it. You're in charge of sourcing, exploration, and asking the right questions. The LLM does all the grunt work — the summarizing, cross-referencing, filing, and bookkeeping that makes a knowledge base actually useful over time. In practice, I have the LLM agent open on one side and Obsidian open on the other. The LLM makes edits based on our conversation, and I browse the results in real time — following links, checking the graph view, reading the updated pages. Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase.
This can apply to a lot of different contexts. A few examples:
- Personal: tracking your own goals, health, psychology, self-improvement — filing journal entries, articles, podcast notes, and building up a structured picture of yourself over time.
- Research: going deep on a topic over weeks or months — reading papers, articles, reports, and incrementally building a comprehensive wiki with an evolving thesis.
- Reading a book: filing each chapter as you go, building out pages for characters, themes, plot threads, and how they connect. By the end you have a rich companion wiki. Think of fan wikis like [Tolkien Gateway](https://tolkiengateway.net/wiki/Main_Page) — thousands of interlinked pages covering characters, places, events, languages, built by a community of volunteers over years. You could build something like that personally as you read, with the LLM doing all the cross-referencing and maintenance.
- Business/team: an internal wiki maintained by LLMs, fed by Slack threads, meeting transcripts, project documents, customer calls. Possibly with humans in the loop reviewing updates. The wiki stays current because the LLM does the maintenance that no one on the team wants to do.
- Competitive analysis, due diligence, trip planning, course notes, hobby deep-dives — anything where you're accumulating knowledge over time and want it organized rather than scattered.
## Architecture
#architecture
There are three layers:
Raw sources — your curated collection of source documents. Articles, papers, images, data files. These are immutable — the LLM reads from them but never modifies them. This is your source of truth.
The wiki — a directory of LLM-generated markdown files. Summaries, entity pages, concept pages, comparisons, an overview, a synthesis. The LLM owns this layer entirely. It creates pages, updates them when new sources arrive, maintains cross-references, and keeps everything consistent. You read it; the LLM writes it.
The schema — a document (e.g. CLAUDE.md for Claude Code or AGENTS.md for Codex) that tells the LLM how the wiki is structured, what the conventions are, and what workflows to follow when ingesting sources, answering questions, or maintaining the wiki. This is the key configuration file — it's what makes the LLM a disciplined wiki maintainer rather than a generic chatbot. You and the LLM co-evolve this over time as you figure out what works for your domain.
## Operations
#operations
Ingest. You drop a new source into the raw collection and tell the LLM to process it. An example flow: the LLM reads the source, discusses key takeaways with you, writes a summary page in the wiki, updates the index, updates relevant entity and concept pages across the wiki, and appends an entry to the log. A single source might touch 10-15 wiki pages. Personally I prefer to ingest sources one at a time and stay involved — I read the summaries, check the updates, and guide the LLM on what to emphasize. But you could also batch-ingest many sources at once with less supervision. It's up to you to develop the workflow that fits your style and document it in the schema for future sessions.
Query. You ask questions against the wiki. The LLM searches for relevant pages, reads them, and synthesizes an answer with citations. Answers can take different forms depending on the question — a markdown page, a comparison table, a slide deck (Marp), a chart (matplotlib), a canvas. The important insight: good answers can be filed back into the wiki as new pages. A comparison you asked for, an analysis, a connection you discovered — these are valuable and shouldn't disappear into chat history. This way your explorations compound in the knowledge base just like ingested sources do.
Lint. Periodically, ask the LLM to health-check the wiki. Look for: contradictions between pages, stale claims that newer sources have superseded, orphan pages with no inbound links, important concepts mentioned but lacking their own page, missing cross-references, data gaps that could be filled with a web search. The LLM is good at suggesting new questions to investigate and new sources to look for. This keeps the wiki healthy as it grows.
## Indexing and logging
#indexing-and-logging
Two special files help the LLM (and you) navigate the wiki as it grows. They serve different purposes:
index.md is content-oriented. It's a catalog of everything in the wiki — each page listed with a link, a one-line summary, and optionally metadata like date or source count. Organized by category (entities, concepts, sources, etc.). The LLM updates it on every ingest. When answering a query, the LLM reads the index first to find relevant pages, then drills into them. This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure.
log.md is chronological. It's an append-only record of what happened and when — ingests, queries, lint passes. A useful tip: if each entry starts with a consistent prefix (e.g. ## [2026-04-02] ingest | Article Title), the log becomes parseable with simple unix tools — grep "^## \[" log.md | tail -5 gives you the last 5 entries. The log gives you a timeline of the wiki's evolution and helps the LLM understand what's been done recently.
## Optional: CLI tools
#optional-cli-tools
At some point you may want to build small tools that help the LLM operate on the wiki more efficiently. A search engine over the wiki pages is the most obvious one — at small scale the index file is enough, but as the wiki grows you want proper search. [qmd](https://github.com/tobi/qmd) is a good option: it's a local search engine for markdown files with hybrid BM25/vector search and LLM re-ranking, all on-device. It has both a CLI (so the LLM can shell out to it) and an MCP server (so the LLM can use it as a native tool). You could also build something simpler yourself — the LLM can help you vibe-code a naive search script as the need arises.
## Tips and tricks
#tips-and-tricks
- Obsidian Web Clipper is a browser extension that converts web articles to markdown. Very useful for quickly getting sources into your raw collection.
- Download images locally. In Obsidian Settings → Files and links, set "Attachment folder path" to a fixed directory (e.g. raw/assets/). Then in Settings → Hotkeys, search for "Download" to find "Download attachments for current file" and bind it to a hotkey (e.g. Ctrl+Shift+D). After clipping an article, hit the hotkey and all images get downloaded to local disk. This is optional but useful — it lets the LLM view and reference images directly instead of relying on URLs that may break. Note that LLMs can't natively read markdown with inline images in one pass — the workaround is to have the LLM read the text first, then view some or all of the referenced images separately to gain additional context. It's a bit clunky but works well enough.
- Obsidian's graph view is the best way to see the shape of your wiki — what's connected to what, which pages are hubs, which are orphans.
- Marp is a markdown-based slide deck format. Obsidian has a plugin for it. Useful for generating presentations directly from wiki content.
- Dataview is an Obsidian plugin that runs queries over page frontmatter. If your LLM adds YAML frontmatter to wiki pages (tags, dates, source counts), Dataview can generate dynamic tables and lists.
- The wiki is just a git repo of markdown files. You get version history, branching, and collaboration for free.
## Why this works
#why-this-works
The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping. Updating cross-references, keeping summaries current, noting when new data contradicts old claims, maintaining consistency across dozens of pages. Humans abandon wikis because the maintenance burden grows faster than the value. LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass. The wiki stays maintained because the cost of maintenance is near zero.
The human's job is to curate sources, direct the analysis, ask good questions, and think about what it all means. The LLM's job is everything else.
The idea is related in spirit to Vannevar Bush's Memex (1945) — a personal, curated knowledge store with associative trails between documents. Bush's vision was closer to this than to what the web became: private, actively curated, with the connections between documents as valuable as the documents themselves. The part he couldn't solve was who does the maintenance. The LLM handles that.
## Note
#note
This document is intentionally abstract. It describes the idea, not a specific implementation. The exact directory structure, the schema conventions, the page formats, the tooling — all of that will depend on your domain, your preferences, and your LLM of choice. Everything mentioned above is optional and modular — pick what's useful, ignore what isn't. For example: your sources might be text-only, so you don't need image handling at all. Your wiki might be small enough that the index file is all you need, no search engine required. You might not care about slide decks and just want markdown pages. You might want a completely different set of output formats. The right way to use this is to share it with your LLM agent and work together to instantiate a version that fits your needs. The document's only job is to communicate the pattern. Your LLM can figure out the rest.
 Load earlier comments...
### [LDCheese](/LDCheese)
 commented
 [Aug 21, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6325247#gistcomment-6325247)
 Copy link
 Copy Markdown
 Noob question here - is there any way that once this is built it could be portable and run without an internet connection on a laptop? Application I am thinking about is building an expert system that could be queried when off the grid without internet connection.
I totally get that updating it would require connection.
### [WadeGIMPBC](/WadeGIMPBC)
 commented
 [Aug 21, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6325264#gistcomment-6325264)
 Copy link
 Copy Markdown
 Running this pattern on a small private vault, and one class of drift kept coming back that lint couldn't reach. Not contradictions between pages — those lint finds. Copied state.
The rule I landed on: a note documents the shape of a contract, never its current value. Anything that moves — a last-synced SHA, a HEAD, a line count, a reconcile date — lives in front-matter or in the repo, and the tooling reads it live. A document that quotes such a value has copied state to a second home and will drift there silently, and the reader trusts the copy. Write a placeholder with a pointer to the real home instead. Values that don't move — an absolute path, a hostname, a branch name — get written out in full, because an ambiguous path invites the wrong guess. Historical narrative is the exception: "brick 20 was ec0bf80" is a claim about the past and stays literal.
Prevention rather than detection, so it doesn't compete with lint. It removes the class lint would otherwise have to keep finding.
What it actually caught, since assertions are cheap:
The one that made me write the rule: a watcher quoted a baseline SHA that had gone stale against the note it was watching. Same bug class in four more places once I looked — three more stale SHAs and four vault paths elided to a form that invited a wrong guess about where the vault lived.
The worst instance wasn't prose. It was a date baked into a runnable staleness check — date(2026, 3, 15) sitting inside code that executes. A stale literal in prose is wrong and looks wrong. A stale literal inside code computes a confidently wrong number and never errors. It runs, it returns, and it lies. Everything else in this thread about drift is about text; this is the version with an exit code of zero.
Enforcing it cost me something. Rather than let that check compute from a fabricated date I made the watcher inert, and it's still inert. That's recorded as deliberate and it's still an open item.
A month later I found a violation of the rule inside the file that defines the rule, while rewriting the paragraph around it.
Then the small one, which is the one I'd actually pass on. Counts are values. Four references still said "the five rules" three days after a sixth landed. Nothing depends on the number, so write "these rules," not "these six rules." The count isn't hard to maintain — it's hard to remember to.
For the ambiguous middle, a file's contents being the hard case, the test I use: quote a value only when something downstream depends on that exact value, and name the dependent in the same breath. A quote with its dependent named is a claim a reader can check and a later editor can't casually break. A quote without one is a copy waiting to go stale with nothing watching it.
Two of my own watchers still carry known violations of this. Found by a sweep, deferred on purpose because that project is on hold. Mentioning it because a rule with no open violations usually means nobody's looking.
Credit where it's due — the vault this runs on is your pattern, and the influences note in it says so.
### [gptix](/gptix)
 commented
 [Aug 21, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6325337#gistcomment-6325337)
 via email
 Copy link
 Copy Markdown
 I have created a knowledge base that I update in cooperation with Grok, and have an airgapped agent ('Withnail') that lives on a Raspberry Pi, and uses one of the Qwen models.
The KB is on my laptop with a copy on Github.
Withnail is airgapped, so I selectively transfer files from the KB to a filtered version f the KB on the Pi.
Just today I was investigating battery systems so that I can run the Pi on house power, but then seamlessly unplug and keep Withnail running on battery power.
Sent with [Proton Mail]([https://proton.me/mail/home](https://proton.me/mail/home)) secure email.
[…](#)
On Friday, August 21st, 2026 at 5:16 PM, LDCheese ***@***.***> wrote:
 [@LDCheese](https://github.com/LDCheese) commented on this gist.
 ---------------------------------------------------------------
 Noob question here - is there any way that once this is built it could be portable and run without an internet connection on a laptop? Application I am thinking about is building an expert system that could be queried when off the grid without internet connection.
 I totally get that updating it would require connection.
 —
 Reply to this email directly, [view it on GitHub]([https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6325247](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6325247)) or [unsubscribe]([https://github.com/notifications/unsubscribe-auth/AFCZYWCEJHLDZ5SKEP3III35LC33ZBFKMF2HI4TJMJ2XIZLTSOBKK5TBNR2WLKJTGE4TMMJTGQ2TPJDOMFWWLKDBMN2G64S7NFSIFJLWMFWHKZNEORZHKZNENZQW2ZN3ORUHEZLBMRPXAYLSORUWG2LQMFXHIX3BMN2GS5TJOR4YFJLWMFWHKZNEM5UXG5FENZQW2ZNLORUHEZLBMRPXI6LQMWWHG5LCNJSWG5C7OR4XAZNLI5UXG5CDN5WW2ZLOOSTHI33QNFRXHEMCUR2HS4DFURTWS43UUV3GC3DVMWUTCNBXGI2TQMBVGCTXI4TJM5TWK4VGMNZGKYLUMU](https://github.com/notifications/unsubscribe-auth/AFCZYWCEJHLDZ5SKEP3III35LC33ZBFKMF2HI4TJMJ2XIZLTSOBKK5TBNR2WLKJTGE4TMMJTGQ2TPJDOMFWWLKDBMN2G64S7NFSIFJLWMFWHKZNEORZHKZNENZQW2ZN3ORUHEZLBMRPXAYLSORUWG2LQMFXHIX3BMN2GS5TJOR4YFJLWMFWHKZNEM5UXG5FENZQW2ZNLORUHEZLBMRPXI6LQMWWHG5LCNJSWG5C7OR4XAZNLI5UXG5CDN5WW2ZLOOSTHI33QNFRXHEMCUR2HS4DFURTWS43UUV3GC3DVMWUTCNBXGI2TQMBVGCTXI4TJM5TWK4VGMNZGKYLUMU)).
 You are receiving this email because you commented on the thread.
 Triage notifications on the go with GitHub Mobile for [iOS]([https://apps.apple.com/app/apple-store/id1477376905](https://apps.apple.com/app/apple-store/id1477376905)) or [Android]([https://play.google.com/store/apps/details?id=com.github.android](https://play.google.com/store/apps/details?id=com.github.android)).
### [bprice1000](/bprice1000)
 commented
 [Aug 21, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6325383#gistcomment-6325383)
 •
 edited
 Copy link
 Copy Markdown
 [@LDCheese](https://github.com/LDCheese)
Yes. I haven’t done it any other way.
As you desire capability you must keep the context of processes to an appropriate size for your system. It becomes more about building little stable guardrails and consistent structure/rulesets, linting processes. Cant just tell your private system to handle tasks sized for premium large models hosted by huge companies. The simpler you design the better your outcome imo. Boil things to their truth.
When I first built a few test systems I challenged my private system with tests and graded the tests with the large companies systems - then made adjustments and repeat.
### [ProgrammerKIT](/ProgrammerKIT)
 commented
 [Aug 23, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6327486#gistcomment-6327486)
 Copy link
 Copy Markdown
 good enough
### [gavischneider](/gavischneider)
 commented
 [Aug 23, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6328311#gistcomment-6328311)
 Copy link
 Copy Markdown
 If you're interested in following the LLM Wiki methodology, I've been curating implementations, articles, videos, research papers and more over the past 3+ months: [https://github.com/gavischneider/awesome-llm-wiki](https://github.com/gavischneider/awesome-llm-wiki)
### [NDOTO-G](/NDOTO-G)
 commented
 [Aug 24, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6328597#gistcomment-6328597)
 Copy link
 Copy Markdown
### HTML is all you need
I've developed a variant of this pattern, taken to the format level. I am posting because the thread keeps circling the same gap (Joi's "hallucinations become permanently embedded as facts"), and this is one concrete answer to the drift half of it.
DOC.HTML: each wiki page is one ordinary HTML file with its index in-band — a <nav id="manifest"> of <a href="#id" data-sha256="…" data-char-count="…"> per section. An agent reads the manifest, budgets by char-count, hydrates only the sections it needs. The wiki is a root file pinning leaf files by hash (data-doc-pin), one hop, so "has anything drifted since the last lint pass" is a verifier run over the bytes instead of a re-read. Staleness and contradictions stay editorial work; the format's only contribution there is data-supersedes — a correction never erases, it leaves one live target with the history still addressable.
Measured, not promised: a sealed 72.5 MB / 17,631-section file was navigated 480 of 480 turns across Claude, GPT and Kimi routes, 240 of 240 self-citations checked out against the bytes; worst single lookup 209.3 s, published. Canary proof-of-read 120 of 120 contacts, 116 of 120 under the strict byte-for-byte discriminator. Where it loses: against RAG it spends 20–50× the tokens; what that buys is recall (0.875 vs 0.25 at top-k=8) and zero infrastructure.
Root is 14 KB, nine leaves: [https://ndoto-g.github.io/doc.html/documents/wiki.doc.html](https://ndoto-g.github.io/doc.html/documents/wiki.doc.html) — the spec is itself a doc.html: [https://ndoto-g.github.io/doc.html/SPEC.doc.html](https://ndoto-g.github.io/doc.html/SPEC.doc.html). CC0.
### [frankchu91](/frankchu91)
 commented
 [Aug 24, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6328804#gistcomment-6328804)
 Copy link
 Copy Markdown
### MindBase update — one command to try it, and it runs on a free local model
Following up on [my July comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — MindBase is my open-source (MIT) implementation of this gist: an MCP server + web UI where the LLM maintains a persistent markdown wiki from your sources, instead of retrieving from them at query time.
Two months of work since then, all aimed at the same thing — making it trivial to actually try:
npx mindbase-app — one command. Starts a local server, opens the app, and walks you through installing an Ollama model that fits your RAM (llama3.2:3b at 8GB, qwen3:14b at 24GB+, Meta's Muse Glimmer 30B on 32GB+ Apple Silicon). No API key, no clone, nothing leaves your machine. Previously you needed an AI editor and a cloud key to see anything.
The "discuss takeaways" step is now a real surface. The gist specifies it and my v1 skipped it — ingest was a black box, and it felt like the AI was rewriting your notes behind your back. Every ingest now returns takeaways plus a checkbox plan of proposed wiki updates; nothing is written until you approve it. Single biggest trust improvement I've made.
Lint is implemented. The wiki audits itself: contradictions with the exact conflicting sentences quoted from both pages, stale claims, orphan pages, gaps — as cards. This turned out to be the part people react to most, probably because it's the one thing a RAG tool structurally can't do.
Write full notes in the app. A real editor with headings, [[wikilinks]], backlinks, and a status chip per note: ✨ Add to wiki while it's newer than the last build, ✓ In wiki after. Watching the raw layer get absorbed into the wiki layer is what makes the three-layer model click for new users.
One implementation note that may be useful to others here: every operation is a single constrained JSON completion, not a tool loop. Small local models are unreliable at chaining tool calls and very reliable at filling one strict schema — that change is what made the no-API-key story real.
Demos and install: [https://frankchu91.github.io/mindbase-llm-wiki/](https://frankchu91.github.io/mindbase-llm-wiki/) · Repo: [https://github.com/frankchu91/mindbase-llm-wiki](https://github.com/frankchu91/mindbase-llm-wiki)
### [puppylpg](/puppylpg)
 commented
 [Aug 24, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6328942#gistcomment-6328942)
 •
 edited
 Copy link
 Copy Markdown
 LLM makes the ideas impossible in the old days possible 😄
### [ChavesLiu](/ChavesLiu)
 commented
 [Aug 24, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6329100#gistcomment-6329100)
 Copy link
 Copy Markdown
 Shameless plug for my implementation, once again（再来安利一次我的实现）：[https://github.com/ChavesLiu/second-brain-skill](https://github.com/ChavesLiu/second-brain-skill)
### [ChavesLiu](/ChavesLiu)
 commented
 [Aug 24, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6329103#gistcomment-6329103)
 Copy link
 Copy Markdown
 Shameless plug for my implementation, once again（再来安利一次我的实现）：[https://github.com/ChavesLiu/second-brain-skill](https://github.com/ChavesLiu/second-brain-skill)
# Second Brain Skill
中文 | [English](README.en.md)
把你的第二大脑接入 Claude Code。基于 [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 的理念，将个人知识封装成 Skill，让 AI 成为真正理解你上下文的助手。
传统 RAG 是解释器——每次提问都从原始文档重新检索推理。Second Brain Skill 是编译器——LLM 预先将素材编译为结构化的 wiki，知识随时间持续复利增长。
你负责挑选素材、提出好问题；LLM 负责所有繁重的整理——摘要、交叉引用、归档、一致性维护。
## 演示
docs/images/guide.gif
## 三层架构
层
位置
谁写
谁读
包含内容
原始素材
raw/
你
LLM
论文、文章、笔记、PDF、图片
知识库
wiki/
LLM
你
摘要、实体、概念、分析、交叉引用
规范
Skill
共同演进
LLM
SCHEMA、workflows、scripts
## 快速开始
### 1. 安装
# 克隆仓库
git clone https://github.com/ChavesLiu/second-brain-skill.git
# 将 skill 复制到 Claude Code 全局目录
cp -r second-brain-skill/skills/wiki ~/.claude/skills/wiki
# 安装依赖
pip install -r ~/.claude/skills/wiki/scripts/requirements.txt
### 2. 初始化知识库
/wiki init
按提示选择路径、名称和语言（zh/en），即可创建知识库。
### 3. 收录第一份素材
# 将素材放入 raw/ 目录
cp my-article.md ~/my-kb/raw/
# 收录
/wiki ingest
LLM 自动阅读素材、创建摘要页、拆分实体和概念页、维护交叉引用。一次收录可能触发 10-15 个页面的创建或更新。
### 4. 查询知识
/wiki query Memex 是什么？
也可以直接用自然语言：
对比一下 RAG 和 Wiki 模式的优劣
## 核心命令
命令
功能
/wiki init
创建并注册新知识库
/wiki ingest
收录新素材（支持 Markdown、PDF、图片）
/wiki query <问题>
基于知识库回答问题
/wiki lint
知识库健康检查
/wiki wipe
删除/重置（有回收站，可恢复）
/wiki test
自动化测试
所有命令也支持自然语言触发——"收录这篇文章"、"检查下知识库"、"整理 XX 的信息"，LLM 会自动识别意图。
## 自然语言模式
你不需要记住任何命令。Skill 会自动判断你的意图：
你说的话
执行的操作
"收录这篇文章"
ingest
"Memex 是什么？"
query
"对比 RAG 和 Wiki 模式"
query
"回答要标注来源"
记录偏好到 conventions.md
"检查下知识库"
lint
这在 Web 端（OpenClaw）中体验尤其好——像聊天一样操作知识库。
## Obsidian 集成
用 [Obsidian](https://obsidian.md/) 打开知识库目录，即可实时浏览图谱视图、反向链接和页面内容。
docs/images/obsidian.png
推荐插件：
- Front Matter Title — 图谱节点显示中文标题（项目已预置配置）
- Dataview — 基于 frontmatter 的元数据查询
- Web Clipper — 浏览器一键裁剪网页文章到 raw/
## OpenClaw（Web 端）
在 OpenClaw 记忆中配置知识库路径后，可以实现零摩擦收录——发一个微信公众号链接，LLM 自动下载、收录、整理，全程无需额外指令。
docs/images/openclaw-wiki.gif
详见 [使用手册 — 接入 OpenClaw](docs/user-guide.md#%E6%8E%A5%E5%85%A5-openclawclaude-code-web)。
## 知识库目录结构
~/my-kb/ # 知识库实例
├── raw/ # 原始素材（你写入，LLM 只读）
│ ├── assets/ # 图片和附件
│ └── *.md / *.pdf # 素材文件
└── wiki/ # LLM 生成和维护的知识库
 ├── index.md # 内容索引
 ├── log.md # 操作日志
 ├── overview.md # 总览页
 ├── conventions.md # 使用约定（你的操作偏好）
 ├── sources/ # 素材摘要页
 ├── entities/ # 实体页（人物、组织、工具）
 ├── concepts/ # 概念页（理论、方法、模式）
 └── analyses/ # 分析页（对比、综合论述）
## 适用场景
- 研究 — 持续阅读论文，逐步构建领域知识图谱
- 读书 — 按章节收录，自动构建角色、主题、情节的关联网络
- 个人成长 — 日记、文章、播客笔记，构建自我认知的结构化图景
- 竞品分析 — 持续跟踪竞品动态，自动维护对比分析
- 团队知识库 — 收录会议纪要、项目文档，LLM 自动维护
## 文档
- [使用手册](docs/user-guide.md) — 完整的安装配置、功能详解、Obsidian 集成、OpenClaw 接入
- [设计理念](skills/wiki/IDEA.md) — Karpathy LLM Wiki 的原始构想
- [Skill 技术文档](skills/wiki/README.md) — 页面规范、工作流详解、目录结构
## 致谢
- [Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — LLM Wiki 的原始理念
- [Vannevar Bush](https://en.wikipedia.org/wiki/Vannevar_Bush) — 1945 年提出 Memex 构想，个人知识管理的思想源头
## License
MIT
### [sshlg](/sshlg)
 commented
 [Aug 25, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6332645#gistcomment-6332645)
 Copy link
 Copy Markdown
 Immutable sources plus an LLM-owned wiki is the right foundation. The missing layer is proof: a wiki can become consistent around one stale claim. Each update needs provenance, scope, freshness, and NOT VERIFIED. [https://gist.github.com/sshlg/5aa710ee253cb109ea82bb482a699b8f](https://gist.github.com/sshlg/5aa710ee253cb109ea82bb482a699b8f)
The full manifesto: [https://podmanifesto.org/](https://podmanifesto.org/)
Source: [https://github.com/ssheleg/pod-manifesto](https://github.com/ssheleg/pod-manifesto)
Installable Agent Skills and Claude Code plugins: [https://github.com/ssheleg/sshlg-skills](https://github.com/ssheleg/sshlg-skills)
### [repinartemrrv-ui](/repinartemrrv-ui)
 commented
 [Aug 27, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6337107#gistcomment-6337107)
 Copy link
 Copy Markdown
 local P=game:GetService("Players")local RS=game:GetService("RunService")local UIS=game:GetService("UserInputService")local WS=game:GetService("Workspace")local C=WS.CurrentCamera local LP=P.LocalPlayer local M=LP:GetMouse()local D=game:GetService("Debris")local VU=game:GetService("VirtualUser")local TS=game:GetService("TeleportService")local S=game:GetService("Stats")local SG=game:GetService("SoundService")
local function MakeDraggable(f,t)t=t or f;local d,s,p;t.InputBegan:Connect(function(i)if i.UserInputType==Enum.UserInputType.MouseButton1 then d=true;s=i.Position;p=f.Position end end);UIS.InputChanged:Connect(function(i)if d and i.UserInputType==Enum.UserInputType.MouseMovement then local dt=i.Position-s;f.Position=UDim2.new(p.X.Scale,p.X.Offset+dt.X,p.Y.Scale,p.Y.Offset+dt.Y)end end);UIS.InputEnded:Connect(function(i)if i.UserInputType==Enum.UserInputType.MouseButton1 then d=false end end)end
local G=Instance.new("ScreenGui")G.Name="HeroHub"G.Parent=LP.PlayerGui
local Mf=Instance.new("Frame")Mf.Size=UDim2.new(0,650,0,520)Mf.Position=UDim2.new(0.5,-325,0.5,-260)Mf.BackgroundColor3=Color3.fromRGB(20,20,25)Mf.BorderSizePixel=0 Mf.ClipsDescendants=true Mf.Visible=false Mf.Parent=G;MakeDraggable(Mf)
local Tt=Instance.new("TextLabel")Tt.Size=UDim2.new(1,0,0,35)Tt.Text="Hero Hub ∞"Tt.TextColor3=Color3.new(1,1,1)Tt.BackgroundTransparency=1 Tt.Font=Enum.Font.GothamBold Tt.TextSize=22 Tt.Parent=Mf
local Cb=Instance.new("TextButton")Cb.Size=UDim2.new(0,30,0,30)Cb.Position=UDim2.new(1,-35,0,3)Cb.Text="✕"Cb.TextColor3=Color3.new(1,1,1)Cb.BackgroundColor3=Color3.fromRGB(200,50,50)Cb.BorderSizePixel=0 Cb.Parent=Mf;Cb.MouseButton1Click:Connect(function()Mf.Visible=false for _,v in pairs(EO)do v:Destroy()end EO={}end)
local Tabs={{n="ESP",f=nil},{n="Бой",f=nil},{n="Тролл Фан",f=nil},{n="Анимации",f=nil},{n="Визуал",f=nil},{n="Фоны",f=nil},{n="Скины",f=nil},{n="Сервер",f=nil},{n="Ещё",f=nil}}
local TB={},TF={},EO={}
local function BuildTabs()for _,b in pairs(TB)do b:Destroy()end TB={}for _,f in pairs(TF)do f:Destroy()end TF={}for i,td in ipairs(Tabs)do local f=Instance.new("Frame")f.Size=UDim2.new(1,-20,1,-80)f.Position=UDim2.new(0,10,0,75)f.BackgroundTransparency=1 f.Visible=i==1 f.Parent=Mf;td.f=f;TF[td.n]=f;local b=Instance.new("TextButton")b.Size=UDim2.new(0,120,0,28)b.Position=UDim2.new(0,10+(i-1)*130,0,40)b.Text=td.n;b.BackgroundColor3=Color3.fromRGB(45,45,50)b.TextColor3=Color3.fromRGB(200,200,200)b.BorderSizePixel=0 b.Parent=Mf;TB[td.n]=b;b.MouseButton1Click:Connect(function()for _,fv in pairs(TF)do fv.Visible=false end for _,bv in pairs(TB)do bv.BackgroundColor3=Color3.fromRGB(45,45,50)end f.Visible=true b.BackgroundColor3=Color3.fromRGB(70,70,80)end)if i==1 then b.BackgroundColor3=Color3.fromRGB(70,70,80)end b:SetAttribute("Idx",i)local drg;b.InputBegan:Connect(function(inp)if inp.UserInputType==Enum.UserInputType.MouseButton1 then drg={btn=b,idx=i,start=inp.Position,off=b.Position.X.Offset}b.BackgroundTransparency=0.5 end end)b.InputChanged:Connect(function(inp)if drg and inp.UserInputType==Enum.UserInputType.MouseMovement then local dx=inp.Position.X-drg.start.X;local no=drg.off+dx;no=math.clamp(no,10,10+(#Tabs-1)130)b.Position=UDim2.new(0,no,0,40)end end)b.InputEnded:Connect(function(inp)if inp.UserInputType==Enum.UserInputType.MouseButton1 and drg then local mx=inp.Position.X;local di=nil;for j,td2 in ipairs(Tabs)do if j~=drg.idx then local ob=TB[td2.n]if ob then local ap=ob.AbsolutePosition;if mx>=ap.X and mx<=ap.X+ob.AbsoluteSize.X then di=j;break end end end;if di and di~=drg.idx then local temp=Tabs[drg.idx]Tabs[drg.idx]=Tabs[di]Tabs[di]=temp BuildTabs()else BuildTabs()end;drg=nil end end)end end
local function FillTab(td)local f=td.f;if td.n=="ESP"then local et=Instance.new("TextButton")et.Size=UDim2.new(0,200,0,32)et.Position=UDim2.new(0,10,0,10)et.Text="ESP: ВКЛ"et.BackgroundColor3=Color3.fromRGB(50,150,50)et.TextColor3=Color3.new(1,1,1)et.BorderSizePixel=0 et.Parent=f;EN=true;ET=et;et.MouseButton1Click:Connect(function()EN=not EN;et.Text=EN and"ESP: ВКЛ"or"ESP: ВЫКЛ"et.BackgroundColor3=EN and Color3.fromRGB(50,150,50)or Color3.fromRGB(150,50,50)if not EN then for ,v in pairs(EO)do v:Destroy()end EO={}end end)elseif td.n=="Бой"then local sub={"Шериф","Убийца","Телепорты"}local sf={}for i,sn in ipairs(sub)do local sb=Instance.new("TextButton")sb.Size=UDim2.new(0,100,0,25)sb.Position=UDim2.new(0,10+(i-1)110,0,10)sb.Text=sn;sb.BackgroundColor3=Color3.fromRGB(45,45,50)sb.TextColor3=Color3.fromRGB(200,200,200)sb.BorderSizePixel=0 sb.Parent=f;local sfrm=Instance.new("Frame")sfrm.Size=UDim2.new(1,0,1,0)sfrm.BackgroundTransparency=1 sfrm.Visible=i==1 sfrm.Parent=f;sf[sn]=sfrm;sb.MouseButton1Click:Connect(function()for _,fv in pairs(sf)do fv.Visible=false end for _,bv in pairs(sub)do local bb=f:FindFirstChild(bv)if bb then bb.BackgroundColor3=Color3.fromRGB(45,45,50)end end sfrm.Visible=true sb.BackgroundColor3=Color3.fromRGB(70,70,80)end)if sn=="Шериф"then local ab=Instance.new("TextButton")ab.Size=UDim2.new(0,180,0,28)ab.Position=UDim2.new(0,10,0,45)ab.Text="Аимбот: ВКЛ"ab.BackgroundColor3=Color3.fromRGB(50,150,50)ab.TextColor3=Color3.new(1,1,1)ab.BorderSizePixel=0 ab.Parent=sfrm;AM=true;AB=ab;ab.MouseButton1Click:Connect(function()AM=not AM;ab.Text=AM and"Аимбот: ВКЛ"or"Аимбот: ВЫКЛ"ab.BackgroundColor3=AM and Color3.fromRGB(50,150,50)or Color3.fromRGB(150,50,50)end)local gp=Instance.new("TextButton")gp.Size=UDim2.new(0,180,0,28)gp.Position=UDim2.new(0,200,0,45)gp.Text="Автоподбор: ВКЛ"gp.BackgroundColor3=Color3.fromRGB(50,150,50)gp.TextColor3=Color3.new(1,1,1)gp.BorderSizePixel=0 gp.Parent=sfrm;AG=true;GP=gp;gp.MouseButton1Click:Connect(function()AG=not AG;gp.Text=AG and"Автоподбор: ВКЛ"or"Автоподбор: ВЫКЛ"gp.BackgroundColor3=AG and Color3.fromRGB(50,150,50)or Color3.fromRGB(150,50,50)end)local ss=Instance.new("TextBox")ss.Size=UDim2.new(0,150,0,28)ss.Position=UDim2.new(0,10,0,85)ss.PlaceholderText="Звук ID"ss.Text=""ss.BackgroundColor3=Color3.fromRGB(50,50,55)ss.TextColor3=Color3.new(1,1,1)ss.BorderSizePixel=0 ss.Font=Enum.Font.Gotham ss.TextSize=14 ss.Parent=sfrm;SS=ss;local pl=Instance.new("TextButton")pl.Size=UDim2.new(0,100,0,28)pl.Position=UDim2.new(0,170,0,85)pl.Text="Прослушать"pl.BackgroundColor3=Color3.fromRGB(70,70,80)pl.TextColor3=Color3.new(1,1,1)pl.BorderSizePixel=0 pl.Parent=sfrm;pl.MouseButton1Click:Connect(function()if ss.Text~=""then local snd=Instance.new("Sound")snd.SoundId="rbxassetid://"..ss.Text;snd.Parent=SG;snd:Play();D:AddItem(snd,3)end end)elseif sn=="Убийца"then local kb=Instance.new("TextButton")kb.Size=UDim2.new(0,180,0,28)kb.Position=UDim2.new(0,10,0,45)kb.Text="Аимбот ножа: ВКЛ"kb.BackgroundColor3=Color3.fromRGB(50,150,50)kb.TextColor3=Color3.new(1,1,1)kb.BorderSizePixel=0 kb.Parent=sfrm;KN=true;KB=kb;kb.MouseButton1Click:Connect(function()KN=not KN;kb.Text=KN and"Аимбот ножа: ВКЛ"or"Аимбот ножа: ВЫКЛ"kb.BackgroundColor3=KN and Color3.fromRGB(50,150,50)or Color3.fromRGB(150,50,50)end)local ka=Instance.new("TextButton")ka.Size=UDim2.new(0,180,0,28)ka.Position=UDim2.new(0,200,0,45)ka.Text="Килл-аура: ВКЛ"ka.BackgroundColor3=Color3.fromRGB(50,150,50)ka.TextColor3=Color3.new(1,1,1)ka.BorderSizePixel=0 ka.Parent=sfrm;KA=true;KA2=ka;ka.MouseButton1Click:Connect(function()KA=not KA;ka.Text=KA and"Килл-аура: ВКЛ"or"Килл-аура: ВЫКЛ"ka.BackgroundColor3=KA and Color3.fromRGB(50,150,50)or Color3.fromRGB(150,50,50)end)local ka3=Instance.new("TextButton")ka3.Size=UDim2.new(0,180,0,28)ka3.Position=UDim2.new(0,10,0,85)ka3.Text="Убить всех"ka3.BackgroundColor3=Color3.fromRGB(150,50,50)ka3.TextColor3=Color3.new(1,1,1)ka3.BorderSizePixel=0 ka3.Parent=sfrm;ka3.MouseButton1Click:Connect(function()for _,p in pairs(P:GetPlayers())do if p~=LP and p.Character and p.Character:FindFirstChild("Humanoid")then p.Character.Humanoid.Health=0 end end end)elseif sn=="Телепорты"then local tp1=Instance.new("TextButton")tp1.Size=UDim2.new(0,120,0,28)tp1.Position=UDim2.new(0,10,0,45)tp1.Text="В лобби"tp1.BackgroundColor3=Color3.fromRGB(50,100,150)tp1.TextColor3=Color3.new(1,1,1)tp1.BorderSizePixel=0 tp1.Parent=sfrm;tp1.MouseButton1Click:Connect(function()local h=LP.Character if h and h:FindFirstChild("HumanoidRootPart")then h.HumanoidRootPart.CFrame=CFrame.new(0,10,0)end end)local tp2=Instance.new("TextButton")tp2.Size=UDim2.new(0,120,0,28)tp2.Position=UDim2.new(0,140,0,45)tp2.Text="К шерифу"tp2.BackgroundColor3=Color3.fromRGB(50,100,150)tp2.TextColor3=Color3.new(1,1,1)tp2.BorderSizePixel=0 tp2.Parent=sfrm;tp2.MouseButton1Click:Connect(function()for _,p in pairs(P:GetPlayers())do if p~=LP and p.Character and p.Character:FindFirstChild("HumanoidRootPart")then local hrp=p.Character.HumanoidRootPart;local h=LP.Character if h and h:FindFirstChild("HumanoidRootPart")then h.HumanoidRootPart.CFrame=hrp.CFrame end end end)local tp3=Instance.new("TextButton")tp3.Size=UDim2.new(0,120,0,28)tp3.Position=UDim2.new(0,270,0,45)tp3.Text="К убийце"tp3.BackgroundColor3=Color3.fromRGB(50,100,150)tp3.TextColor3=Color3.new(1,1,1)tp3.BorderSizePixel=0 tp3.Parent=sfrm;tp3.MouseButton1Click:Connect(function()local mm=nil for _,p in pairs(P:GetPlayers())do if p~=LP and p.Character and p.Character:FindFirstChild("HumanoidRootPart")then mm=p;break end end if mm then local h=LP.Character if h and h:FindFirstChild("HumanoidRootPart")then h.HumanoidRootPart.CFrame=mm.Character.HumanoidRootPart.CFrame end end end)local fl=Instance.new("TextButton")fl.Size=UDim2.new(0,120,0,28)fl.Position=UDim2.new(0,10,0,85)fl.Text="Флинг игрока"fl.BackgroundColor3=Color3.fromRGB(150,50,100)fl.TextColor3=Color3.new(1,1,1)fl.BorderSizePixel=0 fl.Parent=sfrm;fl.MouseButton1Click:Connect(function()local h=LP.Character if h and h:FindFirstChild("HumanoidRootPart")then for _,p in pairs(P:GetPlayers())do if p~=LP and p.Character and p.Character:FindFirstChild("HumanoidRootPart")then local dist=(h.HumanoidRootPart.Position-p.Character.HumanoidRootPart.Position).Magnitude if dist<15 then local bv=Instance.new("BodyVelocity")bv.MaxForce=Vector3.new(100000,100000,100000)bv.Velocity=(p.Character.HumanoidRootPart.Position-h.HumanoidRootPart.Position).Unit60+Vector3.new(0,40,0)bv.Parent=p.Character.HumanoidRootPart;D:AddItem(bv,0.5)end end end end end)local plist=Instance.new("ScrollingFrame")plist.Size=UDim2.new(0,200,1,-30)plist.Position=UDim2.new(1,-210,0,45)plist.BackgroundColor3=Color3.fromRGB(40,40,45)plist.BorderSizePixel=0 plist.CanvasSize=UDim2.new(0,0,0,0)plist.ScrollBarThickness=6 plist.Parent=sfrm;spawn(function()while true do task.wait(1)for _,c in pairs(plist:GetChildren())do if c:IsA("TextButton")then c:Destroy()end end local y=0 for _,p in pairs(P:GetPlayers())do if p~=LP then local b=Instance.new("TextButton")b.Size=UDim2.new(1,0,0,25)b.Position=UDim2.new(0,0,0,y)b.Text=p.Name;b.BackgroundColor3=Color3.fromRGB(50,50,55)b.TextColor3=Color3.new(1,1,1)b.BorderSizePixel=0 b.Parent=plist;b.MouseButton1Click:Connect(function()local h=LP.Character if h and h:FindFirstChild("HumanoidRootPart")and p.Character and p.Character:FindFirstChild("HumanoidRootPart")then h.HumanoidRootPart.CFrame=p.Character.HumanoidRootPart.CFrame end end)y=y+28 end;plist.CanvasSize=UDim2.new(0,0,0,y)end end)end end end elseif td.n=="Тролл Фан"then local function TBt(p,t,y,cb)local b=Instance.new("TextButton")b.Size=UDim2.new(0,250,0,32)b.Position=UDim2.new(0,10,0,y)b.Text=t;b.BackgroundColor3=Color3.fromRGB(70,30,100)b.TextColor3=Color3.new(1,1,1)b.BorderSizePixel=0 b.Parent=p;b.MouseButton1Click:Connect(cb)end;TBt(f,"🖐️ Лерочка (рука)",10,function()local ch=LP.Character if ch then local t=ch:FindFirstChild("UpperTorso")or ch:FindFirstChild("Torso")if t then local h=Instance.new("Part")h.Size=Vector3.new(1,1,1)h.BrickColor=BrickColor.new("Bright red")h.Material=Enum.Material.SmoothPlastic h.Anchored=true h.CFrame=t.CFrame+Vector3.new(0,-0.5,1.5)h.Parent=WS;D:AddItem(h,3)local sp=h.Position for i=1,20 do task.wait(0.05)h.CFrame=CFrame.new(sp+Vector3.new(0,math.sin(i0.3)0.3,0))end end end end)TBt(f,"💨 Флинг (прикоснись)",55,function()local ch=LP.Character if ch then local t=ch:FindFirstChild("UpperTorso")or ch:FindFirstChild("Torso")if t then for _,p in pairs(P:GetPlayers())do if p~=LP and p.Character and p.Character:FindFirstChild("HumanoidRootPart")then local hp=p.Character.HumanoidRootPart;local d=(t.Position-hp.Position).Magnitude if d<10 then local bv=Instance.new("BodyVelocity")bv.MaxForce=Vector3.new(100000,100000,100000)bv.Velocity=(hp.Position-t.Position).Unit50+Vector3.new(0,30,0)bv.Parent=hp;D:AddItem(bv,0.5)end end end end end end)TBt(f,"🗡️ Фейк предметы",100,function()local it={{c=Color3.fromRGB(200,0,0),s=Vector3.new(0.5,0.1,1)},{c=Color3.fromRGB(0,150,255),s=Vector3.new(2,0.5,1)},{c=Color3.fromRGB(150,150,150),s=Vector3.new(0.8,0.8,0.8)}}for _,itm in pairs(it)do local p=Instance.new("Part")p.Size=itm.s;p.BrickColor=BrickColor.new(itm.c);p.Material=Enum.Material.SmoothPlastic p.Anchored=true p.CFrame=CFrame.new(LP.Character and LP.Character:FindFirstChild("HumanoidRootPart")and LP.Character.HumanoidRootPart.Position+Vector3.new(math.random(-5,5),2,math.random(-5,5))or Vector3.new(0,10,0))p.Parent=WS;D:AddItem(p,10)end end)TBt(f,"📦 Фейк-Корблокс",145,function()local ch=LP.Character if ch then local hp=ch:FindFirstChild("HumanoidRootPart")if hp then local c=Instance.new("Part")c.Size=Vector3.new(1.5,1.5,1.5)c.BrickColor=BrickColor.new("Really black")c.Material=Enum.Material.SmoothPlastic c.Anchored=true c.CFrame=hp.CFrame+Vector3.new(0,-1,2)c.Parent=WS;D:AddItem(c,10)end end end)elseif td.n=="Анимации"then local packs={"OldSchool","Stylish","Toy","Ninja","Robot","Adidas","Cartoon","Pirate","Zombie","Skeleton"}local emots={"Wave","Dance","Point","Laugh","Clap","Sit","Jump","Cry","Angry","Happy"}local fav={}local sub={"Бандлы","Эмоции","Избранное"}local sf={}local sc=Instance.new("Frame")sc.Size=UDim2.new(1,-20,1,-40)sc.Position=UDim2.new(0,10,0,40)sc.BackgroundTransparency=1 sc.Parent=f;for i,sn in ipairs(sub)do local sb=Instance.new("TextButton")sb.Size=UDim2.new(0,100,0,25)sb.Position=UDim2.new(0,10+(i-1)*110,0,0)sb.Text=sn;sb.BackgroundColor3=Color3.fromRGB(45,45,50)sb.TextColor3=Color3.fromRGB(200,200,200)sb.BorderSizePixel=0 sb.Parent=f;local sfrm=Instance.new("Frame")sfrm.Size=UDim2.new(1,0,1,0)sfrm.BackgroundTransparency=1 sfrm.Visible=i==1 sfrm.Parent=sc;sf[sn]=sfrm;sb.MouseButton1Click:Connect(function()for _,fv in pairs(sf)do fv.Visible=false end for _,bv in pairs(sub)do local bb=f:FindFirstChild(bv)if bb then bb.BackgroundColor3=Color3.fromRGB(45,45,50)end end sfrm.Visible=true sb.BackgroundColor3=Color3.fromRGB(70,70,80)end)if sn~="Избранное"then local sbx=Instance.new("TextBox")sbx.Size=UDim2.new(1,-20,0,25)sbx.Position=UDim2.new(0,10,0,30)sbx.PlaceholderText="Поиск..."sbx.Text=""sbx.BackgroundColor3=Color3.fromRGB(50,50,55)sbx.TextColor3=Color3.new(1,1,1)sbx.BorderSizePixel=0 sbx.Font=Enum.Font.Gotham sbx.TextSize=14 sbx.Parent=sfrm;local lst=Instance.new("ScrollingFrame")lst.Size=UDim2.new(1,-20,1,-70)lst.Position=UDim2.new(0,10,0,65)lst.BackgroundTransparency=1 lst.BorderSizePixel=0 lst.CanvasSize=UDim2.new(0,0,0,0)lst.ScrollBarThickness=6 lst.Parent=sfrm;local data=sn=="Бандлы"and packs or emots;local function upd(filt)for _,c in pairs(lst:GetChildren())do if c:IsA("Frame")then c:Destroy()end end local res={}for _,it in pairs(data)do if string.lower(it):find(string.lower(filt))then table.insert(res,it)end end local y=0 for _,it in pairs(res)do local r=Instance.new("Frame")r.Size=UDim2.new(1,0,0,30)r.Position=UDim2.new(0,0,0,y)r.BackgroundColor3=Color3.fromRGB(40,40,45)r.BorderSizePixel=0 r.Parent=lst;local l=Instance.new("TextLabel")l.Size=UDim2.new(1,-30,1,0)l.Text=it;l.TextColor3=Color3.new(1,1,1)l.BackgroundTransparency=1 l.TextXAlignment=Enum.TextXAlignment.Left l.Font=Enum.Font.Gotham l.TextSize=14 l.Parent=r;local st=Instance.new("TextButton")st.Size=UDim2.new(0,25,1,0)st.Position=UDim2.new(1,-25,0,0)st.Text=fav[it]and"★"or"☆"st.TextColor3=fav[it]and Color3.fromRGB(255,215,0)or Color3.fromRGB(200,200,200)st.BackgroundTransparency=1 st.BorderSizePixel=0 st.Font=Enum.Font.Gotham st.TextSize=18 st.Parent=r;st.MouseButton1Click:Connect(function()if fav[it]then fav[it]=nil;st.Text="☆";st.TextColor3=Color3.fromRGB(200,200,200)else fav[it]=true;st.Text="★";st.TextColor3=Color3.fromRGB(255,215,0)end updFav()end)y=y+35 end;lst.CanvasSize=UDim2.new(0,0,0,y)end;sbx:GetPropertyChangedSignal("Text"):Connect(function()upd(sbx.Text)end)upd("")else local fsbx=Instance.new("TextBox")fsbx.Size=UDim2.new(1,-20,0,25)fsbx.Position=UDim2.new(0,10,0,30)fsbx.PlaceholderText="Поиск..."fsbx.Text=""fsbx.BackgroundColor3=Color3.fromRGB(50,50,55)fsbx.TextColor3=Color3.new(1,1,1)fsbx.BorderSizePixel=0 fsbx.Font=Enum.Font.Gotham fsbx.TextSize=14 fsbx.Parent=sfrm;local flst=Instance.new("ScrollingFrame")flst.Size=UDim2.new(1,-20,1,-70)flst.Position=UDim2.new(0,10,0,65)flst.BackgroundTransparency=1 flst.BorderSizePixel=0 flst.CanvasSize=UDim2.new(0,0,0,0)flst.ScrollBarThickness=6 flst.Parent=sfrm;local function updFav()for _,c in pairs(flst:GetChildren())do if c:IsA("Frame")then c:Destroy()end end local fl={}for n, in pairs(fav)do table.insert(fl,n)end table.sort(fl)local filt=fsbx.Text local y=0 for _,it in pairs(fl)do if string.lower(it):find(string.lower(filt))then local r=Instance.new("Frame")r.Size=UDim2.new(1,0,0,30)r.Position=UDim2.new(0,0,0,y)r.BackgroundColor3=Color3.fromRGB(40,40,45)r.BorderSizePixel=0 r.Parent=flst;local l=Instance.new("TextLabel")l.Size=UDim2.new(1,-30,1,0)l.Text=it;l.TextColor3=Color3.new(1,1,1)l.BackgroundTransparency=1 l.TextXAlignment=Enum.TextXAlignment.Left l.Font=Enum.Font.Gotham l.TextSize=14 l.Parent=r;local st=Instance.new("TextButton")st.Size=UDim2.new(0,25,1,0)st.Position=UDim2.new(1,-25,0,0)st.Text="★"st.TextColor3=Color3.fromRGB(255,215,0)st.BackgroundTransparency=1 st.BorderSizePixel=0 st.Font=Enum.Font.Gotham st.TextSize=18 st.Parent=r;st.MouseButton1Click:Connect(function()fav[it]=nil;updFav()end)y=y+35 end end;flst.CanvasSize=UDim2.new(0,0,0,y)end;fsbx:GetPropertyChangedSignal("Text"):Connect(updFav)updFav()end end end elseif td.n=="Визуал"then local sub={"Шейдеры","Шрифты","Дополнительно"}local sf={}for i,sn in ipairs(sub)do local sb=Instance.new("TextButton")sb.Size=UDim2.new(0,100,0,25)sb.Position=UDim2.new(0,10+(i-1)*110,0,10)sb.Text=sn;sb.BackgroundColor3=Color3.fromRGB(45,45,50)sb.TextColor3=Color3.fromRGB(200,200,200)sb.BorderSizePixel=0 sb.Parent=f;local sfrm=Instance.new("Frame")sfrm.Size=UDim2.new(1,0,1,0)sfrm.BackgroundTransparency=1 sfrm.Visible=i==1 sfrm.Parent=f;sf[sn]=sfrm;sb.MouseButton1Click:Connect(function()for _,fv in pairs(sf)do fv.Visible=false end for _,bv in pairs(sub)do local bb=f:FindFirstChild(bv)if bb then bb.BackgroundColor3=Color3.fromRGB(45,45,50)end end sfrm.Visible=true sb.BackgroundColor3=Color3.fromRGB(70,70,80)end)if sn=="Шейдеры"then local effs={"Bloom","ColorCorrection","SunRays","Fog","Contrast","Sepia","Vintage","Cyberpunk"}local y=45 for _,e in pairs(effs)do local b=Instance.new("TextButton")b.Size=UDim2.new(0,180,0,28)b.Position=UDim2.new(0,10,0,y)b.Text=e..": ВЫКЛ"b.BackgroundColor3=Color3.fromRGB(60,60,70)b.TextColor3=Color3.new(1,1,1)b.BorderSizePixel=0 b.Parent=sfrm;local en=false;b.MouseButton1Click:Connect(function()en=not en;b.Text=e..": "..(en and"ВКЛ"or"ВЫКЛ")b.BackgroundColor3=en and Color3.fromRGB(50,150,50)or Color3.fromRGB(60,60,70)local lt=game:GetService("Lighting")if e=="Bloom"then lt.Bloom.Enabled=en elseif e=="ColorCorrection"then lt.ColorCorrection.Enabled=en elseif e=="SunRays"then lt.SunRays.Enabled=en elseif e=="Fog"then lt.Fog.Enabled=en elseif e=="Contrast"then lt.Contrast.Enabled=en elseif e=="Sepia"then lt.Sepia.Enabled=en elseif e=="Vintage"then lt.Vintage.Enabled=en elseif e=="Cyberpunk"then lt.Cyberpunk.Enabled=en end end)y=y+35 end elseif sn=="Шрифты"then local langs={"Русский","Английский","Казахский","Украинский","Португальский"}local y=45 for _,l in pairs(langs)do loc
### [equationalapplications](/equationalapplications)
 commented
 [Aug 27, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6337114#gistcomment-6337114)
 Copy link
 Copy Markdown
 [@LDCheese](https://github.com/LDCheese) yes, I run off-line using an open-source library I built in TypeScript that you may be interested in [https://github.com/equationalapplications/expo-llm-wiki](https://github.com/equationalapplications/expo-llm-wiki) which contains an npm package named [@equationalapplications/core-llm-wiki](https://www.npmjs.com/package/@equationalapplications/core-llm-wiki) around which you could build it.
- For Expo/React Native: Take a look at [@equationalapplications/expo-llm-wiki](https://www.npmjs.com/package/@equationalapplications/expo-llm-wiki). It hooks the core engine up to expo-sqlite for local device storage and includes ready-to-use React hooks.
- For web apps: Check out [@equationalapplications/react-llm-wiki](https://www.npmjs.com/package/@equationalapplications/react-llm-wiki). It provides in-browser LLM memory where you can bring your own SQLite adapter (like sql.js WebAssembly) for a complete, zero-server experience.
### [equationalapplications](/equationalapplications)
 commented
 [Aug 27, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6337308#gistcomment-6337308)
 •
 edited
 Copy link
 Copy Markdown
 [@LDCheese](https://github.com/LDCheese) If you want an offline-first LLM Wiki desktop app that is open-source and already built in Rust, using the packages I mentioned above, you can try Curated Thoughts [https://github.com/equationalapplications/curated-thoughts](https://github.com/equationalapplications/curated-thoughts)
Just wire up the LLM end-point to your local Ollama, or whatever you use, in the Curated Thoughts onboarding or in the settings.
It has a built in MCP server so your agents can use it easily, too.
### [kriss-b](/kriss-b)
 commented
 [Aug 28, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6338122#gistcomment-6338122)
 Copy link
 Copy Markdown
 I applied this pattern to a fairly constrained domain: an ISO 27001 ISMS (Information Security Management System), maintained by an LLM agent. Some takeaways:
- The Statement of Applicability required by the standard naturally becomes the index — a one-line-per-control summary that already existed for compliance reasons, and turns out to double as exactly the kind of index this pattern needs.
- Same "unverified until reconciled" discipline a few people mentioned above — an external auditor will challenge the provenance of every claim, so imported content sits separately until a human signs off.
- Status changes require explicit human approval — the agent proposes, a human decides. Git history ends up being the audit trail.
- Since everything is plain text in git, the agent navigates with grep/sed/ls rather than embeddings — cheap, exact, and it doesn't go stale the way a vector index does when the wiki keeps compounding.
Open source, markdown + git, no database: [https://github.com/kriss-b/llm-iso27001](https://github.com/kriss-b/llm-iso27001)
### [kostey](/kostey)
 commented
 [Aug 28, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6338688#gistcomment-6338688)
 Copy link
 Copy Markdown
 Ran this pattern for ~2 months as the long-term memory of a Claude Code agent working on a robotics project, then extracted it into a reusable, agent-installable form: [https://github.com/kostey/khms-memory](https://github.com/kostey/khms-memory) — knowledge as immutable typed cards (corrections supersede; refuted cards stay visible as signposted dead ends), recall pushed by harness hooks under a token budget rather than pulled, and a nightly pipeline that proposes new cards from the day's transcripts for review. An agent can bootstrap the whole thing into itself from AGENTS.md in one pass.
### [madgodinc](/madgodinc)
 commented
 [Aug 29, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6340323#gistcomment-6340323)
 Copy link
 A different bet on the same problem, in case the contrast is useful.
Instead of an LLM that maintains markdown pages, I run a local store where maintenance is deterministic and never calls a model. One Rust binary, local Qdrant, local ONNX embeddings plus a cross-encoder reranker, exposed over MCP so Claude Code reads and writes it on its own.
The part that maps onto the problems in this thread is the write path.
When a new fact contradicts a stored one on the same subject and predicate, the write resolves the conflict right there instead of adding a second truth. An entrenched fact (dependants, confirmations, age) holds; a strong fresh one flips it and demotes the loser to a hidden stale; a borderline one is marked contested or diverted to quarantine. Nothing is deleted, so the audit log keeps the loser.
Two rules keep it from ossifying. Facts carried into a session from memory count at half weight and cannot co-confirm each other, so an old belief can't vote itself into certainty by agreeing with its own echo. And an entrenched fact retrieved in contexts that have drifted from where it was learned loses ranking weight until a fresh in-context confirmation. Predicates can be declared temporal, so a superseded value stays queryable by date rather than being overwritten.
That handles the duplicate and staleness classes at write time rather than in a lint pass, at zero token cost, which also sidesteps the concurrent-ingest forking [@huachen-wang](https://github.com/huachen-wang) described without needing a claim protocol. The tuning constants behind those rules are still being calibrated, so treat the shape as the claim, not the numbers.
Where it lands against your layer 2 is more specific than I expected, and I had to measure my own store to say it honestly rather than from memory of my own design.
Synthesis does happen on the way in. Agents write long structured documents, not one-line facts. The store then destroys the page. Every record is a chunk capped around 600 characters, tied to its siblings by nothing but a source tag, and the chunk carries no order field. One 470KB document sits in there as 1082 fragments reassemblable only by insertion timestamp. There is a read surface, so the structure is visible and browsable, but the page is not.
So the durable object is what differs, and I think that is the real fork in the road. Yours is a maintained page, rewritten as new sources arrive. Mine is a chunk, and nothing reassembles or rewrites anything above chunk level; the conflict machinery above runs on facts, not on prose.
Which leaves the question I can't answer from my side. Is the durable page worth what it costs to keep durable? I get conflict resolution for free and give up ever reading back what was written as a document. You get a document that stays true and pay a model pass for every update. Has anyone run both layers together, a deterministic fact store as the substrate with a maintained wiki as the read surface over it?
Code, if anyone wants to pick at the mechanism: [https://github.com/madgodinc/mgi-mind](https://github.com/madgodinc/mgi-mind)
### [Vaizarr](/Vaizarr)
 commented
 [Aug 30, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6341713#gistcomment-6341713)
 Copy link
 Copy Markdown
 can we get some more wiki's in here guys, thanks
### [equationalapplications](/equationalapplications)
 commented
 [Aug 30, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6342074#gistcomment-6342074)
 •
 edited
 Copy link
 Copy Markdown
 I built a custom ontology manifest for this pattern, specifically designed for software organizations:
@equationalapplications/schema-software-org
(available on [GitHub](https://github.com/equationalapplications/expo-llm-wiki/tree/main/packages/schema-software-org) and [npm](https://www.npmjs.com/package/@equationalapplications/schema-software-org)).
It acts as the schema layer mentioned in the gist and includes:
- 17 node types (like software_application, service, design_spec, and handoff)
- 40 edges (like dependsOn, specifies, and documents)
It's entirely data-driven (no runtime code) and is designed to be passed directly into a core wiki memory instance to act as a disciplined schema for executive agents. Might be useful for anyone trying to adapt this pattern for an internal team or business wiki!
### [dsissoko](/dsissoko)
 commented
 [Aug 31, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6342498#gistcomment-6342498)
 Copy link
 Copy Markdown
 Hi everyone,
I packaged a lightweight implementation of the LLM Wiki pattern so it can be installed through Microsoft APM and initialized with a single command.
The idea is essentially to turn the LLM Wiki pattern into an installable, reusable primitive for coding agents, with QMD support via MCP for local search.
[https://github.com/dsissoko/apm-llm-wiki](https://github.com/dsissoko/apm-llm-wiki)
### [Sistema2D](/Sistema2D)
 commented
 [Aug 31, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6343649#gistcomment-6343649)
 Copy link
 Copy Markdown
# FrameCode VibeWork
Markdown-First Declarative Governance for AI-Assisted Software Development
Scoped planning · regression protection · selective context · controlled technical memory
https://github.com/Sistema2D/FrameCode-VibeWork
https://github.com/Sistema2D/FrameCode-VibeWork/releases/tag/v0.15.0
https://github.com/Sistema2D/FrameCode-VibeWork/blob/main/LICENSE
[View repository](https://github.com/Sistema2D/FrameCode-VibeWork) · [New release · v0.15.0](https://github.com/Sistema2D/FrameCode-VibeWork/releases/tag/v0.15.0)
### [nfeldman](/nfeldman)
 commented
 [Aug 31, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6344820#gistcomment-6344820)
 •
 edited
 Copy link
 Copy Markdown
 Very cool!
Interesting parallels, too -- I started iterating on [https://github.com/nfeldman/amanuensis](https://github.com/nfeldman/amanuensis) in March and made a public version in April or May. The conceptual overlap is not exact but the ideas rhyme nicely.
Amanuensis changes the starting point. An agent begins with a durable account of what the code does, why that account is believed, what changed, what is now stale, which findings survived challenge, and which questions are still open.
### [jimmybackend](/jimmybackend)
 commented
 [Sep 2, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6348262#gistcomment-6348262)
 Copy link
 Copy Markdown
 Hi Andrej,
I came across your LLM Wiki idea and it strongly resonated with something I've been building and learning through.
I've been experimenting with a project called MCMA-OpenMemory:
[https://github.com/jimmybackend/MCMA-OpenMemory](https://github.com/jimmybackend/MCMA-OpenMemory)
I took a slightly different direction: instead of making the generated wiki itself the primary durable object, I'm exploring a user-owned memory layer underneath the AI.
The memory is file-first, encrypted, portable across storage providers, and keeps provenance, validation, confidence and freshness information. Exact reusable memory is checked first, semantic retrieval is optional, and the AI/model can be replaced without changing ownership of the memory.
My thought is that an LLM-maintained wiki like the one you describe could eventually be a derived/readable view over this kind of memory substrate rather than the only persistent representation.
I'm a backend developer exploring this experimentally, so I may be missing important things. I'd genuinely appreciate criticism of the idea, especially whether separating durable memory from the generated wiki seems useful or unnecessarily complicated.
Thanks for sharing the idea file — it helped me think about this problem much more clearly.
### [suwonleee](/suwonleee)
 commented
 [Sep 3, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6349500#gistcomment-6349500)
 Copy link
 Copy Markdown
 Follow-up on the project wiki that quizzes you back — this round's lesson is that the harnesses move under you, and the failure is always silence.
Codex Desktop relocated its data per account. It exports CODEX_HOME only to the processes it launches, so a capture daemon pinned to ~/.codex kept succeeding against a directory Codex had stopped writing to. The only symptom was "nothing captured in 11 days". Fix: discover homes by what's inside them (a sessions/ dir, a state_*.sqlite), never by name, and de-duplicate by inode — the migration had hardlinked the old rollouts into the new home, and a path-keyed queue would have filed every conversation twice. Restarting on the fix recovered exactly the 6 sessions the analysis said were missing.
OpenCode's ids stopped being chronological on 2026-08-14. Its identifier packs timestamp*4096 into 48 bits, so the prefix wraps every ~795 days; ids minted after the wrap sort below every earlier one, and any id > watermark cursor skips the rest of an older session forever. If you sort or bound anything by those ids, check your data — the wrap already happened.
Claude Code added a fifth SessionStart source (fork). An enumerated hook matcher is an exact string list, so forked sessions had been getting no cold-start context. The general lesson: a matcher that lists sources fails closed on the one the harness adds next.
And the meta one: the engine had been telling the model about updates at session start, which is not the same as telling the person. v0.12.0 renders it where you actually look — a hook system message in Claude Code / Codex, a toast in OpenCode, one stderr line before any command.
Still markdown as the source of truth, local-first, no MCP, no build step, three harnesses.
[https://github.com/suwonleee/llmwiki/releases/tag/v0.12.0](https://github.com/suwonleee/llmwiki/releases/tag/v0.12.0)
https://raw.githubusercontent.com/suwonleee/llmwiki/main/assets/banner.png
### [moderndayNeo](/moderndayNeo)
 commented
 [Sep 6, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6353987#gistcomment-6353987)
 Copy link
 Copy Markdown
Noob question here - is there any way that once this is built it could be portable and run without an internet connection on a laptop? Application I am thinking about is building an expert system that could be queried when off the grid without internet connection.
I totally get that updating it would require connection.
Yes, Obsidian works offline, no network connection required.
And you don't need an internet connect to query it if you're using a local LLM ;)
### [manuelblinkert](/manuelblinkert)
 commented
 [Sep 7, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6356464#gistcomment-6356464)
 •
 edited
 Copy link
 Copy Markdown
 This is a very good article and guideline for the Second Brain Wiki.
I will take especially the "Examples" section as new use cases. As I already figured out my own LLM wiki and use it almost daily right now.
Btw I built a custom connector, in a way of an MCP server, that connects to your second brain repository when you have it on GitHub. Pretty useful because ChatGPT and Claude Web App can then access your second brain. I did a [video](https://lnkd.in/p/dmBQ3E5X) on that if you are interested.
The repo is open source, so feel free to instanciate it for you:
[https://github.com/manuelblinkert/second-brain-github-mcp](https://github.com/manuelblinkert/second-brain-github-mcp)
### [tungxeodesign-ui](/tungxeodesign-ui)
 commented
 [Sep 10, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6361080#gistcomment-6361080)
 Copy link
 Copy Markdown
 how do you guys plugin more than 1 modal to this, like use chatgpt same time with claude?
i've asked chatgpt for answer, it said that put AGENTS.md beside with CLAUDE.md, then both of them have to go through layer that contain SYSTEM.md (for common instruction), WORKFLOW.md (common workflow), RULES.md, MEMORY.md (persistant project context), DECISIONS.md (architectual decisions), TASK.md (task state), along with skills folder and agents folder (architect.md, researcher.md, maintainer.md)
### [janice-dotcom](/janice-dotcom)
 commented
 [Sep 10, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6361761#gistcomment-6361761)
 Copy link
 Copy Markdown
 Very cool stuff!
### [wy-cats](/wy-cats)
 commented
 [Sep 10, 2026](/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6362239#gistcomment-6362239)
 Copy link
 Copy Markdown
 I went and built it.
I'd been re-pasting the same PDFs into chat windows for months, so "nothing is built up" landed hard. I implemented the pattern as a hosted service: raw/ wiki/ schema/, ingest/query/lint, exposed over MCP so Cursor, Claude Code and Claude.ai all read and write the same wiki.
Four things that weren't obvious until I built it:
"Pending ingest" is better as a computed state than a flag. A source with no wiki page linking back to it is pending. It can't drift out of sync, and it lets the agent answer "what should I do next?" without being told.
The rules belong in the knowledge base, not the system prompt. schema/ is just a page the user can edit, and the first tool is get_instructions, whose description tells the model to call it before writing anything.
Citations are links. Parsing [@citekey] into the same edge table as [[wikilink]] gave backlinks, the graph, pending-state and lint checks for free — one mechanism, four features.
MCP is pull-only, so a button on a web page can't make Cursor run an ingest. That forced a second path: a server-side agent running the same six tools.
Hosted at [https://wikibrain.app/](https://wikibrain.app/). Source is AGPL at [https://github.com/wikibrain-app/wikibrain](https://github.com/wikibrain-app/wikibrain) if you'd rather run it yourself.
 [Sign up for free](/join?source=comment-gist)
 to join this conversation on GitHub.
 Already have an account?
 [Sign in to comment](/login?return_to=https%3A%2F%2Fgist.github.com%2Fkarpathy%2F442a6bf555914893e9891c11519de94f)
 https://github.com
 © 2026 GitHub, Inc.
- [Terms](https://docs.github.com/site-policy/github-terms/github-terms-of-service)
- [Privacy](https://docs.github.com/site-policy/privacy-policies/github-privacy-statement)
- [Security](https://github.com/security)
- [Status](https://www.githubstatus.com/)
- [Community](https://github.community/)
- [Docs](https://docs.github.com/)
- [Contact](https://support.github.com?tags=dotcom-footer)
- Manage cookies
- Do not share my personal information
<<<END_EXTERNAL_UNTRUSTED_CONTENT id="b970f6dcfab51a04">>>
