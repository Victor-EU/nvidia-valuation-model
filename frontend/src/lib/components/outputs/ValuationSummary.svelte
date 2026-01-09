<script lang="ts">
	import { calculationsState } from '$lib/stores/calculations.svelte';
	import { formatCurrency, formatPercent, formatCompact } from '$lib/utils/formatting';

	// Get value CSS class
	function getValueClass(value: number): string {
		if (value > 0) return 'text-green-600';
		if (value < 0) return 'text-red-600';
		return 'text-gray-900';
	}

	// Calculate upside percentage
	function getUpside(): number {
		const result = calculationsState.result;
		if (!result?.current_price) return 0;
		return ((result.value_per_share - result.current_price) / result.current_price) * 100;
	}

	// Get price to value ratio
	function getPriceToValue(): number {
		return calculationsState.result?.price_to_value ?? 0;
	}
</script>

<div class="card">
	<h2 class="card-header">Valuation Summary</h2>

	{#if calculationsState.result}
		<!-- Hero metrics -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
			<div class="metric-card bg-gradient-to-br from-nvidia-green-50 to-nvidia-green-100 border-nvidia-green-200">
				<div class="metric-label">Value per Share</div>
				<div class="metric-value text-nvidia-green-700">
					{formatCurrency(calculationsState.result?.value_per_share ?? 0, 'USD', 2)}
				</div>
				<div class="metric-subtext">
					{#if getUpside() > 0}
						<span class="text-green-600">+{getUpside().toFixed(1)}% upside</span>
					{:else if getUpside() < 0}
						<span class="text-red-600">{getUpside().toFixed(1)}% downside</span>
					{:else}
						<span>Fair valued</span>
					{/if}
				</div>
			</div>

			<div class="metric-card">
				<div class="metric-label">Current Price</div>
				<div class="metric-value">
					{formatCurrency(calculationsState.result?.current_price ?? 0, 'USD', 2)}
				</div>
				<div class="metric-subtext">Market price</div>
			</div>

			<div class="metric-card">
				<div class="metric-label">Price / Value</div>
				<div class="metric-value {getPriceToValue() < 1 ? 'text-green-600' : 'text-red-600'}">
					{getPriceToValue().toFixed(2)}x
				</div>
				<div class="metric-subtext">
					{getPriceToValue() < 1 ? 'Undervalued' : getPriceToValue() > 1 ? 'Overvalued' : 'Fair'}
				</div>
			</div>
		</div>

		<!-- Valuation bridge -->
		<div class="space-y-4">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Enterprise to Equity Bridge</h3>

			<div class="bg-gray-50 rounded-lg p-4 space-y-3">
				<!-- Operating value -->
				<div class="flex justify-between items-center py-2">
					<span class="text-gray-600">PV of Operating Cash Flows</span>
					<span class="font-mono font-medium">{formatCompact(calculationsState.result?.pv_fcff_total ?? 0)}</span>
				</div>

				<div class="flex justify-between items-center py-2">
					<span class="text-gray-600">PV of Terminal Value</span>
					<span class="font-mono font-medium">{formatCompact(calculationsState.result?.pv_terminal_total ?? 0)}</span>
				</div>

				<div class="flex justify-between items-center py-2 border-t border-gray-200 pt-3">
					<span class="font-medium">Going Concern Value</span>
					<span class="font-mono font-semibold">{formatCompact(calculationsState.result?.going_concern_value ?? 0)}</span>
				</div>

				{#if (calculationsState.result?.failure_adjustment ?? 0) !== 0}
					<div class="flex justify-between items-center py-2 text-amber-600">
						<span>Failure Adjustment</span>
						<span class="font-mono">{formatCompact(calculationsState.result?.failure_adjustment ?? 0)}</span>
					</div>
				{/if}

				<div class="flex justify-between items-center py-2 border-t border-gray-200 pt-3">
					<span class="font-medium">Operating Assets Value</span>
					<span class="font-mono font-semibold">{formatCompact(calculationsState.result?.operating_assets_value ?? 0)}</span>
				</div>

				<!-- Adjustments -->
				<div class="border-t border-gray-200 pt-3 mt-3 space-y-2">
					<div class="flex justify-between items-center py-1 text-sm">
						<span class="text-gray-600">− Debt</span>
						<span class="font-mono text-red-600">({formatCompact(calculationsState.result?.debt ?? 0)})</span>
					</div>

					{#if (calculationsState.result?.minority_interests ?? 0) > 0}
						<div class="flex justify-between items-center py-1 text-sm">
							<span class="text-gray-600">− Minority Interests</span>
							<span class="font-mono text-red-600">({formatCompact(calculationsState.result?.minority_interests ?? 0)})</span>
						</div>
					{/if}

					<div class="flex justify-between items-center py-1 text-sm">
						<span class="text-gray-600">+ Cash & Securities</span>
						<span class="font-mono text-green-600">{formatCompact(calculationsState.result?.cash ?? 0)}</span>
					</div>

					{#if (calculationsState.result?.non_operating_assets ?? 0) > 0}
						<div class="flex justify-between items-center py-1 text-sm">
							<span class="text-gray-600">+ Non-Operating Assets</span>
							<span class="font-mono text-green-600">{formatCompact(calculationsState.result?.non_operating_assets ?? 0)}</span>
						</div>
					{/if}
				</div>

				<div class="flex justify-between items-center py-2 border-t border-gray-200 pt-3">
					<span class="font-medium">Equity Value</span>
					<span class="font-mono font-semibold">{formatCompact(calculationsState.result?.equity_value ?? 0)}</span>
				</div>

				{#if (calculationsState.result?.option_value ?? 0) > 0}
					<div class="flex justify-between items-center py-1 text-sm">
						<span class="text-gray-600">− Employee Options Value</span>
						<span class="font-mono text-red-600">({formatCompact(calculationsState.result?.option_value ?? 0)})</span>
					</div>
				{/if}

				<div class="flex justify-between items-center py-2 border-t-2 border-gray-300 pt-3 bg-white -mx-4 px-4 rounded-b-lg">
					<span class="font-semibold text-lg">Equity in Common Stock</span>
					<span class="font-mono font-bold text-lg">{formatCompact(calculationsState.result?.equity_in_common ?? 0)}</span>
				</div>
			</div>

			<!-- Per share calculation -->
			<div class="flex items-center justify-center gap-4 text-sm text-gray-500 mt-4">
				<span>{formatCompact(calculationsState.result?.equity_in_common ?? 0)}</span>
				<span>÷</span>
				<span>{((calculationsState.result?.shares_outstanding ?? 0) / 1e6).toFixed(0)}M shares</span>
				<span>=</span>
				<span class="font-semibold text-nvidia-green-600 text-lg">
					{formatCurrency(calculationsState.result?.value_per_share ?? 0, 'USD', 2)}
				</span>
			</div>
		</div>
	{:else}
		<div class="text-center py-12 text-gray-500">
			<svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
					d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
			</svg>
			<p>Run calculation to see valuation results</p>
		</div>
	{/if}
</div>
