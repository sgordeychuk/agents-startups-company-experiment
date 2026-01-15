<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, Badge, LoadingSpinner } from '$components/shared';
	import { formatExperimentName, formatDuration } from '$utils/formatters';
	import type { Experiment, TestResult } from '$types';

	let experiments = $state<Experiment[]>([]);
	let testResults = $state<TestResult[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const [expRes, testRes] = await Promise.all([
				fetch('/api/experiments'),
				fetch('/api/tests')
			]);

			experiments = await expRes.json();
			testResults = await testRes.json();
		} catch (error) {
			console.error('Error loading data:', error);
		} finally {
			loading = false;
		}
	});

	let recentExperiments = $derived(experiments.slice(0, 5));
	let recentTests = $derived(testResults.slice(0, 5));
	let fullExperiments = $derived(experiments.filter((e) => e.type === 'full'));
	let stageRuns = $derived(experiments.filter((e) => e.type === 'stage_run'));
	let successfulTests = $derived(testResults.filter((t) => t.success));
</script>

<svelte:head>
	<title>Dashboard | AI Innovators Results Viewer</title>
</svelte:head>

<div class="max-w-svw mx-auto">
	<div class="mb-10">
		<h1 class="text-3xl font-bold text-surface-50 mb-1">Dashboard</h1>
		<p class="subtitle text-surface-300">AI Innovators Multi-Agent System Results</p>
	</div>

	{#if loading}
		<LoadingSpinner message="Loading dashboard..." />
	{:else}
		<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-10">
			<div class="stat-card bg-surface-800 rounded-xl p-5 text-center shadow-lg" data-testid="stat-card">
				<span class="block text-4xl font-bold text-primary-400">{experiments.length}</span>
				<span class="stat-label block text-surface-300 text-sm mt-1">Total Experiments</span>
			</div>
			<div class="stat-card bg-surface-800 rounded-xl p-5 text-center shadow-lg" data-testid="stat-card">
				<span class="block text-4xl font-bold text-primary-400">{fullExperiments.length}</span>
				<span class="stat-label block text-surface-300 text-sm mt-1">Full Pipelines</span>
			</div>
			<div class="stat-card bg-surface-800 rounded-xl p-5 text-center shadow-lg" data-testid="stat-card">
				<span class="block text-4xl font-bold text-primary-400">{stageRuns.length}</span>
				<span class="stat-label block text-surface-300 text-sm mt-1">Stage Runs</span>
			</div>
			<div class="stat-card bg-surface-800 rounded-xl p-5 text-center shadow-lg" data-testid="stat-card">
				<span class="block text-4xl font-bold text-primary-400">{testResults.length}</span>
				<span class="stat-label block text-surface-300 text-sm mt-1">Test Results</span>
			</div>
			<div class="stat-card bg-surface-800 rounded-xl p-5 text-center shadow-lg" data-testid="stat-card">
				<span class="block text-4xl font-bold text-success-400">{successfulTests.length}</span>
				<span class="stat-label block text-surface-300 text-sm mt-1">Passed Tests</span>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
			<Card title="Recent Experiments">
				{#if recentExperiments.length === 0}
					<p class="text-surface-300 text-center py-6">No experiments found</p>
				{:else}
					<div class="flex flex-col gap-2">
						{#each recentExperiments as exp}
							<a href="/experiments/{exp.id}" class="flex justify-between items-center p-4 bg-surface-700/50 rounded-lg no-underline transition-colors hover:bg-surface-700">
								<div class="flex flex-col gap-1">
									<span class="font-medium text-surface-50">{formatExperimentName(exp.id)}</span>
									<span class="text-sm text-surface-300">
										{exp.type === 'full' ? 'Full Pipeline' : 'Stage Run'}
										&bull; {exp.contextFiles.length} context files
									</span>
								</div>
								<Badge variant={exp.hasCompleteContext ? 'success' : 'warning'} size="sm">
									{exp.hasCompleteContext ? 'Complete' : 'Partial'}
								</Badge>
							</a>
						{/each}
					</div>
					<a href="/experiments" class="block mt-4 text-center text-primary-400 font-medium hover:text-primary-300">
						View all experiments &rarr;
					</a>
				{/if}
			</Card>

			<Card title="Recent Test Results">
				{#if recentTests.length === 0}
					<p class="text-surface-300 text-center py-6">No test results found</p>
				{:else}
					<div class="flex flex-col gap-2">
						{#each recentTests as test}
							<a href="/tests/{test.id}" class="flex justify-between items-center p-4 bg-surface-700/50 rounded-lg no-underline transition-colors hover:bg-surface-700">
								<div class="flex flex-col gap-1">
									<span class="font-medium text-surface-50">{test.stage_name || test.test_name || test.id}</span>
									<span class="text-sm text-surface-300">
										{test.agent_name ? `${test.agent_name} \u2022` : ''}
										{test.execution_time_ms ? formatDuration(test.execution_time_ms) : ''}
									</span>
								</div>
								<Badge variant={test.success ? 'success' : 'error'} size="sm">
									{test.success ? 'Passed' : 'Failed'}
								</Badge>
							</a>
						{/each}
					</div>
					<a href="/tests" class="block mt-4 text-center text-primary-400 font-medium hover:text-primary-300">
						View all test results &rarr;
					</a>
				{/if}
			</Card>
		</div>

		<Card title="Pipeline Stages">
			<div class="flex flex-col lg:flex-row items-center justify-between gap-4">
				<div class="stage-item flex-1 min-w-[200px] flex items-start gap-4 p-4 bg-surface-700/50 rounded-lg">
					<div class="text-3xl">💡</div>
					<div>
						<h3 class="font-semibold text-surface-50 mb-1">Idea Development</h3>
						<p class="text-sm text-surface-300 m-0">CEO generates ideas, Researcher validates, Legal Advisor reviews compliance</p>
					</div>
				</div>
				<div class="text-2xl text-primary-400 font-bold lg:rotate-0 rotate-90">&rarr;</div>
				<div class="stage-item flex-1 min-w-[200px] flex items-start gap-4 p-4 bg-surface-700/50 rounded-lg">
					<div class="text-3xl">🏗️</div>
					<div>
						<h3 class="font-semibold text-surface-50 mb-1">Prototyping</h3>
						<p class="text-sm text-surface-300 m-0">Developer creates architecture, Designer builds UI, QA validates quality</p>
					</div>
				</div>
				<div class="text-2xl text-primary-400 font-bold lg:rotate-0 rotate-90">&rarr;</div>
				<div class="stage-item flex-1 min-w-[200px] flex items-start gap-4 p-4 bg-surface-700/50 rounded-lg">
					<div class="text-3xl">🎯</div>
					<div>
						<h3 class="font-semibold text-surface-50 mb-1">Pitch</h3>
						<p class="text-sm text-surface-300 m-0">Marketer develops strategy, Deck Strategist creates pitch deck</p>
					</div>
				</div>
			</div>
		</Card>
	{/if}
</div>
