<script lang="ts">
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import { fly } from 'svelte/transition';

	import { CODING_COMMANDS } from '$lib/constants';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	export let onClose: Function;
	export let onChoose: Function;
	let show = false;

	// TODO: renesas
	let commands = [...CODING_COMMANDS];
</script>

<Dropdown
	bind:show
	on:change={(e) => {
		if (e.detail === false) {
			onClose();
		}
	}}
>
	<Tooltip content={'Commands'}>
		<button
			class="bg-transparent hover:bg-gray-100 text-gray-800 dark:text-white dark:hover:bg-gray-800 transition rounded-full p-1.5 outline-hidden focus:outline-hidden"
			type="button"
			aria-label="More"
		>
			<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="size-5">
				<path d="M13 3 L7 17" stroke="currentColor" stroke-width="2"/>
			</svg>
		</button>
	</Tooltip>

	<div slot="content">
		<div
			class="w-70 rounded-2xl px-1 py-1 border border-gray-100 dark:border-gray-800 z-50 bg-white dark:bg-gray-850 dark:text-white shadow-lg max-h-72 overflow-y-auto overflow-x-hidden scrollbar-thin transition"
		>
		{#each commands as command}
			<div in:fly={{ x: -20, duration: 150 }}>
				<button
					class="flex w-full gap-2 items-center px-3 py-1.5 text-sm select-none cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded-xl"
					type="button"
					on:click={() => {
								onChoose(command.content || command.command)
							}}
				>
					<div class="line-clamp-1">{command.title}</div>
				</button>
			</div>
		{/each}
		</div>
	</div>
</Dropdown>
