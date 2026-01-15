import { json } from '@sveltejs/kit';
import { readFile } from 'fs/promises';
import { join } from 'path';
import type { RequestHandler } from './$types';

const EXPERIMENTS_DIR = join(process.cwd(), '..', 'experiments');

export const GET: RequestHandler = async ({ params }) => {
	try {
		const statsPath = join(EXPERIMENTS_DIR, params.id, 'statistics.json');
		const statsData = await readFile(statsPath, 'utf-8');
		return json(JSON.parse(statsData));
	} catch (error) {
		console.error('Error loading statistics:', error);
		return json({ error: 'Statistics not found' }, { status: 404 });
	}
};
