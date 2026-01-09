<script lang="ts">
	import NumberInput from '$lib/components/shared/NumberInput.svelte';
	import PercentInput from '$lib/components/shared/PercentInput.svelte';
	import { modelState } from '$lib/stores/model.svelte';

	function markDirty() {
		modelState.markDirty();
	}
</script>

<div class="card">
	<h2 class="card-header">Value Drivers</h2>

	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
		<!-- Year 1 Estimates -->
		<div class="space-y-4">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Year 1 Estimates</h3>

			<PercentInput
				label="Revenue Growth (Year 1)"
				bind:value={modelState.valueDrivers.revenue_growth_yr1}
				min={-1}
				max={2}
				onchange={markDirty}
			/>

			<PercentInput
				label="Operating Margin (Year 1)"
				bind:value={modelState.valueDrivers.operating_margin_yr1}
				min={0}
				max={1}
				onchange={markDirty}
			/>
		</div>

		<!-- Growth Phase (Years 2-5) -->
		<div class="space-y-4">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Growth Phase (2-5)</h3>

			<PercentInput
				label="Compounded Revenue Growth (2-5)"
				bind:value={modelState.valueDrivers.compounded_growth_2_5}
				min={-0.5}
				max={1}
				onchange={markDirty}
			/>

			<NumberInput
				label="Sales/Capital (Years 1-5)"
				bind:value={modelState.valueDrivers.sales_to_capital_1_5}
				decimals={2}
				min={0.1}
				max={10}
				onchange={markDirty}
				suffix="x"
			/>
		</div>

		<!-- Convergence & Terminal -->
		<div class="space-y-4">
			<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider">Terminal Phase</h3>

			<PercentInput
				label="Target Operating Margin"
				bind:value={modelState.valueDrivers.target_margin}
				min={0}
				max={1}
				onchange={markDirty}
			/>

			<NumberInput
				label="Convergence Year"
				bind:value={modelState.valueDrivers.convergence_year}
				decimals={0}
				min={1}
				max={10}
				onchange={markDirty}
			/>

			<NumberInput
				label="Sales/Capital (Years 6-10)"
				bind:value={modelState.valueDrivers.sales_to_capital_6_10}
				decimals={2}
				min={0.1}
				max={10}
				onchange={markDirty}
				suffix="x"
			/>
		</div>
	</div>

	<!-- Visual timeline -->
	<div class="mt-6 pt-6 border-t border-gray-100">
		<h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">Projection Timeline</h3>
		<div class="relative">
			<!-- Timeline bar -->
			<div class="h-2 bg-gray-100 rounded-full overflow-hidden">
				<div class="h-full bg-gradient-to-r from-nvidia-green-500 to-nvidia-green-300"
					style="width: {(modelState.valueDrivers.convergence_year / 10) * 100}%"></div>
			</div>
			<!-- Timeline markers -->
			<div class="flex justify-between mt-2 text-xs text-gray-500">
				<span>Year 1</span>
				<span>Year {modelState.valueDrivers.convergence_year} (Convergence)</span>
				<span>Year 10</span>
				<span>Terminal</span>
			</div>
		</div>

		<!-- Growth trajectory preview -->
		<div class="mt-4 grid grid-cols-4 gap-2 text-center">
			<div class="bg-nvidia-green-50 rounded-lg p-2">
				<div class="text-xs text-nvidia-green-700 font-medium">Year 1 Growth</div>
				<div class="text-sm font-semibold">{(modelState.valueDrivers.revenue_growth_yr1 * 100).toFixed(1)}%</div>
			</div>
			<div class="bg-nvidia-green-50 rounded-lg p-2">
				<div class="text-xs text-nvidia-green-700 font-medium">CAGR 2-5</div>
				<div class="text-sm font-semibold">{(modelState.valueDrivers.compounded_growth_2_5 * 100).toFixed(1)}%</div>
			</div>
			<div class="bg-gray-100 rounded-lg p-2">
				<div class="text-xs text-gray-600 font-medium">Years 6-10</div>
				<div class="text-sm font-semibold text-gray-500">Decay to Rf</div>
			</div>
			<div class="bg-gray-100 rounded-lg p-2">
				<div class="text-xs text-gray-600 font-medium">Terminal</div>
				<div class="text-sm font-semibold text-gray-500">{(modelState.marketInputs.risk_free_rate * 100).toFixed(1)}%</div>
			</div>
		</div>
	</div>
</div>
