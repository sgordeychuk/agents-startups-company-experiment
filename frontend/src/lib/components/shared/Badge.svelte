<script lang="ts">
	interface Props {
		variant?: 'success' | 'error' | 'warning' | 'neutral' | 'primary';
		size?: 'sm' | 'md' | 'lg';
		children?: import('svelte').Snippet;
	}

	let { variant = 'neutral', size = 'md', children }: Props = $props();

	const variantClasses: Record<string, string> = {
		success: 'bg-success-500/20 text-success-400 border border-success-500/30',
		error: 'bg-error-500/20 text-error-400 border border-error-500/30',
		warning: 'bg-warning-500/20 text-warning-400 border border-warning-500/30',
		neutral: 'bg-surface-600 text-surface-200 border border-surface-500',
		primary: 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
	};

	const sizeClasses: Record<string, string> = {
		sm: 'px-2 py-0.5 text-xs',
		md: 'px-3 py-1 text-sm',
		lg: 'px-4 py-1.5 text-base'
	};
</script>

<span class="badge inline-block rounded-full font-semibold uppercase tracking-wide whitespace-nowrap {variantClasses[variant]} {sizeClasses[size]}">
	{@render children?.()}
</span>
