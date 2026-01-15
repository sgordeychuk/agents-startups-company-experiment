<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { Card, Badge, TabGroup, LoadingSpinner, JsonBlock } from '$components/shared';
	import { formatDuration, formatCurrency } from '$utils/formatters';
	import type { Statistics, ExperimentContext } from '$types';

	let statistics = $state<Statistics | null>(null);
	let experimentData = $state<{ hasStatistics: boolean; context?: ExperimentContext } | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	const expId = $derived($page.params.id);

	onMount(async () => {
		try {
			const [statsRes, expRes] = await Promise.all([
				fetch(`/api/experiments/${expId}/statistics`),
				fetch(`/api/experiments/${expId}`)
			]);

			if (!statsRes.ok) throw new Error('Failed to load statistics');
			statistics = await statsRes.json();

			if (expRes.ok) {
				experimentData = await expRes.json();
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load statistics';
		} finally {
			loading = false;
		}
	});

	let context = $derived(experimentData?.context);
	let stageOutputs = $derived(context?.state?.stage_outputs);
	let hasIdea = $derived(!!stageOutputs?.idea_development);
	let hasPrototype = $derived(!!stageOutputs?.prototyping);
	let hasPitch = $derived(!!stageOutputs?.pitch);

	const tabs = $derived([
		{ id: 'overview', label: 'Overview', href: `/experiments/${expId}` },
		...(hasIdea ? [{ id: 'idea', label: 'Idea Development', href: `/experiments/${expId}/idea` }] : []),
		...(hasPrototype ? [{ id: 'prototype', label: 'Prototyping', href: `/experiments/${expId}/prototype` }] : []),
		...(hasPitch ? [{ id: 'pitch', label: 'Pitch', href: `/experiments/${expId}/pitch` }] : []),
		{ id: 'stats', label: 'Statistics' }
	]);

	function formatNumber(num: number): string {
		return num.toLocaleString();
	}

	function formatPercent(num: number): string {
		return num.toFixed(1) + '%';
	}

	function getStageIcon(stage: string): string {
		const icons: Record<string, string> = {
			idea_development: '💡',
			prototyping: '🏗️',
			pitch: '🎯'
		};
		return icons[stage] || '📊';
	}

	function getStageName(stage: string): string {
		const names: Record<string, string> = {
			idea_development: 'Idea Development',
			prototyping: 'Prototyping',
			pitch: 'Pitch'
		};
		return names[stage] || stage;
	}
</script>

<svelte:head>
	<title>Statistics | {expId}</title>
</svelte:head>

<div class="stats-page">
	<div class="page-header">
		<h1>Statistics</h1>
		<p class="subtitle">{expId}</p>
	</div>

	{#if loading}
		<LoadingSpinner message="Loading statistics..." />
	{:else if error}
		<Card>
			<p class="error-message">{error}</p>
		</Card>
	{:else if statistics}
		<TabGroup {tabs} activeTab="stats" />

		<div class="stats-grid">
			<Card title="Cost Overview">
				<div class="cost-dashboard">
					<div class="cost-main">
						<span class="cost-label">Total Cost</span>
						<span class="cost-value">{formatCurrency(statistics.total_cost)}</span>
					</div>
					<div class="budget-bar">
						<div class="budget-label">
							<span>Budget Used</span>
							<span>{formatPercent(statistics.budget_used_percent)} of {formatCurrency(statistics.max_budget)}</span>
						</div>
						<div class="progress-bar">
							<div
								class="progress-fill"
								class:warning={statistics.budget_used_percent > 70}
								class:danger={statistics.budget_used_percent > 90}
								style="width: {Math.min(statistics.budget_used_percent, 100)}%"
							></div>
						</div>
					</div>
				</div>
			</Card>

			<Card title="Token Usage">
				<div class="token-stats">
					<div class="token-item">
						<span class="token-label">Total Tokens</span>
						<span class="token-value">{formatNumber(statistics.total_tokens)}</span>
					</div>
					<div class="token-breakdown">
						<div class="token-type">
							<span class="type-label">Prompt</span>
							<span class="type-value">{formatNumber(statistics.total_prompt_tokens)}</span>
						</div>
						<div class="token-type">
							<span class="type-label">Completion</span>
							<span class="type-value">{formatNumber(statistics.total_completion_tokens)}</span>
						</div>
					</div>
				</div>
			</Card>

			<Card title="Execution Time">
				<div class="time-stats">
					<div class="time-main">
						<span class="time-label">Total Time</span>
						<span class="time-value">{formatDuration(statistics.total_execution_time_ms)}</span>
					</div>
					<div class="time-detail">
						<span class="detail-label">API Calls</span>
						<span class="detail-value">{statistics.total_calls}</span>
					</div>
				</div>
			</Card>
		</div>

		<Card title="Stage Breakdown">
			<div class="stages-table">
				<div class="table-header">
					<span>Stage</span>
					<span>Cost</span>
					<span>Tokens</span>
					<span>Time</span>
					<span>Calls</span>
				</div>
				{#each Object.entries(statistics.stages) as [stageName, stageStats]}
					<div class="table-row">
						<span class="stage-name">
							<span class="stage-icon">{getStageIcon(stageName)}</span>
							{getStageName(stageName)}
						</span>
						<span class="stage-cost">{formatCurrency(stageStats.total_cost)}</span>
						<span>{formatNumber(stageStats.total_tokens)}</span>
						<span>{formatDuration(stageStats.execution_time_ms)}</span>
						<span>{stageStats.total_calls}</span>
					</div>
				{/each}
			</div>
		</Card>

		<Card title="Agent Breakdown">
			<div class="agents-grid">
				{#each Object.entries(statistics.agents) as [agentName, agentStats]}
					<div class="agent-card">
						<div class="agent-header">
							<h4>{agentName}</h4>
							<Badge variant="neutral">{agentStats.call_count} calls</Badge>
						</div>
						<div class="agent-metrics">
							<div class="metric">
								<span class="metric-label">Cost</span>
								<span class="metric-value">{formatCurrency(agentStats.cost)}</span>
							</div>
							<div class="metric">
								<span class="metric-label">Tokens</span>
								<span class="metric-value">{formatNumber(agentStats.total_tokens)}</span>
							</div>
							<div class="metric">
								<span class="metric-label">Time</span>
								<span class="metric-value">{formatDuration(agentStats.execution_time_ms)}</span>
							</div>
						</div>
						<div class="token-split">
							<div class="split-item">
								<span>Prompt:</span>
								<span>{formatNumber(agentStats.prompt_tokens)}</span>
							</div>
							<div class="split-item">
								<span>Completion:</span>
								<span>{formatNumber(agentStats.completion_tokens)}</span>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</Card>

		<Card title="Raw Statistics" collapsible expanded={false}>
			<JsonBlock data={statistics} maxHeight="600px" />
		</Card>
	{:else}
		<Card>
			<p class="empty-message">No statistics available for this experiment</p>
		</Card>
	{/if}
</div>

<style>
	.stats-page {
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

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: var(--space-lg);
		margin-bottom: var(--space-lg);
	}

	.cost-dashboard {
		display: flex;
		flex-direction: column;
		gap: var(--space-lg);
	}

	.cost-main {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-xs);
	}

	.cost-label {
		font-size: 0.9em;
		color: var(--text-muted);
	}

	.cost-value {
		font-size: 2.5em;
		font-weight: 700;
		color: var(--primary-dark);
	}

	.budget-bar {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.budget-label {
		display: flex;
		justify-content: space-between;
		font-size: 0.85em;
		color: var(--text-muted);
	}

	.progress-bar {
		height: 12px;
		background: var(--card-bg-secondary);
		border-radius: 6px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: var(--success-text);
		border-radius: 6px;
		transition: width 0.3s ease;
	}

	.progress-fill.warning {
		background: var(--warning-text);
	}

	.progress-fill.danger {
		background: var(--error-text);
	}

	.token-stats {
		display: flex;
		flex-direction: column;
		gap: var(--space-lg);
	}

	.token-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-xs);
	}

	.token-label {
		font-size: 0.9em;
		color: var(--text-muted);
	}

	.token-value {
		font-size: 2em;
		font-weight: 700;
		color: var(--primary-dark);
	}

	.token-breakdown {
		display: flex;
		justify-content: space-around;
		padding-top: var(--space-md);
		border-top: 1px solid var(--card-border);
	}

	.token-type {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-xs);
	}

	.type-label {
		font-size: 0.8em;
		color: var(--text-muted);
	}

	.type-value {
		font-weight: 600;
		color: #444;
	}

	.time-stats {
		display: flex;
		flex-direction: column;
		gap: var(--space-lg);
	}

	.time-main {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-xs);
	}

	.time-label {
		font-size: 0.9em;
		color: var(--text-muted);
	}

	.time-value {
		font-size: 2em;
		font-weight: 700;
		color: var(--primary-dark);
	}

	.time-detail {
		display: flex;
		justify-content: center;
		gap: var(--space-sm);
		padding-top: var(--space-md);
		border-top: 1px solid var(--card-border);
	}

	.detail-label {
		color: var(--text-muted);
	}

	.detail-value {
		font-weight: 600;
	}

	.stages-table {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.table-header,
	.table-row {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr 1fr 0.5fr;
		gap: var(--space-md);
		padding: var(--space-md);
		align-items: center;
	}

	.table-header {
		font-weight: 600;
		color: var(--text-muted);
		font-size: 0.85em;
		border-bottom: 2px solid var(--card-border);
	}

	.table-row {
		background: var(--card-bg-secondary);
		border-radius: 8px;
	}

	.stage-name {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		font-weight: 500;
	}

	.stage-icon {
		font-size: 1.2em;
	}

	.stage-cost {
		font-weight: 600;
		color: var(--primary-dark);
	}

	.agents-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: var(--space-lg);
	}

	.agent-card {
		padding: var(--space-lg);
		background: var(--card-bg-secondary);
		border-radius: 8px;
		border-left: 4px solid var(--primary-light);
	}

	.agent-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-md);
	}

	.agent-header h4 {
		margin: 0;
		color: var(--primary-dark);
	}

	.agent-metrics {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-md);
		margin-bottom: var(--space-md);
		padding-bottom: var(--space-md);
		border-bottom: 1px solid var(--card-border);
	}

	.metric {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
	}

	.metric-label {
		font-size: 0.75em;
		color: var(--text-muted);
		text-transform: uppercase;
	}

	.metric-value {
		font-weight: 600;
		font-size: 0.95em;
	}

	.token-split {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
		font-size: 0.85em;
	}

	.split-item {
		display: flex;
		justify-content: space-between;
		color: var(--text-muted);
	}

	@media (max-width: 768px) {
		.stats-grid {
			grid-template-columns: 1fr;
		}

		.table-header,
		.table-row {
			grid-template-columns: 1fr 1fr;
			gap: var(--space-sm);
		}

		.table-header span:nth-child(n + 4),
		.table-row span:nth-child(n + 4) {
			display: none;
		}

		.agents-grid {
			grid-template-columns: 1fr;
		}

		.agent-metrics {
			grid-template-columns: 1fr;
		}
	}
</style>
