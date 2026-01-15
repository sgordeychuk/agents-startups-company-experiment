<script lang="ts">
	import { Card, TruncatedText } from '$components/shared';
	import type { Idea } from '$types';

	interface Props {
		idea: Idea;
	}

	let { idea }: Props = $props();

	const sections = [
		{ key: 'problem', title: 'Problem', icon: '⚠️' },
		{ key: 'solution', title: 'Solution', icon: '💡' },
		{ key: 'target_market', title: 'Target Market', icon: '🎯' },
		{ key: 'value_proposition', title: 'Value Proposition', icon: '✨' },
		{ key: 'novelty', title: 'Novelty', icon: '🆕' },
		{ key: 'market_size_estimate', title: 'Market Size Estimate', icon: '📊' },
		{ key: 'competitive_advantage', title: 'Competitive Advantage', icon: '🏆' }
	] as const;
</script>

<Card title="Startup Idea">
	<div class="idea-grid">
		{#each sections as section}
			<div class="idea-section">
				<h3>
					<span class="icon">{section.icon}</span>
					{section.title}
				</h3>
				<div class="content">
					<p><TruncatedText text={idea[section.key]} maxLength={250} /></p>
				</div>
			</div>
		{/each}
	</div>
</Card>

<style>
	.idea-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
		gap: var(--space-lg);
	}

	.idea-section {
		background: var(--card-bg-secondary);
		border-radius: 8px;
		padding: var(--space-lg);
		border-left: 4px solid var(--primary-light);
	}

	.idea-section h3 {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		margin: 0 0 var(--space-md) 0;
		font-size: 1.1em;
		color: var(--primary-dark);
	}

	.icon {
		font-size: 1.2em;
	}

	.content p {
		margin: 0;
		line-height: 1.7;
		color: var(--text-secondary);
		white-space: pre-wrap;
		word-wrap: break-word;
	}
</style>
