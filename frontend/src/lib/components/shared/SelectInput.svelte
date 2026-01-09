<script lang="ts">
	interface Option {
		value: string;
		label: string;
	}

	interface Props {
		value: string;
		options: Option[];
		label?: string;
		placeholder?: string;
		disabled?: boolean;
		class?: string;
		onchange?: (value: string) => void;
	}

	let {
		value = $bindable(),
		options,
		label,
		placeholder = 'Select...',
		disabled = false,
		class: className = '',
		onchange,
	}: Props = $props();

	function handleChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		value = target.value;
		onchange?.(target.value);
	}
</script>

<div class="select-input-wrapper {className}">
	{#if label}
		<label class="input-label">{label}</label>
	{/if}
	<select class="input-field" {disabled} {value} onchange={handleChange}>
		{#if placeholder}
			<option value="" disabled>{placeholder}</option>
		{/if}
		{#each options as option}
			<option value={option.value}>{option.label}</option>
		{/each}
	</select>
</div>
