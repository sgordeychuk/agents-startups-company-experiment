import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
	test('loads and displays dashboard', async ({ page }) => {
		await page.goto('/');

		await expect(page.locator('h1')).toContainText('Dashboard');
		await expect(page.locator('.subtitle')).toContainText('AI Innovators');
	});

	test('shows statistics cards', async ({ page }) => {
		await page.goto('/');

		const statCards = page.locator('[data-testid="stat-card"]');
		await expect(statCards).toHaveCount(5);

		await expect(page.locator('.stat-label').first()).toBeVisible();
	});

	test('displays recent experiments', async ({ page }) => {
		await page.goto('/');

		const experimentsCard = page.locator('.card', { hasText: 'Recent Experiments' });
		await expect(experimentsCard).toBeVisible();
	});

	test('displays recent test results', async ({ page }) => {
		await page.goto('/');

		const testsCard = page.locator('.card', { hasText: 'Recent Test Results' });
		await expect(testsCard).toBeVisible();
	});

	test('displays pipeline stages overview', async ({ page }) => {
		await page.goto('/');

		const stagesCard = page.locator('.card', { hasText: 'Pipeline Stages' });
		await expect(stagesCard).toBeVisible();

		await expect(page.locator('.stage-item')).toHaveCount(3);
	});

	test('navigates to experiments page', async ({ page }) => {
		await page.goto('/');

		await page.click('a:has-text("View all experiments")');
		await expect(page).toHaveURL('/experiments');
	});

	test('navigates to tests page', async ({ page }) => {
		await page.goto('/');

		await page.click('a:has-text("View all test results")');
		await expect(page).toHaveURL('/tests');
	});
});
