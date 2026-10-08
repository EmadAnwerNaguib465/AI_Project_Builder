import assert from "node:assert/strict";
import { chromium } from "@playwright/test";

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: 1365, height: 900 } });
try {
  await page.goto("http://127.0.0.1:3001", { waitUntil: "networkidle" });
  await page.locator(".service-indicator.ready").waitFor();
  await page.locator("textarea").fill("Build a small English movie review sentiment classifier for a student project using a public dataset, a CPU laptop, and a simple web interface.");
  await page.getByRole("button", { name: /Build project plan/ }).click();
  await page.locator(".report-view, .inline-error").first().waitFor({ timeout: 600000 });
  if (await page.locator(".inline-error").count()) {
    throw new Error(await page.locator(".inline-error").textContent());
  }
  const title = await page.locator("#report-title").textContent();
  assert.ok(title);
  assert.ok(await page.locator(".roadmap-list li").count() || await page.getByRole("tab", { name: "Roadmap" }).count());
  await page.screenshot({ path: ".screens/live-report.png", fullPage: true });
  console.log(`LIVE_REPORT_OK: ${title}`);
} finally {
  await browser.close();
}
