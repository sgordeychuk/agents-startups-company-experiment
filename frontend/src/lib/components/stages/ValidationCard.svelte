<script lang="ts">
	import { Card, Badge, TruncatedText } from '$components/shared';
	import type { Validation } from '$types';
	import { getRecommendationClass } from '$utils/formatters';

	interface Props {
		validation: Validation;
	}

	let { validation }: Props = $props();

	let recommendationVariant = $derived.by(() => {
		switch (validation.recommendation?.toUpperCase()) {
			case 'GO':
				return 'success' as const;
			case 'PIVOT':
				return 'warning' as const;
			default:
				return 'error' as const;
		}
	});
</script>

<Card title="Market Validation">
	<div class="validation-header">
		<div class="recommendation-box">
			<span class="label">Recommendation</span>
			<Badge variant={recommendationVariant} size="lg">{validation.recommendation}</Badge>
		</div>
	</div>

	<div class="section">
		<h3>Market Analysis</h3>
		<div class="content-box">
			<p><TruncatedText text={validation.market_analysis} maxLength={400} /></p>
		</div>
	</div>

	<div class="section">
		<h3>Market Size</h3>
		<div class="market-size-grid">
			<div class="market-item">
				<span class="market-label">TAM</span>
				<span class="market-value">{validation.market_size.TAM}</span>
			</div>
			<div class="market-item">
				<span class="market-label">SAM</span>
				<span class="market-value">{validation.market_size.SAM}</span>
			</div>
			<div class="market-item">
				<span class="market-label">SOM</span>
				<span class="market-value">{validation.market_size.SOM}</span>
			</div>
		</div>
		{#if validation.market_size.sources}
			<p class="sources"><strong>Sources:</strong> {validation.market_size.sources}</p>
		{/if}
	</div>

	<div class="section">
		<h3>Reasoning</h3>
		<div class="content-box highlight">
			<p><TruncatedText text={validation.reasoning} maxLength={400} /></p>
		</div>
	</div>
</Card>

<style>
	.validation-header {
		display: flex;
		justify-content: flex-end;
		margin-bottom: var(--space-lg);
	}

	.recommendation-box {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-sm);
	}

	.recommendation-box .label {
		font-size: 0.85em;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.section {
		margin-bottom: var(--space-xl);
	}

	.section:last-child {
		margin-bottom: 0;
	}

	.section h3 {
		color: var(--primary-dark);
		margin: 0 0 var(--space-md) 0;
		padding-bottom: var(--space-sm);
		border-bottom: 2px solid var(--primary-light);
	}

	.content-box {
		background: var(--card-bg-secondary);
		padding: var(--space-lg);
		border-radius: 8px;
	}

	.content-box.highlight {
		border-left: 4px solid var(--primary-light);
	}

	.content-box p {
		margin: 0;
		line-height: 1.7;
		white-space: pre-wrap;
		word-wrap: break-word;
		color: var(--text-secondary);
	}

	.market-size-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-md);
		margin-bottom: var(--space-md);
	}

	.market-item {
		background: var(--card-bg-secondary);
		padding: var(--space-lg);
		border-radius: 8px;
		text-align: center;
	}

	.market-label {
		display: block;
		font-weight: 600;
		color: var(--primary-dark);
		margin-bottom: var(--space-sm);
		font-size: 1.1em;
	}

	.market-value {
		display: block;
		font-size: 0.9em;
		color: var(--text-muted);
		line-height: 1.5;
	}

	.sources {
		font-size: 0.85em;
		color: var(--text-muted);
		margin: var(--space-md) 0 0 0;
		line-height: 1.6;
	}

	@media (max-width: 768px) {
		.market-size-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
