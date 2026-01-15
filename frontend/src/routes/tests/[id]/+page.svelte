<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { Card, Badge, LoadingSpinner, JsonBlock, ExpandableSection } from '$components/shared';
	import { formatDuration, formatDate, formatStageName } from '$utils/formatters';
	import type { TestResult } from '$types';

	let testResult = $state<TestResult | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	const testId = $derived($page.params.id);

	onMount(async () => {
		try {
			const res = await fetch(`/api/tests/${testId}`);
			if (!res.ok) throw new Error('Failed to load test result');
			testResult = await res.json();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load test result';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>{testId} | Test Results</title>
</svelte:head>

<div class="test-detail-page">
	<div class="page-header">
		<h1>{testResult?.stage_name || testResult?.test_name || testId}</h1>
		{#if testResult}
			<Badge variant={testResult.success ? 'success' : 'error'}>
				{testResult.success ? 'Passed' : 'Failed'}
			</Badge>
		{/if}
	</div>

	{#if loading}
		<LoadingSpinner message="Loading test result..." />
	{:else if error}
		<Card>
			<p class="error-message">{error}</p>
		</Card>
	{:else if testResult}
		<div class="content-grid">
			<Card title="Test Overview">
				<div class="overview-grid">
					{#if testResult.stage_name}
						<div class="overview-item">
							<span class="label">Stage</span>
							<span class="value">{formatStageName(testResult.stage_name)}</span>
						</div>
					{/if}
					{#if testResult.agent_name}
						<div class="overview-item">
							<span class="label">Agent</span>
							<span class="value">{testResult.agent_name}</span>
						</div>
					{/if}
					{#if testResult.test_type}
						<div class="overview-item">
							<span class="label">Test Type</span>
							<span class="value">{testResult.test_type}</span>
						</div>
					{/if}
					{#if testResult.execution_time_ms}
						<div class="overview-item">
							<span class="label">Execution Time</span>
							<span class="value">{formatDuration(testResult.execution_time_ms)}</span>
						</div>
					{/if}
					{#if testResult.timestamp || testResult.timestamp_start}
						<div class="overview-item">
							<span class="label">Started</span>
							<span class="value">{formatDate(testResult.timestamp || testResult.timestamp_start || '')}</span>
						</div>
					{/if}
					{#if testResult.timestamp_end}
						<div class="overview-item">
							<span class="label">Ended</span>
							<span class="value">{formatDate(testResult.timestamp_end)}</span>
						</div>
					{/if}
				</div>
			</Card>

			{#if testResult.input}
				<Card title="Input">
					<JsonBlock data={testResult.input} maxHeight="300px" />
				</Card>
			{/if}
		</div>

		{#if testResult.iterations && testResult.iterations.length > 0}
			<Card title="Iterations" class="iteration-details">
				{#each testResult.iterations as iteration}
					<ExpandableSection
						title="Iteration {iteration.iteration + 1}"
						count={iteration.agents?.length}
						expanded={iteration.iteration === 0}
					>
						<div class="agents-list">
							{#each iteration.agents || [] as agent}
								<div class="agent-execution">
									<div class="agent-header">
										<span class="agent-name">{agent.agent_name}</span>
										<span class="agent-method">{agent.method}</span>
										{#if agent.execution_time_ms}
											<span class="agent-time">{formatDuration(agent.execution_time_ms)}</span>
										{/if}
									</div>
									{#if agent.output}
										<div class="agent-output">
											<JsonBlock data={agent.output} maxHeight="400px" title="Output" />
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</ExpandableSection>
				{/each}
			</Card>
		{/if}

		{#if testResult.tools && testResult.tools.length > 0}
			<Card title="Agent Tools">
				<div class="tools-list">
					{#each testResult.tools as tool}
						<ExpandableSection title={tool.name}>
							<div class="tool-detail">
								<p class="tool-description">{tool.description}</p>
								{#if tool.parameters}
									<h4>Parameters</h4>
									<JsonBlock data={tool.parameters} maxHeight="300px" />
								{/if}
							</div>
						</ExpandableSection>
					{/each}
				</div>
				{#if testResult.tool_count}
					<p class="tool-count">Total tools: {testResult.tool_count}</p>
				{/if}
			</Card>
		{/if}

		{#if testResult.events && testResult.events.length > 0}
			<Card title="Events">
				<div class="events-list">
					{#each testResult.events as event}
						<div class="event-item" class:passed={event.passed} class:failed={event.passed === false}>
							<span class="event-type">{event.type}</span>
							{#if event.name}
								<span class="event-name">{event.name}</span>
							{/if}
							{#if event.passed !== undefined}
								<Badge variant={event.passed ? 'success' : 'error'} size="sm">
									{event.passed ? 'Passed' : 'Failed'}
								</Badge>
							{/if}
						</div>
					{/each}
				</div>
			</Card>
		{/if}

		{#if testResult.final_output}
			<Card title="Final Output" collapsible>
				<JsonBlock data={testResult.final_output} maxHeight="600px" />
			</Card>
		{/if}

		{#if testResult.error}
			<Card title="Error" accent="error">
				<div class="error-content">
					<pre>{testResult.error}</pre>
				</div>
			</Card>
		{/if}

		<Card title="Raw Test Result" collapsible expanded={false}>
			<JsonBlock data={testResult} maxHeight="600px" />
		</Card>
	{/if}
</div>

<style>
	.test-detail-page {
		max-width: 1200px;
		margin: 0 auto;
	}

	.page-header {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		margin-bottom: var(--space-xl);
		flex-wrap: wrap;
	}

	.page-header h1 {
		color: var(--text-on-gradient);
		text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
		word-break: break-all;
	}

	.content-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
		gap: var(--space-lg);
	}

	.overview-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: var(--space-md);
	}

	.overview-item {
		padding: var(--space-md);
		background: var(--card-bg-secondary);
		border-radius: 8px;
		border-left: 4px solid var(--primary-light);
	}

	.overview-item .label {
		display: block;
		font-size: 0.85em;
		color: var(--text-muted);
		margin-bottom: var(--space-xs);
	}

	.overview-item .value {
		display: block;
		font-weight: 600;
		color: var(--primary-dark);
	}

	.error-message {
		color: var(--error-text);
		text-align: center;
		padding: var(--space-xl);
	}

	.agents-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-lg);
	}

	.agent-execution {
		padding: var(--space-md);
		background: var(--card-bg-secondary);
		border-radius: 8px;
	}

	.agent-header {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		margin-bottom: var(--space-md);
		flex-wrap: wrap;
	}

	.agent-name {
		font-weight: 600;
		color: var(--primary-dark);
	}

	.agent-method {
		font-family: var(--font-mono);
		font-size: 0.9em;
		color: var(--primary-light);
		padding: var(--space-xs) var(--space-sm);
		background: white;
		border-radius: 4px;
	}

	.agent-time {
		font-size: 0.85em;
		color: var(--text-muted);
		margin-left: auto;
	}

	.agent-output {
		margin-top: var(--space-md);
	}

	.tools-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.tool-detail {
		padding: var(--space-md);
	}

	.tool-description {
		margin: 0 0 var(--space-md) 0;
		color: var(--text-muted);
	}

	.tool-detail h4 {
		margin: var(--space-md) 0 var(--space-sm) 0;
		color: var(--primary-dark);
	}

	.tool-count {
		margin: var(--space-lg) 0 0 0;
		font-size: 0.9em;
		color: var(--text-muted);
	}

	.events-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.event-item {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		padding: var(--space-md);
		background: var(--card-bg-secondary);
		border-radius: 6px;
		border-left: 4px solid var(--neutral-border);
	}

	.event-item.passed {
		border-left-color: var(--success-text);
	}

	.event-item.failed {
		border-left-color: var(--error-text);
	}

	.event-type {
		font-weight: 600;
		color: var(--primary-dark);
	}

	.event-name {
		color: var(--text-muted);
	}

	.error-content {
		background: var(--error-bg);
		padding: var(--space-lg);
		border-radius: 8px;
		overflow: auto;
	}

	.error-content pre {
		margin: 0;
		font-family: var(--font-mono);
		font-size: 0.9em;
		color: var(--error-text);
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	@media (max-width: 768px) {
		.content-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
