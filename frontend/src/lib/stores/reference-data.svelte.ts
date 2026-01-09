/**
 * Reference Data Store
 *
 * Manages country, industry, and rating reference data.
 */

import { api, type Country, type Industry, type RatingSpread } from '$lib/services/api';

/**
 * Reference Data State Class
 */
export class ReferenceDataState {
	// Data arrays
	countries = $state<Country[]>([]);
	industriesUS = $state<Industry[]>([]);
	industriesGlobal = $state<Industry[]>([]);
	ratings = $state<RatingSpread[]>([]);

	// Loading states
	isLoadingCountries = $state(false);
	isLoadingIndustries = $state(false);
	isLoadingRatings = $state(false);

	// Error states
	countriesError = $state<string | null>(null);
	industriesError = $state<string | null>(null);
	ratingsError = $state<string | null>(null);

	// Derived: has data loaded
	hasCountries = $derived(() => this.countries.length > 0);
	hasIndustriesUS = $derived(() => this.industriesUS.length > 0);
	hasIndustriesGlobal = $derived(() => this.industriesGlobal.length > 0);
	hasRatings = $derived(() => this.ratings.length > 0);

	// Derived: loading any
	isLoading = $derived(
		() => this.isLoadingCountries || this.isLoadingIndustries || this.isLoadingRatings
	);

	/**
	 * Load all reference data
	 */
	async loadAll() {
		await Promise.all([this.loadCountries(), this.loadIndustries(), this.loadRatings()]);
	}

	/**
	 * Load countries
	 */
	async loadCountries() {
		if (this.hasCountries) return;

		this.isLoadingCountries = true;
		this.countriesError = null;

		try {
			this.countries = await api.reference.countries();
		} catch (error) {
			this.countriesError = error instanceof Error ? error.message : 'Failed to load countries';
		} finally {
			this.isLoadingCountries = false;
		}
	}

	/**
	 * Load industries
	 */
	async loadIndustries() {
		if (this.hasIndustriesUS && this.hasIndustriesGlobal) return;

		this.isLoadingIndustries = true;
		this.industriesError = null;

		try {
			const [us, global] = await Promise.all([
				api.reference.industries('US'),
				api.reference.industries('Global'),
			]);
			this.industriesUS = us;
			this.industriesGlobal = global;
		} catch (error) {
			this.industriesError =
				error instanceof Error ? error.message : 'Failed to load industries';
		} finally {
			this.isLoadingIndustries = false;
		}
	}

	/**
	 * Load rating spreads
	 */
	async loadRatings() {
		if (this.hasRatings) return;

		this.isLoadingRatings = true;
		this.ratingsError = null;

		try {
			this.ratings = await api.reference.ratings();
		} catch (error) {
			this.ratingsError = error instanceof Error ? error.message : 'Failed to load ratings';
		} finally {
			this.isLoadingRatings = false;
		}
	}

	/**
	 * Get country by name
	 */
	getCountryByName(name: string): Country | undefined {
		return this.countries.find((c) => c.name === name);
	}

	/**
	 * Get industry by name and region
	 */
	getIndustry(name: string, region: 'US' | 'Global'): Industry | undefined {
		const industries = region === 'US' ? this.industriesUS : this.industriesGlobal;
		return industries.find((i) => i.name === name);
	}

	/**
	 * Get spread for rating
	 */
	getSpreadForRating(rating: string): number | undefined {
		return this.ratings.find((r) => r.rating === rating)?.spread;
	}

	/**
	 * Search countries
	 */
	searchCountries(query: string): Country[] {
		if (!query.trim()) return this.countries;
		const lower = query.toLowerCase();
		return this.countries.filter((c) => c.name.toLowerCase().includes(lower));
	}

	/**
	 * Search industries
	 */
	searchIndustries(query: string, region: 'US' | 'Global'): Industry[] {
		const industries = region === 'US' ? this.industriesUS : this.industriesGlobal;
		if (!query.trim()) return industries;
		const lower = query.toLowerCase();
		return industries.filter((i) => i.name.toLowerCase().includes(lower));
	}
}

// Create singleton instance
export const referenceData = new ReferenceDataState();
