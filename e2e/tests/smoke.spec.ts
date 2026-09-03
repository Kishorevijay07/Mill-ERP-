import { expect, test } from "@playwright/test";

test.describe("Phase 0 smoke", () => {
  test("app shell renders", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Rice Mill ERP" }),
    ).toBeVisible();
  });
});

// The critical Phase-1 release-gate journey lives here once the business modules
// exist (see docs/TESTING.md):
//   login → government load → weighment → paddy QC → accept → paddy lot →
//   milling batch → consume → category 1 & 2 → rice QC → rice lot → dispatch →
//   delivery receipt → claim → PDF → payment → PAID
test.fixme("critical release-gate journey", async () => {
  // Implemented incrementally from Stage 1 onward.
});
