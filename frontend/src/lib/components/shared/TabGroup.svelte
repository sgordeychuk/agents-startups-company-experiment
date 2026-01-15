<script lang="ts">
	interface Tab {
		id: string;
		label: string;
		href?: string;
	}

	interface Props {
		tabs: Tab[];
		activeTab?: string;
		onSelect?: (tabId: string) => void;
	}

	let { tabs, activeTab = $bindable(tabs[0]?.id), onSelect }: Props = $props();

	function selectTab(tabId: string) {
		activeTab = tabId;
		onSelect?.(tabId);
	}
</script>

<div class="tab-group flex gap-1 border-b-2 border-surface-600 mb-6 overflow-x-auto overflow-y-hidden">
	{#each tabs as tab}
		{#if tab.href}
			<a
				href={tab.href}
				class="tab px-5 py-3 border-b-2 -mb-0.5 text-sm font-medium whitespace-nowrap no-underline transition-all duration-200
					{activeTab === tab.id
					? 'text-primary-400 border-b-primary-500 bg-surface-800'
					: 'text-surface-200 border-b-transparent hover:text-primary-300 hover:bg-surface-700/50'}"
				data-testid="tab-{tab.id}"
			>
				{tab.label}
			</a>
		{:else}
			<button
				class="tab px-5 py-3 border-b-2 -mb-0.5 text-sm font-medium whitespace-nowrap transition-all duration-200 bg-transparent border-none cursor-pointer
					{activeTab === tab.id
					? 'text-primary-400 border-b-primary-500 bg-surface-800'
					: 'text-surface-200 border-b-transparent hover:text-primary-300 hover:bg-surface-700/50'}"
				data-testid="tab-{tab.id}"
				onclick={() => selectTab(tab.id)}
			>
				{tab.label}
			</button>
		{/if}
	{/each}
</div>
