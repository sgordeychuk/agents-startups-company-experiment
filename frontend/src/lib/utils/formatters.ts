/**
 * Format a number as currency (USD)
 */
export function formatCurrency(value: number, decimals = 2): string {
	return `$${value.toFixed(decimals)}`;
}

/**
 * Format a number with thousands separators
 */
export function formatNumber(value: number): string {
	return value.toLocaleString();
}

/**
 * Format milliseconds as a human-readable duration
 */
export function formatDuration(ms: number): string {
	if (ms < 1000) {
		return `${ms}ms`;
	}
	const seconds = ms / 1000;
	if (seconds < 60) {
		return `${seconds.toFixed(1)}s`;
	}
	const minutes = seconds / 60;
	if (minutes < 60) {
		return `${minutes.toFixed(1)}min`;
	}
	const hours = minutes / 60;
	return `${hours.toFixed(1)}h`;
}

/**
 * Format a percentage
 */
export function formatPercent(value: number, decimals = 1): string {
	return `${value.toFixed(decimals)}%`;
}

/**
 * Format an ISO date string as a readable date
 */
export function formatDate(dateStr: string): string {
	try {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	} catch {
		return dateStr;
	}
}

/**
 * Format an experiment ID into a readable name
 */
export function formatExperimentName(id: string): string {
	if (id.startsWith('experiment_')) {
		const timestamp = id.replace('experiment_', '');
		return `Experiment ${formatTimestamp(timestamp)}`;
	}
	if (id.startsWith('stage_run_')) {
		const parts = id.replace('stage_run_', '').split('_');
		const stageName = parts.slice(0, -2).join('_');
		const timestamp = parts.slice(-2).join('_');
		return `${formatStageName(stageName)} (${formatTimestamp(timestamp)})`;
	}
	return id;
}

/**
 * Format a timestamp string (YYYYMMDD_HHMMSS) into a readable date
 */
export function formatTimestamp(timestamp: string): string {
	try {
		const [date, time] = timestamp.split('_');
		const year = date.slice(0, 4);
		const month = date.slice(4, 6);
		const day = date.slice(6, 8);
		const hour = time.slice(0, 2);
		const minute = time.slice(2, 4);
		return `${year}-${month}-${day} ${hour}:${minute}`;
	} catch {
		return timestamp;
	}
}

/**
 * Format a stage name for display
 */
export function formatStageName(stage: string): string {
	return stage
		.split('_')
		.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
		.join(' ');
}

/**
 * Truncate text to a maximum length
 */
export function truncate(text: string, maxLength: number): string {
	if (text.length <= maxLength) return text;
	return text.slice(0, maxLength - 3) + '...';
}

/**
 * Get the recommendation badge class
 */
export function getRecommendationClass(recommendation: string): string {
	switch (recommendation?.toUpperCase()) {
		case 'GO':
			return 'badge-success';
		case 'PASS':
		case 'NO-GO':
			return 'badge-error';
		case 'PIVOT':
			return 'badge-warning';
		default:
			return 'badge-neutral';
	}
}

/**
 * Get HTTP method badge class
 */
export function getMethodClass(method: string): string {
	switch (method?.toUpperCase()) {
		case 'GET':
			return 'badge-success';
		case 'POST':
			return 'badge-primary';
		case 'PUT':
		case 'PATCH':
			return 'badge-warning';
		case 'DELETE':
			return 'badge-error';
		default:
			return 'badge-neutral';
	}
}
