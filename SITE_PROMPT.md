# Prompt for Claude Code — the site

Run from the repo root. Paste everything below the line, then attach your
reference screenshots when it asks.

---

I'm making the landing page in `frontend/` look production-quality. It
currently has the right structure and the wrong visual layer.

**Read first:** `DESIGN_RULES.md`, then `frontend/README.md`, then
`frontend/app/page.tsx` to see the seven sections and their order.

## How we're working

I will give you reference sites — screenshots or URLs. Your job is to **match
them**, not to interpret them. Do not invent a look. When I give you a
reference:

1. Tell me what specifically you're taking from it: the type scale, the
   spacing rhythm, a particular layout, the motion. Name it before you build.
2. If two references disagree, ask me which wins rather than averaging them.
   An average of two good designs is a bad design.
3. Pull components from `shadcn/ui`, Aceternity UI or Magic UI where they fit
   rather than writing from scratch. Adapt them to our tokens. Say which
   library each one came from.

## Verify by looking

After any visual change, screenshot it and open the image before telling me
it's done:

```bash
cd frontend && npm run build && npx next start -p 3000 &
npx playwright screenshot --viewport-size=1440,900 http://localhost:3000 /tmp/check.png
```

Check for text collisions, overflow at 375px width, sections that don't fill
the viewport, and anything centred that should be left-aligned. **A change you
haven't looked at is not finished.** If you can't screenshot it, say so rather
than assuming it worked.

## Constraints

- **No arbitrary Tailwind values.** No `text-[17px]`, no `mt-[13px]`, no
  `bg-[#1e1e1e]`. Only tokens from `tailwind.config.ts`. If you need a value
  that doesn't exist, add it as a named token and tell me why.
- **Five type sizes.** Every section heading is identical in size.
- **One accent.** Orange `target` appears about three times per screen. Blue
  `scene` means one thing only: the world as it is, against orange as what we
  do about it.
- Keep `brand.ts` as the only place the product is named.
- Keep the `placeholder` flag in `lib/clips.ts` working — it drives three
  separate warnings, and the film is the second thing anyone sees.
- Don't reorder or remove sections without asking. The order is deliberate.

## What already exists — don't rebuild it

- Seven sections in `frontend/components/`, all wired into `app/page.tsx`
- `lib/content.ts` — all the copy. Change the design, not the words
- `lib/brand.ts` — name, tagline, headline numbers
- `.section-page` in `globals.css` — full-height screens
- `Reveal.tsx` — scroll animation, ready to be replaced by something better

## What to do first

Before touching anything, tell me:

1. What's visually weakest right now, in order, with a reason for each
2. Which of the seven sections would gain most from a real component
3. What you'd need from me — references, images, footage — to fix the top one

Then wait. Don't start until I've given you a reference to match.

## Two things to protect

- The film is section 2 and it's currently a bare `<video>`. It's the most
  important element on the page.
- The reasoning has to stay visible somewhere on every screen that has it.
  That's the difference between an agent and a shuffle button, and it's most
  of why the technical work reads as serious.
