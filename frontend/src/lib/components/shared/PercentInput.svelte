<script lang="ts">
	import { formatPercent } from '$lib/utils/formatting';

	interface Props {
		value: number;  // Value as decimal (0.1 = 10%)
		label?: string;
		placeholder?: string;
		decimals?: number;
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
		decimals = 2,
		min = 0,
		max = 1,
		disabled = false,
		readonly = false,
		class: className = '',
		onchange,
	}: Props = $props();

	let inputElement: HTMLInputElement;
	let isFocused = $state(false);
	let editValue = $state('');

	// Format value for display (convert decimal to percentage display)
	function formatDisplayValue(val: number): string {
		if (!Number.isFinite(val)) return '0';
		return (val * 100).toFixed(decimals);
	}

	// Derived display value - shows formatted when not focused, raw when editing
	let displayValue = $derived(isFocused ? editValue : formatDisplayValue(value));

	function handleFocus() {
		isFocused = true;
		// Show raw percentage when editing (e.g., "10" for 10%)
		editValue = (value * 100).toString();
		setTimeout(() => inputElement?.select(), 0);
	}

	function handleBlur() {
		isFocused = false;
		// Parse as percentage and convert to decimal
		let parsed = parseFloat(editValue.replace('%', ''));
		if (isNaN(parsed)) parsed = 0;

		// Convert from percentage to decimal
		let newValue = parsed / 100;

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
			editValue = formatDisplayValue(value);
			inputElement?.blur();
		}
	}
</script>

<div class="percent-input-wrapper {className}">
	{#if label}
		<label class="input-label">{label}</label>
	{/if}
	<div class="relative">
		<input
			bind:this={inputElement}
			type="text"
			inputmode="decimal"
			class="input-field-mono pr-8"
			{placeholder}
			{disabled}
			{readonly}
			value={displayValue}
			onfocus={handleFocus}
			onblur={handleBlur}
			oninput={handleInput}
			onkeydown={handleKeydown}
		/>
		<span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm pointer-events-none">
			%
		</span>
	</div>
</div>
