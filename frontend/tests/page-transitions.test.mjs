import assert from "node:assert/strict";
import test from "node:test";
import { chromium } from "playwright";

test("section handoffs mix motion modes and animate the results colour fill", async (t) => {
  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());

  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto("http://localhost:3000/", { waitUntil: "networkidle" });

  const modes = await page.locator("main > div").evaluateAll((sections) =>
    sections.map((section) => section.getAttribute("data-page-transition")),
  );

  assert.deepEqual(modes, [null, "fade", "wipe", "fade", "lift", "fill", "wipe"]);

  const fill = page.locator('[data-page-transition-layer="fill"]');
  assert.equal(await fill.count(), 1);

  await page.locator("#pipeline").evaluate((section) => section.scrollIntoView());
  await page.mouse.wheel(0, 120);
  await page.waitForTimeout(220);

  const scale = await fill.evaluate((layer) => getComputedStyle(layer).transform);
  assert.notEqual(scale, "none");
  assert.notEqual(scale, "matrix(1, 0, 0, 0, 0, 0)");
});
