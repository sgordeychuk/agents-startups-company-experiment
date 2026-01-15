<script lang="ts">
	import { Card, TruncatedText } from '$components/shared';

	interface Props {
		risks: string[];
		opportunities: string[];
	}

	let { risks, opportunities }: Props = $props();
</script>

<div class="risk-opp-grid">
	<Card title="Risks" accent="error">
		<div class="list risks">
			{#each risks as risk, i}
				<div class="list-item">
					<span class="number">{i + 1}</span>
					<p><TruncatedText text={risk} maxLength={200} /></p>
				</div>
			{/each}
		</div>
	</Card>

	<Card title="Opportunities" accent="success">
		<div class="list opportunities">
			{#each opportunities as opportunity, i}
				<div class="list-item">
					<span class="number">{i + 1}</span>
					<p><TruncatedText text={opportunity} maxLength={200} /></p>
				</div>
			{/each}
		</div>
	</Card>
</div>

<style>
	.risk-opp-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
		gap: var(--space-lg);
	}

	.list {
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
	}

	.list-item {
		display: flex;
		gap: var(--space-md);
		padding: var(--space-md);
		background: var(--card-bg-secondary);
		border-radius: 8px;
	}

	.number {
		flex-shrink: 0;
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		font-weight: 600;
		font-size: 0.85em;
	}

	.risks .number {
		background: var(--error-bg);
		color: var(--error-text);
	}

	.opportunities .number {
		background: var(--success-bg);
		color: var(--success-text);
	}

	.list-item p {
		margin: 0;
		line-height: 1.6;
		flex: 1;
		color: var(--text-secondary);
	}

	@media (max-width: 768px) {
		.risk-opp-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
