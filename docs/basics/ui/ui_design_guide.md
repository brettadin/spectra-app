# UI Design Guide



You want “pretty, fast, snappy, flexible, modular, credible, accurate, reliable, safe, informative, and again pretty.” So… basically you want the Holy Grail and you’d like it delivered yesterday. Fine. Here’s the whole playbook, distilled so you can actually ship.



\# Foundations: what “good” looks like

\- \*\*Pretty\*\*: clear visual hierarchy, consistent spacing, balanced type scale, restrained color palette, purposeful motion. Pretty isn’t glitter; it’s alignment, rhythm, and good contrast.

\- \*\*Fast/snappy\*\*: perceived speed > raw speed. Preload, optimistic UI, instant feedback. Never leave users staring at a dead screen wondering if their click worked.

\- \*\*Easy to use\*\*: spare people choices you can make for them. Defaults > settings. Progressive disclosure beats dumping the cockpit on page one.

\- \*\*Flexible/modular\*\*: design tokens + composable components + clean state boundaries. If you’re copying CSS twice, you’ve already lost.

\- \*\*Credible/accurate/reliable\*\*: provenance, units, timestamps, uncertainty ranges, and verifiable links. If data can be wrong, show how wrong.

\- \*\*Safe\*\*: accessibility, input validation, least-privilege permissions, clear undo/escape hatches, privacy by default.

\- \*\*Informative\*\*: context at the elbow. Inline help, empty states that teach, and error messages that actually say what broke.



\# Visual system: make it pretty without trying too hard

\- \*\*Type\*\*: two families max (UI: Inter/Roboto/System; Display: the fun one). Use an 8-pt spacing grid and a 1.125–1.25 modular scale for headings.

\- \*\*Color\*\*: one brand hue, one accent, neutrals doing the heavy lifting. Provide semantic roles (info/success/warn/error) and auto-derive light/dark variants via tokens.

\- \*\*Density\*\*: compact by default for power users; a “comfortable” toggle for normal humans.

\- \*\*Icons\*\*: pick one set. Don’t mix styles. Pair icons with labels unless the icon is universally obvious.

\- \*\*Motion\*\*: 120–200 ms enter/exit, 60–120 ms micro-interactions. Easing: standard, not circus. Motion communicates state change, not personality quirks.



\# Information design: say more with fewer pixels

\- \*\*Hierarchy\*\*: page title > primary action > primary data > secondary actions > metadata. If everything is bold, nothing is.

\- \*\*Tables\*\*: freeze the identity column, right-align numbers, monospace for IDs, row hover, column filters, and a “copy row as JSON.”

\- \*\*Charts\*\*: show units, uncertainty, and sources. Provide tooltips with exact values and keyboard-accessible data download. Avoid dual y-axes unless you like confusion.

\- \*\*Empty states\*\*: teach what goes here, how to add it, and link to an example. Screens shouldn’t look broken just because the user hasn’t done anything yet.



\# Interaction model: reduce cognitive tax

\- \*\*Navigation\*\*: shallow beats deep. 3 clicks that make sense are better than 1 click into a labyrinth.

\- \*\*Forms\*\*: validate on blur, summarize errors at top, inline specifics near fields, and always preserve input on error. Offer sensible defaults.

\- \*\*Shortcuts\*\*: power users live on keyboards. Offer global search (k), recent items (g r), and contextual actions.

\- \*\*Selection\*\*: checkbox groups with “select all in view,” not “select the invisible 10,000.” Batch actions should preview what they’ll do.



\# Architecture: flexible, modular, expandable

\- \*\*Design tokens\*\*: colors, spacing, radius, shadows, typography, motion. Store as JSON. Source of truth for web, mobile, and exported assets.

\- \*\*Component strategy\*\*:

&nbsp; - Headless primitives (Radix/Headless UI-style) for behavior.

&nbsp; - Skinnable shells for visuals (your theme).

&nbsp; - Use composition over props explosion. If your component takes 20 props, you built a god-object.

\- \*\*State\*\*:

&nbsp; - Server state: keep it server-side with a cache layer (TanStack Query/RTK Query). It’s not your component’s pet.

&nbsp; - UI state: colocate. Keep global state tiny. Cross-cutting: feature stores or contexts with selectors.

\- \*\*Data contracts\*\*: strict schemas (Zod/Pydantic) at boundaries. Parse and validate everything that comes from outside your process. Log rejections with reasons.

\- \*\*Module boundaries\*\*: feature-first folders (feature/ui, feature/logic, feature/api). Every feature exports a public API; internal bits stay internal.



\# Performance: make it feel instant

\- \*\*Critical path\*\*: inline critical CSS, lazy-load below-the-fold. Ship modern bundles (ESM), split by route and by component.

\- \*\*Hydration pain\*\*: minimize client JS where possible. Use islands or partial hydration if your stack supports it.

\- \*\*Perceived speed\*\*: skeletons that resemble final layout, optimistic updates, prefetch on hover/visible.

\- \*\*Lists\*\*: window big collections. Avoid rendering 50k DOM nodes in a fit of optimism.

\- \*\*Images\*\*: responsive sizes, modern formats, lazy with priority hints for above-the-fold.

\- \*\*Metrics budget\*\*: LCP < 2.5s, INP < 200ms, CLS < 0.1. If you don’t measure, you’re guessing.



\# Accessibility: non-negotiable

\- \*\*Semantics\*\*: use real buttons, real links, real headings. ARIA is for when semantics aren’t enough, not as a default.

\- \*\*Contrast\*\*: meet WCAG AA minimums in both light and dark themes.

\- \*\*Focus\*\*: visible outlines, logical tab order, no keyboard traps. Dialogs must trap focus and announce themselves.

