/**
 * Full-page screenshots with the reveals settled.
 *
 *   node shot.cjs http://localhost:3100 /tmp/d.png 1440 900
 *
 * Playwright's `--full-page` flag captures immediately, which fires every
 * IntersectionObserver at once and photographs the page mid-reveal — every
 * section looks half-faded and you conclude the contrast is wrong. This
 * scrolls through first, waits for the 700ms reveals, then shoots.
 *
 * DESIGN_RULES.md: a change you haven't looked at is not finished.
 */
const { chromium } = require("playwright");

(async () => {
  const [url, out, w, h] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +w, height: +h } });
  await page.goto(url, { waitUntil: "networkidle" });

  const height = await page.evaluate(() => document.body.scrollHeight);
  for (let y = 0; y < height; y += +h) {
    await page.evaluate((y) => window.scrollTo(0, y), y);
    await page.waitForTimeout(220);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(900);

  await page.screenshot({ path: out, fullPage: true });
  await browser.close();
})();
