import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "@playwright/test";
import sharp from "sharp";

const browser = await chromium.launch({ channel: "msedge", headless: true });
const base = "http://127.0.0.1:3001";
await fs.mkdir(".screens", { recursive: true });

async function checkViewport(name, width, height) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(base, { waitUntil: "networkidle" });
  await page.locator(".service-indicator.ready").waitFor();
  await page.locator(".pipeline-scene canvas").waitFor();
  await page.waitForFunction(() => document.querySelector(".pipeline-scene")?.getAttribute("data-rendering") === "active");
  assert.equal(await page.locator(".agent-item").count(), 6);
  assert.equal(await page.locator("textarea").count(), 1);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  assert.equal(overflow, false, `${name} has horizontal overflow`);
  const canvas = page.locator(".pipeline-scene canvas");
  const canvasBefore = await canvas.screenshot();
  const stats = await sharp(canvasBefore).stats();
  const variance = stats.channels.slice(0, 3).reduce((sum, channel) => sum + channel.stdev, 0);
  assert.ok(variance > 12, `${name} 3D canvas is blank (${variance})`);
  await page.mouse.move(width * 0.82, height * 0.34);
  await page.waitForTimeout(350);
  const canvasAfter = await canvas.screenshot();
  assert.notEqual(Buffer.compare(canvasBefore, canvasAfter), 0, `${name} 3D canvas did not move`);
  if (name === "desktop") {
    const bounds = await canvas.boundingBox();
    assert.ok(bounds);
    await page.mouse.move(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2);
    await page.mouse.down();
    assert.equal(await canvas.evaluate((element) => getComputedStyle(element).cursor), "grabbing");
    await page.mouse.move(bounds.x + bounds.width / 2 + 100, bounds.y + bounds.height / 2 + 35, { steps: 12 });
    await page.mouse.up();
    assert.equal(await canvas.evaluate((element) => getComputedStyle(element).cursor), "grab");
    console.log("desktop: sculpture drag and pointer release OK");
  }
  await page.getByRole("button", { name: "Pause 3D animation" }).click();
  await page.waitForFunction(() => document.querySelector(".pipeline-scene")?.getAttribute("data-rendering") === "paused");
  await page.waitForTimeout(300);
  const pausedCanvas = await canvas.screenshot();
  await page.waitForTimeout(250);
  assert.equal(Buffer.compare(pausedCanvas, await canvas.screenshot()), 0, `${name} paused sculpture kept moving`);
  await page.getByRole("button", { name: "Vision", exact: true }).click();
  const visionCanvas = await canvas.screenshot();
  assert.notEqual(Buffer.compare(pausedCanvas, visionCanvas), 0, `${name} example selection did not update the sculpture`);
  await page.locator("textarea").fill("");
  await page.getByRole("button", { name: "Play 3D animation" }).click();
  await page.waitForFunction(() => document.querySelector(".pipeline-scene")?.getAttribute("data-rendering") === "active");
  await page.locator(".agent-grid").scrollIntoViewIfNeeded();
  await page.waitForTimeout(650);
  assert.ok(await page.locator(".agent-item").evaluateAll((items) => items.every((item) => Number(getComputedStyle(item).opacity) > 0.99)), `${name} pipeline stages stayed hidden`);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(".screens", `${name}.png`), fullPage: true });
  assert.deepEqual(errors, []);
  console.log(`${name}: canvas variance ${variance.toFixed(1)}, motion and layout OK`);
  return page;
}

