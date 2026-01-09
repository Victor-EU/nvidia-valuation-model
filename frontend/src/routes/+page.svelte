<script lang="ts">
	import { onMount } from 'svelte';
	import { modelState } from '$lib/stores/model.svelte';
	import { calculationsState } from '$lib/stores/calculations.svelte';
	import { referenceData } from '$lib/stores/reference-data.svelte';
	import { api } from '$lib/services/api';

	// Input components
	import CompanyInputs from '$lib/components/inputs/CompanyInputs.svelte';
	import ValueDrivers from '$lib/components/inputs/ValueDrivers.svelte';
	import SegmentInputs from '$lib/components/inputs/SegmentInputs.svelte';
	import CostOfCapitalInputs from '$lib/components/inputs/CostOfCapitalInputs.svelte';
	import OverrideInputs from '$lib/components/inputs/OverrideInputs.svelte';

	// Output components
	import ValuationSummary from '$lib/components/outputs/ValuationSummary.svelte';
	import CostOfCapitalDisplay from '$lib/components/outputs/CostOfCapitalDisplay.svelte';
	import ProjectionTable from '$lib/components/outputs/ProjectionTable.svelte';
	import SegmentBreakdown from '$lib/components/outputs/SegmentBreakdown.svelte';

	// Shared components
	import AutoUpdateModal from '$lib/components/shared/AutoUpdateModal.svelte';

	// Tab management
	let activeTab = $state<'inputs' | 'outputs'>('inputs');
	let activeInputSection = $state(0);

	// Auto update modal
	let showAutoUpdateModal = $state(false);

	const inputSections = [
		{ id: 'company', label: 'Company Data' },
		{ id: 'drivers', label: 'Value Drivers' },
		{ id: 'segments', label: 'Segments' },
		{ id: 'coc', label: 'Cost of Capital' },
		{ id: 'overrides', label: 'Overrides' },
	];

	// Load reference data on mount
	onMount(async () => {
		await referenceData.loadAll();
		// Set some default NVIDIA values
		loadNvidiaDefaults();
	});

	function resetApp() {
		// Clear calculation results
		calculationsState.clear();
		// Reset model ID so a new model is created
		modelState.id = null;
		// Reload defaults
		loadNvidiaDefaults();
		// Switch to inputs tab
		activeTab = 'inputs';
		activeInputSection = 0;
	}

	function loadNvidiaDefaults() {
		// Set NVIDIA Jan 2025 default values
		modelState.name = 'NVIDIA DCF Valuation';
		modelState.companyName = 'NVIDIA Corporation';
		modelState.valuationDate = '2025-01-15';

		modelState.baseYearData = {
			revenues: 113270000000, // $113.27B TTM
			operating_income: 72900000000, // ~$72.9B EBIT
			interest_expense: 257000000, // $257M
			book_equity: 62442000000, // ~$62.4B
			book_debt: 10388000000, // ~$10.4B
			cash: 38489000000, // ~$38.5B
			cross_holdings: 0,
			minority_interests: 0,
			shares: 24530000000, // 24.53B shares
			stock_price: 138.77, // ~$138.77
			effective_tax_rate: 0.13,
			marginal_tax_rate: 0.25,
		};

		modelState.valueDrivers = {
			revenue_growth_yr1: 0.15, // 15% Year 1 growth (Excel B25)
			operating_margin_yr1: 0.65, // 65% initial operating margin (Excel)
			compounded_growth_2_5: 0.15, // 15% growth Years 2-5 (Excel B27)
			target_margin: 0.60, // 60% target margin (Excel - converges over 5 years)
			convergence_year: 5,
			sales_to_capital_1_5: 2.00,
			sales_to_capital_6_10: 1.50,
		};

		modelState.marketInputs = {
			risk_free_rate: 0.045,
			country: 'United States',
			industry_us: 'Semiconductor',
			industry_global: 'Semiconductor',
		};

		modelState.segments = [
			{
				name: 'Rest of Business',
				segment_type: 'rest',
				segment_order: 0,
			},
			{
				name: 'AI Chips',
				segment_type: 'ai',
				segment_order: 1,
				// From Excel: AI revenue = $80B market × 80% share = $64B
				// Rest = Total ($113.27B) - AI ($64B) - Auto ($1.2B) = $48.07B
				total_market_current: 80000000000, // $80B current AI chip market (Excel B44)
				total_market_year10: 300000000000, // $300B projected market Year 10 (Excel C44)
				market_share_current: 0.80, // 80% current market share (Excel B45)
				market_share_year10: 0.60, // 60% share Year 10 (Excel C45)
				operating_margin_current: 0.65, // 65% (Excel B46)
				operating_margin_year10: 0.60, // 60% (Excel C46)
			},
			{
				name: 'Auto Chips',
				segment_type: 'auto',
				segment_order: 2,
				// From Excel: Auto revenue = $20B market × 6% share = $1.2B
				total_market_current: 20000000000, // $20B current auto chip market (Excel B50)
				total_market_year10: 200000000000, // $200B projected market Year 10 (Excel C50)
				market_share_current: 0.06, // 6% current market share (Excel B51)
				market_share_year10: 0.15, // 15% share Year 10 (Excel C51)
				operating_margin_current: 0.65, // 65% (Excel B52)
				operating_margin_year10: 0.60, // 60% (Excel C52)
			},
		];

		modelState.costOfCapital = {
			approach: 'detailed',
			direct_coc: null,
			beta_approach: 'single_business_us',
			direct_beta: null,
			erp_approach: 'operating_countries',
			direct_erp: null,
			operating_countries: [
				{ country: 'United States', revenues: 56635000000 },
				{ country: 'Taiwan', revenues: 22654000000 },
				{ country: 'China', revenues: 17017000000 },
				{ country: 'Singapore', revenues: 11327000000 },
			],
			debt_approach: 'synthetic',
			actual_rating: null,
			firm_type: 1,
			debt_maturity: 3,
			preferred_shares: null,
			preferred_price: null,
			preferred_dividend: null,
		};

		modelState.isDirty = false;
	}

	async function runCalculation() {
		if (!modelState.id) {
			// Create model first
			try {
				calculationsState.setLoading(true);
				const created = await api.models.create(modelState.toApiFormat());
				modelState.id = created.id;

				// Now calculate
				const result = await api.calculate.valuation(created.id);
				calculationsState.setResult(result);
				modelState.lastCalculated = new Date();
				modelState.isDirty = false;
				activeTab = 'outputs';
			} catch (error) {
				calculationsState.setError(error instanceof Error ? error.message : 'Calculation failed');
			}
		} else {
			// Update and calculate
			try {
				calculationsState.setLoading(true);
				await api.models.update(modelState.id, modelState.toApiFormat());
				const result = await api.calculate.valuation(modelState.id);
				calculationsState.setResult(result);
				modelState.lastCalculated = new Date();
				modelState.isDirty = false;
				activeTab = 'outputs';
			} catch (error) {
				calculationsState.setError(error instanceof Error ? error.message : 'Calculation failed');
			}
		}
	}
