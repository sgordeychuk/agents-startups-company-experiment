import { json } from '@sveltejs/kit';
import { readdir, readFile, stat } from 'fs/promises';
import { join } from 'path';
import type { RequestHandler } from './$types';
import type { ExperimentContext } from '$types';

const EXPERIMENTS_DIR = join(process.cwd(), '..', 'experiments');

/**
 * Populate stage_outputs from direct state properties if empty.
 * This handles backwards compatibility with experiments created before
 * stage_outputs was properly populated by the pipeline.
 */
function normalizeContext(context: ExperimentContext): ExperimentContext {
	if (!context?.state) return context;

	const state = context.state;
	const stageOutputs = state.stage_outputs || {};

	// Populate idea_development from direct state if missing
	if (!stageOutputs.idea_development && state.idea) {
		stageOutputs.idea_development = {
			idea: state.idea,
			research: state.research,
			final_validation: state.research_final || state.research,
			legal_insights: state.legal_insights ?? undefined,
			refinement_feedback: state.refinement_feedback
		};
	}

	// Populate prototyping from direct state if missing
	if (!stageOutputs.prototyping && state.prototype) {
		stageOutputs.prototyping = {
			architecture: state.architecture,
			design: state.design,
			final_designs: state.final_designs,
			prototype: state.prototype
		};
	}

	// Populate pitch from direct state if missing
	if (!stageOutputs.pitch && state.pitch) {
		stageOutputs.pitch = {
			marketing_strategies: state.marketing_strategies,
			pitch_deck: state.pitch
		};
	}

	return {
		...context,
		state: {
			...state,
			stage_outputs: stageOutputs
		}
	};
}

export const GET: RequestHandler = async ({ params }) => {
	try {
		const expDir = join(EXPERIMENTS_DIR, params.id);
		const files = await readdir(expDir);

		const dirStat = await stat(expDir);
		const contextFiles = files.filter((f) => f.endsWith('.json'));
		const hasStatistics = files.includes('statistics.json');
		const hasFinalContext = files.includes('context_final.json');
		const hasResults = files.includes('results.json');

		const experiment = {
			id: params.id,
			type: params.id.startsWith('experiment_') ? 'full' : 'stage_run',
			hasStatistics,
			hasCompleteContext: hasFinalContext,
			hasResults,
			contextFiles,
			timestamp: dirStat.mtime.toISOString(),
			subfolders: files.filter((f) => !f.includes('.'))
		};

		if (hasFinalContext) {
			const contextPath = join(expDir, 'context_final.json');
			const contextData = await readFile(contextPath, 'utf-8');
			const context = normalizeContext(JSON.parse(contextData));
			return json({ ...experiment, context });
		} else if (hasResults) {
			const resultsPath = join(expDir, 'results.json');
			const resultsData = await readFile(resultsPath, 'utf-8');
			const results = JSON.parse(resultsData);
			if (results.full_context) {
				results.full_context = normalizeContext(results.full_context);
			}
			return json({ ...experiment, results });
		} else {
			const firstContext = contextFiles.find((f) => f.startsWith('context_'));
			if (firstContext) {
				const contextPath = join(expDir, firstContext);
				const contextData = await readFile(contextPath, 'utf-8');
				const context = normalizeContext(JSON.parse(contextData));
				return json({ ...experiment, context });
			}
		}

		return json(experiment);
	} catch (error) {
		console.error('Error loading experiment:', error);
		return json({ error: 'Failed to load experiment' }, { status: 500 });
	}
};
