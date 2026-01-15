<script lang="ts">
	import { Card, ExpandableSection, TruncatedText } from '$components/shared';
	import type { Competitor } from '$types';

	interface Props {
		competitors: Competitor[];
	}

	let { competitors }: Props = $props();
</script>

<Card title="Competitor Analysis" subtitle="{competitors.length} competitors identified">
	<div class="table-wrapper">
		<table>
			<thead>
				<tr>
					<th>Competitor</th>
					<th>Description</th>
					<th>Strengths</th>
					<th>Weaknesses</th>
				</tr>
			</thead>
			<tbody>
				{#each competitors as competitor}
					<tr>
						<td class="name-cell">
							<strong>{competitor.name}</strong>
						</td>
						<td class="desc-cell"><TruncatedText text={competitor.description} maxLength={150} /></td>
						<td class="strengths-cell"><TruncatedText text={competitor.strengths} maxLength={150} /></td>
						<td class="weaknesses-cell"><TruncatedText text={competitor.weaknesses} maxLength={150} /></td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<div class="mobile-cards">
		{#each competitors as competitor, i}
			<ExpandableSection title={competitor.name} expanded={i === 0}>
				<div class="competitor-detail">
					<div class="detail-section">
						<h4>Description</h4>
						<p><TruncatedText text={competitor.description} maxLength={200} /></p>
					</div>
					<div class="detail-section strengths">
						<h4>Strengths</h4>
						<p><TruncatedText text={competitor.strengths} maxLength={200} /></p>
					</div>
					<div class="detail-section weaknesses">
						<h4>Weaknesses</h4>
						<p><TruncatedText text={competitor.weaknesses} maxLength={200} /></p>
					</div>
				</div>
			</ExpandableSection>
		{/each}
	</div>
</Card>

<style>
	.table-wrapper {
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		min-width: 800px;
	}

	th,
	td {
		padding: var(--space-md);
		text-align: left;
		border-bottom: 1px solid var(--card-border);
		vertical-align: top;
		color: var(--text-secondary);
	}

	th {
		background: var(--card-bg-secondary);
		font-weight: 600;
		color: var(--primary-dark);
		white-space: nowrap;
	}

	.name-cell {
		white-space: nowrap;
		min-width: 120px;
	}

	.desc-cell {
		min-width: 200px;
	}

	.strengths-cell {
		color: var(--success-text);
		min-width: 200px;
	}

	.weaknesses-cell {
		color: var(--error-text);
		min-width: 200px;
	}

	.mobile-cards {
		display: none;
	}

	.competitor-detail {
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
	}

	.detail-section h4 {
		margin: 0 0 var(--space-xs) 0;
		font-size: 0.9em;
		color: var(--text-muted);
	}

	.detail-section p {
		margin: 0;
		line-height: 1.6;
		color: var(--text-secondary);
	}

	.detail-section.strengths p {
		color: var(--success-text);
	}

	.detail-section.weaknesses p {
		color: var(--error-text);
	}

	@media (max-width: 900px) {
		.table-wrapper {
			display: none;
		}

		.mobile-cards {
			display: block;
		}
	}
</style>
