<script lang="ts">
	interface Props {
		checked: boolean;
		label?: string;
		description?: string;
		disabled?: boolean;
		class?: string;
		onchange?: (checked: boolean) => void;
	}

	let {
		checked = $bindable(),
		label,
		description,
		disabled = false,
		class: className = '',
		onchange,
	}: Props = $props();

	function handleClick() {
		if (disabled) return;
		checked = !checked;
		onchange?.(checked);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === ' ' || event.key === 'Enter') {
			event.preventDefault();
			handleClick();
		}
	}
</script>

<div class="toggle-wrapper flex items-start gap-3 {className}">
	<button
		type="button"
		role="switch"
		aria-checked={checked}
		{disabled}
		class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-nvidia-green-500 focus:ring-offset-2"
		class:bg-nvidia-green-500={checked}
		class:bg-gray-200={!checked}
		class:cursor-not-allowed={disabled}
		class:opacity-50={disabled}
		onclick={handleClick}
		onkeydown={handleKeydown}
	>
		<span
			class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
			class:translate-x-5={checked}
			class:translate-x-0={!checked}
		></span>
	</button>
	{#if label || description}
		<div class="flex flex-col">
			{#if label}
				<span
					class="text-sm font-medium text-gray-900"
					class:text-gray-400={disabled}
				>
					{label}
				</span>
			{/if}
			{#if description}
				<span class="text-sm text-gray-500">{description}</span>
			{/if}
		</div>
	{/if}
</div>
