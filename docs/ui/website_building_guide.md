Website building guide


You’re asking how I build sites that don’t feel like a filing cabinet from 1997. Fine. Here’s the full kit: the tools, the logic, the sources, and a step-by-step you can hand to another chat and it won’t cry.

# What I reach for (and why)

## 1) Two battle-tested build paths
- **Content-heavy or docs/marketing**: **Astro** with **React islands** when you need static speed plus a sprinkle of interactivity. It ships almost zero JavaScript by default, which your users’ batteries will appreciate.
- **App-heavy, data-rich**: **TypeScript + a meta-framework** like **Next.js** or **SvelteKit**. You get routing, server rendering, API routes, file-based conventions, good DX, and first-class data fetching. Pick one and stop re-litigating it every Tuesday.

Both paths play nicely with:
- **Styling**: CSS variables + **Tailwind** for speed and consistency, or vanilla CSS with a tiny utility layer if you hate class soup.
- **Headless UI**: **Radix UI** or **Headless UI** for accessible primitives; you skin them with your tokens.
- **Data**: **TanStack Query** for server-state caching; **Zod** for runtime validation of inputs/outputs.
- **State**: Local component state for UI, **Zustand** for small global bits. If you’re reaching for a global store because you’re tired, take a walk.
- **Charts**: A11y-friendly chart lib that can render thousands of points smoothly (Canvas/WebGL). Provide CSV export hooks.
- **Testing**: **Playwright** for E2E, **Vitest/Jest** for units, Storybook for components with visual and a11y checks.

## 2) Backend options that don’t fight you
- **Node**: Next/SvelteKit API routes or **Fastify/Nest** if you want a dedicated service.
- **Python**: **FastAPI** + Jinja or HTMX for classic SSR ergonomics and clean APIs. If you need a CMS, Django still slaps.
- **DB layer**: **Prisma** for TS, **SQLModel/SQLAlchemy** for Python. Start with SQLite locally, flip a switch to Postgres in prod. Migrations or it didn’t happen.
- **Auth**: Provider-agnostic auth with session cookies set HttpOnly, Secure, SameSite=Lax. JWTs only where they make sense.

## 3) Infra sanity
- **CI/CD**: lint, type-check, test, build, preview deploy for every PR. If the branch doesn’t have a live preview, you’re guessing.
- **Monitoring**: error tracking (e.g., Sentry), performance traces (OpenTelemetry), product analytics (PostHog). Keep PII out of logs.
- **Security**: OWASP Top 10 basics, CSP, rate limiting, input validation everywhere. Least privilege or enjoy your 3 a.m. incident.

# The build logic, end to end

## A. Plan the shape of the app
1) **Jobs to be done** → user stories → success metrics.  
2) **Information architecture**: shallow nav, names that read like labels not riddles.  
3) **Design tokens**: color, type, spacing, radius, shadow, motion. Store as JSON and generate CSS variables. One source of truth.

## B. Ship an accessible, fast UI
- **Layout**: 12-column fluid grid, 8-pt spacing, 1.125–1.25 type scale, 44×44 touch targets.  
- **A11y**: semantic HTML first; ARIA only when you must. Visible focus rings, logical tab order, reduced-motion support.  
- **Motion**: 120–200 ms transitions, 60–120 ms micro-interactions. Motion explains state change; it’s not a personality test.  
- **Theming**: dark and light from the same tokens; keep contrast at or above WCAG AA.

## C. Data fetching and truth
- **Validate everything at the boundary** with Zod/Pydantic. If the payload lies, reject it loudly.  
- **Cache server state** with TanStack Query. Retry with backoff, stale-while-revalidate, optimistic updates for snappy feels.  
- **Schema-first**: define types once, generate clients when possible. Consistency beats vibes.

## D. Performance budget
- SSR for first paint, **code-split** per route and per heavy component, **island architecture** to keep hydration cheap.  
- **Virtualize large lists**, stream big results, use web workers for expensive transforms.  
- Responsive images, modern formats, prefetch on hover, defer non-critical scripts.  
- Track LCP/INP/CLS and fail CI when you regress. If you don’t measure, you’re cosplaying engineering.

## E. Displaying lots of data without melting brains
- **Overview → filter → detail**. Start with trend cards and small multiples, not a CSV avalanche.  
- **Small multiples** with shared scales beat one mega-spaghetti chart.  
- **Side-by-side compare** and overlaid plots with consistent units. Show provenance right in the legend.  
- **Brush/zoom** sync across charts; tooltips show value, unit, source, and uncertainty.  
- **“Export what I see”**: PNG + CSV + manifest of filters, units, transforms.

## F. Quality gates
- Unit tests on logic, a11y checks in CI, visual regression on core components, contract tests at API boundaries.  
- Feature flags, gradual rollout, honest changelogs. You can’t roll forward if you never shipped.

# Sources I actually use (and how)

Standards and fundamentals:
- **MDN Web Docs** for the canonical “how does the web work, actually.” Read reference pages, not Medium posts.
- **W3C / WHATWG** specs for HTML, CSS, fetch. When docs disagree, the standard wins.
- **WCAG / WAI-ARIA** for accessibility rules that keep you out of lawsuit bingo.
- **OWASP** cheatsheets for security guardrails you shouldn’t be trying to invent.

