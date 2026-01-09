<script lang="ts">
	import { calculationsState } from '$lib/stores/calculations.svelte';
	import { formatPercent } from '$lib/utils/formatting';

	// Get cost of capital directly from result
	function getCostOfCapital() {
		return calculationsState.result?.cost_of_capital ?? null;
	}
</script>

<div class="card">
	<h2 class="card-header">Cost of Capital</h2>

	{#if getCostOfCapital()}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<!-- Cost of Equity -->
			<div class="space-y-4">
				<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Cost of Equity</h3>

				<div class="bg-blue-50 rounded-lg p-4">
					<div class="text-2xl font-bold font-mono text-blue-700 mb-2">
						{formatPercent(getCostOfCapital()?.cost_of_equity)}
					</div>
					<div class="text-xs text-blue-600">
						= Rf + β × ERP
					</div>
				</div>

				<div class="space-y-2 text-sm">
					<div class="flex justify-between">
						<span class="text-gray-600">Risk-Free Rate</span>
						<span class="font-mono">{formatPercent(getCostOfCapital()?.risk_free_rate)}</span>
					</div>
					<div class="flex justify-between">
						<span class="text-gray-600">Unlevered Beta</span>
						<span class="font-mono">{getCostOfCapital()?.unlevered_beta?.toFixed(2) ?? '—'}</span>
					</div>
					<div class="flex justify-between">
						<span class="text-gray-600">Levered Beta</span>
						<span class="font-mono">{getCostOfCapital()?.levered_beta?.toFixed(2) ?? '—'}</span>
					</div>
					<div class="flex justify-between">
						<span class="text-gray-600">Equity Risk Premium</span>
						<span class="font-mono">{formatPercent(getCostOfCapital()?.equity_risk_premium)}</span>
					</div>
				</div>
			</div>

			<!-- Cost of Debt -->
			<div class="space-y-4">
				<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Cost of Debt</h3>

				<div class="bg-orange-50 rounded-lg p-4">
					<div class="text-2xl font-bold font-mono text-orange-700 mb-2">
						{formatPercent(getCostOfCapital()?.after_tax_cost_of_debt)}
					</div>
					<div class="text-xs text-orange-600">
						After-tax cost of debt
					</div>
				</div>

				<div class="space-y-2 text-sm">
					<div class="flex justify-between">
						<span class="text-gray-600">Pre-tax Cost of Debt</span>
						<span class="font-mono">{formatPercent(getCostOfCapital()?.pretax_cost_of_debt)}</span>
					</div>
					<div class="flex justify-between text-gray-400 text-xs">
						<span>= Rf + Default Spread</span>
					</div>
				</div>
			</div>
		</div>

		<!-- WACC Calculation -->
		<div class="mt-6 pt-6 border-t border-gray-100">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">Weighted Average Cost of Capital</h3>

			<div class="bg-gradient-to-r from-nvidia-green-50 to-nvidia-green-100 rounded-lg p-6">
				<div class="grid grid-cols-2 gap-4 mb-4">
					<div class="text-center">
						<div class="text-3xl font-bold font-mono text-nvidia-green-700">
							{formatPercent(getCostOfCapital()?.wacc)}
						</div>
						<div class="text-sm text-nvidia-green-600">Current WACC</div>
					</div>
					<div class="text-center">
						<div class="text-3xl font-bold font-mono text-gray-600">
							{formatPercent(getCostOfCapital()?.stable_wacc)}
						</div>
						<div class="text-sm text-gray-500">Stable Period WACC</div>
					</div>
				</div>

				<!-- WACC formula breakdown -->
				<div class="bg-white/50 rounded-lg p-4 text-sm">
					<div class="font-mono text-center text-gray-600 mb-2">
						WACC = E/(D+E) × Ke + D/(D+E) × Kd(1-t)
					</div>
					<div class="flex justify-center gap-8 text-xs">
						<div class="text-center">
							<div class="font-semibold">{formatPercent(getCostOfCapital()?.equity_weight)}</div>
							<div class="text-gray-500">Equity Weight</div>
						</div>
						<div class="text-center">
							<div class="font-semibold">{formatPercent(getCostOfCapital()?.debt_weight)}</div>
							<div class="text-gray-500">Debt Weight</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	{:else}
		<div class="text-center py-8 text-gray-500">
			<p>Run calculation to see cost of capital breakdown</p>
		</div>
	{/if}
</div>
