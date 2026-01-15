<script lang="ts">
	interface Props {
		text: string;
		maxLength?: number;
		class?: string;
	}

	let { text, maxLength = 300, class: className = '' }: Props = $props();

	let expanded = $state(false);

	let needsTruncation = $derived(text.length > maxLength);
	let displayText = $derived(
		needsTruncation && !expanded ? text.slice(0, maxLength).trimEnd() + '...' : text
	);

	function toggle() {
		expanded = !expanded;
	}
</script>

<span class="truncated-text {className}">
	<span class="text-content">{displayText}</span>
	{#if needsTruncation}
		<button class="toggle-btn" onclick={toggle}>
			{expanded ? 'See less' : 'See more'}
		</button>
	{/if}
</span>

<style>
	.truncated-text {
		display: inline;
	}

	.text-content {
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	.toggle-btn {
		display: inline;
		background: none;
		border: none;
		color: var(--primary-light);
		cursor: pointer;
		padding: 0;
		margin-left: 0.5em;
		font-size: inherit;
		font-weight: 500;
		text-decoration: none;
		transition: color 0.2s ease;
	}

	.toggle-btn:hover {
		color: var(--primary-dark);
		text-decoration: underline;
	}
</style>
