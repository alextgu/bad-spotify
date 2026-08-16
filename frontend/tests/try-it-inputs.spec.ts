import { expect, test } from "playwright/test";

test("Try It stays video-only and links to the separate glasses surface", async ({ page }) => {
  await page.goto("/#try");

  await expect(page.getByRole("button", { name: /Library → Birthday → Gym/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "Upload your own" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Open Meta glasses live/i })).toHaveAttribute(
    "href",
    "/glasses",
  );
  await expect(page.getByRole("button", { name: "Check connection" })).toHaveCount(0);
});

test("Meta connection check uses the wearable capabilities endpoint", async ({ page }) => {
  await page.route("**/api/wearables/v1/capabilities", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        service: "slopify",
        protocol_version: 1,
        ready: true,
        authentication: "bearer",
      }),
    });
  });
  await page.goto("/glasses");

  await page.getByRole("button", { name: "Check connection" }).click();

  await expect(page.getByText("Wearables API v1 is ready")).toBeVisible();
});

test("glasses surface never mounts video samples or upload controls", async ({ page }) => {
  await page.goto("/glasses");

  await expect(page.getByText("Native companion required")).toBeVisible();
  await expect(page.getByRole("button", { name: "Check connection" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Upload your own" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Library → Birthday → Gym/ })).toHaveCount(0);
  await expect(page.getByRole("link", { name: /Back to video demo/i })).toHaveAttribute(
    "href",
    "/#try",
  );
});

test("video inputs remain reachable on a phone-sized page", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#try");
  const upload = page.getByRole("button", { name: "Upload your own" });
  const chooser = page.locator("#try");

  expect(await chooser.evaluate((element) => getComputedStyle(element).overflowY)).not.toBe(
    "hidden",
  );
  expect(await page.evaluate(() => document.documentElement.scrollHeight)).toBeGreaterThan(844);

  for (let step = 0; step < 40; step += 1) {
    const current = await upload.boundingBox();
    if (current && current.y >= 0 && current.y + current.height <= 844) break;
    await page.mouse.wheel(0, current && current.y < 0 ? -100 : 100);
    await page.waitForTimeout(40);
  }
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0);

  const box = await upload.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.y + box!.height).toBeLessThanOrEqual(844);
});
