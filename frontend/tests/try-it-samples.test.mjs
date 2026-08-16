import assert from "node:assert/strict";
import test from "node:test";
import { chromium } from "playwright";

test("the try-it section lists a sample before entering the workbench", async (t) => {
  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());

  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto("http://localhost:3000/", { waitUntil: "networkidle" });

  const section = page.locator("#try");
  await section.evaluate((element) => element.scrollIntoView());

  assert.equal(await section.locator("[data-sample-card]").count(), 1);
  assert.equal(await section.getByRole("button", { name: /use a sample clip/i }).count(), 0);
  assert.equal(await section.getByRole("button", { name: /upload your own/i }).count(), 0);

  await section.locator("[data-sample-card]").click();

  assert.equal(await section.locator("video").count(), 1);
  assert.equal(
    await section.getByRole("button", { name: /change sample clip/i }).count(),
    1,
  );
});
