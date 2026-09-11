# LinkedIn blurb — 200 days post (Aaron's verbatim rewrite + 3 approved tactical edits)

200 days ago I set up an OpenClaw AI chief of staff named Dru.

Dru was the first of what is now 10 agents. Dru is my orchestrator and my right hand man. A lot of my starting assumptions were proven false: what I thought was critical wasn't, and the single biggest cause of long term performance was something I'd never really considered at all: How an agent dreams and keeps memories.

A chatbot only knows what is in its current session (with some exceptions in recent days). For a long term Layer 4 agent (if you don't know what that means, the article below is for you!) this just isn't possible. So how do you move from session data to agentic memory systems? The harness is the gem. I'd rather have an optimal harness with Sonnet than a ChatBot with Fable 5. I'm not saying the models are comparable, but a V12 F1 engine sitting on stand won't do the day to day work that a fully working complete Honda civic can.

That's really it in a nutshell: The harness is more important than the model in terms of getting work done day to day.

Everything Dru knows lives in files on disk: about 120 of them, indexed by a small embedding model running on my own machine. Anything he does is immediately written to disk, not at session end or overnight. These 120 files are referenced as needed, never loaded into a session wholesale.

Curious about what Dru and the rest of my agents actually do that a chatbot can't? In the post below I talk all about what I do and how my partner also has her own Chief of Staff (her agent is named Fern, on the same harness) for all the personal life "girlie things" (her words).
