import { json } from '@sveltejs/kit';
import { readFile } from 'fs/promises';
import { join } from 'path';
import type { RequestHandler } from './$types';

const TEST_RESULTS_DIR = join(process.cwd(), '..', 'test_results');

export const GET: RequestHandler = async ({ params }) => {
	try {
		const testPath = join(TEST_RESULTS_DIR, `${params.id}.json`);
		const testData = await readFile(testPath, 'utf-8');
		return json({ id: params.id, ...JSON.parse(testData) });
	} catch (error) {
		console.error('Error loading test result:', error);
		return json({ error: 'Failed to load test result' }, { status: 500 });
	}
};
