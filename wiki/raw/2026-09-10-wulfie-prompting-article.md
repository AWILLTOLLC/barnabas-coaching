---
source: https://x.com/wulfie_bain_/status/2098060386813566990
fetched: 2026-09-11
type: article
author: wulfie_bain_ (Lead Applied AI Eng, OpenAI startups EMEA/APAC)
---

## TLDR

- Most prompts are bad because prompt evolution tends to be accretive: we only add, never remove, over time. This leads to spaghetti prompts, with contradictions and ambiguity. This has real business impact.

- We need to treat prompt changes as product changes (because agent behaviour is product), and treat prompts as code (modularised, MECE, and all your other favourite acronyms; refactored if need be & actively maintained).

- Well structured prompts enable teams to move faster, prevent regressions, and have better agents. I propose a very simple structure at the end.

Prompting decisions are product decisions, and using structure to make unambiguous, maintainable prompts is critical for making great agents. This is a guide on how to do that.

# Background

I think I have one of the best jobs in the world. I lead Applied AI Engineering for the OpenAI startups team across EMEA & APAC, and that means that every week I get to see behind the scenes of the best AI startups globally. And I get pretty hands on in how I work with their engineers to improve their agents: on everything from prompts to evals to finetuning.

These startups are advanced. Some have ARR in the hundreds of millions. Some have their own data annotation teams. Some train their own models.

So it came as a surprise that often, when I look behind the curtains, they have prompts that just don't make sense. This is not about being beautifully written prose, or nicely formatted; it's about logical errors that lead to the mistakes their agents make.

This is not a critique of those startups - indeed, they are more successful than any company I have ever built, and their teams are full of the best engineers globally. They are a true pleasure to work with.

But they're leaving huge gains on the table. After only a couple of days re-writing agents together, I've seen some startups speed up their agents by 50%; others increase 7 day retention by 40%; and still others reduce costs by 30%. These results hold across the LLMs they use, from every provider. When you're talking millions of ARR & LLM spend, this is pretty material.

Don't believe me? See this Loveable engineer's post about how he decreased their LLM spend by $20M per year… because his mum caught inconsistencies & duplication in their prompt.

In fact it's because they are so incredible, that I'm writing this. Because clearly even when you are genuinely world class, our current paradigm for prompting leads to suboptimal results.

So I thought I would try to scale my impact beyond the startups I can work with directly by writing this. First, I'll cover why the world's best startups write bad prompts; then, I'll cover my prompting philosophy; finally, I'll propose a prompt template.