try {
  for (const [name, width, height] of [["wide", 1920, 1080], ["tablet", 768, 1024], ["small-mobile", 360, 740]]) {
    const page = await checkViewport(name, width, height);
    await page.close();
  }
  const desktop = await checkViewport("desktop", 1440, 900);
  const mobile = await checkViewport("mobile", 390, 844);
  const report = {
    project_title: "Student knowledge assistant",
    executive_summary: "A grounded assistant for university course documents.",
    objectives: ["Answer course questions with citations"],
    technical_architecture: "## System\nUpload PDFs, index chunks, retrieve relevant sections.",
    dataset_plan: "Use approved course materials. [Unconfirmed source](https://fabricated.example/not-a-dataset)",
    dataset_discovery_note: "Source-backed candidates. These benchmarks do not replace your university documents.",
    dataset_recommendations: [
      { name: "rajpurkar/squad", url: "https://huggingface.co/datasets/rajpurkar/squad", provider: "Hugging Face", description: "A reading comprehension benchmark.", relevance: "Useful for testing question answering; not a substitute for course-specific documents.", discovery_source: "Hugging Face API", data_type: "text", size: null, license: null, access: "Check the dataset terms" },
      { name: "Bank Marketing", url: "https://archive.ics.uci.edu/dataset/222/bank+marketing", provider: "UCI", description: "Tabular benchmark fixture for layout coverage.", relevance: "Fixture only; not recommended for this RAG project.", discovery_source: "Web search", data_type: null, size: null, license: null, access: null },
    ],
    model_plan: "Use a small language model with retrieval.",
    implementation_roadmap: ["Collect documents", "Build retrieval", "Evaluate answers"],
    risks_and_mitigations: ["Outdated content: refresh the index."],
    success_metrics: ["At least 90% grounded answers"],
    estimated_timeline_weeks: 4,
    required_skills: ["Python", "RAG"],
    recommended_tools: ["FastAPI", "ChromaDB"],
    revision_count: 1,
    sources: ["https://example.com/source"],
  };
  const mockBuild = (route) => route.fulfill({ status: 200, contentType: "application/x-ndjson", body: [
    { type: "started" },
    { type: "step", node: "supervisor", revision_count: null, critic_status: null, next_agent: "research" },
    { type: "step", node: "report", revision_count: 1, critic_status: null, next_agent: "done" },
    { type: "complete", report },
  ].map((line) => JSON.stringify(line)).join("\n") + "\n" });
  async function checkReportScroll(page, name) {
    await page.waitForTimeout(900);
    await page.waitForFunction(() => document.querySelector(".pipeline-scene")?.getAttribute("data-rendering") === "paused");
    const start = await page.evaluate(() => ({ y: window.scrollY, max: document.documentElement.scrollHeight - innerHeight }));
    assert.ok(start.max - start.y > 500, `${name} report has no room to scroll after appearing`);
    assert.equal(await page.locator(".report-section").count(), 6);
    await page.mouse.move(page.viewportSize().width / 2, page.viewportSize().height / 2);
    await page.mouse.wheel(0, 350);
    await page.waitForTimeout(250);
    const down = await page.evaluate(() => window.scrollY);
    assert.ok(down > start.y + 100, `${name} cannot scroll down through the report`);
    await page.mouse.wheel(0, -350);
    await page.waitForTimeout(250);
    const up = await page.evaluate(() => window.scrollY);
    assert.ok(up < down - 100, `${name} cannot scroll back up`);
    await page.locator('.report-nav a[href="#report-roadmap"]').click();
    const roadmapTop = await page.locator("#report-roadmap").evaluate((element) => element.getBoundingClientRect().top);
    assert.ok(roadmapTop >= 0 && roadmapTop < page.viewportSize().height / 2, `${name} roadmap navigation missed its section (${roadmapTop})`);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForFunction(() => document.querySelector(".pipeline-scene")?.getAttribute("data-rendering") === "active");
    console.log(`${name} report: vertical scroll, section navigation, and 3D pause/resume OK`);
  }
  await desktop.route("**/api/build", mockBuild);
  await desktop.getByRole("button", { name: "Knowledge" }).click();
  await desktop.getByRole("button", { name: /Build project plan/ }).click();
  await desktop.getByRole("heading", { name: report.project_title }).waitFor();
  await checkReportScroll(desktop, "desktop");
  assert.equal(await desktop.locator("#trace, .trace-payload").count(), 0);
  assert.equal(await desktop.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false);
  assert.equal(await desktop.locator(".roadmap-list li").count(), 3);
  assert.equal(await desktop.locator(".dataset-recommendation").count(), 2);
  assert.equal(await desktop.locator(".dataset-link").first().getAttribute("href"), report.dataset_recommendations[0].url);
  assert.equal(await desktop.locator('#report-dataset a[href*="fabricated.example"]').count(), 0);
  assert.ok((await desktop.locator(".dataset-metadata").first().textContent()).includes("Not provided by source"));
  const download = desktop.waitForEvent("download");
  await desktop.getByRole("button", { name: "Download JSON" }).click();
  const downloaded = await download;
  assert.match(downloaded.suggestedFilename(), /student-knowledge-assistant\.json/);
  const exported = JSON.parse(await fs.readFile(await downloaded.path(), "utf8"));
  assert.deepEqual(exported.dataset_recommendations, report.dataset_recommendations);
  await desktop.screenshot({ path: ".screens/report.png", fullPage: true });
  console.log("report: JSON download OK");
  await mobile.route("**/api/build", mockBuild);
  await mobile.getByRole("button", { name: "Knowledge" }).click();
  await mobile.getByRole("button", { name: /Build project plan/ }).click();
  await mobile.getByRole("heading", { name: report.project_title }).waitFor();
  assert.equal(await mobile.locator("#trace, .trace-payload").count(), 0);
  await checkReportScroll(mobile, "mobile");
  assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false);
  await mobile.screenshot({ path: ".screens/mobile-report.png", fullPage: true });
  console.log("mobile report: layout OK");
  await mobile.close();
  await desktop.close();
} finally {
  await browser.close();
}
