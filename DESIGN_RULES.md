# Design rules

Paste this into `AGENTS.md` so every session inherits it.

---

## Design

The failure mode we're avoiding: a page that is technically fine and looks
generated. That look comes from *undesigned* output — no type scale, no
spacing rhythm, too many greys — not from bad code. These rules exist to
remove the decisions that produce it.

### Never invent a value

Use only the tokens in `tailwind.config.ts`. **No arbitrary Tailwind values**
(`text-[17px]`, `mt-[13px]`, `bg-[#1e1e1e]`) in any component. If a value you
need doesn't exist, add it to the config as a named token and say why — don't
inline it. One-off values are how a page ends up with eleven font sizes.

### The type scale is five sizes

Display, heading, subheading, body, caption. Nothing between them. A section
heading is the same size as every other section heading, always. If something
needs to feel bigger, it goes up a step — it does not get a custom size.

### One accent, three appearances

Orange (`--target`) is the only accent, and it should appear roughly three
times per screen. More than that and it stops meaning anything. Blue
(`--scene`) is reserved for one thing: the world as it is, against orange as
what we do about it. Never use either decoratively.

### Spacing is a scale, not a feeling

Section padding, gap between cards, gap between a heading and its body — each
has one correct value, reused. If two similar things have 32px and 36px
between them, that's a bug.

### Look at what you built

Before claiming a visual change works, screenshot it and open the image.
Playwright is already available:

```
npx playwright screenshot --viewport-size=1440,900 http://localhost:3000 out.png
```

Check for: text colliding, elements overflowing on narrow widths, sections
that don't fill the viewport, and anything centred that should be aligned.
A change you have not looked at is not finished.

### Tells to avoid

These read as machine-generated to anyone who looks at a lot of sites:

- Gradient text, and purple-to-blue gradients of any kind
- Emoji used as icons
- Glassmorphism on more than one element
- `rounded-2xl` and a drop shadow on everything, including flat elements
- Every section centred
- Three-column feature grids with an icon above each heading
- "Powered by AI", "seamless", "revolutionary", "state of the art"

### Prefer editing to generating

Adapting an existing component beats writing one from scratch. `shadcn/ui`,
Aceternity and Magic UI are all copy-paste and already carry sensible spacing,
focus states and accessibility. Take the component, then change it — don't
reimplement it from a description.

### Motion has a job or it goes

Every animation should communicate something: that a section has arrived,
that state changed, that the agent is thinking. Motion added for texture makes
a page feel less confident, not more. One easing curve across the whole site.