Framework/docs I reference while building:
- Astro, Next.js, SvelteKit, Tailwind, Radix UI, TanStack Query, Zod, Playwright, Prisma, FastAPI, SQLAlchemy.  
Method: read the “Getting Started,” then the “Concepts” or “Architecture” section, then copy one official example and delete half of it until you grok the parts.

High-signal design systems for patterns:
- **GOV.UK Design System**, **USWDS**, **Carbon**. You don’t need to copy their look to learn their structure, content rules, and a11y patterns.

Performance and a11y tooling:
- **Lighthouse-style audits** in any modern browser, plus axe DevTools for accessibility checks.  
- **WebPageTest** for network waterfalls when something feels sticky.

How to use these sources like an adult:
1) Start with MDN to confirm semantics and browser quirks.  
2) Check framework docs for the blessed way to do the thing.  
3) Sanity-check patterns in a mature design system.  
4) Run a11y and perf audits locally.  
5) If you still have a question, read the actual spec. It’s less scary than Twitter says.

# Concrete, reproducible setups

## Path A: Content-first site with Astro
```bash
# scaffold
npm create astro@latest my-site
cd my-site
npm i

# add React islands and Tailwind
npm i -D @astrojs/react tailwindcss postcss autoprefixer
npx astro add react
npx tailwindcss init -p

# tokens (example)
# src/design/tokens.json -> generate :root CSS vars in a small build script or by hand

# run
npm run dev
```
Use Astro for pages, drop in React components only where interactivity is needed. Ship near-zero JS to most pages. Add MDX for docs/blogs. Deploy to any static host or edge runtime.

## Path B: App-first with Next.js + Prisma + TanStack Query
```bash
# scaffold
npx create-next-app@latest app --ts --eslint
cd app

# deps
npm i @tanstack/react-query zod zustand
npm i -D @typescript-eslint/parser @types/node @types/react @types/react-dom

# db
npm i -D prisma
npm i @prisma/client
npx prisma init --datasource-provider sqlite
# define schema.prisma, then:
npx prisma migrate dev --name init

# run
npm run dev
```
Patterns:
- Use server components for data fetching; hydrate islands where you need client interactivity.
- Validate route handlers with Zod, convert to typed responses.
- Query mutations wrapped in react-query with optimistic updates and error toasts.
- Protect routes with middleware; store sessions in secure cookies.

## Path C: Python service with FastAPI + HTMX
```bash
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn jinja2 pydantic[dotenv] sqlalchemy

# run
uvicorn app.main:app --reload
```
Use server-rendered templates for most UI, sprinkle HTMX for interactivity without a SPA. Great for admin tools and data apps that want snappy perceived performance and simple deployment.

# Data-heavy rendering playbook
- **Virtualize** rows and DOM lists.  
- **Canvas/WebGL** plots for tens of thousands of points.  
- **Web Workers** for parsing and resampling; keep the main thread for interaction.  
- **Progressive reveal**: show summary stats and first chunk fast, stream the rest with a visible “loading more” row.  
- **Unit normalization**: pick a canonical axis unit for plots, show the original in tooltips. Log conversions to a side panel.

# Security and privacy essentials
- CSP with nonces/hashes. No wildcard soup.  
- HttpOnly, Secure cookies. SameSite=Lax or Strict for auth.  
- Rotate secrets, short-lived tokens, per-route rate limits.  
- Don’t collect PII you don’t need. Shockingly controversial, I know.

# Hand-off brief for another chat (neutral tone on purpose)

**Goal**: Build a fast, accessible web app with credible data presentation, robust provenance, and snappy interactions.

**Architecture**
- Choose Astro for content-first sites or Next/SvelteKit for app-first.
- Centralize design tokens; generate CSS variables.
- Use headless UI primitives for accessibility and theme control.
- Validate all external data with Zod/Pydantic at boundaries.
- Cache server state with TanStack Query; keep UI state local.

**Key features**
- Overview → filter → detail workflow.
- Small multiples, side-by-side compare, and overlay with consistent units.
- Tooltips with value, unit, source, and uncertainty.
- “Export what I see” with PNG + CSV + manifest of filters and conversions.

**Quality gates**
- a11y checks and perf audits in CI; fail on regression.
- Visual regression on design system components.
- Contract tests for APIs.

**References**
- MDN Web Docs, W3C/WHATWG specs, WCAG/WAI-ARIA, OWASP.
- Framework docs for Astro/Next/SvelteKit, Tailwind, Radix UI, TanStack Query, Zod, Playwright, Prisma, FastAPI/SQLAlchemy.

**Workflow**
1) Define IA and tokens.  
2) Scaffold framework, add headless UI and Tailwind.  
3) Build one end-to-end flow with SSR, validation, and caching.  
4) Implement charts with Canvas/WebGL and virtualization.  
5) Add a11y and perf audits to CI; fix issues.  
6) Ship behind a feature flag, monitor errors and performance, iterate.

There. That’s the map, the compass, and the snacks. Pick a path, keep your types tight, keep your UI honest, and stop shipping spinners that last longer than a microwave burrito.
