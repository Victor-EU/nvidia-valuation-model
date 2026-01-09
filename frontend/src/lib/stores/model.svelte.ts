/**
 * Valuation Model Store
 *
 * Main state management using Svelte 5 runes.
 * Holds all input data for the DCF valuation model.
 */

import type { OperatingCountry, BusinessSegment, CostOfCapitalSettings } from '$lib/services/api';

// Base year data interface
export interface BaseYearData {
	revenues: number;
	operating_income: number;
	interest_expense: number;
	book_equity: number;
	book_debt: number;
	cash: number;
	cross_holdings: number;
	minority_interests: number;
	shares: number;
	stock_price: number;
	effective_tax_rate: number;
	marginal_tax_rate: number;
}

// Value drivers interface
export interface ValueDrivers {
	revenue_growth_yr1: number;
	operating_margin_yr1: number;
	compounded_growth_2_5: number;
	target_margin: number;
	convergence_year: number;
	sales_to_capital_1_5: number;
	sales_to_capital_6_10: number;
}

// Market inputs interface
export interface MarketInputs {
	risk_free_rate: number;
	country: string;
	industry_us: string;
	industry_global: string;
}

// R&D settings interface
export interface RDSettings {
	capitalize_rd: boolean;
	amortization_years: number;
	current_rd: number;
	rd_expenses: number[];
}

// Option settings interface
export interface OptionSettings {
	has_options: boolean;
	num_options: number;
	avg_strike: number;
	avg_maturity: number;
	std_dev: number;
}

// Override settings interface
export interface Overrides {
	override_stable_coc: boolean;
	stable_coc: number;
	override_stable_roic: boolean;
	stable_roic: number;
	override_failure: boolean;
	failure_prob: number;
	distress_proceeds_type: 'B' | 'V';
	distress_proceeds_pct: number;
	override_nol: boolean;
	nol: number;
	reinvestment_lag: number;
	override_growth: boolean;
	perpetual_growth: number;
}

// Segment input interface
export interface SegmentInput {
	id?: string;
	name: string;
	segment_type: 'rest' | 'ai' | 'auto';
	segment_order: number;
	total_market_current?: number;
	total_market_year10?: number;
	market_share_current?: number;
	market_share_year10?: number;
	operating_margin_current?: number;
	operating_margin_year10?: number;
}

// Default values
function createDefaultBaseYearData(): BaseYearData {
	return {
		revenues: 0,
		operating_income: 0,
		interest_expense: 0,
		book_equity: 0,
		book_debt: 0,
		cash: 0,
		cross_holdings: 0,
		minority_interests: 0,
		shares: 0,
		stock_price: 0,
		effective_tax_rate: 0.21,
		marginal_tax_rate: 0.25,
	};
}

function createDefaultValueDrivers(): ValueDrivers {
	return {
		revenue_growth_yr1: 0.10,
		operating_margin_yr1: 0.20,
		compounded_growth_2_5: 0.10,
		target_margin: 0.20,
		convergence_year: 5,
		sales_to_capital_1_5: 2.0,
		sales_to_capital_6_10: 2.0,
	};
}

function createDefaultMarketInputs(): MarketInputs {
	return {
		risk_free_rate: 0.045,
		country: 'United States',
		industry_us: 'Semiconductor',
		industry_global: 'Semiconductor',
	};
}

function createDefaultRDSettings(): RDSettings {
	return {
		capitalize_rd: false,
		amortization_years: 5,
		current_rd: 0,
		rd_expenses: [],
	};
}

function createDefaultOptionSettings(): OptionSettings {
	return {
		has_options: false,
		num_options: 0,
		avg_strike: 0,
		avg_maturity: 5,
		std_dev: 0.40,
	};
}

function createDefaultOverrides(): Overrides {
	return {
		override_stable_coc: false,
		stable_coc: 0.08,
		override_stable_roic: false,
		stable_roic: 0.10,
		override_failure: false,
		failure_prob: 0,
		distress_proceeds_type: 'V',
		distress_proceeds_pct: 0.5,
		override_nol: false,
		nol: 0,
		reinvestment_lag: 1,
		override_growth: false,
		perpetual_growth: 0.025,
	};
}

function createDefaultCostOfCapital(): CostOfCapitalSettings {
	return {
		approach: 'detailed',
		direct_coc: null,
		beta_approach: 'single_business_us',
		direct_beta: null,
		erp_approach: 'operating_countries',
		direct_erp: null,
		operating_countries: [],
		debt_approach: 'synthetic',
		actual_rating: null,
		firm_type: 1,
		debt_maturity: 3,
		preferred_shares: null,
		preferred_price: null,
		preferred_dividend: null,
	};
}

/**
 * Valuation Model State Class
 *
 * Uses Svelte 5 $state rune for reactive state management.
 */
export class ValuationModelState {
	// Model metadata
	id = $state<string | null>(null);
	name = $state('New Valuation Model');
	companyName = $state('');
	valuationDate = $state(new Date().toISOString().split('T')[0]);
	currency = $state('USD');

	// Input sections
	baseYearData = $state<BaseYearData>(createDefaultBaseYearData());
	valueDrivers = $state<ValueDrivers>(createDefaultValueDrivers());
	marketInputs = $state<MarketInputs>(createDefaultMarketInputs());
	rdSettings = $state<RDSettings>(createDefaultRDSettings());
	optionSettings = $state<OptionSettings>(createDefaultOptionSettings());
	overrides = $state<Overrides>(createDefaultOverrides());

	// Business segments
	segments = $state<SegmentInput[]>([
		{
			name: 'Rest of Business',
			segment_type: 'rest',
			segment_order: 0,
		},
	]);

