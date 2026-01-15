<script lang="ts">
	interface Props {
		title?: string;
		subtitle?: string;
		collapsible?: boolean;
		expanded?: boolean;
		accent?: 'primary' | 'success' | 'warning' | 'error' | 'neutral';
		class?: string;
		children?: import('svelte').Snippet;
	}

	let {
		title = '',
		subtitle = '',
		collapsible = false,
		expanded = $bindable(true),
		accent = 'primary',
		class: className = '',
		children
	}: Props = $props();

	function toggle() {
		if (collapsible) {
			expanded = !expanded;
		}
	}

	const accentClasses: Record<string, string> = {
		primary: 'border-l-primary-500',
		success: 'border-l-success-500',
		warning: 'border-l-warning-500',
		error: 'border-l-error-500',
		neutral: 'border-l-surface-500'
	};
</script>

<div class="card bg-surface-800 rounded-xl shadow-lg overflow-hidden mb-6 {className}">
	{#if title}
		{#if collapsible}
			<button
				type="button"
				class="card-header w-full p-5 border-l-4 {accentClasses[accent]} bg-surface-700/50 flex justify-between items-center cursor-pointer select-none hover:bg-surface-700 border-0 text-left"
				onclick={toggle}
			>
				<div class="title-content">
					<h2 class="text-lg font-semibold text-surface-50 m-0">{title}</h2>
					{#if subtitle}
						<p class="mt-1 text-sm text-surface-300 m-0">{subtitle}</p>
					{/if}
				</div>
				<span class="text-2xl font-bold text-primary-400 w-8 text-center">
					{expanded ? '−' : '+'}
				</span>
			</button>
		{:else}
			<div class="card-header p-5 border-l-4 {accentClasses[accent]} bg-surface-700/50 flex justify-between items-center">
				<div class="title-content">
					<h2 class="text-lg font-semibold text-surface-50 m-0">{title}</h2>
					{#if subtitle}
						<p class="mt-1 text-sm text-surface-300 m-0">{subtitle}</p>
					{/if}
				</div>
			</div>
		{/if}
	{/if}
	{#if expanded}
		<div class="card-body p-5">
			{@render children?.()}
		</div>
	{/if}
</div>
