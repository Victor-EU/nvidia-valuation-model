<script lang="ts">
	import { formatNumber, parseFormattedNumber } from '$lib/utils/formatting';

	interface Props {
		value: number;
		label?: string;
		placeholder?: string;
		decimals?: number;
		min?: number;
		max?: number;
		step?: number;
		prefix?: string;
		suffix?: string;
		disabled?: boolean;
		readonly?: boolean;
		compact?: boolean;
		class?: string;
		onchange?: (value: number) => void;
	}

	let {
		value = $bindable(),
		label,
		placeholder = '0',
		decimals = 0,
		min,
		max,
		step = 1,
		prefix,
		suffix,
		disabled = false,
		readonly = false,
		compact = false,
		class: className = '',
		onchange,
	}: Props = $props();

	let inputElement: HTMLInputElement;
	let isFocused = $state(false);
	let editValue = $state('');

	// Format value for display
	function formatDisplayValue(val: number): string {
		if (!Number.isFinite(val)) return '0';
		if (compact && Math.abs(val) >= 1e6) {
			if (Math.abs(val) >= 1e9) {
				return (val / 1e9).toFixed(2) + 'B';
			}
			return (val / 1e6).toFixed(2) + 'M';
		}
		return formatNumber(val, decimals);
	}

	// Derived display value
	let displayValue = $derived(isFocused ? editValue : formatDisplayValue(value));

	function handleFocus() {
		isFocused = true;
		editValue = value.toString();
		setTimeout(() => inputElement?.select(), 0);
	}

	function handleBlur() {
		isFocused = false;
		const parsed = parseFormattedNumber(editValue);
		let newValue = parsed;

		// Apply bounds
		if (min !== undefined && newValue < min) newValue = min;
		if (max !== undefined && newValue > max) newValue = max;

		value = newValue;
		onchange?.(newValue);
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

<div class="number-input-wrapper {className}">
	{#if label}
		<label class="input-label">{label}</label>
	{/if}
	<div class="relative">
		{#if prefix}
			<span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm pointer-events-none">
				{prefix}
			</span>
		{/if}
		<input
			bind:this={inputElement}
			type="text"
			inputmode="decimal"
			class="input-field-mono"
			class:pl-7={prefix}
			class:pr-16={suffix}
			{placeholder}
			{disabled}
			{readonly}
			value={displayValue}
			onfocus={handleFocus}
			onblur={handleBlur}
			oninput={handleInput}
			onkeydown={handleKeydown}
		/>
		{#if suffix}
			<span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm pointer-events-none">
				{suffix}
			</span>
		{/if}
	</div>
</div>