	// Cost of capital settings
	costOfCapital = $state<CostOfCapitalSettings>(createDefaultCostOfCapital());

	// UI state
	isDirty = $state(false);
	isCalculating = $state(false);
	lastCalculated = $state<Date | null>(null);

	/**
	 * Reset to default values
	 */
	reset() {
		this.id = null;
		this.name = 'New Valuation Model';
		this.companyName = '';
		this.valuationDate = new Date().toISOString().split('T')[0];
		this.currency = 'USD';
		this.baseYearData = createDefaultBaseYearData();
		this.valueDrivers = createDefaultValueDrivers();
		this.marketInputs = createDefaultMarketInputs();
		this.rdSettings = createDefaultRDSettings();
		this.optionSettings = createDefaultOptionSettings();
		this.overrides = createDefaultOverrides();
		this.segments = [
			{
				name: 'Rest of Business',
				segment_type: 'rest',
				segment_order: 0,
			},
		];
		this.costOfCapital = createDefaultCostOfCapital();
		this.isDirty = false;
		this.isCalculating = false;
		this.lastCalculated = null;
	}

	/**
	 * Load from API response
	 */
	loadFromApi(data: {
		id: string;
		name: string;
		company_name: string | null;
		valuation_date: string | null;
		currency: string;
		base_year_data: Record<string, number>;
		value_drivers: Record<string, number>;
		market_inputs: Record<string, unknown>;
		rd_settings: Record<string, unknown>;
		option_settings: Record<string, unknown>;
		overrides: Record<string, unknown>;
		segments: BusinessSegment[];
		cost_of_capital: CostOfCapitalSettings | null;
	}) {
		this.id = data.id;
		this.name = data.name;
		this.companyName = data.company_name || '';
		this.valuationDate = data.valuation_date || new Date().toISOString().split('T')[0];
		this.currency = data.currency;

		// Merge with defaults to ensure all fields are present
		this.baseYearData = { ...createDefaultBaseYearData(), ...data.base_year_data };
		this.valueDrivers = { ...createDefaultValueDrivers(), ...data.value_drivers };
		this.marketInputs = {
			...createDefaultMarketInputs(),
			...(data.market_inputs as Partial<MarketInputs>),
		};
		this.rdSettings = {
			...createDefaultRDSettings(),
			...(data.rd_settings as Partial<RDSettings>),
		};
		this.optionSettings = {
			...createDefaultOptionSettings(),
			...(data.option_settings as Partial<OptionSettings>),
		};
		this.overrides = {
			...createDefaultOverrides(),
			...(data.overrides as Partial<Overrides>),
		};

		// Load segments
		this.segments = data.segments.map((seg) => ({
			id: seg.id,
			name: seg.name,
			segment_type: seg.segment_type as 'rest' | 'ai' | 'auto',
			segment_order: seg.segment_order,
			...seg.inputs,
		}));

		// Load cost of capital
		if (data.cost_of_capital) {
			this.costOfCapital = { ...createDefaultCostOfCapital(), ...data.cost_of_capital };
		}

		this.isDirty = false;
	}

	/**
	 * Convert to API format for saving
	 */
	toApiFormat() {
		return {
			name: this.name,
			company_name: this.companyName || null,
			valuation_date: this.valuationDate,
			currency: this.currency,
			base_year_data: this.baseYearData,
			value_drivers: this.valueDrivers,
			market_inputs: this.marketInputs,
			rd_settings: this.rdSettings,
			option_settings: this.optionSettings,
			overrides: this.overrides,
			segments: this.segments.map((seg) => ({
				name: seg.name,
				segment_type: seg.segment_type,
				segment_order: seg.segment_order,
				inputs: {
					total_market_current: seg.total_market_current,
					total_market_year10: seg.total_market_year10,
					market_share_current: seg.market_share_current,
					market_share_year10: seg.market_share_year10,
					operating_margin_current: seg.operating_margin_current,
					operating_margin_year10: seg.operating_margin_year10,
				},
			})),
			cost_of_capital: this.costOfCapital,
		};
	}

	/**
	 * Add a new segment
	 */
	addSegment(type: 'ai' | 'auto') {
		const names = {
			ai: 'AI Chips',
			auto: 'Auto Chips',
		};
		this.segments = [
			...this.segments,
			{
				name: names[type],
				segment_type: type,
				segment_order: this.segments.length,
				total_market_current: 0,
				total_market_year10: 0,
				market_share_current: 0,
				market_share_year10: 0,
				operating_margin_current: 0.20,
				operating_margin_year10: 0.20,
			},
		];
		this.isDirty = true;
	}

	/**
	 * Remove a segment
	 */
	removeSegment(index: number) {
		if (this.segments[index]?.segment_type === 'rest') {
			return; // Cannot remove the base segment
		}
		this.segments = this.segments.filter((_, i) => i !== index);
		this.isDirty = true;
	}

	/**
	 * Add operating country
	 */
	addOperatingCountry(country: string, revenues: number) {
		this.costOfCapital.operating_countries = [
			...this.costOfCapital.operating_countries,
			{ country, revenues },
		];
		this.isDirty = true;
	}

	/**
	 * Remove operating country
	 */
	removeOperatingCountry(index: number) {
		this.costOfCapital.operating_countries = this.costOfCapital.operating_countries.filter(
			(_, i) => i !== index
		);
		this.isDirty = true;
	}

	/**
	 * Mark as dirty when any value changes
	 */
	markDirty() {
		this.isDirty = true;
	}
}

// Create singleton instance
export const modelState = new ValuationModelState();
