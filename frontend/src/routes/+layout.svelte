<script lang="ts">
	import '../app.css';
	import { Header, Sidebar } from '$lib/components/layout';

	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<div class="h-screen flex flex-col bg-surface-50-900-token">
	<Header />
	<div class="flex flex-1 overflow-hidden">
		<Sidebar />
		<main class="flex-1 overflow-y-auto p-6">
			{@render children?.()}
		</main>
	</div>
</div>
