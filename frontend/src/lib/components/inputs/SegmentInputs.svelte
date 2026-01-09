<script lang="ts">
	import CurrencyInput from '$lib/components/shared/CurrencyInput.svelte';
	import PercentInput from '$lib/components/shared/PercentInput.svelte';
	import { modelState } from '$lib/stores/model.svelte';

	const segmentColors = {
		rest: 'bg-gray-100 border-gray-200',
		ai: 'bg-emerald-50 border-emerald-200',
		auto: 'bg-blue-50 border-blue-200',
	};

	const segmentLabels = {
		rest: 'Rest of Business',
		ai: 'AI Chips',
		auto: 'Auto Chips',
	};

	function addAISegment() {
		if (!modelState.segments.find((s) => s.segment_type === 'ai')) {
			modelState.addSegment('ai');
		}
	}

	function addAutoSegment() {
		if (!modelState.segments.find((s) => s.segment_type === 'auto')) {
			modelState.addSegment('auto');
		}
	}

	function removeSegment(index: number) {
		modelState.removeSegment(index);
	}

	function markDirty() {
		modelState.markDirty();
	}

	const hasAI = $derived(modelState.segments.some((s) => s.segment_type === 'ai'));
	const hasAuto = $derived(modelState.segments.some((s) => s.segment_type === 'auto'));
</script>

<div class="card">
	<div class="flex items-center justify-between mb-4">
		<h2 class="text-lg font-semibold text-gray-900">Business Segments</h2>
		<div class="flex gap-2">
			{#if !hasAI}
				<button class="btn-secondary text-xs py-1.5" onclick={addAISegment}>
					<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					Add AI Segment
				</button>
			{/if}
			{#if !hasAuto}
				<button class="btn-secondary text-xs py-1.5" onclick={addAutoSegment}>
					<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					Add Auto Segment
				</button>
			{/if}
		</div>
	</div>

	<div class="space-y-6">
		{#each modelState.segments as segment, index (segment.segment_type)}
			<div class="border rounded-lg p-4 {segmentColors[segment.segment_type]}">
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-2">
						<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
							{segment.segment_type === 'rest' ? 'bg-gray-200 text-gray-800' : ''}
							{segment.segment_type === 'ai' ? 'bg-emerald-200 text-emerald-800' : ''}
							{segment.segment_type === 'auto' ? 'bg-blue-200 text-blue-800' : ''}"
						>
							{segmentLabels[segment.segment_type]}
						</span>
						<input
							type="text"
							class="text-sm font-medium bg-transparent border-none focus:ring-0 p-0"
							bind:value={segment.name}
							onchange={markDirty}
						/>
					</div>
					{#if segment.segment_type !== 'rest'}
						<button
							class="text-gray-400 hover:text-red-500 transition-colors"
							onclick={() => removeSegment(index)}
							title="Remove segment"
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
									d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
							</svg>
						</button>
					{/if}
				</div>

				{#if segment.segment_type === 'rest'}
					<p class="text-sm text-gray-500">
						This segment captures all business not explicitly modeled (Gaming, Professional Visualization, etc.).
						Values are derived from total company data minus other segments.
					</p>
				{:else}
					<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
						<!-- Market Size -->
						<div class="space-y-4">
							<h4 class="text-sm font-medium text-gray-600">Total Addressable Market</h4>

							<CurrencyInput
								label="Current Market Size"
								bind:value={segment.total_market_current}
								onchange={markDirty}
							/>

							<CurrencyInput
								label="Year 10 Market Size"
								bind:value={segment.total_market_year10}
								onchange={markDirty}
							/>

							{#if segment.total_market_current && segment.total_market_year10}
								<div class="text-xs text-gray-500 bg-white/50 rounded p-2">
									Implied CAGR: {(
										(Math.pow(segment.total_market_year10 / segment.total_market_current, 1 / 10) - 1) *
										100
									).toFixed(1)}%
								</div>
							{/if}
						</div>

						<!-- Market Share & Margin -->
						<div class="space-y-4">
							<h4 class="text-sm font-medium text-gray-600">Share & Profitability</h4>

							<PercentInput
								label="Current Market Share"
								bind:value={segment.market_share_current}
								max={1}
								onchange={markDirty}
							/>

							<PercentInput
								label="Year 10 Market Share"
								bind:value={segment.market_share_year10}
								max={1}
								onchange={markDirty}
							/>

							<PercentInput
								label="Current Operating Margin"
								bind:value={segment.operating_margin_current}
								max={1}
								onchange={markDirty}
							/>

							<PercentInput
								label="Year 10 Operating Margin"
								bind:value={segment.operating_margin_year10}
								max={1}
								onchange={markDirty}
							/>
						</div>
					</div>

					<!-- Computed segment metrics -->
					{#if segment.total_market_current && segment.market_share_current}
						<div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2 text-center bg-white/50 rounded-lg p-3">
							<div>
								<div class="text-xs text-gray-500">Current Revenue</div>
								<div class="font-semibold font-mono text-sm">
									${((segment.total_market_current * segment.market_share_current) / 1e9).toFixed(1)}B
								</div>
							</div>
							<div>
								<div class="text-xs text-gray-500">Year 10 Revenue</div>
								<div class="font-semibold font-mono text-sm">
									${((segment.total_market_year10 || 0) * (segment.market_share_year10 || 0) / 1e9).toFixed(1)}B
								</div>
							</div>
							<div>
								<div class="text-xs text-gray-500">Revenue CAGR</div>
								<div class="font-semibold font-mono text-sm">
									{(() => {
										const current = segment.total_market_current * segment.market_share_current;
										const year10 = (segment.total_market_year10 || 0) * (segment.market_share_year10 || 0);
										if (current > 0 && year10 > 0) {
											return ((Math.pow(year10 / current, 1 / 10) - 1) * 100).toFixed(1) + '%';
										}
										return '—';
									})()}
								</div>
							</div>
							<div>
								<div class="text-xs text-gray-500">Current EBIT</div>
								<div class="font-semibold font-mono text-sm">
									${((segment.total_market_current * segment.market_share_current * (segment.operating_margin_current || 0)) / 1e9).toFixed(1)}B
								</div>
							</div>
						</div>
					{/if}
				{/if}
			</div>
		{/each}
	</div>
</div>
