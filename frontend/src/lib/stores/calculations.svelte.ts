/**
 * Calculations Store
 *
 * Derived calculations using Svelte 5 $derived rune.
 * Computes valuation metrics from model inputs.
 */

import type { ValuationResult, CostOfCapitalResult, SegmentProjections } from '$lib/services/api';

/**
 * Calculations State Class
 *
 * Stores results from backend calculations.
 */
export class CalculationsState {
	// Raw result from API
	result = $state<ValuationResult | null>(null);

	// Loading and error state
	isLoading = $state(false);
	error = $state<string | null>(null);

	// Cost of capital derived values
	costOfCapital = $derived<CostOfCapitalResult | null>(() => {
		return this.result?.cost_of_capital ?? null;
	});

	// Segment projections
	segmentProjections = $derived<SegmentProjections[]>(() => {
		return this.result?.segment_projections ?? [];
	});

	// Key valuation metrics
	wacc = $derived(() => {
		return this.costOfCapital?.wacc ?? 0;
	});

	stableWacc = $derived(() => {
		return this.costOfCapital?.stable_wacc ?? 0;
	});

	costOfEquity = $derived(() => {
		return this.costOfCapital?.cost_of_equity ?? 0;
	});

	leveredBeta = $derived(() => {
		return this.costOfCapital?.levered_beta ?? 0;
	});

	// Valuation bridge values
	pvFcffTotal = $derived(() => {
		return this.result?.pv_fcff_total ?? 0;
	});

	pvTerminalTotal = $derived(() => {
		return this.result?.pv_terminal_total ?? 0;
	});

	goingConcernValue = $derived(() => {
		return this.result?.going_concern_value ?? 0;
	});

	failureAdjustment = $derived(() => {
		return this.result?.failure_adjustment ?? 0;
	});

	operatingAssetsValue = $derived(() => {
		return this.result?.operating_assets_value ?? 0;
	});

	debt = $derived(() => {
		return this.result?.debt ?? 0;
	});

	cash = $derived(() => {
		return this.result?.cash ?? 0;
	});

	minorityInterests = $derived(() => {
		return this.result?.minority_interests ?? 0;
	});

	nonOperatingAssets = $derived(() => {
		return this.result?.non_operating_assets ?? 0;
	});

	equityValue = $derived(() => {
		return this.result?.equity_value ?? 0;
	});

	optionValue = $derived(() => {
		return this.result?.option_value ?? 0;
	});

	equityInCommon = $derived(() => {
		return this.result?.equity_in_common ?? 0;
	});

	sharesOutstanding = $derived(() => {
		return this.result?.shares_outstanding ?? 0;
	});

	valuePerShare = $derived(() => {
		return this.result?.value_per_share ?? 0;
	});

	currentPrice = $derived(() => {
		return this.result?.current_price ?? 0;
	});

	priceToValue = $derived(() => {
		return this.result?.price_to_value ?? 0;
	});

	// R&D adjustments
	rdAssetValue = $derived(() => {
		return this.result?.rd_asset_value ?? 0;
	});

	rdAmortization = $derived(() => {
		return this.result?.rd_amortization ?? 0;
	});

	rdOperatingAdjustment = $derived(() => {
		return this.result?.rd_operating_adjustment ?? 0;
	});

	// Computed helpers
	isUndervalued = $derived(() => {
		const ptv = this.priceToValue;
		return ptv > 0 && ptv < 1;
	});

	isOvervalued = $derived(() => {
		const ptv = this.priceToValue;
		return ptv > 1;
	});

	upside = $derived(() => {
		if (this.currentPrice === 0) return 0;
		return ((this.valuePerShare - this.currentPrice) / this.currentPrice) * 100;
	});

	// Total segment value
	totalSegmentValue = $derived(() => {
		return this.segmentProjections.reduce((sum, seg) => sum + seg.segment_value, 0);
	});

	// Segment value breakdown
	segmentValueBreakdown = $derived(() => {
		const total = this.totalSegmentValue;
		if (total === 0) return [];

		return this.segmentProjections.map((seg) => ({
			name: seg.segment_name,
			type: seg.segment_type,
			value: seg.segment_value,
			percentage: (seg.segment_value / total) * 100,
			terminalValue: seg.terminal_value,
			pvTerminal: seg.pv_terminal,
		}));
	});

	/**
	 * Load calculation result from API
	 */
	setResult(result: ValuationResult) {
		this.result = result;
		this.isLoading = false;
		this.error = null;
	}

	/**
	 * Set loading state
	 */
	setLoading(loading: boolean) {
		this.isLoading = loading;
		if (loading) {
			this.error = null;
		}
	}

	/**
	 * Set error state
	 */
	setError(error: string) {
		this.error = error;
		this.isLoading = false;
	}

	/**
	 * Clear all results
	 */
	clear() {
		this.result = null;
		this.isLoading = false;
		this.error = null;
	}
}

// Create singleton instance
export const calculationsState = new CalculationsState();
