import assert from "node:assert/strict";
import test from "node:test";
import { chromium } from "playwright";

test("section handoffs mix motion modes and animate the results colour fill", async (t) => {
  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());

  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto("http://localhost:3000/", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);

  const modes = await page.locator("main > div").evaluateAll((sections) =>
    sections.map((section) => section.getAttribute("data-page-transition")),
  );

  assert.deepEqual(modes, [null, "fade", "fade", "fade", "lift", "fill", "fade"]);

  const fill = page.locator('[data-page-transition-layer="fill"]');
  assert.equal(await fill.count(), 1);

  await fill.evaluate((layer) => {
    window.__fillTransitionSeen = false;
    new MutationObserver(() => {
      const transform = getComputedStyle(layer).transform;
      if (transform !== "none" && transform !== "matrix(1, 0, 0, 0, 0, 0)") {
        window.__fillTransitionSeen = true;
      }
    }).observe(layer, { attributes: true, attributeFilter: ["style"] });
  });

  await page.locator("#pipeline").evaluate((section) => section.scrollIntoView());
  await page.waitForTimeout(120);
  await page.keyboard.press("PageDown");
  await page.waitForTimeout(1000);

  assert.equal(await page.evaluate(() => window.__fillTransitionSeen), true);
});
