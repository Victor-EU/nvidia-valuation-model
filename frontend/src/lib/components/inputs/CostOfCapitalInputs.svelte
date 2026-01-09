<script lang="ts">
	import NumberInput from '$lib/components/shared/NumberInput.svelte';
	import PercentInput from '$lib/components/shared/PercentInput.svelte';
	import SelectInput from '$lib/components/shared/SelectInput.svelte';
	import { modelState } from '$lib/stores/model.svelte';
	import { referenceData } from '$lib/stores/reference-data.svelte';

	function markDirty() {
		modelState.markDirty();
	}

	const approachOptions = [
		{ value: 'detailed', label: 'Detailed CAPM' },
		{ value: 'direct', label: 'Direct Input' },
		{ value: 'industry', label: 'Industry Average' },
	];

	const betaOptions = [
		{ value: 'single_business_us', label: 'Single Business (US Industry)' },
		{ value: 'single_business_global', label: 'Single Business (Global)' },
		{ value: 'direct', label: 'Direct Input' },
	];

	const erpOptions = [
		{ value: 'operating_countries', label: 'Operating Countries Weighted' },
		{ value: 'country_of_incorporation', label: 'Country of Incorporation' },
		{ value: 'direct', label: 'Direct Input' },
	];

	const debtOptions = [
		{ value: 'synthetic', label: 'Synthetic Rating' },
		{ value: 'actual_rating', label: 'Actual Rating' },
	];

	const ratingOptions = [
		{ value: 'Aaa/AAA', label: 'Aaa/AAA' },
		{ value: 'Aa2/AA', label: 'Aa2/AA' },
		{ value: 'A1/A+', label: 'A1/A+' },
		{ value: 'A2/A', label: 'A2/A' },
		{ value: 'A3/A-', label: 'A3/A-' },
		{ value: 'Baa2/BBB', label: 'Baa2/BBB' },
		{ value: 'Ba1/BB+', label: 'Ba1/BB+' },
		{ value: 'Ba2/BB', label: 'Ba2/BB' },
		{ value: 'B1/B+', label: 'B1/B+' },
		{ value: 'B2/B', label: 'B2/B' },
		{ value: 'B3/B-', label: 'B3/B-' },
		{ value: 'Caa/CCC', label: 'Caa/CCC' },
	];

	// Country search state
	let countrySearch = $state('');
	let countryRevenue = $state(0);
	let showCountryDropdown = $state(false);

	const filteredCountries = $derived(
		countrySearch.length > 0 ? referenceData.searchCountries(countrySearch) : []
	);

	function addOperatingCountry(countryName: string) {
		if (countryRevenue > 0) {
			modelState.addOperatingCountry(countryName, countryRevenue);
			countrySearch = '';
			countryRevenue = 0;
			showCountryDropdown = false;
		}
	}

	function removeOperatingCountry(index: number) {
		modelState.removeOperatingCountry(index);
	}

	// Calculate total operating revenue for percentage display
	const totalOperatingRevenue = $derived(
		modelState.costOfCapital.operating_countries.reduce((sum, c) => sum + c.revenues, 0)
	);
</script>

