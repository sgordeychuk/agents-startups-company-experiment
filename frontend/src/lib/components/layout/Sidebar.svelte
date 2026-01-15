<script lang="ts">
	import { page } from '$app/stores';

	interface NavItem {
		label: string;
		href: string;
		icon: string;
		testId: string;
	}

	const navItems: NavItem[] = [
		{ label: 'Dashboard', href: '/', icon: '📊', testId: 'nav-home' },
		{ label: 'Experiments', href: '/experiments', icon: '🧪', testId: 'nav-experiments' },
		{ label: 'Test Results', href: '/tests', icon: '✅', testId: 'nav-tests' }
	];

	let isActive = (href: string) => {
		const path = $page.url.pathname;
		if (href === '/') return path === '/';
		return path.startsWith(href);
	};
</script>

<aside class="w-64 bg-surface-800 border-r border-surface-700 flex-col hidden md:flex">
	<nav class="flex-1 p-4 flex flex-col gap-1">
		{#each navItems as item}
			<a
				href={item.href}
				class="flex items-center gap-3 px-4 py-3 rounded-lg no-underline transition-all duration-200
					{isActive(item.href)
					? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white'
					: 'text-surface-200 hover:bg-surface-700 hover:text-surface-50'}"
				data-testid={item.testId}
			>
				<span class="text-xl">{item.icon}</span>
				<span class="font-medium">{item.label}</span>
			</a>
		{/each}
	</nav>

	<div class="p-4 border-t border-surface-700">
		<p class="text-surface-500 text-xs">AI Innovators v0.1.0</p>
	</div>
</aside>
