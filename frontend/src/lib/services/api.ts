/**
 * API Service
 *
 * Client for communicating with the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RequestOptions {
	method?: string;
	body?: unknown;
	headers?: Record<string, string>;
}

class ApiError extends Error {
	constructor(
		public status: number,
		public statusText: string,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
	const { method = 'GET', body, headers = {} } = options;

	const config: RequestInit = {
		method,
		headers: {
			'Content-Type': 'application/json',
			...headers,
		},
	};

	if (body) {
		config.body = JSON.stringify(body);
	}

	const response = await fetch(`${API_BASE}${endpoint}`, config);

	if (!response.ok) {
		let errorMessage = response.statusText;
		try {
			const errorData = await response.json();
			errorMessage = errorData.detail || errorMessage;
		} catch {
			// Use default error message
		}
		throw new ApiError(response.status, response.statusText, errorMessage);
	}

	return response.json();
}

// Type definitions
export interface Country {
	id: number;
	name: string;
	moodys_rating: string | null;
	adj_default_spread: number | null;
	equity_risk_premium: number | null;
	country_risk_premium: number | null;
	corporate_tax_rate: number | null;
}

export interface Industry {
	id: number;
	name: string;
	region: string;
	num_firms: number | null;
	revenue_growth_5yr: number | null;
	operating_margin: number | null;
	after_tax_roc: number | null;
	effective_tax_rate: number | null;
	unlevered_beta: number | null;
	levered_beta: number | null;
	cost_of_equity: number | null;
	std_dev_stock: number | null;
	pretax_cost_of_debt: number | null;
	debt_to_capital: number | null;
	cost_of_capital: number | null;
	sales_to_capital: number | null;
}

export interface RatingSpread {
	rating: string;
	spread: number;
}

export interface ValuationModelSummary {
	id: string;
	name: string;
	company_name: string | null;
	valuation_date: string | null;
	currency: string;
	created_at: string;
	updated_at: string;
}

export interface OperatingCountry {
	country: string;
	revenues: number;
}

export interface CostOfCapitalSettings {
	approach: string;
	direct_coc: number | null;
	beta_approach: string;
	direct_beta: number | null;
	erp_approach: string;
	direct_erp: number | null;
	operating_countries: OperatingCountry[];
	debt_approach: string;
	actual_rating: string | null;
	firm_type: number;
	debt_maturity: number;
	preferred_shares: number | null;
	preferred_price: number | null;
	preferred_dividend: number | null;
}

export interface BusinessSegment {
	id: string;
	name: string;
	segment_type: string;
	segment_order: number;
	inputs: Record<string, number>;
}

export interface ValuationModel {
	id: string;
	name: string;
	company_name: string | null;
	valuation_date: string | null;
	currency: string;
	base_year_data: Record<string, number>;
	value_drivers: Record<string, number>;
	market_inputs: Record<string, unknown>;
	rd_settings: Record<string, unknown>;
	lease_settings: Record<string, unknown>;
	option_settings: Record<string, unknown>;
	overrides: Record<string, unknown>;
	segments: BusinessSegment[];
	cost_of_capital: CostOfCapitalSettings | null;
}

export interface YearProjection {
	year: number;
	revenue_growth: number;
	revenues: number;
	operating_margin: number;
	ebit: number;
	ebit_1_t: number;
	reinvestment: number;
	fcff: number;
	cost_of_capital: number;
	discount_factor: number;
	pv_fcff: number;
}

export interface SegmentProjections {
	segment_name: string;
	segment_type: string;
	projections: YearProjection[];
	terminal_value: number;
	pv_terminal: number;
	segment_value: number;
}

export interface CostOfCapitalResult {
	approach: string;
	risk_free_rate: number;
	unlevered_beta: number;
	levered_beta: number;
	equity_risk_premium: number;
	cost_of_equity: number;
	pretax_cost_of_debt: number;
	after_tax_cost_of_debt: number;
	equity_weight: number;
	debt_weight: number;
	wacc: number;
	stable_wacc: number;
}

export interface ValuationResult {
	segment_projections: SegmentProjections[];
	cost_of_capital: CostOfCapitalResult;
	pv_fcff_total: number;
	pv_terminal_total: number;
	going_concern_value: number;
	failure_adjustment: number;
	operating_assets_value: number;
	debt: number;
	minority_interests: number;
	cash: number;
	non_operating_assets: number;
	equity_value: number;
	option_value: number;
	equity_in_common: number;
	shares_outstanding: number;
	value_per_share: number;
	current_price: number;
	price_to_value: number;
	rd_asset_value: number | null;
	rd_amortization: number | null;
	rd_operating_adjustment: number | null;
}

export interface CompanyData {
	ticker: string;
	company_name: string;
	revenues: number;
	operating_income: number;
	interest_expense: number;
	book_equity: number;
	book_debt: number;
	cash: number;
	stock_price: number;
	shares_outstanding: number;
	market_cap: number;
	effective_tax_rate: number;
	data_as_of: string;
	fiscal_year_end: string | null;
	most_recent_quarter: string | null;
	currency: string;
	data_source: string;
	// Data quality indicators
	has_full_financials: boolean;
	data_notes: string[];
}

// API methods
export const api = {
	// Reference data
	reference: {
		countries: (search?: string): Promise<Country[]> =>
			request(`/reference/countries${search ? `?search=${encodeURIComponent(search)}` : ''}`),

		countryByName: (name: string): Promise<Country> =>
			request(`/reference/countries/by-name/${encodeURIComponent(name)}`),

		industries: (region?: string, search?: string): Promise<Industry[]> => {
			const params = new URLSearchParams();
			if (region) params.append('region', region);
			if (search) params.append('search', search);
			const queryString = params.toString();
			return request(`/reference/industries${queryString ? `?${queryString}` : ''}`);
		},

		industryByName: (name: string, region = 'US'): Promise<Industry> =>
			request(`/reference/industries/by-name/${encodeURIComponent(name)}?region=${region}`),

		ratings: (): Promise<RatingSpread[]> => request('/reference/ratings'),
	},

	// Valuation models
	models: {
		list: (): Promise<ValuationModelSummary[]> => request('/models'),

		get: (id: string): Promise<ValuationModel> => request(`/models/${id}`),

		create: (data: Partial<ValuationModel>): Promise<ValuationModel> =>
			request('/models', { method: 'POST', body: data }),

		update: (id: string, data: Partial<ValuationModel>): Promise<ValuationModel> =>
			request(`/models/${id}`, { method: 'PUT', body: data }),

		delete: (id: string): Promise<{ status: string; id: string }> =>
			request(`/models/${id}`, { method: 'DELETE' }),

		addSegment: (modelId: string, segment: Partial<BusinessSegment>): Promise<BusinessSegment> =>
			request(`/models/${modelId}/segments`, { method: 'POST', body: segment }),

		deleteSegment: (modelId: string, segmentId: string): Promise<{ status: string; id: string }> =>
			request(`/models/${modelId}/segments/${segmentId}`, { method: 'DELETE' }),

		updateCostOfCapital: (modelId: string, settings: Partial<CostOfCapitalSettings>) =>
			request(`/models/${modelId}/cost-of-capital`, { method: 'PUT', body: settings }),
	},

	// Calculations
	calculate: {
		valuation: (modelId: string): Promise<ValuationResult> =>
			request(`/calculate/${modelId}`, { method: 'POST' }),
	},

	// Data fetching (Yahoo Finance)
	data: {
		fetch: (ticker: string): Promise<CompanyData> =>
			request(`/data/fetch/${encodeURIComponent(ticker)}`),

		validate: (ticker: string): Promise<{ ticker: string; valid: boolean; company_name: string | null }> =>
			request(`/data/validate/${encodeURIComponent(ticker)}`),
	},
};

export { ApiError };
