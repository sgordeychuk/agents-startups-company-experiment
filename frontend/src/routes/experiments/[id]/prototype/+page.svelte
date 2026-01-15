<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { Card, Badge, TabGroup, LoadingSpinner, JsonBlock } from '$components/shared';
	import type { ExperimentContext, PrototypingOutput } from '$types';

	let context = $state<ExperimentContext | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let selectedImage = $state<string | null>(null);

	const expId = $derived($page.params.id);

	onMount(async () => {
		try {
			const res = await fetch(`/api/experiments/${expId}`);
			if (!res.ok) throw new Error('Failed to load experiment');
			const data = await res.json();
			context = data.context || data.results?.full_context;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load experiment';
		} finally {
			loading = false;
		}
	});

	let protoOutput = $derived(context?.state?.stage_outputs?.prototyping as PrototypingOutput | undefined);
	let hasIdea = $derived(!!context?.state?.stage_outputs?.idea_development);
	let hasPitch = $derived(!!context?.state?.stage_outputs?.pitch);

	const tabs = $derived([
		{ id: 'overview', label: 'Overview', href: `/experiments/${expId}` },
		...(hasIdea ? [{ id: 'idea', label: 'Idea Development', href: `/experiments/${expId}/idea` }] : []),
		{ id: 'prototype', label: 'Prototyping' },
		...(hasPitch ? [{ id: 'pitch', label: 'Pitch', href: `/experiments/${expId}/pitch` }] : [])
	]);

	function getMethodVariant(method: string): 'success' | 'primary' | 'warning' | 'error' | 'neutral' {
		switch (method?.toUpperCase()) {
			case 'GET': return 'success';
			case 'POST': return 'primary';
			case 'PUT':
			case 'PATCH': return 'warning';
			case 'DELETE': return 'error';
			default: return 'neutral';
		}
	}

	function getImageUrl(filepath: string): string {
		const filename = (filepath || '').split('/').pop() || '';
		return `/api/experiments/${expId}/designs/${filename}`;
	}

	function openLightbox(imageSrc: string) {
		selectedImage = imageSrc;
	}

	function closeLightbox() {
		selectedImage = null;
	}
</script>

<svelte:head>
	<title>Prototyping | {expId}</title>
</svelte:head>

