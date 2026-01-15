<script lang="ts">
	import { page } from '$app/stores';
	import { AppBar } from '@skeletonlabs/skeleton-svelte';

	interface Breadcrumb {
		label: string;
		href?: string;
	}

	let breadcrumbs = $derived.by(() => {
		const path = $page.url.pathname;
		const parts = path.split('/').filter(Boolean);
		const crumbs: Breadcrumb[] = [{ label: 'Home', href: '/' }];

		let currentPath = '';
		for (const part of parts) {
			currentPath += `/${part}`;
			if (part === 'experiments') {
				crumbs.push({ label: 'Experiments', href: '/experiments' });
			} else if (part === 'tests') {
				crumbs.push({ label: 'Test Results', href: '/tests' });
			} else if (part === 'idea') {
				crumbs.push({ label: 'Idea Development' });
			} else if (part === 'prototype') {
				crumbs.push({ label: 'Prototyping' });
			} else if (part === 'pitch') {
				crumbs.push({ label: 'Pitch' });
			} else if (part === 'stats') {
				crumbs.push({ label: 'Statistics' });
			} else if (
				part.startsWith('experiment_') ||
				part.startsWith('stage_run_') ||
				part.includes('_202')
			) {
				crumbs.push({ label: part, href: `/experiments/${part}` });
			} else if (parts.includes('tests') && parts.indexOf(part) > 0) {
				crumbs.push({ label: part });
			}
		}

		return crumbs;
	});
</script>

<AppBar class="border-b border-surface-500/20">
	<AppBar.Toolbar class="grid-cols-[auto_1fr_auto]">
		<AppBar.Lead>
			<a href="/" class="logo flex items-center gap-2 no-underline" data-testid="logo-link">
				<span class="bg-gradient-to-br from-primary-500 to-secondary-500 text-white font-bold text-sm px-2 py-1 rounded">
					AI
				</span>
				<span class="font-semibold text-surface-50 hidden sm:inline">
					Innovators Results Viewer
				</span>
			</a>
		</AppBar.Lead>

		<AppBar.Trail>
			<nav class="flex items-center gap-2 text-sm breadcrumb" aria-label="Breadcrumb">
				{#each breadcrumbs as crumb, i}
					{#if i > 0}
						<span class="text-surface-200">/</span>
					{/if}
					{#if crumb.href && i < breadcrumbs.length - 1}
						<a href={crumb.href} class="text-primary-400 hover:text-primary-300 hover:underline">
							{crumb.label}
						</a>
					{:else}
						<span class="text-surface-200 max-w-[200px] truncate">
							{crumb.label}
						</span>
					{/if}
				{/each}
			</nav>
		</AppBar.Trail>
	</AppBar.Toolbar>
</AppBar>
