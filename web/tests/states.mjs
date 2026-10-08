import assert from "node:assert/strict";
import { chromium } from "@playwright/test";

const browser = await chromium.launch({ channel: "msedge", headless: true });
const base = "http://127.0.0.1:3001";
const report = {
  project_title: "Visual inspection system",
  executive_summary: "A practical computer vision project for production quality control.",
  objectives: ["Detect defects"], technical_architecture: "An image classifier with an inspection API.",
  dataset_plan: "Use approved inspection images.", model_plan: "Fine-tune a small vision model.",
  implementation_roadmap: ["Collect images", "Train", "Evaluate"],
  risks_and_mitigations: ["Monitor changing lighting."], success_metrics: ["High defect recall"],
  estimated_timeline_weeks: 4, required_skills: ["Python"], recommended_tools: ["PyTorch"],
  revision_count: 0, sources: ["https://example.com/research"],
};

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(base, { waitUntil: "networkidle" });
  await page.locator(".service-indicator.ready").waitFor();
  const fonts = await page.evaluate(() => [...new Set([...document.fonts].filter((font) => font.status === "loaded").map((font) => font.family))]);
  console.log("Loaded fonts:", fonts.join(", ") || "fallback only");
  assert.ok(fonts.includes("Bricolage Grotesque") && fonts.includes("Manrope") && fonts.includes("IBM Plex Mono"), "Design fonts did not load");

  await page.getByRole("button", { name: "Build project plan" }).click();
  assert.match(await page.locator(".inline-error").textContent(), /at least five words/);
  await page.getByRole("button", { name: "Vision", exact: true }).click();
  assert.equal(await page.locator(".inline-error").count(), 0);

  let attempt = 0;
  let release;
  const pending = new Promise((resolve) => { release = resolve; });
  await page.route("**/api/build", async (route) => {
    attempt += 1;
    if (attempt === 1) return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Research service temporarily unavailable." }) });
    await pending;
    await route.fulfill({ contentType: "application/x-ndjson", body: JSON.stringify({ type: "complete", report }) + "\n" });
  });
  await page.getByRole("button", { name: "Build project plan" }).click();
  await page.locator(".inline-error").waitFor();
  assert.match(await page.locator(".inline-error").textContent(), /temporarily unavailable/);
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await page.locator(".agent-item.active").waitFor();
  assert.equal(await page.locator("textarea").isDisabled(), true);
  assert.equal(await page.getByRole("button", { name: "Building your plan" }).isDisabled(), true);
  await page.locator(".pipeline-section").scrollIntoViewIfNeeded();
  await page.waitForTimeout(650);
  await page.screenshot({ path: ".screens/running.png" });
  release();
  await page.getByRole("heading", { name: report.project_title }).waitFor();
  await page.locator('.report-actions button[aria-label="New plan"]').click();
  await page.locator(".report-view").waitFor({ state: "detached" });
  assert.equal(await page.locator("textarea").inputValue(), "");
  assert.equal(await page.getByRole("progressbar").getAttribute("aria-valuenow"), "0");
  assert.deepEqual(errors, []);
  await page.close();
  console.log("Validation, server error, retry, running state, completion, and reset OK");

  const reduced = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce" });
  await reduced.goto(base, { waitUntil: "networkidle" });
  await reduced.locator(".pipeline-scene canvas").waitFor();
  assert.equal(await reduced.locator(".pipeline-scene").getAttribute("data-rendering"), "paused");
  assert.equal(await reduced.locator(".scene-toggle").isDisabled(), true);
  await reduced.close();
  console.log("Reduced-motion preference OK");
} finally {
  await browser.close();
}
