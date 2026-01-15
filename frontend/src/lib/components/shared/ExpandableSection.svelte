<script lang="ts">
	interface Props {
		title: string;
		expanded?: boolean;
		count?: number;
		children?: import('svelte').Snippet;
	}

	let { title, expanded = $bindable(false), count, children }: Props = $props();

	function toggle() {
		expanded = !expanded;
	}
</script>

<div class="expandable border border-surface-600 rounded-lg mb-2 overflow-hidden">
	<button
		class="header flex items-center gap-2 w-full p-4 bg-surface-700/50 border-none cursor-pointer text-left text-base transition-colors hover:bg-surface-700"
		onclick={toggle}
	>
		<span class="text-xs text-primary-400 w-4">{expanded ? '▼' : '▶'}</span>
		<span class="font-semibold text-surface-50">{title}</span>
		{#if count !== undefined}
			<span class="text-surface-300 text-sm">({count})</span>
		{/if}
	</button>
	{#if expanded}
		<div class="content p-4 bg-surface-800 border-t border-surface-600">
			{@render children?.()}
		</div>
	{/if}
</div>
