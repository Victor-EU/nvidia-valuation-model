<script lang="ts">
	import NumberInput from '$lib/components/shared/NumberInput.svelte';
	import PercentInput from '$lib/components/shared/PercentInput.svelte';
	import SelectInput from '$lib/components/shared/SelectInput.svelte';
	import Toggle from '$lib/components/shared/Toggle.svelte';
	import CurrencyInput from '$lib/components/shared/CurrencyInput.svelte';
	import { modelState } from '$lib/stores/model.svelte';

	function markDirty() {
		modelState.markDirty();
	}
</script>

<div class="card">
	<h2 class="card-header">Override Assumptions</h2>

	<p class="text-sm text-gray-500 mb-6">
		Override default calculations with custom values. Use sparingly for specific scenarios.
	</p>

	<div class="space-y-6">
		<!-- Stable Period Overrides -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<!-- Stable Cost of Capital -->
			<div class="p-4 bg-gray-50 rounded-lg space-y-3">
				<Toggle
					label="Override Stable Cost of Capital"
					description="Use custom WACC for terminal value"
					bind:checked={modelState.overrides.override_stable_coc}
					onchange={markDirty}
				/>
				{#if modelState.overrides.override_stable_coc}
					<PercentInput
						label="Stable Period WACC"
						bind:value={modelState.overrides.stable_coc}
						decimals={2}
						onchange={markDirty}
					/>
				{/if}
			</div>

			<!-- Stable ROIC -->
			<div class="p-4 bg-gray-50 rounded-lg space-y-3">
				<Toggle
					label="Override Stable ROIC"
					description="Use custom return on invested capital"
					bind:checked={modelState.overrides.override_stable_roic}
					onchange={markDirty}
				/>
				{#if modelState.overrides.override_stable_roic}
					<PercentInput
						label="Stable Period ROIC"
						bind:value={modelState.overrides.stable_roic}
						decimals={2}
						onchange={markDirty}
					/>
				{/if}
			</div>
		</div>

		<!-- Growth Override -->
		<div class="p-4 bg-gray-50 rounded-lg space-y-3">
			<Toggle
				label="Override Perpetual Growth Rate"
				description="Use custom terminal growth instead of risk-free rate"
				bind:checked={modelState.overrides.override_growth}
				onchange={markDirty}
			/>
			{#if modelState.overrides.override_growth}
				<PercentInput
					label="Perpetual Growth Rate"
					bind:value={modelState.overrides.perpetual_growth}
					decimals={2}
					max={0.1}
					onchange={markDirty}
				/>
			{/if}
		</div>

		<!-- Failure Probability -->
		<div class="p-4 bg-amber-50 rounded-lg border border-amber-200 space-y-3">
			<Toggle
				label="Include Failure Probability"
				description="Adjust value for probability of distress/bankruptcy"
				bind:checked={modelState.overrides.override_failure}
				onchange={markDirty}
			/>
			{#if modelState.overrides.override_failure}
				<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
					<PercentInput
						label="Failure Probability"
						bind:value={modelState.overrides.failure_prob}
						decimals={2}
						max={1}
						onchange={markDirty}
					/>
					<SelectInput
						label="Distress Proceeds Based On"
						options={[
							{ value: 'V', label: 'Operating Value' },
							{ value: 'B', label: 'Book Value' },
						]}
						bind:value={modelState.overrides.distress_proceeds_type}
						onchange={markDirty}
					/>
					<PercentInput
						label="Distress Proceeds %"
						bind:value={modelState.overrides.distress_proceeds_pct}
						decimals={0}
						max={1}
						onchange={markDirty}
					/>
				</div>
			{/if}
		</div>

		<!-- NOL Override -->
		<div class="p-4 bg-gray-50 rounded-lg space-y-3">
			<Toggle
				label="Include Net Operating Losses"
				description="Carry forward tax losses to offset future income"
				bind:checked={modelState.overrides.override_nol}
				onchange={markDirty}
			/>
			{#if modelState.overrides.override_nol}
				<CurrencyInput
					label="NOL Amount"
					bind:value={modelState.overrides.nol}
					onchange={markDirty}
				/>
			{/if}
		</div>

		<!-- Reinvestment Lag -->
		<div class="p-4 bg-gray-50 rounded-lg">
			<div class="flex items-start justify-between mb-3">
				<div>
					<h4 class="text-sm font-medium text-gray-700">Reinvestment Lag</h4>
					<p class="text-xs text-gray-500">Years before reinvestment generates revenue</p>
				</div>
			</div>
			<NumberInput
				bind:value={modelState.overrides.reinvestment_lag}
				decimals={0}
				min={0}
				max={5}
				onchange={markDirty}
				suffix="years"
			/>
		</div>
	</div>
</div>
