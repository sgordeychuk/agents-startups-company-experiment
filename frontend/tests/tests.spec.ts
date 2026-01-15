import { test, expect } from '@playwright/test';

test.describe('Test Results Page', () => {
	test('loads and displays test results', async ({ page }) => {
		await page.goto('/tests');

		await expect(page.locator('h1')).toContainText('Test Results');

		// Wait for cards to load
		await page.waitForSelector('[data-testid="test-result-card"]', { timeout: 10000 });

		const cards = page.locator('[data-testid="test-result-card"]');
		const count = await cards.count();
		expect(count).toBeGreaterThan(0);
	});

	test('displays test cards with status badges', async ({ page }) => {
		await page.goto('/tests');

		const firstCard = page.locator('[data-testid="test-result-card"]').first();
		await expect(firstCard).toBeVisible();

		// Badge is now rendered as a span with badge class
		const badge = firstCard.locator('.badge');
		await expect(badge).toBeVisible();
	});

	test('filters by status', async ({ page }) => {
		await page.goto('/tests');

		await page.selectOption('[data-testid="filter-status"]', 'passed');

		const cards = page.locator('[data-testid="test-result-card"]');
		const count = await cards.count();

		for (let i = 0; i < Math.min(count, 5); i++) {
			const card = cards.nth(i);
			await expect(card.locator('.badge')).toContainText('Passed');
		}
	});

	test('searches test results', async ({ page }) => {
		await page.goto('/tests');

		await page.fill('.search-input', 'idea');

		// Check results count text is visible
		const resultsCount = page.locator('.results-count');
		await expect(resultsCount).toBeVisible();
	});

	test('navigates to test detail on click', async ({ page }) => {
		await page.goto('/tests');

		await page.locator('[data-testid="test-result-card"]').first().click();

		await expect(page).toHaveURL(/\/tests\/.+/);
	});
});

test.describe('Test Result Detail Page', () => {
	test('displays test overview', async ({ page }) => {
		await page.goto('/tests');
		await page.locator('[data-testid="test-result-card"]').first().click();

		await expect(page.locator('h1')).toBeVisible();

		// Look for a badge anywhere in the header area
		const badge = page.locator('.badge').first();
		await expect(badge).toBeVisible();
	});

	test('shows test overview card', async ({ page }) => {
		await page.goto('/tests');
		await page.locator('[data-testid="test-result-card"]').first().click();

		const overviewCard = page.locator('.card', { hasText: 'Test Overview' });
		await expect(overviewCard).toBeVisible();
	});

	test('shows raw test result', async ({ page }) => {
		await page.goto('/tests');
		await page.locator('[data-testid="test-result-card"]').first().click();

		const rawCard = page.locator('.card', { hasText: 'Raw Test Result' });
		await expect(rawCard).toBeVisible();
	});
});
