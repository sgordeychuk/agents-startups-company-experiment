<script lang="ts">
	interface Props {
		size?: 'sm' | 'md' | 'lg';
		message?: string;
	}

	let { size = 'md', message = 'Loading...' }: Props = $props();

	const sizeClasses = {
		sm: 'w-6 h-6 border-2',
		md: 'w-10 h-10 border-3',
		lg: 'w-16 h-16 border-4'
	};
</script>

<div class="flex flex-col items-center justify-center p-10">
	<div
		class="rounded-full border-surface-600 border-t-primary-500 animate-spin {sizeClasses[size]}"
	></div>
	{#if message}
		<p class="mt-4 text-surface-300 text-sm">{message}</p>
	{/if}
</div>

<style>
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	.animate-spin {
		animation: spin 1s linear infinite;
	}
</style>
