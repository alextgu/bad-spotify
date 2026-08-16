import { expect, test } from "playwright/test";

test("Try It offers Meta glasses without hiding the video samples", async ({ page }) => {
  await page.goto("/#try");

  await expect(page.getByRole("button", { name: "Any video" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Meta glasses · live" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Library → Birthday → Gym/ })).toBeVisible();

  await page.getByRole("button", { name: "Meta glasses · live" }).click();

  await expect(page.getByText("Native companion required")).toBeVisible();
  await expect(page.getByText(/browser does not connect to the glasses directly/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Check connection" })).toBeVisible();

  await page.getByRole("button", { name: "Any video" }).click();
  await expect(page.getByRole("button", { name: /Library → Birthday → Gym/ })).toBeVisible();
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
  await page.goto("/#try");
  await page.getByRole("button", { name: "Meta glasses · live" }).click();

  await page.getByRole("button", { name: "Check connection" }).click();

  await expect(page.getByText("Wearables API v1 is ready")).toBeVisible();
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
