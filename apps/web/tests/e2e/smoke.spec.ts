import { expect, type Page, test } from "@playwright/test";

async function waitForMapReady(page: Page) {
  const map = page.getByTestId("map");
  await expect(map).toBeVisible();
  await expect(map.locator("canvas")).toHaveCount(1, { timeout: 15_000 });
  await page.waitForTimeout(800);
}

async function placeCommutePins(page: Page) {
  await waitForMapReady(page);
  const map = page.getByTestId("map");
  const box = await map.boundingBox();
  if (!box) throw new Error("Map bounding box unavailable");
  await page.mouse.click(box.x + box.width * 0.35, box.y + box.height * 0.45);
  await page.mouse.click(box.x + box.width * 0.65, box.y + box.height * 0.55);
  await expect(page.getByTestId("compare-button")).toBeEnabled({
    timeout: 5_000,
  });
}

test.describe.configure({ mode: "serial" });

test.describe("15menit smoke", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.getByTestId("floating-top-panel")).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByRole("heading", { name: "15menit" })).toBeVisible();
    await waitForMapReady(page);
  });

  test("home loads with floating UI and commute mode default", async ({
    page,
  }) => {
    await expect(page.getByText(/^v\d/)).toBeVisible();
    await expect(page.getByTestId("mode-commute")).toHaveAttribute(
      "data-state",
      "active",
    );
    await expect(page.getByTestId("commute-route-inputs")).toBeVisible();
    await expect(page.getByTestId("map")).toBeVisible();
  });

  test("commute compare shows fastest indicator", async ({ page }) => {
    await placeCommutePins(page);
    const compareBtn = page.getByTestId("compare-button");
    await compareBtn.click();
    await expect(page.getByTestId("comparison-cards")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("fastest-badge")).toContainText(
      "Paling cepat",
      { timeout: 15_000 },
    );
  });

  test("transit card expands", async ({ page }) => {
    await placeCommutePins(page);
    await page.getByTestId("compare-button").click();
    const transitCard = page.getByTestId("comparison-card-transit");
    await expect(transitCard).toBeVisible({ timeout: 15_000 });
    await transitCard.click();
    await expect(page.getByText(/Koridor|Halte|Jalan/i)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("isochrone map click does not error", async ({ page }) => {
    await page.getByTestId("mode-isochrone").click();
    await expect(page.getByTestId("iso-minutes-label")).toBeVisible();
    const map = page.getByTestId("map");
    const box = await map.boundingBox();
    if (!box) throw new Error("Map bounding box unavailable");
    await page.mouse.click(box.x + box.width * 0.5, box.y + box.height * 0.5);
    await expect(
      page.locator('[data-sonner-toast][data-type="error"]'),
    ).toHaveCount(0, { timeout: 10_000 });
    await expect(page.getByTestId("map-marker-titik-asal")).toBeVisible({
      timeout: 5_000,
    });
  });

  test("geocode search finds Monas in Dari field", async ({ page }) => {
    const search = page.getByTestId("commute-dari-search").getByLabel("Dari");
    await search.fill("Monas");
    const result = page.locator("ul li button").first();
    await expect(result).toBeVisible({ timeout: 10_000 });
    await expect(result).toContainText(/Monumen Nasional|Monas/i);
    await result.click();
    await expect(search).toHaveValue(/Monumen Nasional|Monas/i, {
      timeout: 5_000,
    });
  });

  test("map style toggle switches dark/light icon", async ({ page }) => {
    const toggle = page.getByTestId("map-style-toggle");
    await expect(toggle).toBeVisible();
    const before = await toggle.getAttribute("aria-label");
    await toggle.click();
    await expect(toggle).not.toHaveAttribute("aria-label", before ?? "");
  });

  test("share URL loads commute pins from query params", async ({ page }) => {
    await page.goto("/?a=-6.17511,106.82715&b=-6.20876,106.84560");
    await waitForMapReady(page);
    await expect(page.getByTestId("compare-button")).toBeEnabled({
      timeout: 5_000,
    });
  });
});

test.describe("api unreachable", () => {
  test("shows banner when health check fails", async ({ page }) => {
    await page.route("**/api/health", (route) => route.abort("failed"));
    await page.goto("/");
    await expect(page.getByTestId("api-unreachable-banner")).toBeVisible({
      timeout: 10_000,
    });
  });
});

test.describe("mobile floating UI", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("bottom mode chips and top search visible without sheet", async ({
    page,
  }) => {
    await page.goto("/");
    await waitForMapReady(page);
    await expect(page.getByTestId("mode-commute")).toBeVisible();
    await expect(page.getByTestId("mode-isochrone")).toBeVisible();
    await expect(page.getByTestId("commute-dari-search")).toBeVisible();
    await expect(page.getByRole("button", { name: "Panel" })).toHaveCount(0);
  });
});