</script>

<svelte:head>
	<title>NVIDIA DCF Valuation Model</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<header class="bg-white border-b border-gray-200 sticky top-0 z-50">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between h-16">
				<div class="flex items-center gap-4">
					<button
						class="flex items-center gap-2 hover:opacity-80 transition-opacity"
						onclick={resetApp}
						title="Reset to defaults"
					>
						<div class="w-8 h-8 bg-nvidia-green-500 rounded-lg flex items-center justify-center">
							<span class="text-white font-bold text-sm">N</span>
						</div>
						<h1 class="text-xl font-semibold text-gray-900">DCF Valuation</h1>
					</button>
					<span class="text-sm text-gray-500">{modelState.companyName || 'New Model'}</span>
				</div>

				<div class="flex items-center gap-4">
					<!-- Auto Update Button -->
					<button
						class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
						onclick={() => (showAutoUpdateModal = true)}
						title="Fetch latest data from Yahoo Finance"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
						</svg>
						Auto Update
					</button>

					{#if modelState.isDirty}
						<span class="text-sm text-amber-600 flex items-center gap-1">
							<span class="w-2 h-2 bg-amber-500 rounded-full"></span>
							Unsaved changes
						</span>
					{/if}

					<button
						class="btn-primary"
						onclick={runCalculation}
						disabled={calculationsState.isLoading}
					>
						{#if calculationsState.isLoading}
							<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							Calculating...
						{:else}
							<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
							</svg>
							Run Valuation
						{/if}
					</button>
				</div>
			</div>
		</div>
	</header>

	<!-- Main content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Error display -->
		{#if calculationsState.error}
			<div class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
				<svg class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
				</svg>
				<div class="flex-1">
					<h3 class="text-sm font-medium text-red-800">Calculation Error</h3>
					<p class="text-sm text-red-700 mt-1">{calculationsState.error}</p>
				</div>
				<button
					class="text-red-500 hover:text-red-700"
					onclick={() => (calculationsState.error = null)}
				>
					<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
					</svg>
				</button>
			</div>
		{/if}

		<!-- Main tabs -->
		<div class="flex gap-4 mb-6">
			<button
				class="px-6 py-2 rounded-lg font-medium transition-colors
					{activeTab === 'inputs'
						? 'bg-nvidia-green-500 text-white'
						: 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'}"
				onclick={() => (activeTab = 'inputs')}
			>
				Inputs
			</button>
			<button
				class="px-6 py-2 rounded-lg font-medium transition-colors
					{activeTab === 'outputs'
						? 'bg-nvidia-green-500 text-white'
						: 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'}"
				onclick={() => (activeTab = 'outputs')}
			>
				Results
			</button>
		</div>

		{#if activeTab === 'inputs'}
			<!-- Input sections -->
			<div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
				<!-- Sidebar navigation -->
				<div class="lg:col-span-1">
					<nav class="sticky top-24 space-y-1">
						{#each inputSections as section, index}
							<button
								class="w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
									{activeInputSection === index
										? 'bg-nvidia-green-100 text-nvidia-green-700'
										: 'text-gray-600 hover:bg-gray-100'}"
								onclick={() => (activeInputSection = index)}
							>
								{section.label}
							</button>
						{/each}
					</nav>
				</div>

				<!-- Content -->
				<div class="lg:col-span-3 space-y-6">
					{#if activeInputSection === 0}
						<CompanyInputs />
					{:else if activeInputSection === 1}
						<ValueDrivers />
					{:else if activeInputSection === 2}
						<SegmentInputs />
					{:else if activeInputSection === 3}
						<CostOfCapitalInputs />
					{:else if activeInputSection === 4}
						<OverrideInputs />
					{/if}
				</div>
			</div>
		{:else}
			<!-- Output sections -->
			<div class="space-y-6">
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
					<ValuationSummary />
					<CostOfCapitalDisplay />
				</div>
				<SegmentBreakdown />
				<ProjectionTable />
			</div>
		{/if}
	</main>

	<!-- Footer -->
	<footer class="bg-white border-t border-gray-200 mt-12">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center justify-between text-sm text-gray-500">
				<span>DCF Valuation Model • Based on Damodaran methodology</span>
				{#if modelState.lastCalculated}
					<span>Last calculated: {modelState.lastCalculated.toLocaleTimeString()}</span>
				{/if}
			</div>
		</div>
	</footer>
</div>

<!-- Auto Update Modal -->
<AutoUpdateModal bind:open={showAutoUpdateModal} onclose={() => (showAutoUpdateModal = false)} />
