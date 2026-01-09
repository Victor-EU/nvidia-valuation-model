/**
 * Formatting Utilities
 *
 * Number, currency, and percentage formatting helpers.
 */

/**
 * Format a number as currency
 */
export function formatCurrency(
	value: number,
	currency = 'USD',
	decimals = 0,
	compact = false
): string {
	if (!Number.isFinite(value)) return '—';

	const options: Intl.NumberFormatOptions = {
		style: 'currency',
		currency,
		minimumFractionDigits: decimals,
		maximumFractionDigits: decimals,
	};

	if (compact && Math.abs(value) >= 1e9) {
		return `$${(value / 1e9).toFixed(1)}B`;
	}
	if (compact && Math.abs(value) >= 1e6) {
		return `$${(value / 1e6).toFixed(1)}M`;
	}

	return new Intl.NumberFormat('en-US', options).format(value);
}

/**
 * Format a number as percentage
 */
export function formatPercent(value: number, decimals = 2): string {
	if (!Number.isFinite(value)) return '—';

	return new Intl.NumberFormat('en-US', {
		style: 'percent',
		minimumFractionDigits: decimals,
		maximumFractionDigits: decimals,
	}).format(value);
}

/**
 * Format a number with thousands separators
 */
export function formatNumber(value: number, decimals = 0): string {
	if (!Number.isFinite(value)) return '—';

	return new Intl.NumberFormat('en-US', {
		minimumFractionDigits: decimals,
		maximumFractionDigits: decimals,
	}).format(value);
}

/**
 * Format a number in compact notation (e.g., 1.2M, 3.4B)
 */
export function formatCompact(value: number): string {
	if (!Number.isFinite(value)) return '—';

	const absValue = Math.abs(value);
	const sign = value < 0 ? '-' : '';

	if (absValue >= 1e12) {
		return `${sign}${(absValue / 1e12).toFixed(2)}T`;
	}
	if (absValue >= 1e9) {
		return `${sign}${(absValue / 1e9).toFixed(2)}B`;
	}
	if (absValue >= 1e6) {
		return `${sign}${(absValue / 1e6).toFixed(2)}M`;
	}
	if (absValue >= 1e3) {
		return `${sign}${(absValue / 1e3).toFixed(2)}K`;
	}

	return formatNumber(value, 2);
}

/**
 * Format a multiplier (e.g., 1.23x)
 */
export function formatMultiple(value: number, decimals = 2): string {
	if (!Number.isFinite(value)) return '—';
	return `${value.toFixed(decimals)}x`;
}

/**
 * Parse a formatted number string back to a number
 */
export function parseFormattedNumber(value: string): number {
	if (!value) return 0;

	// Remove currency symbols, commas, and whitespace
	const cleaned = value.replace(/[$,\s]/g, '');

	// Handle percentage
	if (cleaned.endsWith('%')) {
		return parseFloat(cleaned) / 100;
	}

	// Handle compact notation
	const match = cleaned.match(/^(-?\d+\.?\d*)(K|M|B|T)?$/i);
	if (match) {
		const num = parseFloat(match[1]);
		const suffix = match[2]?.toUpperCase();
		const multipliers: Record<string, number> = {
			K: 1e3,
			M: 1e6,
			B: 1e9,
			T: 1e12,
		};
		return num * (suffix ? multipliers[suffix] : 1);
	}

	return parseFloat(cleaned) || 0;
}

/**
 * Format a date
 */
export function formatDate(date: string | Date): string {
	const d = typeof date === 'string' ? new Date(date) : date;
	return d.toLocaleDateString('en-US', {
		year: 'numeric',
		month: 'short',
		day: 'numeric',
	});
}

/**
 * Get CSS class for positive/negative values
 */
export function getValueClass(value: number): string {
	if (value > 0) return 'value-positive';
	if (value < 0) return 'value-negative';
	return '';
}

/**
 * Format basis points
 */
export function formatBasisPoints(value: number): string {
	if (!Number.isFinite(value)) return '—';
	return `${(value * 10000).toFixed(0)} bps`;
}
