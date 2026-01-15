<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { Card, Badge, TabGroup, LoadingSpinner, JsonBlock, ExpandableSection } from '$components/shared';
	import type { ExperimentContext, PitchOutput, PitchSlide } from '$types';

	let context = $state<ExperimentContext | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let currentSlide = $state(0);

	const expId = $derived($page.params.id);

	onMount(async () => {
		try {
			const res = await fetch(`/api/experiments/${expId}`);
			if (!res.ok) throw new Error('Failed to load experiment');
			const data = await res.json();
			context = data.context || data.results?.full_context;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load experiment';
		} finally {
			loading = false;
		}
	});

	let pitchOutput = $derived(context?.state?.stage_outputs?.pitch as PitchOutput | undefined);
	let hasIdea = $derived(!!context?.state?.stage_outputs?.idea_development);
	let hasPrototype = $derived(!!context?.state?.stage_outputs?.prototyping);
	let slides = $derived(pitchOutput?.pitch_deck?.slides || []);

	const tabs = $derived([
		{ id: 'overview', label: 'Overview', href: `/experiments/${expId}` },
		...(hasIdea ? [{ id: 'idea', label: 'Idea Development', href: `/experiments/${expId}/idea` }] : []),
		...(hasPrototype ? [{ id: 'prototype', label: 'Prototyping', href: `/experiments/${expId}/prototype` }] : []),
		{ id: 'pitch', label: 'Pitch' }
	]);

	function nextSlide() {
		if (currentSlide < slides.length - 1) currentSlide++;
	}

	function prevSlide() {
		if (currentSlide > 0) currentSlide--;
	}

	function goToSlide(index: number) {
		currentSlide = index;
	}
</script>

<svelte:head>
	<title>Pitch | {expId}</title>
</svelte:head>