\- \*\*Media\*\*: captions, transcripts, alt text that’s actually useful.

\- \*\*Motion\*\*: respect “reduced motion.” No parallax nausea.



\# Trust, credibility, and safety

\- \*\*Provenance\*\*: show source, timestamp, version/DOI, unit systems, and transforms applied. “Trust us bro” isn’t provenance.

\- \*\*Auditability\*\*: export “what I see” plus a manifest of filters, transforms, units.

\- \*\*Safe actions\*\*: confirm destructive ops with specific consequences. Offer undo when possible. Always allow cancel/escape.

\- \*\*Privacy-by-default\*\*: minimal data retention, client-side encryption where possible, and explicit scopes for tokens/keys.



\# Content and microcopy

\- \*\*Tone\*\*: specific, concise, slightly human. “Something went wrong” is useless; “Upload failed: CSV header missing ‘wavelength\_nm’. Fix and retry.” is helpful.

\- \*\*Naming\*\*: nouns for places (Datasets), verbs for actions (Export). Don’t invent jargon to sound clever.

\- \*\*Progress\*\*: percent + step names. Users want to know if they should make coffee or not.



\# Observability and quality

\- \*\*Telemetry\*\*: log page views, API latencies, error rates, and rage-clicks. Respect privacy and let users opt out.

\- \*\*User feedback\*\*: “Was this helpful?” on docs and complex screens. Lightweight issue reporter with screenshot + console log redaction.

\- \*\*Testing\*\*:

&nbsp; - Visual regression on the design system.

&nbsp; - Component tests for logic.

&nbsp; - Contract tests at API boundaries.

&nbsp; - Accessibility checks in CI.

\- \*\*Release hygiene\*\*: feature flags, gradual rollout, and meaningful changelogs.



\# Documentation and governance

\- \*\*Design system site\*\*: tokens, components, usage do’s/don’ts, live code sandboxes, accessibility notes, and copy guidelines.

\- \*\*Decision records\*\*: short ADRs. Future you will forget why you chose option B.

\- \*\*Contribution model\*\*: lint rules, commit conventions, preview builds per PR, and a human actually reviewing diffs.



\# Opinionated stack that won’t fight you

Pick equivalents if you must, but pick once.

\- \*\*Core\*\*: TypeScript + a modern meta-framework with routing, SSR/SSG, and API endpoints. Build with Vite or the framework’s default.

\- \*\*Components\*\*: Headless library (Radix/Headless UI). Style with CSS variables + utility classes or a typed CSS-in-TS. Theming via tokens.

\- \*\*Data\*\*: typed fetch client, TanStack Query for caching. Schema validation with Zod. Feature-based API modules.

\- \*\*State\*\*: small global store (Zustand) for cross-cutting UI; everything else local or server cached.

\- \*\*Charts\*\*: a capable lib that handles thousands of points smoothly and supports accessibility. Provide CSV export hooks.

\- \*\*QA\*\*: Playwright for E2E, Vitest/Jest for unit, Storybook for components with a11y and visual tests.



\# Concrete checklists you can actually use



\## Design review (5 minutes before you ship)

\- Hierarchy reads left to right, top to bottom

\- One primary action per page, visually distinct

\- Consistent grid and spacing; no “floating” elements

\- All text >= 14px, body ~16px, headings scaled x1.125–x1.25

\- Dark mode contrast verified; disabled state still legible

\- Motion consistent and useful, not decorative clutter



\## Usability sanity pass

\- Keyboard-only navigation works everywhere

\- Every icon button has a label or tooltip

\- Errors are actionable and persistent until resolved

\- Empty states instruct and link to the next step

\- Undo exists for destructive actions or there’s a delay-to-commit



\## Performance pass

\- Bundle split by route; heavy charts lazy-load

\- Images sized to containers; no 4K icons

\- Long lists virtualized; filters debounce at ~250 ms

\- Prefetch on hover for likely next routes

\- Metrics tracked in a dashboard with budgets



\## Data credibility pass

\- Units and significant figures shown

\- Source/DOI/version displayed with timestamp

\- Transformations listed and exportable

\- “Copy exact value” and “Export what I see” available



\# Patterns that save your bacon

\- \*\*Command palette\*\* for power navigation.

\- \*\*Inline diff\*\* when editing structured objects.

\- \*\*Side-by-side compare\*\* for datasets and settings.

\- \*\*Autosave + explicit “Saved” state\*\* with timestamp.

\- \*\*Session restore\*\* after refresh/crash, including unsaved form input.



\# Things to stop doing immediately

\- Ship settings pages to dodge making decisions.

\- Hide critical actions behind hover-only controls.

\- Use color as the only signal for status.

\- Animate everything like a toddler with a sugar rush.

\- Show spinners longer than 300 ms without contextual info.



\# Starter blueprint (adapt as needed)

1\. Define tokens (color, type, space, radius, shadow, motion) in JSON. Generate CSS variables.

2\. Build primitives: Button, Input, Select, Dialog, Tabs, Tooltip, Toast, Table, Skeleton, EmptyState.

3\. Establish data contracts with schemas. Reject and log invalid payloads at the edge.

4\. Create page templates: Index, List, Details, Editor, Wizard. Lock header/toolbar patterns.

5\. Implement data layer with cache, retries, optimistic mutations, and toasts.

6\. Wire telemetry, error boundary, a11y checks, and feature flags before feature #2.

7\. Ship one end-to-end flow. Measure. Fix the slowest thing first. Repeat.



You asked for “all the works.” That’s the works. It’s not magic; it’s discipline, taste, and refusing to cut corners you’ll trip over later. Now go make something that doesn’t make future-you cry.



