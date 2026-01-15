import { json } from '@sveltejs/kit';
import { readdir, readFile } from 'fs/promises';
import { join } from 'path';
import type { RequestHandler } from './$types';

const TEST_RESULTS_DIR = join(process.cwd(), '..', 'test_results');

export const GET: RequestHandler = async () => {
	try {
		const files = await readdir(TEST_RESULTS_DIR);
		const jsonFiles = files.filter((f) => f.endsWith('.json') && !f.includes('latest'));

		const testResults = await Promise.all(
			jsonFiles.map(async (file) => {
				try {
					const content = await readFile(join(TEST_RESULTS_DIR, file), 'utf-8');
					const data = JSON.parse(content);
					return {
						id: file.replace('.json', ''),
						filename: file,
						stage_name: data.stage_name,
						test_name: data.test_name,
						agent_name: data.agent_name,
						test_type: data.test_type,
						timestamp: data.timestamp || data.timestamp_start,
						execution_time_ms: data.execution_time_ms,
						success: data.success
					};
				} catch {
					return null;
				}
			})
		);

		const validResults = testResults.filter(Boolean);
		validResults.sort((a, b) => {
			const aTime = a?.timestamp || a?.id || '';
			const bTime = b?.timestamp || b?.id || '';
			return bTime.localeCompare(aTime);
		});

		return json(validResults);
	} catch (error) {
		console.error('Error loading test results:', error);
		return json({ error: 'Failed to load test results' }, { status: 500 });
	}
};
