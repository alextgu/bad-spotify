import assert from "node:assert/strict";
import test from "node:test";
import { chromium } from "playwright";

test("the try-it section lists a sample before entering the workbench", async (t) => {
  const browser = await chromium.launch({ headless: true });
  t.after(() => browser.close());

  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto("http://localhost:3000/", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);

  const section = page.locator("#try");
  await section.evaluate((element) => element.scrollIntoView());

  assert.equal(await section.locator("[data-sample-card]").count(), 3);
  assert.equal(
    await section.getByRole("link", { name: /upload your own video/i }).count(),
    1,
  );
  await section.locator("[data-sample-card]").first().click();
  await section.getByRole("button", { name: /change sample clip/i }).waitFor();

  assert.equal(await section.locator("video").count(), 1);
  assert.equal(
    await section.getByRole("button", { name: /change sample clip/i }).count(),
    1,
  );
});
