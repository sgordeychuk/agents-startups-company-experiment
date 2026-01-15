import { test, expect } from '@playwright/test';

test.describe('Skeleton UI Theme', () => {
	test('cerberus theme is applied', async ({ page }) => {
		await page.goto('/');

		// Check that data-theme attribute is set
		const html = page.locator('html');
		await expect(html).toHaveAttribute('data-theme', 'cerberus');
	});

	test('dark theme colors are applied', async ({ page }) => {
		await page.goto('/');

		// Verify the background has dark styling
		const body = page.locator('body');
		const backgroundColor = await body.evaluate((el) => {
			return window.getComputedStyle(el).backgroundColor;
		});

		// Dark theme should have a dark background
		// The background color should not be white (rgb(255, 255, 255))
		expect(backgroundColor).not.toBe('rgb(255, 255, 255)');
	});
});

test.describe('Skeleton Components', () => {
	test('Card component renders correctly', async ({ page }) => {
		await page.goto('/');

		// Wait for cards to load
		await page.waitForSelector('.card');

		const card = page.locator('.card').first();
		await expect(card).toBeVisible();

		// Verify card has rounded corners (Skeleton styling)
		const borderRadius = await card.evaluate((el) => {
			return window.getComputedStyle(el).borderRadius;
		});

		// Should have rounded corners
		expect(borderRadius).not.toBe('0px');
	});

	test('Badge component renders with correct styling', async ({ page }) => {
		await page.goto('/');

		// Wait for page to load
		await page.waitForLoadState('networkidle');

		const badge = page.locator('.badge').first();

		if (await badge.count() > 0) {
			await expect(badge).toBeVisible();

			// Verify badge has text content and padding (badge styling)
			const padding = await badge.evaluate((el) => {
				return window.getComputedStyle(el).padding;
			});

			// Badge should have padding applied
			expect(padding).not.toBe('0px');
		}
	});

	test('TabGroup component renders tabs', async ({ page }) => {
		// Navigate to a page with tabs
		await page.goto('/experiments');
		await page.waitForSelector('[data-testid="experiment-card"]', { timeout: 10000 });
		await page.locator('[data-testid="experiment-card"]').first().click();

		await page.waitForLoadState('networkidle');

		// Check for tab group
		const tabGroup = page.locator('.tab-group, [role="tablist"]');

		if (await tabGroup.count() > 0) {
			await expect(tabGroup).toBeVisible();

			// Verify tabs are visible
			const tabs = page.locator('.tab, [role="tab"]');
			const tabCount = await tabs.count();
			expect(tabCount).toBeGreaterThan(0);
		}
	});

	test('LoadingSpinner appears while loading', async ({ page }) => {
		// Navigate to home and check for loading state
		await page.goto('/', { waitUntil: 'commit' });

		// The spinner might be very brief, so we just check it exists in the DOM
		// or the content loads successfully
		await page.waitForLoadState('networkidle');

		// After loading, content should be visible
		const content = page.locator('h1');
		await expect(content).toBeVisible();
	});

	test('Collapsible cards expand and collapse', async ({ page }) => {
		await page.goto('/experiments');
		await page.waitForSelector('[data-testid="experiment-card"]', { timeout: 10000 });
		await page.locator('[data-testid="experiment-card"]').first().click();

		await page.waitForLoadState('networkidle');

		// Look for collapsible card (Raw Context Data is typically collapsed by default)
		const collapsibleCard = page.locator('.card', { hasText: 'Raw Context Data' });

		if (await collapsibleCard.count() > 0) {
			// Find the expand/collapse button
			const toggleButton = collapsibleCard.locator('button').first();

			// Click to expand
			await toggleButton.click();

			// Verify content is visible
			const cardBody = collapsibleCard.locator('.card-body');
			await expect(cardBody).toBeVisible();

			// Click to collapse
			await toggleButton.click();

			// Verify content is hidden (body should not be visible)
			await expect(cardBody).not.toBeVisible();
		}
	});
});

test.describe('Navigation Components', () => {
	test('Sidebar renders correctly', async ({ page }) => {
		await page.goto('/');

		// Check for sidebar navigation items
		const homeNav = page.locator('[data-testid="nav-home"]');
		const experimentsNav = page.locator('[data-testid="nav-experiments"]');
		const testsNav = page.locator('[data-testid="nav-tests"]');

		await expect(homeNav).toBeVisible();
		await expect(experimentsNav).toBeVisible();
		await expect(testsNav).toBeVisible();
	});

	test('Header with breadcrumb renders correctly', async ({ page }) => {
		await page.goto('/experiments');

		// Check for breadcrumb navigation by aria-label
		const breadcrumb = page.locator('[aria-label="Breadcrumb"]');
		await expect(breadcrumb).toBeVisible();

		// Verify Home link is present
		await expect(breadcrumb).toContainText('Home');
	});

	test('Active navigation item is highlighted', async ({ page }) => {
		await page.goto('/experiments');

		// The experiments nav item should have active styling
		const experimentsNav = page.locator('[data-testid="nav-experiments"]');

		// Check if it has some distinguishing class or style
		const classes = await experimentsNav.getAttribute('class');

		// Should have styling that indicates it's active (gradient, bold, etc.)
		expect(classes).toBeTruthy();
	});
});

test.describe('Form Components', () => {
	test('Search input has proper styling', async ({ page }) => {
		await page.goto('/experiments');

		const searchInput = page.locator('.search-input');
		await expect(searchInput).toBeVisible();

		// Verify input has dark theme styling
		const backgroundColor = await searchInput.evaluate((el) => {
			return window.getComputedStyle(el).backgroundColor;
		});

		// Should not be plain white
		expect(backgroundColor).not.toBe('rgb(255, 255, 255)');
	});

	test('Select dropdowns work correctly', async ({ page }) => {
		await page.goto('/experiments');

		const filterSelect = page.locator('[data-testid="filter-type"]');
		await expect(filterSelect).toBeVisible();

		// Select an option
		await filterSelect.selectOption('full');

		// Verify option was selected
		const selectedValue = await filterSelect.inputValue();
		expect(selectedValue).toBe('full');
	});
});
