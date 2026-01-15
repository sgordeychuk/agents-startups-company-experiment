import { json } from '@sveltejs/kit';
import { readdir, stat } from 'fs/promises';
import { join } from 'path';
import type { RequestHandler } from './$types';

const EXPERIMENTS_DIR = join(process.cwd(), '..', 'experiments');

export const GET: RequestHandler = async () => {
	try {
		const entries = await readdir(EXPERIMENTS_DIR, { withFileTypes: true });
		const experiments = [];

		for (const entry of entries) {
			if (entry.isDirectory() && !entry.name.startsWith('.')) {
				const expDir = join(EXPERIMENTS_DIR, entry.name);
				const files = await readdir(expDir);

				const contextFiles = files.filter((f) => f.endsWith('.json'));
				const hasStatistics = files.includes('statistics.json');
				const hasFinalContext = files.includes('context_final.json');
				const hasResults = files.includes('results.json');

				const dirStat = await stat(expDir);

				experiments.push({
					id: entry.name,
					type: entry.name.startsWith('stage_run_') ? 'stage_run' : 'full',
					hasStatistics,
					hasCompleteContext: hasFinalContext,
					hasResults,
					contextFiles,
					timestamp: dirStat.mtime.toISOString()
				});
			}
		}

		experiments.sort((a, b) => b.id.localeCompare(a.id));

		return json(experiments);
	} catch (error) {
		console.error('Error loading experiments:', error);
		return json({ error: 'Failed to load experiments' }, { status: 500 });
	}
};