(whilst reading this, try giving the link to this article to your coding agent, and ask it to review your repo against this advice + make a markdown file with its findings, ready for you when you're done!)

# Bad prompts

Given this is so common, there are clearly universal tendencies that lead to bad prompts. The two key themes are:

- Our current process for prompting is accretive & leads to contradictions
- Implicit knowledge leads to ambiguity

## Our current process for prompting is accretive & leads to contradictions

Most prompts evolve like this: the first engineer building an agent writes a simple prose prompt. As the agent is being built, the engineer adds more instructions, more specific edge cases, more context. Each paragraph is written in isolation, and without looking at what came before.

The prompt only gets longer.

And no-one reviews the entire prompt end to end. Almost always, that leads to contradictions in the instructions. One paragraph tells the agent to do X, another tells it to do Y. The agent is confused.

## Implicit knowledge leads to ambiguity

Even if an engineer does review a prompt end to end, they often don't truly read it. When you read & write prompts, you're reading the words but also bringing a lot of implicit knowledge to the task. You know what the agent should do, so you fill in the gaps in the prompt with your own understanding.

This is the problem of specificity: the prompt doesn't actually say what we want the agent to do, because the author assumes they've said it.

## Conditional prompts compound this

The above problems are compounded by conditional prompts, where additional prompt content is injected based on context. This is a common pattern: you have a base prompt, and then you add context from the user's input, or from a RAG lookup.

The problem is that now you have even more paragraphs, even more implicit knowledge, even more contradictions.

## The outcome?

We get spaghetti prompts. Thousands of lines, with interaction effects between many paragraphs, and implicit knowledge that's not written down.

And that leads to agents that "make mistakes", not behaving how the team wants them to.

But the above is also why I can add value to these startups fast: I do read the prompt end to end, I understand the implicit knowledge, and I can spot the contradictions.

After I go through the prompt end to end with teams, there's a beautiful moment of anthropomorphism... they say things like "Oh wow, that paragraph says X but that one says Y!"

But so far I've just listed problems. AND if we're honest, these startups are doing incredibly well, and their agents are mostly working.

The results I've mentioned above speak for themselves financially, but I also truly believe we can get even better.

My principles: start treating prompting as product, and prompting as code.

The solution: making MECE, modular, unambiguous prompts.

# Prompt decisions are product decisions

Agents are at the core of product experience. In chat based products, they are the entire product. The prompt is the user interface.

And that's just the output. Agent behaviour is a product decision: should it err on the side of responding quickly, or being more thorough? Should it be concise or comprehensive? Should it be friendly or professional?

It's all product.

So whoever is writing your prompts better understand what user experience you want, because whilst they're writing the prompt, they're also making product decisions.

And not only must they be able to understand it, but they must be able to specify it.

My work with top startups, when looking at a specific error trace, involves me asking 'what do you actually want the agent to do here?'

If you can't specify the desired product experience, you can't expect an LLM to give that experience.

Each time your engineers add to a prompt, or don't add to a prompt and so leave it ambiguous, they are making product decisions. And those decisions compound over time, leading to spaghetti prompts.

# Prompting as code

We use human readable language to get a computer to do what we want. That was true of programming languages in the 1970s. It's true of LLM prompts in 2026.

The same principles apply. We want to write code that is:

- Modular
- Testable
- Maintainable
- Reusable

## Structure with MECE prompt sections

Engineers please forgive me for using a consulting phrase, but it really is relevent. MECE stands for Mutually Exclusive, Collectively Exhaustive.

- Collectively Exhaustive: together, your prompt sections comprehensively cover (specify) the behaviour you want from the agent
- Mutually Exclusive: each prompt section should be self contained, with no overlap

This leads to DRY (Don't Repeat Yourself) prompts, which are easier to maintain & review. When you make a change, you only need to change one place.

Separate concerns where possible. Modular code is good code; modular prompts are good prompts.

For example we will have sections on the general context of the agent, the behaviour we want, and its output format.

## Aim for the specificity of programming

When engineers write code, they are precise in their desires. If this, then that. But as soon as it's an LLM, we go back to prose.

For example, you might wish to still employ IF ELSE logic. For example, when describing how your agent should respond to different types of user input.

The aim is NOT to 'program' every eventuality - otherwise you wouldn't use an LLM. But you do want to be as specific as possible, especially in the sections that matter most.

## Separation of backend and frontend

Above I mentioned having a Behaviour section and an Output section. In my framing of prompts as product, these correspond to the backend and frontend.

- Behaviour: this is how the agent should act whilst preparing its output. It's the way it uses tools, the reasoning it does, the tradeoffs it makes.
- Output: this is the frontend, the user facing part of the agent. What the agent outputs could be totally different from how it got there.

We separate concerns, which means we can make more consistent specifications of what we wish under each.

## Refactor every so often

Even with the best intentions, prompts can get messy. Dedicate some time to paying down your prompt debt.

Look at your prompt, read it end to end, and ask yourself: is this MECE? Is this DRY? Is this specific?

If not, refactor it.

# Template of a good prompt: Background, Behaviour, Output

So we want a nicely structured, MECE prompt, that separates concerns where possible. The below is a template for that.

It has three sections:

1. **Background** — who is the agent, what's its context, what's its mission?
2. **Behaviour** — how should the agent act, what principles should it follow, what tradeoffs should it make?
3. **Output** — what should the agent output, in what format, with what style?

You'll notice this is hierarchically organised, like a tree. This helps it be MECE, and means you can navigate it easily.

So say I'm having issues with my agent outputting markdown, when I want it to output XML. Easy - one section to change, no ambiguity.

It's unambiguous where that content sits.

# A quick note on evals

I like evals more than the average (normal?) person. Most of the time when something is going wrong, it's because the prompt is ambiguous. But evals can help.

Hamel, whose writings on evals everyone should read, emphasises that a lot of the value in evals actually comes from the process of writing them, not from running them.

But I'd add an extra benefit here: evals force you to decide on what you want.

When you make an eval, whether with deterministic ground truth or a rubric for a judge, you have to be specific about what you want.

Evals force clarity, and so they force clear product decisions.

(and go read Hamel for a million other benefits of evals)

# Benefits of structured prompts

## Fewer contradictions

With MECE sections, reviewing the prompt is easy. Each section is self contained, and instead of having to read through hundreds of lines of prose, you can just check that each section is internally consistent.

## Faster & safer iteration

Separating concerns lets you iterate incredibly fast. When you find an issue, you just add a line to the relevant section. You know it won't affect other sections.

## Faster search

In spaghetti prompts, you have to remember key phrases in your prompt or the filenames to find the section you want. With a structured prompt, you just go to the section.

## Everyone's an engineer

Many forward thinking startups want everyone on their team to write prompts. This is great, because it means the product team gets more involved.

But it also means they need a structure that's easy to navigate. A structured prompt is like a well-organised codebase: anyone can find what they need.

# TL;DR - My prompting philosophy

1. Treat prompting as product: whoever writes the prompt should understand the user experience
2. Treat prompting as code: modular, MECE, DRY, maintainable
3. Use the Background/Behaviour/Output template: separates concerns, easy to navigate
4. Evals force clarity: write them to force clear product decisions

# Final thoughts

If you take one thing away from this article, let it be this: prompts are product. They're also code. Treat them like both, and your agents will be better.

---

*This article was written by Wulfie Bain, Lead Applied AI Engineering for OpenAI startups across EMEA & APAC. He works with the best AI startups globally to improve their agents, from prompts to evals to finetuning.*
