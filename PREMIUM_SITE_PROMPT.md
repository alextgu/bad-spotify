# Prompt for Claude Code — premium site pass

Run from the repo root. Paste everything below the line.

---

I'm rebuilding the visual layer of the landing page in `frontend/` to a
premium standard. The structure, copy and section order are already decided
and correct — **do not change them.** This is a design pass only.

**Read first:** `DESIGN_RULES.md`, `frontend/README.md`, then
`frontend/app/page.tsx` for the seven sections and their order.

## The references

Study these three before writing anything. Fetch them if you can; if you
can't, work from the specification below, which is derived from them.

- **daylightcomputer.com** — pacing. One idea per screen, generous emptiness,
  sections that arrive rather than scroll past. This is the primary reference.
- **linear.app** — dark surface discipline. How few greys you can use, how
  restrained a border can be, how little glow is needed to read as premium.
- **teenage.engineering** — confidence. Almost nothing is explained. The type
  and the product carry it.

**What we are NOT taking:** Linear's gradients and purple, Daylight's warm
cream palette, Teenage Engineering's playfulness. Take the *discipline* from
each, not the surface.

## The specification — these are hard values

Put these in `tailwind.config.ts` as named tokens. Nothing may be used that
isn't here. If you need something new, add it as a token and tell me why.

**Type — exactly five sizes, no others**

| Token | Size | Tracking | Weight | Leading |
|---|---|---|---|---|
| display | `clamp(3rem, 8vw, 6rem)` | -0.04em | 600 | 1.0 |
| heading | `clamp(2rem, 4.5vw, 3.25rem)` | -0.035em | 600 | 1.1 |
| subheading | `1.25rem` | -0.02em | 500 | 1.4 |
| body | `1rem` | 0 | 400 | 1.65 |
| caption | `0.8125rem` | 0 | 400 | 1.5 |

Every section heading uses `heading`. Identical, every time.

**Spacing — one rhythm**

| Gap | Value |
|---|---|
| Section padding (vertical) | 160px desktop, 96px below `md` |
| Heading → its subline | 16px |
| Subline → content | 64px |
| Between cards | 32px |
| Inside a card | 12px |

**Measure.** Body text never exceeds `65ch`. Sub-lines never exceed `45ch`.
Content column max-width 1120px; media may go full-bleed.

**Alignment.** Left-align everything except the hero. Centred body text is the
most common tell of an amateur page — premium sites centre almost nothing
below the fold.

**Colour.** One accent (`target` orange), about three appearances per screen.
`scene` blue means one thing only: the world as it is, against orange as what
we do about it. Three greys maximum in the whole page. No gradients on text,
ever.

**Motion — one curve, three durations**

- Curve: `cubic-bezier(0.21, 0.47, 0.32, 0.98)` — nothing else, anywhere
- Reveal: 700ms · Interaction: 250ms · Colour transition: 1400ms
- Stagger siblings by 80ms, never animate a group in unison
- Reveal once. Re-animating on every scroll-past is what makes a page feel cheap
- Everything must respect `prefers-reduced-motion`

**Borders and depth.** Borders are `rgba(255,255,255,0.08)` — if you can
clearly see the border, it's too strong. No drop shadows on flat elements.
No glassmorphism on more than one element in the entire page.

## Components

Two already exist in the house style — read them first and match their
conventions:

- `components/HeroVideoDialog.tsx` — poster expanding to a player
- `components/BlurFade.tsx` — the reveal, replacing `Reveal.tsx`

Needs `npm i motion` before they build.

Take anything else from `shadcn/ui`, Aceternity UI or Magic UI rather than
writing from scratch. Adapt to our tokens and say which library each came from.

## Build order

Do these one at a time. Show me a screenshot after each, and stop.

1. **Tokens.** Put the scale above into `tailwind.config.ts`, then convert
   every existing component to use it. Report every arbitrary value you had
   to remove — that list tells us where the page was undesigned.
2. **Section 2, the film.** Swap the bare `<video>` for `HeroVideoDialog`.
   This is the most important element on the page.
3. **Section 1, the hero.** Type at `display`, one accent use, nothing centred
   except this.
4. **`BlurFade` replacing `Reveal`** everywhere, with 80ms staggers.
5. **Sections 4 and 5** — currently walls of text. Sticky-scroll one of them:
   pin a visual, change the text beside it.
6. **Mobile.** Every section at 375px. This is where it will actually break.

## Verify by looking

After each step:

```bash
cd frontend && npm run build
npx next start -p 3000 &
npx playwright screenshot --viewport-size=1440,900 http://localhost:3000 /tmp/d.png
npx playwright screenshot --viewport-size=375,812 http://localhost:3000 /tmp/m.png
```

Open both images. Check for text collisions, overflow, sections that don't
fill the viewport, and anything centred that shouldn't be. **A change you
haven't looked at is not finished.** If you can't screenshot, say so plainly
rather than assuming it worked.

## Do not

- Change section order, copy, or the seven-section structure
- Rename anything — `brand.ts` is the only place the product is named
- Break the `placeholder` flag in `lib/clips.ts`; it drives three warnings
- Add a navbar
- Use emoji as icons, gradient text, or the phrase "powered by AI"

## First response

Before writing code, tell me:

1. The three weakest things visually right now, in order, with the reason
2. Every arbitrary Tailwind value currently in the codebase (`grep -rn '\-\[' frontend/components frontend/app`)
3. Which of the six build steps you think is highest value, if you disagree
   with my order

Then start on step 1 only.
