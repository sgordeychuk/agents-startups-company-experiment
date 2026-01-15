<script lang="ts">
	interface Props {
		data: unknown;
		maxHeight?: string;
		title?: string;
	}

	let { data, maxHeight = '500px', title = '' }: Props = $props();

	let copied = $state(false);

	const formatted = $derived(JSON.stringify(data, null, 2));

	async function copyToClipboard() {
		try {
			await navigator.clipboard.writeText(formatted);
			copied = true;
			setTimeout(() => (copied = false), 2000);
		} catch {
			console.error('Failed to copy to clipboard');
		}
	}
</script>

<div class="json-container relative">
	{#if title}
		<div class="json-header flex justify-between items-center bg-surface-700 px-4 py-2 rounded-t-lg">
			<span class="text-surface-300 text-sm font-mono">{title}</span>
			<button
				class="copy-btn bg-primary-500 hover:bg-primary-600 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
				onclick={copyToClipboard}
			>
				{copied ? 'Copied!' : 'Copy'}
			</button>
		</div>
	{:else}
		<button
			class="copy-btn absolute top-2 right-2 z-10 bg-primary-500 hover:bg-primary-600 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
			onclick={copyToClipboard}
		>
			{copied ? 'Copied!' : 'Copy'}
		</button>
	{/if}
	<div
		class="json-block bg-surface-900 text-surface-200 p-5 font-mono text-sm leading-relaxed overflow-auto
			{title ? 'rounded-b-lg' : 'rounded-lg'}"
		style="max-height: {maxHeight}"
	>
		<pre class="m-0 whitespace-pre-wrap break-words"><code>{formatted}</code></pre>
	</div>
</div>
