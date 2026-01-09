<script lang="ts">
	import { calculationsState } from '$lib/stores/calculations.svelte';
	import { formatCompact, formatPercent } from '$lib/utils/formatting';

	const segmentColorClasses: Record<string, { bg: string; bar: string; text: string }> = {
		rest: { bg: 'bg-gray-100', bar: 'bg-gray-500', text: 'text-gray-700' },
		ai: { bg: 'bg-emerald-100', bar: 'bg-emerald-500', text: 'text-emerald-700' },
		auto: { bg: 'bg-blue-100', bar: 'bg-blue-500', text: 'text-blue-700' },
	};

	// Compute segment breakdown from result
	function getSegmentBreakdown() {
		const segments = calculationsState.result?.segment_projections ?? [];
		const total = segments.reduce((sum, seg) => sum + seg.segment_value, 0);
		if (total === 0) return [];
		return segments.map((seg) => ({
			name: seg.segment_name,
			type: seg.segment_type,
			value: seg.segment_value,
			percentage: (seg.segment_value / total) * 100,
			terminalValue: seg.terminal_value,
			pvTerminal: seg.pv_terminal,
		}));
	}
</script>

<div class="card">
	<h2 class="card-header">Segment Value Breakdown</h2>

	{#if getSegmentBreakdown().length > 0}
		<!-- Visual bar chart -->
		<div class="space-y-4 mb-6">
			{#each getSegmentBreakdown() as segment}
				{@const colors = segmentColorClasses[segment.type] || segmentColorClasses.rest}
				<div class="space-y-1">
					<div class="flex justify-between text-sm">
						<span class="font-medium {colors.text}">{segment.name}</span>
						<span class="font-mono">{formatCompact(segment.value)}</span>
					</div>
					<div class="h-6 bg-gray-100 rounded-full overflow-hidden">
						<div
							class="h-full {colors.bar} rounded-full transition-all duration-500"
							style="width: {Math.max(segment.percentage, 1)}%"
						>
							<span class="text-white text-xs font-medium px-2 leading-6">
								{segment.percentage.toFixed(1)}%
							</span>
						</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- Summary table -->
		<div class="overflow-x-auto">
			<table class="data-table text-sm">
				<thead>
					<tr>
						<th>Segment</th>
						<th class="text-right">Operating Value</th>
						<th class="text-right">Terminal Value</th>
						<th class="text-right">PV Terminal</th>
						<th class="text-right">% of Total</th>
					</tr>
				</thead>
				<tbody>
					{#each getSegmentBreakdown() as segment}
						{@const colors = segmentColorClasses[segment.type] || segmentColorClasses.rest}
						<tr>
							<td>
								<span class="inline-flex items-center gap-2">
									<span class="w-3 h-3 rounded-full {colors.bar}"></span>
									{segment.name}
								</span>
							</td>
							<td class="text-right font-mono">{formatCompact(segment.value)}</td>
							<td class="text-right font-mono text-gray-500">{formatCompact(segment.terminalValue)}</td>
							<td class="text-right font-mono text-gray-500">{formatCompact(segment.pvTerminal)}</td>
							<td class="text-right font-mono font-medium">{segment.percentage.toFixed(1)}%</td>
						</tr>
					{/each}
				</tbody>
				<tfoot>
					<tr class="border-t-2 border-gray-300">
						<th>Total</th>
						<th class="text-right font-mono">
							{formatCompact(getSegmentBreakdown().reduce((sum, s) => sum + s.value, 0))}
						</th>
						<th colspan="3"></th>
					</tr>
				</tfoot>
			</table>
		</div>
	{:else}
		<div class="text-center py-8 text-gray-500">
			<p>Run calculation to see segment breakdown</p>
		</div>
	{/if}
</div>
