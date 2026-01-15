<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { Card, Badge, TabGroup, LoadingSpinner, JsonBlock } from '$components/shared';
	import type { ExperimentContext, StageRunResult } from '$types';

	let experimentData = $state<{
		id: string;
		type: string;
		context?: ExperimentContext;
		results?: StageRunResult;
		hasStatistics: boolean;
		subfolders?: string[];
	} | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	const expId = $derived($page.params.id);

	onMount(async () => {
		try {
			const res = await fetch(`/api/experiments/${expId}`);
			if (!res.ok) throw new Error('Failed to load experiment');
			experimentData = await res.json();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load experiment';
		} finally {
			loading = false;
		}
	});

	let context = $derived(experimentData?.context || experimentData?.results?.full_context);
	let stageOutputs = $derived(context?.state?.stage_outputs);
	let completedStages = $derived(context?.state?.completed_stages || []);
	let hasIdea = $derived(!!stageOutputs?.idea_development);
	let hasPrototype = $derived(!!stageOutputs?.prototyping);
	let hasPitch = $derived(!!stageOutputs?.pitch);

	const tabs = $derived([
		{ id: 'overview', label: 'Overview' },
		...(hasIdea ? [{ id: 'idea', label: 'Idea Development', href: `/experiments/${expId}/idea` }] : []),
		...(hasPrototype ? [{ id: 'prototype', label: 'Prototyping', href: `/experiments/${expId}/prototype` }] : []),
		...(hasPitch ? [{ id: 'pitch', label: 'Pitch', href: `/experiments/${expId}/pitch` }] : []),
		...(experimentData?.hasStatistics ? [{ id: 'stats', label: 'Statistics', href: `/experiments/${expId}/stats` }] : [])
	]);
</script>

<svelte:head>
	<title>{expId} | AI Innovators Results Viewer</title>
</svelte:head>

<div class="max-w-max mx-auto">
	<div class="flex items-center gap-4 mb-10 flex-wrap">
		<h1 class="text-2xl font-bold text-surface-50 break-all">{expId}</h1>
		{#if experimentData}
			<Badge variant={experimentData.type === 'full' ? 'primary' : 'neutral'}>
				{experimentData.type === 'full' ? 'Full Pipeline' : 'Stage Run'}
			</Badge>
		{/if}
	</div>

	{#if loading}
		<LoadingSpinner message="Loading experiment..." />
	{:else if error}
		<Card>
			<p class="text-error-400 text-center">{error}</p>
		</Card>
	{:else if experimentData}
		<TabGroup {tabs} activeTab="overview" />

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<Card title="Pipeline Status">
				<div class="stage-timeline flex flex-col md:flex-row items-center justify-between py-4 gap-4">
					<div class="stage flex flex-col items-center gap-2 {completedStages.includes('idea_development') || context?.state?.current_stage === 'idea_development' ? 'opacity-100' : 'opacity-50'}">
						<div class="text-3xl">💡</div>
						<div class="font-medium text-sm text-center text-surface-50">Idea Development</div>
						{#if hasIdea}
							<Badge variant="success" size="sm">Complete</Badge>
						{/if}
					</div>
					<div class="hidden md:block flex-1 h-1 mx-2 rounded {completedStages.includes('idea_development') ? 'bg-success-500' : 'bg-surface-600'}"></div>
					<div class="md:hidden w-1 h-8 rounded {completedStages.includes('idea_development') ? 'bg-success-500' : 'bg-surface-600'}"></div>
					<div class="stage flex flex-col items-center gap-2 {completedStages.includes('prototyping') || context?.state?.current_stage === 'prototyping' ? 'opacity-100' : 'opacity-50'}">
						<div class="text-3xl">🏗️</div>
						<div class="font-medium text-sm text-center text-surface-50">Prototyping</div>
						{#if hasPrototype}
							<Badge variant="success" size="sm">Complete</Badge>
						{/if}
					</div>
					<div class="hidden md:block flex-1 h-1 mx-2 rounded {completedStages.includes('prototyping') ? 'bg-success-500' : 'bg-surface-600'}"></div>
					<div class="md:hidden w-1 h-8 rounded {completedStages.includes('prototyping') ? 'bg-success-500' : 'bg-surface-600'}"></div>
					<div class="stage flex flex-col items-center gap-2 {completedStages.includes('pitch') || context?.state?.current_stage === 'pitch' ? 'opacity-100' : 'opacity-50'}">
						<div class="text-3xl">🎯</div>
						<div class="font-medium text-sm text-center text-surface-50">Pitch</div>
						{#if hasPitch}
							<Badge variant="success" size="sm">Complete</Badge>
						{/if}
					</div>
				</div>
			</Card>

			{#if context?.state?.chairman_input}
				<Card title="Input">
					<p class="bg-surface-700/50 p-4 rounded-lg m-0 italic text-surface-200">{context.state.chairman_input}</p>
				</Card>
			{/if}

			{#if stageOutputs?.idea_development?.idea}
				<Card title="Startup Idea" subtitle="Quick Summary" class="lg:col-span-2">
					<div class="grid md:grid-cols-2 gap-6">
						<div class="summary-item">
							<h4 class="text-primary-400 font-semibold mb-2">Problem</h4>
							<p class="text-surface-200 leading-relaxed m-0">{stageOutputs.idea_development.idea.problem.slice(0, 300)}...</p>
						</div>
						<div class="summary-item">
							<h4 class="text-primary-400 font-semibold mb-2">Solution</h4>
							<p class="text-surface-200 leading-relaxed m-0">{stageOutputs.idea_development.idea.solution.slice(0, 300)}...</p>
						</div>
					</div>
					{#if stageOutputs.idea_development.final_validation?.recommendation}
						<div class="flex items-center gap-4 mt-6 pt-6 border-t border-surface-600">
							<span class="font-semibold text-surface-50">Recommendation:</span>
							<Badge variant={stageOutputs.idea_development.final_validation.recommendation === 'GO' ? 'success' : stageOutputs.idea_development.final_validation.recommendation === 'PIVOT' ? 'warning' : 'error'}>
								{stageOutputs.idea_development.final_validation.recommendation}
							</Badge>
						</div>
					{/if}
					<a href="/experiments/{expId}/idea" class="block mt-6 text-primary-400 font-medium hover:text-primary-300">
						View full idea details &rarr;
					</a>
				</Card>
			{/if}

			{#if experimentData.subfolders && experimentData.subfolders.length > 0}
				<Card title="Generated Artifacts">
					<div class="flex flex-wrap gap-2">
						{#each experimentData.subfolders as folder}
							<div class="flex items-center gap-2 px-3 py-2 bg-surface-700/50 rounded-lg">
								<span>📁</span>
								<span class="text-surface-200">{folder}</span>
							</div>
						{/each}
					</div>
				</Card>
			{/if}
		</div>

		{#if context}
			<Card title="Raw Context Data" collapsible expanded={false}>
				<JsonBlock data={context} maxHeight="600px" />
			</Card>
		{/if}
	{/if}
</div>