<div class="card">
	<h2 class="card-header">Cost of Capital</h2>

	<div class="space-y-6">
		<!-- Approach Selection -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
			<SelectInput
				label="Calculation Approach"
				options={approachOptions}
				bind:value={modelState.costOfCapital.approach}
				onchange={markDirty}
			/>

			<PercentInput
				label="Risk-Free Rate"
				bind:value={modelState.marketInputs.risk_free_rate}
				decimals={2}
				onchange={markDirty}
			/>
		</div>

		{#if modelState.costOfCapital.approach === 'direct'}
			<!-- Direct WACC Input -->
			<div class="p-4 bg-gray-50 rounded-lg">
				<PercentInput
					label="Direct Cost of Capital (WACC)"
					bind:value={modelState.costOfCapital.direct_coc}
					decimals={2}
					onchange={markDirty}
				/>
			</div>
		{:else if modelState.costOfCapital.approach === 'detailed'}
			<!-- Detailed CAPM -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
				<!-- Beta Section -->
				<div class="space-y-4">
					<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Beta</h3>

					<SelectInput
						label="Beta Approach"
						options={betaOptions}
						bind:value={modelState.costOfCapital.beta_approach}
						onchange={markDirty}
					/>

					{#if modelState.costOfCapital.beta_approach === 'direct'}
						<NumberInput
							label="Direct Unlevered Beta"
							bind:value={modelState.costOfCapital.direct_beta}
							decimals={2}
							onchange={markDirty}
						/>
					{/if}
				</div>

				<!-- ERP Section -->
				<div class="space-y-4">
					<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Equity Risk Premium</h3>

					<SelectInput
						label="ERP Approach"
						options={erpOptions}
						bind:value={modelState.costOfCapital.erp_approach}
						onchange={markDirty}
					/>

					{#if modelState.costOfCapital.erp_approach === 'direct'}
						<PercentInput
							label="Direct ERP"
							bind:value={modelState.costOfCapital.direct_erp}
							decimals={2}
							onchange={markDirty}
						/>
					{:else if modelState.costOfCapital.erp_approach === 'operating_countries'}
						<!-- Operating Countries -->
						<div class="space-y-3">
							<label class="input-label">Operating Countries</label>

							<!-- Current countries list -->
							{#if modelState.costOfCapital.operating_countries.length > 0}
								<div class="space-y-2">
									{#each modelState.costOfCapital.operating_countries as country, index}
										<div class="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
											<div class="flex-1">
												<span class="font-medium text-sm">{country.country}</span>
												<span class="text-gray-500 text-sm ml-2">
													${(country.revenues / 1e9).toFixed(1)}B
													({totalOperatingRevenue > 0
														? ((country.revenues / totalOperatingRevenue) * 100).toFixed(1)
														: 0}%)
												</span>
											</div>
											<button
												class="text-gray-400 hover:text-red-500 ml-2"
												onclick={() => removeOperatingCountry(index)}
											>
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
												</svg>
											</button>
										</div>
									{/each}
								</div>
							{/if}

							<!-- Add country form -->
							<div class="flex gap-2 items-end">
								<div class="flex-1 relative">
									<label class="input-label text-xs">Country</label>
									<input
										type="text"
										class="input-field text-sm"
										placeholder="Search countries..."
										bind:value={countrySearch}
										onfocus={() => (showCountryDropdown = true)}
									/>
									{#if showCountryDropdown && filteredCountries.length > 0}
										<div class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-auto">
											{#each filteredCountries.slice(0, 10) as country}
												<button
													class="w-full text-left px-3 py-2 hover:bg-gray-50 text-sm"
													onclick={() => {
														countrySearch = country.name;
														showCountryDropdown = false;
													}}
												>
													{country.name}
													<span class="text-gray-400 text-xs ml-1">
														ERP: {((country.equity_risk_premium || 0) * 100).toFixed(2)}%
													</span>
												</button>
											{/each}
										</div>
									{/if}
								</div>
								<div class="w-32">
									<label class="input-label text-xs">Revenue ($)</label>
									<input
										type="text"
										class="input-field text-sm font-mono text-right"
										placeholder="0"
										bind:value={countryRevenue}
									/>
								</div>
								<button
									class="btn-primary py-2 text-sm"
									disabled={!countrySearch || countryRevenue <= 0}
									onclick={() => addOperatingCountry(countrySearch)}
								>
									Add
								</button>
							</div>
						</div>
					{/if}
				</div>
			</div>

			<!-- Cost of Debt -->
			<div class="pt-4 border-t border-gray-100">
				<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">Cost of Debt</h3>

				<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
					<SelectInput
						label="Debt Approach"
						options={debtOptions}
						bind:value={modelState.costOfCapital.debt_approach}
						onchange={markDirty}
					/>

					{#if modelState.costOfCapital.debt_approach === 'actual_rating'}
						<SelectInput
							label="Actual Rating"
							options={ratingOptions}
							bind:value={modelState.costOfCapital.actual_rating}
							onchange={markDirty}
						/>
					{:else}
						<SelectInput
							label="Firm Type"
							options={[
								{ value: '1', label: 'Large Manufacturing' },
								{ value: '2', label: 'Small/Risky' },
							]}
							value={String(modelState.costOfCapital.firm_type)}
							onchange={(v) => {
								modelState.costOfCapital.firm_type = parseInt(v);
								markDirty();
							}}
						/>
					{/if}

					<NumberInput
						label="Avg Debt Maturity (years)"
						bind:value={modelState.costOfCapital.debt_maturity}
						decimals={1}
						min={0.5}
						max={30}
						onchange={markDirty}
					/>
				</div>
			</div>
		{/if}
	</div>
</div>
