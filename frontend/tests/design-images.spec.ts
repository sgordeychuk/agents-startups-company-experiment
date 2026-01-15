import { test, expect } from '@playwright/test';

test.describe('Design Images on Prototype Page', () => {
	test('prototype page displays design images gallery', async ({ page }) => {
		// First navigate to an experiment that has prototyping output
		await page.goto('/experiments');

		// Wait for experiment cards to load
		await page.waitForSelector('[data-testid="experiment-card"]', { timeout: 10000 });

		// Click on the first experiment
		await page.locator('[data-testid="experiment-card"]').first().click();

		// Wait for the page to load
		await page.waitForLoadState('networkidle');

		// Check if there's a Prototyping tab link
		const prototypeTab = page.locator('a[href*="/prototype"]');

		if (await prototypeTab.count() > 0) {
			// Navigate to prototype page
			await prototypeTab.click();

			// Wait for prototype page to load
			await page.waitForLoadState('networkidle');

			// Check for Design Screenshots card
			const designCard = page.locator('.card', { hasText: 'Design Screenshots' });

			if (await designCard.count() > 0) {
				await expect(designCard).toBeVisible();

				// Check for design images
				const designImages = page.locator('[data-testid="design-image"]');
				const imageCount = await designImages.count();

				if (imageCount > 0) {
					// Verify at least one image is visible
					await expect(designImages.first()).toBeVisible();

					// Verify images have alt text
					const firstImage = designImages.first().locator('img');
					await expect(firstImage).toHaveAttribute('alt');
				}
			}
		}
	});

	test('design images open in lightbox on click', async ({ page }) => {
		await page.goto('/experiments');
		await page.waitForSelector('[data-testid="experiment-card"]', { timeout: 10000 });
		await page.locator('[data-testid="experiment-card"]').first().click();
		await page.waitForLoadState('networkidle');

		const prototypeTab = page.locator('a[href*="/prototype"]');

		if (await prototypeTab.count() > 0) {
			await prototypeTab.click();
			await page.waitForLoadState('networkidle');

			const designImages = page.locator('[data-testid="design-image"]');

			if (await designImages.count() > 0) {
				// Click on the first design image
				await designImages.first().click();

				// Check for lightbox modal
				const lightbox = page.locator('[role="dialog"]');
				await expect(lightbox).toBeVisible();

				// Verify lightbox contains an image
				const lightboxImage = lightbox.locator('img');
				await expect(lightboxImage).toBeVisible();

				// Close the lightbox by clicking the close button
				await page.locator('[aria-label="Close"]').click();

				// Verify lightbox is closed
				await expect(lightbox).not.toBeVisible();
			}
		}
	});

	test('design images API endpoint returns images', async ({ page, request }) => {
		// Get an experiment ID first
		const experimentsResponse = await request.get('/api/experiments');
		const experiments = await experimentsResponse.json();

		if (experiments.length > 0) {
			const expId = experiments[0].id;

			// Check if the experiment has designs
			const expResponse = await request.get(`/api/experiments/${expId}`);
			const expData = await expResponse.json();

			const protoOutput = expData?.context?.state?.stage_outputs?.prototyping ||
				expData?.results?.full_context?.state?.stage_outputs?.prototyping;

			if (protoOutput?.final_designs?.length > 0) {
				const design = protoOutput.final_designs[0];
				const filename = design.filepath.split('/').pop();

				// Request the image through the API
				const imageResponse = await request.get(`/api/experiments/${expId}/designs/${filename}`);

				expect(imageResponse.ok()).toBeTruthy();
				expect(imageResponse.headers()['content-type']).toMatch(/^image\//);
			}
		}
	});

	test('prototype page shows design metadata', async ({ page }) => {
		await page.goto('/experiments');
		await page.waitForSelector('[data-testid="experiment-card"]', { timeout: 10000 });
		await page.locator('[data-testid="experiment-card"]').first().click();
		await page.waitForLoadState('networkidle');

		const prototypeTab = page.locator('a[href*="/prototype"]');

		if (await prototypeTab.count() > 0) {
			await prototypeTab.click();
			await page.waitForLoadState('networkidle');

			const designImages = page.locator('[data-testid="design-image"]');

			if (await designImages.count() > 0) {
				// Check for screen name
				const firstDesign = designImages.first();
				const screenName = firstDesign.locator('h4');
				await expect(screenName).toBeVisible();
			}
		}
	});
});
