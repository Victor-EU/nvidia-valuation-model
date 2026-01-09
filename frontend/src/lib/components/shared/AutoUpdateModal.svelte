<script lang="ts">
	import { api, type CompanyData } from '$lib/services/api';
	import { modelState } from '$lib/stores/model.svelte';
	import { formatCurrency, formatNumber, formatPercent } from '$lib/utils/formatting';

	interface Props {
		open: boolean;
		onclose: () => void;
	}

	let { open = $bindable(), onclose }: Props = $props();

	let ticker = $state('NVDA');
	let isLoading = $state(false);
	let error = $state<string | null>(null);
	let fetchedData = $state<CompanyData | null>(null);
	let step = $state<'input' | 'preview'>('input');

	// Current values from model state
	function getCurrentValues() {
		return {
			company_name: modelState.companyName,
			revenues: modelState.baseYearData.revenues,
			operating_income: modelState.baseYearData.operating_income,
			interest_expense: modelState.baseYearData.interest_expense,
			book_equity: modelState.baseYearData.book_equity,
			book_debt: modelState.baseYearData.book_debt,
			cash: modelState.baseYearData.cash,
			shares: modelState.baseYearData.shares,
			stock_price: modelState.baseYearData.stock_price,
			effective_tax_rate: modelState.baseYearData.effective_tax_rate,
		};
	}

	async function fetchData() {
		if (!ticker.trim()) {
			error = 'Please enter a ticker symbol';
			return;
		}

		isLoading = true;
		error = null;

		try {
			fetchedData = await api.data.fetch(ticker.trim().toUpperCase());
			step = 'preview';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to fetch data';
			fetchedData = null;
		} finally {
			isLoading = false;
		}
	}

	function applyData() {
		if (!fetchedData) return;

		// Use the new has_full_financials flag
		const hasFullData = fetchedData.has_full_financials;

		// Always update company name and stock price (these are always available)
		if (fetchedData.company_name) {
			modelState.companyName = fetchedData.company_name;
		}
		if (fetchedData.stock_price > 0) {
			modelState.baseYearData = {
				...modelState.baseYearData,
				stock_price: fetchedData.stock_price,
			};
		}

		// Update shares outstanding if available
		if (fetchedData.shares_outstanding > 0) {
			modelState.baseYearData = {
				...modelState.baseYearData,
				shares: fetchedData.shares_outstanding,
			};
		}

		// Only update full financial data if available
		if (hasFullData) {
			modelState.baseYearData = {
				...modelState.baseYearData,
				revenues: fetchedData.revenues,
				operating_income: fetchedData.operating_income,
				interest_expense: fetchedData.interest_expense,
				book_equity: fetchedData.book_equity,
				book_debt: fetchedData.book_debt,
				cash: fetchedData.cash,
			};

			// Only update effective tax rate if it looks valid
			if (fetchedData.effective_tax_rate > 0 && fetchedData.effective_tax_rate < 0.5) {
				modelState.baseYearData = {
					...modelState.baseYearData,
					effective_tax_rate: fetchedData.effective_tax_rate,
				};
			}
		}

		modelState.markDirty();
		handleClose();
	}

	function handleClose() {
		open = false;
		step = 'input';
		fetchedData = null;
		error = null;
		onclose();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			handleClose();
		}
		if (event.key === 'Enter' && step === 'input' && !isLoading) {
			fetchData();
		}
	}

	// Comparison row helper
	interface ComparisonRow {
		label: string;
		current: number | string;
		new: number | string;
		format: 'currency' | 'number' | 'percent' | 'text';
		changed: boolean;
		available: boolean;
		changePercent: number | null; // For showing % change
		direction: 'up' | 'down' | 'same' | null;
	}

	function calculateChange(current: number, newVal: number): { percent: number | null; direction: 'up' | 'down' | 'same' } {
		if (current === 0 && newVal === 0) return { percent: null, direction: 'same' };
		if (current === 0) return { percent: null, direction: newVal > 0 ? 'up' : 'down' };

		const percent = ((newVal - current) / Math.abs(current)) * 100;
		const direction = Math.abs(percent) < 0.1 ? 'same' : (percent > 0 ? 'up' : 'down');
		return { percent, direction };
	}

	function getComparisonRows(): ComparisonRow[] {
		if (!fetchedData) return [];
		const current = getCurrentValues();

		// Use the flag from the API
		const hasFullData = fetchedData.has_full_financials;

		const rows: ComparisonRow[] = [];

		// Company Name
		const nameChanged = Boolean(fetchedData.company_name && current.company_name !== fetchedData.company_name);
		rows.push({
			label: 'Company Name',
			current: current.company_name,
			new: fetchedData.company_name || current.company_name,
			format: 'text',
			changed: nameChanged,
			available: Boolean(fetchedData.company_name),
			changePercent: null,
			direction: nameChanged ? 'up' : 'same',
		});

		// Stock Price
		const priceChange = calculateChange(current.stock_price, fetchedData.stock_price);
		rows.push({
			label: 'Stock Price',
			current: current.stock_price,
			new: fetchedData.stock_price,
			format: 'currency',
			changed: fetchedData.stock_price > 0 && Math.abs(current.stock_price - fetchedData.stock_price) > 0.01,
			available: fetchedData.stock_price > 0,
			changePercent: priceChange.percent,
			direction: priceChange.direction,
		});

		// Shares Outstanding
		const sharesChange = calculateChange(current.shares, fetchedData.shares_outstanding);
		rows.push({
			label: 'Shares Outstanding',
			current: current.shares,
			new: fetchedData.shares_outstanding,
			format: 'number',
			changed: fetchedData.shares_outstanding > 0 && Math.abs(current.shares - fetchedData.shares_outstanding) > 1000000,
			available: fetchedData.shares_outstanding > 0,
			changePercent: sharesChange.percent,
			direction: sharesChange.direction,
		});

		// Financial data rows
		const financialFields: Array<{
			label: string;
			currentKey: keyof ReturnType<typeof getCurrentValues>;
			newKey: keyof CompanyData;
		}> = [
			{ label: 'Revenues (TTM)', currentKey: 'revenues', newKey: 'revenues' },
			{ label: 'Operating Income (TTM)', currentKey: 'operating_income', newKey: 'operating_income' },
			{ label: 'Interest Expense (TTM)', currentKey: 'interest_expense', newKey: 'interest_expense' },
			{ label: 'Book Equity', currentKey: 'book_equity', newKey: 'book_equity' },
			{ label: 'Book Debt', currentKey: 'book_debt', newKey: 'book_debt' },
			{ label: 'Cash', currentKey: 'cash', newKey: 'cash' },
		];

		for (const field of financialFields) {
			const currentVal = current[field.currentKey] as number;
			const newVal = hasFullData ? (fetchedData[field.newKey] as number) : currentVal;
			const change = calculateChange(currentVal, newVal);

			rows.push({
				label: field.label,
				current: currentVal,
				new: newVal,
				format: 'currency',
				changed: hasFullData && Math.abs(currentVal - (fetchedData[field.newKey] as number)) > 1000,
				available: hasFullData,
				changePercent: change.percent,
				direction: change.direction,
			});
		}

		// Effective Tax Rate
		const taxChange = calculateChange(current.effective_tax_rate, fetchedData.effective_tax_rate);
		rows.push({
			label: 'Effective Tax Rate',
			current: current.effective_tax_rate,
			new: hasFullData ? fetchedData.effective_tax_rate : current.effective_tax_rate,
			format: 'percent',
			changed: hasFullData && Math.abs(current.effective_tax_rate - fetchedData.effective_tax_rate) > 0.01,
			available: hasFullData && fetchedData.effective_tax_rate > 0,
			changePercent: taxChange.percent,
			direction: taxChange.direction,
		});

		return rows;
	}

	function formatChangePercent(percent: number | null): string {
		if (percent === null) return '';
		const sign = percent >= 0 ? '+' : '';
		return `${sign}${percent.toFixed(1)}%`;
	}

	function formatValue(value: number | string, format: string): string {
		if (typeof value === 'string') return value;
		switch (format) {
			case 'currency':
				return formatCurrency(value);
			case 'percent':
				return formatPercent(value);
			case 'number':
				return formatNumber(value, 0);
			default:
				return String(value);
		}
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
		role="dialog"
		aria-modal="true"
		onkeydown={handleKeydown}
	>
		<div class="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
				<div>
					<h2 class="text-lg font-semibold text-gray-900">
						{step === 'input' ? 'Auto Update Data' : 'Review Changes'}
					</h2>
					<p class="text-sm text-gray-500">
						{step === 'input'
							? 'Fetch latest financial data from Yahoo Finance'
							: `Data from ${fetchedData?.data_source || 'Yahoo Finance'}`}
					</p>
				</div>
				<button
					class="text-gray-400 hover:text-gray-600 transition-colors"
					onclick={handleClose}
					aria-label="Close"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto p-6">
				{#if step === 'input'}
					<!-- Ticker Input Step -->
					<div class="space-y-4">
						<div>
							<label for="ticker" class="block text-sm font-medium text-gray-700 mb-1">
								Ticker Symbol
							</label>
							<div class="flex gap-2">
								<input
									id="ticker"
									type="text"
									class="input-field flex-1 uppercase"
									placeholder="NVDA"
									bind:value={ticker}
									disabled={isLoading}
								/>
								<button
									class="btn-primary"
									onclick={fetchData}
									disabled={isLoading || !ticker.trim()}
								>
									{#if isLoading}
										<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
											<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
											<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
										</svg>
										Fetching...
									{:else}
										Fetch Data
									{/if}
								</button>
							</div>
						</div>

						{#if error}
							<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
								{error}
							</div>
						{/if}

						<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
							<h4 class="text-sm font-medium text-blue-800 mb-2">Available Data:</h4>
							<ul class="text-sm text-blue-700 space-y-1">
								<li>Stock price (real-time)</li>
								<li>Company name</li>
							</ul>
							<div class="mt-3 pt-3 border-t border-blue-200">
								<h4 class="text-sm font-medium text-blue-800 mb-2">Note on Financial Data:</h4>
								<p class="text-xs text-blue-600">
									Yahoo Finance heavily rate-limits their financial data API. TTM revenue,
									operating income, and balance sheet data may not be available through this method.
								</p>
								<p class="text-xs text-blue-600 mt-2">
									For full financial data, please enter values manually from SEC filings (10-K, 10-Q)
									or use data providers like Bloomberg, Refinitiv, or FactSet.
								</p>
							</div>
						</div>
					</div>
				{:else if step === 'preview' && fetchedData}
					<!-- Preview Step -->
					<div class="space-y-4">
						<!-- Data Quality Indicator -->
						{#if fetchedData.has_full_financials}
							<div class="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
								<svg class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
								</svg>
								<span class="text-sm font-medium text-green-800">Full financial data available</span>
							</div>
						{:else}
							<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
								<div class="flex items-start gap-2">
									<svg class="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
										<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
									</svg>
									<div>
										<span class="text-sm font-medium text-yellow-800">Partial data available</span>
										<p class="text-xs text-yellow-700 mt-1">
											Yahoo Finance limits free API access. Only stock price is available.
											You can still update the price, then manually enter financial data from SEC filings.
										</p>
									</div>
								</div>
							</div>
						{/if}

						<!-- Metadata -->
						<div class="bg-gray-50 rounded-lg p-4 text-sm">
							<div class="grid grid-cols-2 gap-4">
								<div>
									<span class="text-gray-500">Ticker:</span>
									<span class="font-medium ml-2">{fetchedData.ticker}</span>
								</div>
								<div>
									<span class="text-gray-500">Currency:</span>
									<span class="font-medium ml-2">{fetchedData.currency}</span>
								</div>
								<div>
									<span class="text-gray-500">Data As Of:</span>
									<span class="font-medium ml-2">{new Date(fetchedData.data_as_of).toLocaleString()}</span>
								</div>
								<div>
									<span class="text-gray-500">Most Recent Quarter:</span>
									<span class="font-medium ml-2">{fetchedData.most_recent_quarter || 'N/A'}</span>
								</div>
							</div>
						</div>

						<!-- Data Notes -->
						{#if fetchedData.data_notes && fetchedData.data_notes.length > 0}
							<div class="bg-gray-50 rounded-lg p-4">
								<h4 class="text-sm font-medium text-gray-700 mb-2">Data Sources:</h4>
								<ul class="text-xs text-gray-600 space-y-1">
									{#each fetchedData.data_notes as note}
										<li class="flex items-start gap-1">
											<span class="text-gray-400">•</span>
											<span>{note}</span>
										</li>
									{/each}
								</ul>
							</div>
						{/if}

						<!-- Comparison Table -->
						<div class="overflow-x-auto">
							<table class="w-full text-sm">
								<thead>
									<tr class="border-b border-gray-200">
										<th class="text-left py-2 px-3 font-medium text-gray-500">Field</th>
										<th class="text-right py-2 px-3 font-medium text-gray-500">Current</th>
										<th class="text-right py-2 px-3 font-medium text-gray-500">New</th>
										<th class="text-right py-2 px-3 font-medium text-gray-500">Change</th>
									</tr>
								</thead>
								<tbody>
									{#each getComparisonRows() as row}
										<tr class="border-b border-gray-100" class:bg-blue-50={row.changed} class:opacity-50={!row.available}>
											<td class="py-2 px-3 font-medium text-gray-700">
												{row.label}
												{#if !row.available}
													<span class="text-xs text-gray-400 ml-1">(not available)</span>
												{/if}
											</td>
											<td class="py-2 px-3 text-right font-mono text-gray-500">
												{formatValue(row.current, row.format)}
											</td>
											<td class="py-2 px-3 text-right font-mono" class:text-blue-600={row.changed} class:font-semibold={row.changed}>
												{#if row.available}
													{formatValue(row.new, row.format)}
												{:else}
													<span class="text-gray-400">—</span>
												{/if}
											</td>
											<td class="py-2 px-3 text-right">
												{#if !row.available}
													<span class="text-gray-300">—</span>
												{:else if row.changed}
													<span class="inline-flex items-center gap-1 text-sm font-medium"
														class:text-green-600={row.direction === 'up'}
														class:text-red-600={row.direction === 'down'}>
														{#if row.direction === 'up'}
															<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5m0 0l5 5m-5-5v12" />
															</svg>
														{:else if row.direction === 'down'}
															<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 13l-5 5m0 0l-5-5m5 5V6" />
															</svg>
														{/if}
														{#if row.changePercent !== null}
															<span>{formatChangePercent(row.changePercent)}</span>
														{:else}
															<span>updated</span>
														{/if}
													</span>
												{:else}
													<span class="text-gray-400 text-xs">no change</span>
												{/if}
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>

						<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
							<strong>Info:</strong> Clicking "Apply Changes" will update your model's base year data with the latest SEC filings.
							Segment-specific inputs (AI, Auto market sizes) will not be modified.
						</div>
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
				{#if step === 'input'}
					<button class="btn-secondary" onclick={handleClose}>
						Cancel
					</button>
				{:else}
					<button class="btn-secondary" onclick={() => { step = 'input'; fetchedData = null; }}>
						Back
					</button>
					<button class="btn-primary" onclick={applyData}>
						Apply Changes
					</button>
				{/if}
			</div>
		</div>
	</div>
{/if}
