# FOCUS — Writing & Publishing (trading-knowledge-workspace-site)

*Written 2026-07-02, from a direction-setting interview. This is the focus doc for the writing/blogging track as a whole; this repo is currently its publishing target (GitHub Pages), with `../vineel-wiki` (Astro) as a candidate long-term home.*

## Why write (the honest version)

Three reinforcing purposes:

1. **Learning by writing** — writing something down with data behind it ingrains it far deeper than consuming it.
2. **Credibility & visibility** — public, hiring-visible research notes a fund's hiring manager could read; audience-building over time around Indian derivatives + quant content.
3. **A living fact base** — documents that get *updated as markets evolve*, becoming durable personal references and seeds for future strategy ideas.

## The flagship format: podcast fact-checks

The differentiated idea from the interview, worth building the whole track around:

> Take claims and discussions from finance/markets podcasts — valuations, market events, "everyone knows X" assertions — and **go look at the actual market data**. Add the context the conversation didn't have. Publish it as a living document that gets updated as new data arrives.

Why this format wins: it has a built-in content pipeline (podcasts already being consumed), a unique angle (almost nobody data-checks podcast talk), it exercises the trading-vy data stack (420M rows of NSE data + DuckDB is a real edge for India-focused claims), and every post doubles as a personal learning artifact.

Second content stream: **desk notes** from the trading work — the strategy backtest report and the "what the backtest didn't tell me" note from `../trading-vy/FOCUS.md` are already scheduled artifacts this quarter.

## The 3-month focus: publish 4–6 posts

Volume of finished, public posts is the metric. Perfection is the enemy; a living document can be improved after publishing.

1. **Weeks 1–2 — Unblock publishing.** Decide the venue (simplest that works: this GitHub Pages site, or vineel-wiki if it's closer to ready — decide in one sitting, don't build a blog engine). One post template: claim → data → context → verdict → "last updated" stamp.
2. **Weeks 3–13 — Cadence.** One post every ~2 weeks. Each post: pick one podcast claim, pull the data from `market.db`, one or two charts, 800–1500 words.
3. **Feed the loop.** Capture podcast claims into second-brain-kb as they're heard (`../second-brain-kb/FOCUS.md` month-3 writing pipeline serves this). Link finished posts from LinkedIn — each one is a credibility artifact for `../linkedin/FOCUS.md`.

## Weekly time box

**3–4 hours/week** — roughly one post per two-week cycle.

## Not doing

- Building a custom blog platform/engine (choose an existing venue and ship).
- Waiting for the second-brain writing pipeline before writing — the pipeline serves the habit, not the reverse.
- Long-form evergreen textbook content — the format is timely claim + data + context.
