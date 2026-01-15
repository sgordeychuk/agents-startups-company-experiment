import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
	test('sidebar navigation works correctly', async ({ page }) => {
		await page.goto('/');

		await page.click('[data-testid="nav-experiments"]');
		await expect(page).toHaveURL('/experiments');

		await page.click('[data-testid="nav-tests"]');
		await expect(page).toHaveURL('/tests');

		await page.click('[data-testid="nav-home"]');
		await expect(page).toHaveURL('/');
	});

	test('breadcrumb navigation shows correct path', async ({ page }) => {
		await page.goto('/experiments');

		// Look for breadcrumb by aria-label
		const breadcrumb = page.locator('[aria-label="Breadcrumb"]');
		await expect(breadcrumb).toContainText('Home');
		await expect(breadcrumb).toContainText('Experiments');
	});

	test('breadcrumb links work', async ({ page }) => {
		await page.goto('/experiments');
		await page.locator('[data-testid="experiment-card"]').first().click();

		// Use aria-label to find breadcrumb then find Experiments link
		await page.click('[aria-label="Breadcrumb"] a:has-text("Experiments")');
		await expect(page).toHaveURL('/experiments');
	});

	test('header logo navigates to home', async ({ page }) => {
		await page.goto('/experiments');

		// Click on the logo by finding the link with "AI" text
		await page.click('a.logo');
		await expect(page).toHaveURL('/');
	});
});

test.describe('Responsive Design', () => {
	test('page renders on mobile viewport', async ({ page }) => {
		await page.setViewportSize({ width: 375, height: 667 });
		await page.goto('/');

		await expect(page.locator('h1')).toBeVisible();
		await expect(page.locator('[data-testid="stat-card"]').first()).toBeVisible();
	});

	test('experiments page works on mobile', async ({ page }) => {
		await page.setViewportSize({ width: 375, height: 667 });
		await page.goto('/experiments');

		await expect(page.locator('h1')).toContainText('Experiments');

		const cards = page.locator('[data-testid="experiment-card"]');
		await expect(cards.first()).toBeVisible();
	});

	test('filters work on mobile', async ({ page }) => {
		await page.setViewportSize({ width: 375, height: 667 });
		await page.goto('/experiments');

		await page.selectOption('[data-testid="filter-type"]', 'full');

		// Check that the results count text is visible
		const resultsText = page.locator('text=Showing');
		await expect(resultsText).toBeVisible();
	});
});
