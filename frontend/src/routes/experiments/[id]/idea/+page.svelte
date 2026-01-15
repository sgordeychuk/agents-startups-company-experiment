<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { Card, TabGroup, LoadingSpinner, JsonBlock, ExpandableSection } from '$components/shared';
	import { IdeaCard, ValidationCard, CompetitorTable, RiskOpportunityList } from '$components/stages';
	import type { ExperimentContext, IdeaDevelopmentOutput } from '$types';

	let context = $state<ExperimentContext | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	const expId = $derived($page.params.id);

	onMount(async () => {
		try {
			const res = await fetch(`/api/experiments/${expId}`);
			if (!res.ok) throw new Error('Failed to load experiment');
			const data = await res.json();
			context = data.context || data.results?.full_context;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load experiment';
		} finally {
			loading = false;
		}
	});

	let ideaOutput = $derived(context?.state?.stage_outputs?.idea_development as IdeaDevelopmentOutput | undefined);
	let hasPrototype = $derived(!!context?.state?.stage_outputs?.prototyping);
	let hasPitch = $derived(!!context?.state?.stage_outputs?.pitch);

	const tabs = $derived([
		{ id: 'overview', label: 'Overview', href: `/experiments/${expId}` },
		{ id: 'idea', label: 'Idea Development' },
		...(hasPrototype ? [{ id: 'prototype', label: 'Prototyping', href: `/experiments/${expId}/prototype` }] : []),
		...(hasPitch ? [{ id: 'pitch', label: 'Pitch', href: `/experiments/${expId}/pitch` }] : [])
	]);
</script>

<svelte:head>
	<title>Idea Development | {expId}</title>
</svelte:head>

