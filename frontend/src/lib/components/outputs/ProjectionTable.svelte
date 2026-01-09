<script lang="ts">
	import { calculationsState } from '$lib/stores/calculations.svelte';
	import { formatCurrency, formatPercent, formatCompact } from '$lib/utils/formatting';

	let selectedSegment = $state(0);

	const segmentColors: Record<string, string> = {
		rest: 'bg-gray-100',
		ai: 'bg-emerald-100',
		auto: 'bg-blue-100',
	};

	// Get segment projections directly from result
	function getSegmentProjections() {
		return calculationsState.result?.segment_projections ?? [];
	}

	// Get selected segment
	function getSelectedSegment() {
		const projections = getSegmentProjections();
		return projections[selectedSegment] ?? null;
	}

	// Get total segment value
	function getTotalValue() {
		return getSegmentProjections().reduce((sum, s) => sum + s.segment_value, 0);
	}
</script>

<div class="card">
	<h2 class="card-header">10-Year Projections</h2>

	{#if getSegmentProjections().length > 0}
		<!-- Segment tabs -->
		{#if getSegmentProjections().length > 1}
			<div class="tab-list mb-4">
				{#each getSegmentProjections() as segment, index}
					<button
						class={selectedSegment === index ? 'tab-button-active' : 'tab-button-inactive'}
						onclick={() => (selectedSegment = index)}
					>
						{segment.segment_name}
					</button>
				{/each}
			</div>
		{/if}

		{#if getSelectedSegment()}
			<!-- Summary metrics -->
			<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
				<div class="bg-gray-50 rounded-lg p-3 text-center">
					<div class="text-xs text-gray-500">Segment Value</div>
					<div class="text-lg font-semibold font-mono">{formatCompact(getSelectedSegment()?.segment_value ?? 0)}</div>
				</div>
				<div class="bg-gray-50 rounded-lg p-3 text-center">
					<div class="text-xs text-gray-500">Terminal Value</div>
					<div class="text-lg font-semibold font-mono">{formatCompact(getSelectedSegment()?.terminal_value ?? 0)}</div>
				</div>
				<div class="bg-gray-50 rounded-lg p-3 text-center">
					<div class="text-xs text-gray-500">PV of Terminal</div>
					<div class="text-lg font-semibold font-mono">{formatCompact(getSelectedSegment()?.pv_terminal ?? 0)}</div>
				</div>
				<div class="bg-gray-50 rounded-lg p-3 text-center">
					<div class="text-xs text-gray-500">% of Total Value</div>
					<div class="text-lg font-semibold font-mono">
						{getTotalValue() > 0
							? (((getSelectedSegment()?.segment_value ?? 0) / getTotalValue()) * 100).toFixed(1)
							: 0}%
					</div>
				</div>
			</div>

			<!-- Projection table -->
			<div class="overflow-x-auto">
				<table class="data-table">
					<thead>
						<tr>
							<th class="text-left">Year</th>
							<th class="text-right">Growth</th>
							<th class="text-right">Revenues</th>
							<th class="text-right">Margin</th>
							<th class="text-right">EBIT</th>
							<th class="text-right">EBIT(1-t)</th>
							<th class="text-right">Reinvest</th>
							<th class="text-right">FCFF</th>
							<th class="text-right">WACC</th>
							<th class="text-right">PV(FCFF)</th>
						</tr>
					</thead>
					<tbody>
						{#each getSelectedSegment()?.projections ?? [] as proj}
							<tr class="hover:bg-gray-50">
								<td class="font-medium">{proj.year}</td>
								<td class="text-right font-mono text-sm">
									{formatPercent(proj.revenue_growth, 1)}
								</td>
								<td class="text-right font-mono text-sm">
									{formatCompact(proj.revenues)}
								</td>
								<td class="text-right font-mono text-sm">
									{formatPercent(proj.operating_margin, 1)}
								</td>
								<td class="text-right font-mono text-sm">
									{formatCompact(proj.ebit)}
								</td>
								<td class="text-right font-mono text-sm">
									{formatCompact(proj.ebit_1_t)}
								</td>
								<td class="text-right font-mono text-sm text-red-600">
									({formatCompact(Math.abs(proj.reinvestment))})
								</td>
								<td class="text-right font-mono text-sm font-medium
									{proj.fcff >= 0 ? 'text-green-600' : 'text-red-600'}">
									{formatCompact(proj.fcff)}
								</td>
								<td class="text-right font-mono text-sm text-gray-500">
									{formatPercent(proj.cost_of_capital, 1)}
								</td>
								<td class="text-right font-mono text-sm font-medium">
									{formatCompact(proj.pv_fcff)}
								</td>
							</tr>
						{/each}
						<!-- Terminal row -->
						<tr class="bg-nvidia-green-50 font-medium">
							<td>Terminal</td>
							<td class="text-right font-mono text-sm">—</td>
							<td class="text-right font-mono text-sm">—</td>
							<td class="text-right font-mono text-sm">—</td>
							<td class="text-right font-mono text-sm">—</td>
							<td class="text-right font-mono text-sm">—</td>
							<td class="text-right font-mono text-sm">—</td>
							<td class="text-right font-mono text-sm">—</td>
							<td class="text-right font-mono text-sm">—</td>
							<td class="text-right font-mono text-sm text-nvidia-green-700">
								{formatCompact(getSelectedSegment()?.pv_terminal ?? 0)}
							</td>
						</tr>
					</tbody>
					<tfoot>
						<tr class="border-t-2 border-gray-300">
							<th class="text-left">Total</th>
							<th colspan="8"></th>
							<th class="text-right font-mono">
								{formatCompact(getSelectedSegment()?.segment_value ?? 0)}
							</th>
						</tr>
					</tfoot>
				</table>
			</div>
		{/if}
	{:else}
		<div class="text-center py-12 text-gray-500">
			<svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
					d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
			</svg>
			<p>Run calculation to see projections</p>
		</div>
	{/if}
</div>
