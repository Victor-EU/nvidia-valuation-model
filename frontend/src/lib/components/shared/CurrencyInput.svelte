<script lang="ts">
	import { parseFormattedNumber } from '$lib/utils/formatting';

	interface Props {
		value: number;
		label?: string;
		placeholder?: string;
		currency?: string;
		decimals?: number;
		compact?: boolean;
		min?: number;
		max?: number;
		disabled?: boolean;
		readonly?: boolean;
		class?: string;
		onchange?: (value: number) => void;
	}

	let {
		value = $bindable(),
		label,
		placeholder = '0',
		currency = 'USD',
		decimals = 0,
		compact = true,
		min,
		max,
		disabled = false,
		readonly = false,
		class: className = '',
		onchange,
	}: Props = $props();

	let inputElement: HTMLInputElement;
	let isFocused = $state(false);
	let editValue = $state('');

	// Format value for display
	function formatDisplayValue(val: number): string {
		if (!Number.isFinite(val) || val === 0) return '0';
		if (compact && Math.abs(val) >= 1e6) {
			if (Math.abs(val) >= 1e9) {
				return (val / 1e9).toFixed(2) + 'B';
			}
			return (val / 1e6).toFixed(2) + 'M';
		}
		return new Intl.NumberFormat('en-US', {
			minimumFractionDigits: decimals,
			maximumFractionDigits: decimals,
		}).format(val);
	}

	// Derived display value - shows formatted when not focused, raw when editing
	let displayValue = $derived(isFocused ? editValue : formatDisplayValue(value));

	function handleFocus() {
		isFocused = true;
		editValue = value.toString();
		setTimeout(() => inputElement?.select(), 0);
	}

	function handleBlur() {
		isFocused = false;
		let parsed = parseFormattedNumber(editValue);

		// Apply bounds
		if (min !== undefined && parsed < min) parsed = min;
		if (max !== undefined && parsed > max) parsed = max;

		value = parsed;
		onchange?.(parsed);
	}

	function handleInput(event: Event) {
		const target = event.target as HTMLInputElement;
		editValue = target.value;
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			inputElement?.blur();
		}
		if (event.key === 'Escape') {
			editValue = value.toString();
			inputElement?.blur();
		}
	}
</script>

<div class="currency-input-wrapper {className}">
	{#if label}
		<label class="input-label">{label}</label>
	{/if}
	<div class="relative">
		<span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm pointer-events-none">
			$
		</span>
		<input
			bind:this={inputElement}
			type="text"
			inputmode="decimal"
			class="input-field-mono pl-7"
			{placeholder}
			{disabled}
			{readonly}
			value={displayValue}
			onfocus={handleFocus}
			onblur={handleBlur}
			oninput={handleInput}
			onkeydown={handleKeydown}
		/>
	</div>
</div>