<div class="max-w-max mx-auto">
	<div class="flex items-center gap-4 mb-10 flex-wrap">
		<h1 class="text-2xl font-bold text-surface-50 break-all">Idea Development</h1>
		<span class="text-surface-300 text-sm">{expId}</span>
	</div>

	{#if loading}
		<LoadingSpinner message="Loading idea development stage..." />
	{:else if error}
		<Card>
			<p class="error-message">{error}</p>
		</Card>
	{:else if ideaOutput}
		<TabGroup {tabs} activeTab="idea" />

		{#if ideaOutput.idea}
			<IdeaCard idea={ideaOutput.idea} />
		{/if}

		{#if ideaOutput.final_validation}
			<ValidationCard validation={ideaOutput.final_validation} />

			{#if ideaOutput.final_validation.competitors?.length > 0}
				<CompetitorTable competitors={ideaOutput.final_validation.competitors} />
			{/if}

			{#if ideaOutput.final_validation.risks?.length > 0 || ideaOutput.final_validation.opportunities?.length > 0}
				<RiskOpportunityList
					risks={ideaOutput.final_validation.risks || []}
					opportunities={ideaOutput.final_validation.opportunities || []}
				/>
			{/if}
		{/if}

		{#if ideaOutput.legal_insights}
			<Card title="Legal Insights" collapsible expanded={false}>
				{#if typeof ideaOutput.legal_insights === 'object'}
					{#if ideaOutput.legal_insights.overall_risk_level}
						<div class="risk-level-header">
							<span class="risk-label">Overall Risk Level:</span>
							<span class="risk-badge risk-{ideaOutput.legal_insights.overall_risk_level.toLowerCase()}">
								{ideaOutput.legal_insights.overall_risk_level}
							</span>
						</div>
					{/if}

					{#if ideaOutput.legal_insights.blocking_issues?.length}
						<ExpandableSection title="Blocking Issues ({ideaOutput.legal_insights.blocking_issues.length})" expanded={true}>
							{#each ideaOutput.legal_insights.blocking_issues as issue}
								<div class="blocking-issue">
									<div class="issue-header">
										<span class="severity-badge severity-{issue.severity.toLowerCase()}">{issue.severity}</span>
									</div>
									<p class="issue-text">{issue.issue}</p>
									<div class="resolution">
										<h5>Resolution Path</h5>
										<p>{issue.resolution_path}</p>
									</div>
								</div>
							{/each}
						</ExpandableSection>
					{/if}

					{#if ideaOutput.legal_insights.key_risks?.length}
						<ExpandableSection title="Key Risks ({ideaOutput.legal_insights.key_risks.length})" expanded={false}>
							<div class="risks-grid">
								{#each ideaOutput.legal_insights.key_risks as risk}
									<div class="risk-card">
										<div class="risk-card-header">
											<span class="risk-category">{risk.category}</span>
											<span class="risk-badge risk-{risk.risk_level.toLowerCase()}">{risk.risk_level}</span>
										</div>
										<p class="risk-summary">{risk.summary}</p>
									</div>
								{/each}
							</div>
						</ExpandableSection>
					{/if}

					{#if ideaOutput.legal_insights.recommendations?.length}
						<ExpandableSection title="Recommendations ({ideaOutput.legal_insights.recommendations.length})" expanded={false}>
							{#each ideaOutput.legal_insights.recommendations as rec}
								<div class="recommendation-item">
									<div class="rec-header">
										<span class="priority-badge">P{rec.priority}</span>
										<span class="rec-category">{rec.category}</span>
									</div>
									<p class="rec-action">{rec.action}</p>
								</div>
							{/each}
						</ExpandableSection>
					{/if}

					{#if ideaOutput.legal_insights.ip_analysis}
						<ExpandableSection title="IP Analysis" expanded={false}>
							{#if typeof ideaOutput.legal_insights.ip_analysis === 'string'}
								<p>{ideaOutput.legal_insights.ip_analysis}</p>
							{:else}
								<div class="legal-grid">
									{#if ideaOutput.legal_insights.ip_analysis.patent_landscape}
										<div class="legal-item">
											<h4>Patent Landscape</h4>
											<p>{ideaOutput.legal_insights.ip_analysis.patent_landscape}</p>
										</div>
									{/if}
									{#if ideaOutput.legal_insights.ip_analysis.trademark_considerations}
										<div class="legal-item">
											<h4>Trademark Considerations</h4>
											<p>{ideaOutput.legal_insights.ip_analysis.trademark_considerations}</p>
										</div>
									{/if}
									{#if ideaOutput.legal_insights.ip_analysis.trade_secrets}
										<div class="legal-item">
											<h4>Trade Secrets</h4>
											<p>{ideaOutput.legal_insights.ip_analysis.trade_secrets}</p>
										</div>
									{/if}
								</div>
							{/if}
						</ExpandableSection>
					{/if}

					{#if ideaOutput.legal_insights.regulatory_requirements}
						<ExpandableSection title="Regulatory Requirements" expanded={false}>
							{#if Array.isArray(ideaOutput.legal_insights.regulatory_requirements)}
								{#each ideaOutput.legal_insights.regulatory_requirements as req}
									<div class="regulatory-item">
										<h4>{req.name}</h4>
										<p class="meta">{req.jurisdiction} • Est. Cost: {req.estimated_cost}</p>
										<p>{req.applicability}</p>
										{#if req.compliance_requirements?.length > 0}
											<ul>
												{#each req.compliance_requirements as cr}
													<li>{cr}</li>
												{/each}
											</ul>
										{/if}
									</div>
								{/each}
							{:else}
								<p>{ideaOutput.legal_insights.regulatory_requirements}</p>
							{/if}
						</ExpandableSection>
					{/if}

					{#if ideaOutput.legal_insights.privacy_compliance}
						<ExpandableSection title="Privacy Compliance" expanded={false}>
							{#if typeof ideaOutput.legal_insights.privacy_compliance === 'string'}
								<p>{ideaOutput.legal_insights.privacy_compliance}</p>
							{:else}
								<div class="privacy-section">
									{#if ideaOutput.legal_insights.privacy_compliance.applicable_laws}
										<h4>Applicable Laws</h4>
										<ul>
											{#each ideaOutput.legal_insights.privacy_compliance.applicable_laws as law}
												<li>{law}</li>
											{/each}
										</ul>
									{/if}
									{#if ideaOutput.legal_insights.privacy_compliance.key_requirements}
										<h4>Key Requirements</h4>
										<ul>
											{#each ideaOutput.legal_insights.privacy_compliance.key_requirements as req}
												<li>{req}</li>
											{/each}
										</ul>
									{/if}
								</div>
							{/if}
						</ExpandableSection>
					{/if}

				{:else}
					<p>{ideaOutput.legal_insights}</p>
				{/if}
			</Card>
		{/if}

		<Card title="Raw Stage Output" collapsible expanded={false}>
			<JsonBlock data={ideaOutput} maxHeight="600px" />
		</Card>
	{:else}
		<Card>
			<p class="empty-message">No idea development data found for this experiment</p>
		</Card>
	{/if}
</div>

<style>
	.error-message,
	.empty-message {
		color: var(--text-muted);
		text-align: center;
		padding: var(--space-xl);
	}

	.error-message {
		color: var(--error-text);
	}

	/* Risk Level Header */
	.risk-level-header {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		margin-bottom: var(--space-lg);
		padding-bottom: var(--space-md);
		border-bottom: 1px solid var(--border-color);
	}

	.risk-label {
		font-weight: 600;
		color: var(--text-secondary);
	}

	.risk-badge {
		padding: 4px 12px;
		border-radius: 4px;
		font-size: 0.85rem;
		font-weight: 600;
		text-transform: uppercase;
	}

	.risk-low { background: #1a4731; color: #6ee7b7; }
	.risk-medium { background: #713f12; color: #fcd34d; }
	.risk-high { background: #7f1d1d; color: #fca5a5; }
	.risk-critical { background: #450a0a; color: #f87171; border: 1px solid #dc2626; }

	/* Blocking Issues */
	.blocking-issue {
		padding: var(--space-md);
		background: var(--card-bg-secondary);
		border-radius: 8px;
		margin-bottom: var(--space-md);
		border-left: 4px solid var(--error-text);
	}

	.issue-header {
		margin-bottom: var(--space-sm);
	}

	.severity-badge {
		padding: 2px 8px;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
	}

	.severity-low { background: #1a4731; color: #6ee7b7; }
	.severity-medium { background: #713f12; color: #fcd34d; }
	.severity-high { background: #7f1d1d; color: #fca5a5; }
	.severity-critical { background: #450a0a; color: #f87171; }

	.issue-text {
		color: var(--text-primary);
		line-height: 1.6;
		margin: 0 0 var(--space-md) 0;
	}

	.resolution {
		padding: var(--space-sm) var(--space-md);
		background: rgba(0, 0, 0, 0.2);
		border-radius: 6px;
	}

	.resolution h5 {
		margin: 0 0 var(--space-xs) 0;
		font-size: 0.85rem;
		color: var(--primary-dark);
		font-weight: 600;
	}

	.resolution p {
		margin: 0;
		font-size: 0.9rem;
		color: var(--text-secondary);
		line-height: 1.5;
	}

	/* Key Risks Grid */
	.risks-grid {
		display: grid;
		gap: var(--space-md);
	}

	.risk-card {
		padding: var(--space-md);
		background: var(--card-bg-secondary);
		border-radius: 8px;
		border-left: 4px solid var(--warning-text);
	}

	.risk-card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-sm);
	}

	.risk-category {
		font-weight: 600;
		color: var(--text-primary);
	}

	.risk-summary {
		margin: 0;
		color: var(--text-secondary);
		line-height: 1.6;
	}

	/* Recommendations */
	.recommendation-item {
		padding: var(--space-md);
		background: var(--card-bg-secondary);
		border-radius: 8px;
		margin-bottom: var(--space-md);
		border-left: 4px solid var(--primary-dark);
	}

	.rec-header {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		margin-bottom: var(--space-sm);
	}

	.priority-badge {
		background: var(--primary-dark);
		color: white;
		padding: 2px 8px;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.rec-category {
		font-size: 0.85rem;
		color: var(--text-muted);
		font-weight: 500;
	}

	.rec-action {
		margin: 0;
		color: var(--text-secondary);
		line-height: 1.6;
	}

	/* Legacy Legal Sections */
	.legal-grid {
		display: grid;
		gap: var(--space-lg);
	}

	.legal-item h4 {
		color: var(--primary-dark);
		margin: 0 0 var(--space-sm) 0;
		font-size: 1rem;
		font-weight: 600;
	}

	.legal-item p {
		margin: 0;
		line-height: 1.6;
		color: var(--text-secondary);
	}

	.regulatory-item {
		padding: var(--space-md);
		background: var(--card-bg-secondary);
		border-radius: 8px;
		margin-bottom: var(--space-md);
	}

	.regulatory-item h4 {
		margin: 0 0 var(--space-xs) 0;
		color: var(--primary-dark);
		font-size: 1rem;
		font-weight: 600;
	}

	.regulatory-item p {
		color: var(--text-secondary);
	}

	.regulatory-item .meta {
		font-size: 0.85em;
		color: var(--text-muted);
		margin: 0 0 var(--space-sm) 0;
	}

	.regulatory-item ul {
		margin: var(--space-sm) 0 0 0;
		padding-left: var(--space-lg);
		color: var(--text-secondary);
	}

	.regulatory-item li {
		margin-bottom: var(--space-xs);
	}

	.privacy-section h4 {
		color: var(--primary-dark);
		margin: var(--space-md) 0 var(--space-sm) 0;
		font-size: 1rem;
		font-weight: 600;
	}

	.privacy-section h4:first-child {
		margin-top: 0;
	}

	.privacy-section p {
		color: var(--text-secondary);
	}

	.privacy-section ul {
		margin: 0;
		padding-left: var(--space-lg);
		color: var(--text-secondary);
	}

	.privacy-section li {
		margin-bottom: var(--space-xs);
	}
</style>
