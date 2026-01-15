import { json } from '@sveltejs/kit';
import { readFile } from 'fs/promises';
import { join } from 'path';
import type { RequestHandler } from './$types';

const EXPERIMENTS_DIR = join(process.cwd(), '..', 'experiments');

export const GET: RequestHandler = async ({ params }) => {
	try {
		const contextPath = join(EXPERIMENTS_DIR, params.id, `context_${params.stage}.json`);
		const contextData = await readFile(contextPath, 'utf-8');
		return json(JSON.parse(contextData));
	} catch (error) {
		console.error('Error loading context:', error);
		return json({ error: 'Failed to load context' }, { status: 500 });
	}
};
