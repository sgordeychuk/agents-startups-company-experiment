import { error } from '@sveltejs/kit';
import { readFile, access } from 'fs/promises';
import { join } from 'path';
import type { RequestHandler } from './$types';

const EXPERIMENTS_DIR = join(process.cwd(), '..', 'experiments');

export const GET: RequestHandler = async ({ params }) => {
	const { id, filename } = params;

	if (!id || !filename) {
		throw error(400, 'Missing experiment ID or filename');
	}

	// Prevent directory traversal attacks
	if (id.includes('..') || filename.includes('..')) {
		throw error(400, 'Invalid path');
	}

	const imagePath = join(EXPERIMENTS_DIR, id, 'designs', filename);

	try {
		await access(imagePath);
		const imageBuffer = await readFile(imagePath);

		// Determine content type based on extension
		const ext = filename.toLowerCase().split('.').pop();
		let contentType = 'image/png';
		if (ext === 'jpg' || ext === 'jpeg') {
			contentType = 'image/jpeg';
		} else if (ext === 'gif') {
			contentType = 'image/gif';
		} else if (ext === 'webp') {
			contentType = 'image/webp';
		}

		return new Response(imageBuffer, {
			headers: {
				'Content-Type': contentType,
				'Cache-Control': 'public, max-age=3600'
			}
		});
	} catch (e) {
		throw error(404, 'Image not found');
	}
};