<div class="max-w-max mx-auto">
	<div class="mb-10">
		<h1 class="text-3xl font-bold text-surface-50 mb-1">Prototyping</h1>
		<p class="text-surface-200 break-all">{expId}</p>
	</div>

	{#if loading}
		<LoadingSpinner message="Loading prototyping stage..." />
	{:else if error}
		<Card>
			<p class="text-error-400 text-center">{error}</p>
		</Card>
	{:else if protoOutput}
		<TabGroup {tabs} activeTab="prototype" />

		<!-- Design Screenshots Gallery -->
		{#if protoOutput.final_designs && protoOutput.final_designs.length > 0}
			<Card title="Design Screenshots" subtitle="{protoOutput.final_designs.length} screens generated">
				<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
					{#each protoOutput.final_designs as design}
						<button
							type="button"
							class="design-card bg-surface-700/50 rounded-lg overflow-hidden transition-all duration-200 hover:bg-surface-700 hover:scale-[1.02] cursor-pointer border-none p-0 text-left w-full"
							data-testid="design-image"
							onclick={() => openLightbox(getImageUrl(design.filepath))}
						>
							<img
								src={getImageUrl(design.filepath)}
								alt={design.screen_name}
								class="w-full h-auto"
								loading="lazy"
							/>
							<div class="p-4">
								<h4 class="font-semibold text-surface-50 mb-1">{design.screen_name}</h4>
								<p class="text-sm text-surface-200 mb-2">{design.description || design.viewport || 'Desktop'}</p>
								{#if design.colors_used}
									<div class="flex gap-2 mt-2">
										{#each Object.entries(design.colors_used).slice(0, 4) as [name, color]}
											<div class="flex items-center gap-1" title={name}>
												<div class="w-4 h-4 rounded" style="background-color: {color}"></div>
												<span class="text-xs text-surface-500">{color}</span>
											</div>
										{/each}
									</div>
								{/if}
							</div>
						</button>
					{/each}
				</div>
			</Card>
		{/if}

		{#if protoOutput.prototype}
			<Card title="Prototype Overview">
				<div class="flex flex-wrap gap-8 mb-6">
					<div class="text-center">
						<span class="block text-3xl font-bold text-primary-400">{protoOutput.prototype.files_generated || 0}</span>
						<span class="text-surface-200 text-sm">Files Generated</span>
					</div>
					<div class="text-center">
						<span class="block text-3xl font-bold text-primary-400">{protoOutput.prototype.endpoints?.length || 0}</span>
						<span class="text-surface-200 text-sm">API Endpoints</span>
					</div>
					<div class="text-center">
						<span class="block text-3xl font-bold text-primary-400">{protoOutput.prototype.status || 'Unknown'}</span>
						<span class="text-surface-200 text-sm">Status</span>
					</div>
				</div>
				{#if protoOutput.prototype.directory}
					<p class="m-0 p-4 bg-surface-700/50 rounded-lg">
						<strong class="text-surface-200">Directory:</strong>
						<code class="text-primary-400 ml-2">{protoOutput.prototype.directory}</code>
					</p>
				{/if}
			</Card>
		{/if}

		{#if protoOutput.prototype?.tech_stack || protoOutput.architecture?.tech_stack}
			{@const techStack = protoOutput.architecture?.tech_stack || protoOutput.prototype?.tech_stack}
			<Card title="Tech Stack">
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
					{#if techStack.frontend}
						<div class="p-5 bg-surface-700/50 rounded-lg border-l-4 border-l-primary-500">
							<div class="flex items-center gap-2 mb-3">
								<span class="text-2xl">🖥️</span>
								<h4 class="font-semibold text-surface-50 m-0">Frontend</h4>
							</div>
							<p class="font-semibold text-surface-100 m-0 mb-1">{techStack.frontend.framework}</p>
							<p class="text-surface-200 text-sm m-0 mb-2">{techStack.frontend.language}</p>
							<p class="text-surface-200 text-sm m-0 leading-relaxed">{techStack.frontend.rationale}</p>
						</div>
					{/if}
					{#if techStack.backend}
						<div class="p-5 bg-surface-700/50 rounded-lg border-l-4 border-l-secondary-500">
							<div class="flex items-center gap-2 mb-3">
								<span class="text-2xl">⚙️</span>
								<h4 class="font-semibold text-surface-50 m-0">Backend</h4>
							</div>
							<p class="font-semibold text-surface-100 m-0 mb-1">{techStack.backend.framework}</p>
							<p class="text-surface-200 text-sm m-0 mb-2">{techStack.backend.language}</p>
							<p class="text-surface-200 text-sm m-0 leading-relaxed">{techStack.backend.rationale}</p>
						</div>
					{/if}
					{#if techStack.database}
						<div class="p-5 bg-surface-700/50 rounded-lg border-l-4 border-l-tertiary-500">
							<div class="flex items-center gap-2 mb-3">
								<span class="text-2xl">🗄️</span>
								<h4 class="font-semibold text-surface-50 m-0">Database</h4>
							</div>
							<p class="font-semibold text-surface-100 m-0 mb-1">{techStack.database.primary}</p>
							{#if techStack.database.caching}
								<p class="text-surface-200 text-sm m-0 mb-2">Cache: {techStack.database.caching}</p>
							{/if}
							<p class="text-surface-200 text-sm m-0 leading-relaxed">{techStack.database.rationale}</p>
						</div>
					{/if}
					{#if techStack.infrastructure}
						<div class="p-5 bg-surface-700/50 rounded-lg border-l-4 border-l-success-500">
							<div class="flex items-center gap-2 mb-3">
								<span class="text-2xl">☁️</span>
								<h4 class="font-semibold text-surface-50 m-0">Infrastructure</h4>
							</div>
							<p class="font-semibold text-surface-100 m-0 mb-1">{techStack.infrastructure.framework || techStack.infrastructure.hosting}</p>
							<p class="text-surface-200 text-sm m-0 leading-relaxed">{techStack.infrastructure.rationale}</p>
						</div>
					{/if}
				</div>
			</Card>
		{/if}

		{#if protoOutput.architecture?.api_structure?.endpoints}
			<Card title="API Endpoints">
				<div class="flex flex-col gap-2">
					{#each protoOutput.architecture.api_structure.endpoints as endpoint}
						<div class="flex flex-wrap items-center gap-4 p-4 bg-surface-700/50 rounded-lg">
							<Badge variant={getMethodVariant(endpoint.method)} size="sm">{endpoint.method}</Badge>
							<code class="font-mono text-primary-400 font-medium">{endpoint.path}</code>
							<span class="text-surface-200 text-sm">{endpoint.purpose}</span>
						</div>
					{/each}
				</div>
				{#if protoOutput.architecture.api_structure.authentication}
					<p class="mt-6 p-4 bg-surface-700/50 rounded-lg m-0">
						<strong class="text-surface-200">Authentication:</strong>
						<span class="text-surface-200 ml-2">{protoOutput.architecture.api_structure.authentication}</span>
					</p>
				{/if}
			</Card>
		{/if}

		{#if protoOutput.architecture?.core_components}
			<Card title="Core Components" collapsible>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
					{#each protoOutput.architecture.core_components as component}
						<div class="p-5 bg-surface-700/50 rounded-lg">
							<h4 class="font-semibold text-surface-50 m-0 mb-1">{component.name}</h4>
							<p class="text-primary-400 text-sm m-0 mb-2">{component.technology}</p>
							<p class="text-surface-200 m-0 mb-3 leading-relaxed">{component.responsibility}</p>
							{#if component.key_features?.length > 0}
								<ul class="m-0 pl-5 text-surface-200 text-sm">
									{#each component.key_features as feature}
										<li>{feature}</li>
									{/each}
								</ul>
							{/if}
						</div>
					{/each}
				</div>
			</Card>
		{/if}

		{#if protoOutput.design_system || protoOutput.design?.design_system}
			{@const designSystem = protoOutput.design_system || protoOutput.design?.design_system}
			<Card title="Design System" collapsible expanded={false}>
				{#if designSystem.colors}
					<h3 class="text-lg font-semibold text-surface-50 mb-4">Color Palette</h3>
					<div class="flex flex-wrap gap-4">
						{#each Object.entries(designSystem.colors) as [name, value]}
							{#if typeof value === 'string'}
								<div class="flex flex-col items-center gap-2">
									<div class="w-16 h-16 rounded-lg border border-surface-600" style="background: {value}"></div>
									<span class="text-surface-200 text-sm capitalize">{name}</span>
									<span class="font-mono text-surface-200 text-xs">{value}</span>
								</div>
							{/if}
						{/each}
					</div>
				{/if}
			</Card>
		{/if}

		<Card title="Raw Stage Output" collapsible expanded={false}>
			<JsonBlock data={protoOutput} maxHeight="600px" />
		</Card>
	{:else}
		<Card>
			<p class="text-surface-200 text-center py-10">No prototyping data found for this experiment</p>
		</Card>
	{/if}
</div>

<!-- Lightbox Modal -->
{#if selectedImage}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
		role="dialog"
		aria-modal="true"
		tabindex="-1"
	>
		<button
			type="button"
			class="absolute inset-0 w-full h-full bg-transparent border-none cursor-pointer"
			onclick={closeLightbox}
			onkeydown={(e) => e.key === 'Escape' && closeLightbox()}
			aria-label="Close lightbox"
		></button>
		<button
			type="button"
			class="absolute top-4 right-4 text-white text-3xl bg-transparent border-none cursor-pointer hover:text-surface-200 z-10"
			onclick={closeLightbox}
			aria-label="Close"
		>
			&times;
		</button>
		<img
			src={selectedImage}
			alt="Design preview"
			class="max-w-full max-h-[90vh] rounded-lg shadow-2xl relative z-10 pointer-events-none"
		/>
	</div>
{/if}
