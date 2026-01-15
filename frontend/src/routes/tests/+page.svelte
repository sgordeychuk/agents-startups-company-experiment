<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, Badge, LoadingSpinner } from '$components/shared';
	import { formatDuration, formatDate, formatStageName } from '$utils/formatters';
	import type { TestResult } from '$types';

	let testResults = $state<TestResult[]>([]);
	let loading = $state(true);
	let filterStage = $state('all');
	let filterStatus = $state('all');
	let searchQuery = $state('');

	onMount(async () => {
		try {
			const res = await fetch('/api/tests');
			testResults = await res.json();
		} catch (error) {
			console.error('Error loading test results:', error);
		} finally {
			loading = false;
		}
	});

	let filteredResults = $derived.by(() => {
		let result = testResults;

		if (filterStage !== 'all') {
			result = result.filter((t) => t.stage_name?.includes(filterStage) || t.test_name?.includes(filterStage));
		}

		if (filterStatus !== 'all') {
			const isSuccess = filterStatus === 'passed';
			result = result.filter((t) => t.success === isSuccess);
		}

		if (searchQuery) {
			const query = searchQuery.toLowerCase();
			result = result.filter(
				(t) =>
					t.id.toLowerCase().includes(query) ||
					t.stage_name?.toLowerCase().includes(query) ||
					t.agent_name?.toLowerCase().includes(query)
			);
		}

		return result;
	});

	let stageOptions = $derived.by(() => {
		const stages = new Set<string>();
		testResults.forEach((t) => {
			if (t.stage_name) {
				const stage = t.stage_name.replace('_stage', '');
				stages.add(stage);
			}
			if (t.test_name) {
				const name = t.test_name.replace('_tools', '');
				stages.add(name);
			}
		});
		return Array.from(stages).sort();
	});
</script>

<svelte:head>
	<title>Test Results | AI Innovators Results Viewer</title>
</svelte:head>

<div class="max-w-max mx-auto">
	<div class="mb-10">
		<h1 class="text-3xl font-bold text-surface-50 mb-1">Test Results</h1>
		<p class="text-surface-300">Stage execution tests and agent tool tests</p>
	</div>

	{#if loading}
		<LoadingSpinner message="Loading test results..." />
	{:else}
		<Card>
			<div class="flex flex-wrap gap-4 mb-6">
				<input
					type="text"
					placeholder="Search tests..."
					bind:value={searchQuery}
					class="search-input flex-1 min-w-[200px] px-4 py-2 bg-surface-700 border border-surface-600 rounded-lg text-surface-50 placeholder-surface-400 focus:outline-none focus:border-primary-500"
				/>
				<select bind:value={filterStage} data-testid="filter-stage" class="min-w-[150px] px-4 py-2 bg-surface-700 border border-surface-600 rounded-lg text-surface-50 focus:outline-none focus:border-primary-500">
					<option value="all">All Stages</option>
					{#each stageOptions as stage}
						<option value={stage}>{formatStageName(stage)}</option>
					{/each}
				</select>
				<select bind:value={filterStatus} data-testid="filter-status" class="min-w-[150px] px-4 py-2 bg-surface-700 border border-surface-600 rounded-lg text-surface-50 focus:outline-none focus:border-primary-500">
					<option value="all">All Status</option>
					<option value="passed">Passed</option>
					<option value="failed">Failed</option>
				</select>
			</div>

			<p class="results-count text-surface-300 text-sm mb-6">
				Showing {filteredResults.length} of {testResults.length} test results
			</p>

			{#if filteredResults.length === 0}
				<p class="text-center text-surface-300 py-10">No test results found matching your criteria</p>
			{:else}
				<div class="flex flex-col gap-3">
					{#each filteredResults as test}
						<a
							href="/tests/{test.id}"
							class="flex flex-col p-5 bg-surface-700/50 rounded-lg no-underline transition-all duration-200 border border-transparent hover:bg-surface-700 hover:border-primary-500 hover:-translate-y-0.5"
							data-testid="test-result-card"
						>
							<div class="flex justify-between items-center mb-2">
								<Badge variant={test.success ? 'success' : 'error'} size="sm">
									{test.success ? 'Passed' : 'Failed'}
								</Badge>
								{#if test.timestamp}
									<span class="text-xs text-surface-300">{formatDate(test.timestamp)}</span>
								{/if}
							</div>
							<h3 class="text-sm font-semibold text-surface-50 mb-3 break-all">{test.stage_name || test.test_name || test.id}</h3>
							<div class="flex gap-6 flex-wrap text-xs text-surface-300">
								{#if test.agent_name}
									<span class="flex items-center gap-1">
										<span>🤖</span>
										{test.agent_name}
									</span>
								{/if}
								{#if test.test_type}
									<span class="flex items-center gap-1">
										<span>🏷️</span>
										{test.test_type}
									</span>
								{/if}
								{#if test.execution_time_ms}
									<span class="flex items-center gap-1">
										<span>⏱️</span>
										{formatDuration(test.execution_time_ms)}
									</span>
								{/if}
							</div>
						</a>
					{/each}
				</div>
			{/if}
		</Card>
	{/if}
</div>
