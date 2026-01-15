import { test, expect } from '@playwright/test';

test.describe('Experiments Page', () => {
	test('loads and displays experiments list', async ({ page }) => {
		await page.goto('/experiments');

		await expect(page.locator('h1')).toContainText('Experiments');

		// Wait for cards to load
		await page.waitForSelector('[data-testid="experiment-card"]', { timeout: 10000 });

		const cards = page.locator('[data-testid="experiment-card"]');
		const count = await cards.count();
		expect(count).toBeGreaterThan(0);
	});

	test('displays experiment cards with correct info', async ({ page }) => {
		await page.goto('/experiments');

		const firstCard = page.locator('[data-testid="experiment-card"]').first();
		await expect(firstCard).toBeVisible();

		await expect(firstCard.locator('.experiment-name')).toBeVisible();
	});

	test('filters experiments by type', async ({ page }) => {
		await page.goto('/experiments');

		// Wait for cards to load first
		await page.waitForSelector('[data-testid="experiment-card"]', { timeout: 10000 });
		const initialCount = await page.locator('[data-testid="experiment-card"]').count();

		await page.selectOption('[data-testid="filter-type"]', 'full');

		// Wait for filter to apply
		await page.waitForTimeout(500);

		const filteredCards = page.locator('[data-testid="experiment-card"]');
		const filteredCount = await filteredCards.count();
		expect(filteredCount).toBeLessThanOrEqual(initialCount);
	});

	test('searches experiments', async ({ page }) => {
		await page.goto('/experiments');

		await page.fill('.search-input', 'experiment_');

		const cards = page.locator('[data-testid="experiment-card"]');
		const count = await cards.count();
		expect(count).toBeGreaterThan(0);
	});

	test('navigates to experiment detail on click', async ({ page }) => {
		await page.goto('/experiments');

		await page.locator('[data-testid="experiment-card"]').first().click();

		await expect(page).toHaveURL(/\/experiments\/.+/);
	});
});

test.describe('Experiment Detail Page', () => {
	test('displays experiment overview', async ({ page }) => {
		await page.goto('/experiments');
		await page.locator('[data-testid="experiment-card"]').first().click();

		await expect(page.locator('h1')).toBeVisible();
		await expect(page.locator('.stage-timeline')).toBeVisible();
	});

	test('shows pipeline status', async ({ page }) => {
		await page.goto('/experiments');
		await page.locator('[data-testid="experiment-card"]').first().click();

		const stageCard = page.locator('.card', { hasText: 'Pipeline Status' });
		await expect(stageCard).toBeVisible();
	});

	test('shows raw context data section', async ({ page }) => {
		await page.goto('/experiments');
		await page.locator('[data-testid="experiment-card"]').first().click();

		const rawDataCard = page.locator('.card', { hasText: 'Raw Context Data' });
		await expect(rawDataCard).toBeVisible();
	});
});
