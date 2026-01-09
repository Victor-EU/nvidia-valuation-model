<script lang="ts">
	import CurrencyInput from '$lib/components/shared/CurrencyInput.svelte';
	import NumberInput from '$lib/components/shared/NumberInput.svelte';
	import PercentInput from '$lib/components/shared/PercentInput.svelte';
	import { modelState } from '$lib/stores/model.svelte';

	// Helper to mark dirty on change
	function markDirty() {
		modelState.markDirty();
	}
</script>

<div class="card">
	<h2 class="card-header">Base Year Data</h2>

	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
		<!-- Revenue & Income -->
		<div class="space-y-4">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Revenue & Income</h3>

			<CurrencyInput
				label="Revenues"
				bind:value={modelState.baseYearData.revenues}
				onchange={markDirty}
			/>

			<CurrencyInput
				label="Operating Income (EBIT)"
				bind:value={modelState.baseYearData.operating_income}
				onchange={markDirty}
			/>

			<CurrencyInput
				label="Interest Expense"
				bind:value={modelState.baseYearData.interest_expense}
				onchange={markDirty}
			/>
		</div>

		<!-- Balance Sheet -->
		<div class="space-y-4">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Balance Sheet</h3>

			<CurrencyInput
				label="Book Value of Equity"
				bind:value={modelState.baseYearData.book_equity}
				onchange={markDirty}
			/>

			<CurrencyInput
				label="Book Value of Debt"
				bind:value={modelState.baseYearData.book_debt}
				onchange={markDirty}
			/>

			<CurrencyInput
				label="Cash & Marketable Securities"
				bind:value={modelState.baseYearData.cash}
				onchange={markDirty}
			/>
		</div>

		<!-- Market Data -->
		<div class="space-y-4">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Market Data</h3>

			<NumberInput
				label="Shares Outstanding (millions)"
				bind:value={modelState.baseYearData.shares}
				decimals={2}
				onchange={markDirty}
			/>

			<CurrencyInput
				label="Stock Price"
				bind:value={modelState.baseYearData.stock_price}
				decimals={2}
				compact={false}
				onchange={markDirty}
			/>
		</div>

		<!-- Non-Operating Items -->
		<div class="space-y-4">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Non-Operating</h3>

			<CurrencyInput
				label="Cross Holdings"
				bind:value={modelState.baseYearData.cross_holdings}
				onchange={markDirty}
			/>

			<CurrencyInput
				label="Minority Interests"
				bind:value={modelState.baseYearData.minority_interests}
				onchange={markDirty}
			/>
		</div>

		<!-- Tax Rates -->
		<div class="space-y-4">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Tax Rates</h3>

			<PercentInput
				label="Effective Tax Rate"
				bind:value={modelState.baseYearData.effective_tax_rate}
				onchange={markDirty}
			/>

			<PercentInput
				label="Marginal Tax Rate"
				bind:value={modelState.baseYearData.marginal_tax_rate}
				onchange={markDirty}
			/>
		</div>
	</div>

	<!-- Computed metrics -->
	<div class="mt-6 pt-6 border-t border-gray-100">
		<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">Computed Metrics</h3>
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
			<div class="bg-gray-50 rounded-lg p-3">
				<div class="text-xs text-gray-500">Market Cap</div>
				<div class="text-lg font-semibold font-mono">
					${((modelState.baseYearData.shares * modelState.baseYearData.stock_price) / 1e9).toFixed(1)}B
				</div>
			</div>
			<div class="bg-gray-50 rounded-lg p-3">
				<div class="text-xs text-gray-500">Operating Margin</div>
				<div class="text-lg font-semibold font-mono">
					{modelState.baseYearData.revenues > 0
						? ((modelState.baseYearData.operating_income / modelState.baseYearData.revenues) * 100).toFixed(1)
						: '0.0'}%
				</div>
			</div>
			<div class="bg-gray-50 rounded-lg p-3">
				<div class="text-xs text-gray-500">D/(D+E)</div>
				<div class="text-lg font-semibold font-mono">
					{(() => {
						const total = modelState.baseYearData.book_debt +
							(modelState.baseYearData.shares * modelState.baseYearData.stock_price);
						return total > 0
							? ((modelState.baseYearData.book_debt / total) * 100).toFixed(1)
							: '0.0';
					})()}%
				</div>
			</div>
			<div class="bg-gray-50 rounded-lg p-3">
				<div class="text-xs text-gray-500">ICR</div>
				<div class="text-lg font-semibold font-mono">
					{modelState.baseYearData.interest_expense > 0
						? (modelState.baseYearData.operating_income / modelState.baseYearData.interest_expense).toFixed(1)
						: '∞'}x
				</div>
			</div>
		</div>
	</div>
</div>
