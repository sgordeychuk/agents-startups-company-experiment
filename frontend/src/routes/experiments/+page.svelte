<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, Badge, LoadingSpinner } from '$components/shared';
	import { formatTimestamp } from '$utils/formatters';
	import type { Experiment } from '$types';

	let experiments = $state<Experiment[]>([]);
	let loading = $state(true);
	let filterType = $state<'all' | 'full' | 'stage_run'>('all');
	let searchQuery = $state('');

	onMount(async () => {
		try {
			const res = await fetch('/api/experiments');
			experiments = await res.json();
		} catch (error) {
			console.error('Error loading experiments:', error);
		} finally {
			loading = false;
		}
	});

	let filteredExperiments = $derived.by(() => {
		let result = experiments;

		if (filterType !== 'all') {
			result = result.filter((e) => e.type === filterType);
		}

		if (searchQuery) {
			const query = searchQuery.toLowerCase();
			result = result.filter((e) => e.id.toLowerCase().includes(query));
		}

		result = [...result].sort((a, b) => {
			const tsA = getExperimentTimestamp(a.id);
			const tsB = getExperimentTimestamp(b.id);
			return tsB.localeCompare(tsA);
		});

		return result;
	});

	function getExperimentTimestamp(id: string): string {
		if (id.startsWith('experiment_')) {
			return id.replace('experiment_', '');
		}
		if (id.startsWith('stage_run_')) {
			const parts = id.split('_');
			return parts.slice(-2).join('_');
		}
		const match = id.match(/_(\d{8}_\d{6})$/);
		if (match) return match[1];
		return '';
	}
</script>

<svelte:head>
	<title>Experiments | AI Innovators Results Viewer</title>
</svelte:head>

<div class="max-w-max mx-auto">
	<div class="mb-10">
		<h1 class="text-3xl font-bold text-surface-50 mb-1">Experiments</h1>
		<p class="text-surface-300">Browse all pipeline executions and stage runs</p>
	</div>

	{#if loading}
		<LoadingSpinner message="Loading experiments..." />
	{:else}
		<Card>
			<div class="flex flex-wrap gap-4 mb-6">
				<input
					type="text"
					placeholder="Search experiments..."
					bind:value={searchQuery}
					class="search-input flex-1 min-w-[200px] px-4 py-2 bg-surface-700 border border-surface-600 rounded-lg text-surface-50 placeholder-surface-400 focus:outline-none focus:border-primary-500"
				/>
				<select
					bind:value={filterType}
					data-testid="filter-type"
					class="min-w-[150px] px-4 py-2 bg-surface-700 border border-surface-600 rounded-lg text-surface-50 focus:outline-none focus:border-primary-500"
				>
					<option value="all">All Types</option>
					<option value="full">Full Pipelines</option>
					<option value="stage_run">Stage Runs</option>
				</select>
			</div>

			<p class="text-surface-300 text-sm mb-6">
				Showing {filteredExperiments.length} of {experiments.length} experiments
			</p>

			{#if filteredExperiments.length === 0}
				<p class="text-center text-surface-300 py-10">No experiments found matching your criteria</p>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{#each filteredExperiments as exp}
						<a
							href="/experiments/{exp.id}"
							class="experiment-card flex flex-col p-5 bg-surface-700/50 rounded-lg no-underline transition-all duration-200 border border-transparent hover:bg-surface-700 hover:border-primary-500 hover:-translate-y-0.5"
							data-testid="experiment-card"
						>
							<div class="flex justify-between items-center mb-3">
								<Badge variant={exp.type === 'full' ? 'primary' : 'neutral'} size="sm">
									{exp.type === 'full' ? 'Full Pipeline' : 'Stage Run'}
								</Badge>
								<span class="text-xs text-surface-300">{formatTimestamp(getExperimentTimestamp(exp.id))}</span>
							</div>
							<h3 class="experiment-name text-sm font-semibold text-surface-50 mb-3 break-all">{exp.id}</h3>
							<div class="flex gap-4 mb-3 text-xs text-surface-300">
								<span>📁 {exp.contextFiles.length} files</span>
								{#if exp.hasStatistics}
									<span>📊 Statistics</span>
								{/if}
							</div>
							<div class="mt-auto">
								{#if exp.hasCompleteContext}
									<Badge variant="success" size="sm">Complete</Badge>
								{:else if exp.hasResults}
									<Badge variant="warning" size="sm">Has Results</Badge>
								{:else}
									<Badge variant="neutral" size="sm">Partial</Badge>
								{/if}
							</div>
						</a>
					{/each}
				</div>
			{/if}
		</Card>
	{/if}
</div>