<div class="pitch-page">
	<div class="page-header">
		<h1>Pitch</h1>
		<p class="subtitle">{expId}</p>
	</div>

	{#if loading}
		<LoadingSpinner message="Loading pitch stage..." />
	{:else if error}
		<Card>
			<p class="error-message">{error}</p>
		</Card>
	{:else if pitchOutput}
		<TabGroup {tabs} activeTab="pitch" />

		{#if pitchOutput.pitch_deck}
			<Card>
				<div class="deck-header">
					<h2>{pitchOutput.pitch_deck.title}</h2>
					<p class="tagline">{pitchOutput.pitch_deck.tagline}</p>
				</div>

				{#if slides.length > 0}
					<div class="slide-viewer">
						<div class="slide-navigation">
							<button class="nav-btn" onclick={prevSlide} disabled={currentSlide === 0}>
								← Previous
							</button>
							<span class="slide-counter">
								Slide {currentSlide + 1} of {slides.length}
							</span>
							<button class="nav-btn" onclick={nextSlide} disabled={currentSlide === slides.length - 1}>
								Next →
							</button>
						</div>

						<div class="slide-content">
							{#if slides[currentSlide]}
								{@const slide = slides[currentSlide]}
								<div class="slide-card">
									<div class="slide-header">
										<span class="slide-number">Slide {slide.slide_number}</span>
										<h3>{slide.title}</h3>
										{#if slide.subtitle}
											<p class="slide-subtitle">{slide.subtitle}</p>
										{/if}
									</div>
									<div class="slide-body">
										<p class="slide-text">{slide.content}</p>
									</div>
									{#if slide.talking_points?.length > 0}
										<div class="talking-points">
											<h4>Talking Points</h4>
											<ul>
												{#each slide.talking_points as point}
													<li>{point}</li>
												{/each}
											</ul>
										</div>
									{/if}
									{#if slide.visual_suggestion}
										<div class="visual-note">
											<span class="visual-icon">🎨</span>
											<p>{slide.visual_suggestion}</p>
										</div>
									{/if}
								</div>
							{/if}
						</div>

						<div class="slide-indicators">
							{#each slides as slide, index}
								<button
									class="indicator"
									class:active={index === currentSlide}
									onclick={() => goToSlide(index)}
									title="Slide {slide.slide_number}: {slide.title}"
								>
									{slide.slide_number}
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</Card>

			<Card title="All Slides" collapsible expanded={false}>
				<div class="slides-list">
					{#each slides as slide}
						<ExpandableSection title="Slide {slide.slide_number}: {slide.title}">
							<div class="slide-detail">
								{#if slide.subtitle}
									<p class="detail-subtitle">{slide.subtitle}</p>
								{/if}
								<p class="detail-content">{slide.content}</p>
								{#if slide.talking_points?.length > 0}
									<div class="detail-points">
										<h5>Talking Points</h5>
										<ul>
											{#each slide.talking_points as point}
												<li>{point}</li>
											{/each}
										</ul>
									</div>
								{/if}
							</div>
						</ExpandableSection>
					{/each}
				</div>
			</Card>
		{/if}

		{#if pitchOutput.marketing_strategies?.length > 0}
			<Card title="Marketing Strategies">
				<div class="strategies-grid">
					{#each pitchOutput.marketing_strategies as strategy}
						<div class="strategy-card">
							<h4>{strategy.channel}</h4>
							<div class="strategy-details">
								<div class="detail-row">
									<span class="detail-label">Target Audience</span>
									<p>{strategy.target_audience}</p>
								</div>
								<div class="detail-row">
									<span class="detail-label">Approach</span>
									<p>{strategy.approach}</p>
								</div>
								<div class="detail-row">
									<span class="detail-label">Budget</span>
									<p>{strategy.budget_considerations}</p>
								</div>
								<div class="detail-row">
									<span class="detail-label">Success Metrics</span>
									<p>{strategy.success_metrics}</p>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</Card>
		{/if}

		<Card title="Raw Stage Output" collapsible expanded={false}>
			<JsonBlock data={pitchOutput} maxHeight="600px" />
		</Card>
	{:else}
		<Card>
			<p class="empty-message">No pitch data found for this experiment</p>
		</Card>
	{/if}
</div>

<style>
	.pitch-page {
		max-width: 1200px;
		margin: 0 auto;
	}

	.page-header {
		margin-bottom: var(--space-xl);
	}

	.page-header h1 {
		color: var(--text-on-gradient);
		text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
		margin-bottom: var(--space-xs);
	}

	.subtitle {
		color: var(--text-on-gradient-secondary);
		margin: 0;
		word-break: break-all;
	}

	.error-message,
	.empty-message {
		color: var(--text-muted);
		text-align: center;
		padding: var(--space-xl);
	}

	.deck-header {
		text-align: center;
		padding-bottom: var(--space-xl);
		border-bottom: 1px solid var(--card-border);
		margin-bottom: var(--space-xl);
	}

	.deck-header h2 {
		margin: 0 0 var(--space-sm) 0;
		color: var(--primary-dark);
	}

	.tagline {
		font-size: 1.1em;
		color: var(--text-muted);
		margin: 0;
		font-style: italic;
	}

	.slide-viewer {
		display: flex;
		flex-direction: column;
		gap: var(--space-lg);
	}

	.slide-navigation {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.nav-btn {
		padding: var(--space-sm) var(--space-lg);
		background: var(--primary-light);
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
		transition: background 0.2s;
	}

	.nav-btn:hover:not(:disabled) {
		background: var(--primary-dark);
	}

	.nav-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.slide-counter {
		font-weight: 500;
		color: var(--text-muted);
	}

	.slide-card {
		background: var(--card-bg-secondary);
		border-radius: 12px;
		padding: var(--space-xl);
		min-height: 400px;
	}

	.slide-header {
		margin-bottom: var(--space-lg);
	}

	.slide-number {
		display: inline-block;
		padding: var(--space-xs) var(--space-sm);
		background: var(--primary-light);
		color: white;
		border-radius: 4px;
		font-size: 0.8em;
		font-weight: 600;
		margin-bottom: var(--space-sm);
	}

	.slide-header h3 {
		margin: var(--space-sm) 0 0 0;
		color: var(--primary-dark);
		font-size: 1.5em;
	}

	.slide-subtitle {
		margin: var(--space-sm) 0 0 0;
		color: var(--text-muted);
	}

	.slide-body {
		margin-bottom: var(--space-lg);
	}

	.slide-text {
		line-height: 1.8;
		margin: 0;
		white-space: pre-wrap;
	}

	.talking-points {
		padding: var(--space-md);
		background: var(--card-border);
		border-radius: 8px;
		margin-bottom: var(--space-md);
	}

	.talking-points h4 {
		margin: 0 0 var(--space-sm) 0;
		color: var(--primary-dark);
		font-size: 0.95em;
	}

	.talking-points ul {
		margin: 0;
		padding-left: var(--space-lg);
	}

	.talking-points li {
		margin-bottom: var(--space-xs);
	}

	.visual-note {
		display: flex;
		align-items: flex-start;
		gap: var(--space-sm);
		padding: var(--space-md);
		background: var(--warning-bg);
		border-radius: 8px;
		border-left: 4px solid var(--warning-text);
	}

	.visual-icon {
		font-size: 1.2em;
	}

	.visual-note p {
		margin: 0;
		font-size: 0.9em;
		color: var(--warning-text);
	}

	.slide-indicators {
		display: flex;
		justify-content: center;
		gap: var(--space-xs);
		flex-wrap: wrap;
	}

	.indicator {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		border: 2px solid var(--card-border);
		background: var(--card-border);
		cursor: pointer;
		font-weight: 600;
		font-size: 0.85em;
		transition: all 0.2s;
	}

	.indicator:hover {
		border-color: var(--primary-light);
		background: var(--card-bg-secondary);
	}

	.indicator.active {
		background: var(--primary-light);
		border-color: var(--primary-light);
		color: white;
	}

	.slides-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.slide-detail {
		padding: var(--space-md);
	}

	.detail-subtitle {
		color: var(--text-muted);
		font-style: italic;
		margin: 0 0 var(--space-md) 0;
	}

	.detail-content {
		margin: 0 0 var(--space-md) 0;
		line-height: 1.6;
		white-space: pre-wrap;
	}

	.detail-points h5 {
		margin: 0 0 var(--space-sm) 0;
		color: var(--primary-dark);
	}

	.detail-points ul {
		margin: 0;
		padding-left: var(--space-lg);
	}

	.strategies-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
		gap: var(--space-lg);
	}

	.strategy-card {
		padding: var(--space-lg);
		background: var(--card-bg-secondary);
		border-radius: 8px;
		border-left: 4px solid var(--primary-light);
	}

	.strategy-card h4 {
		margin: 0 0 var(--space-md) 0;
		color: var(--primary-dark);
	}

	.strategy-details {
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
	}

	.detail-row {
		border-bottom: 1px solid var(--card-border);
		padding-bottom: var(--space-sm);
	}

	.detail-row:last-child {
		border-bottom: none;
		padding-bottom: 0;
	}

	.detail-label {
		display: block;
		font-weight: 600;
		font-size: 0.85em;
		color: var(--text-muted);
		margin-bottom: var(--space-xs);
	}

	.detail-row p {
		margin: 0;
		line-height: 1.5;
	}

	@media (max-width: 768px) {
		.strategies-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
