<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { flyAndScale } from '$lib/utils/transitions';
	import { prompts } from '$lib/stores';

	import { CODING_COMMANDS } from '$lib/constants';

	export let onClose: Function;
	export let onChoose: Function;

	// TODO: renesas
	let commands = [...($prompts ?? []), ...CODING_COMMANDS];
</script>

<DropdownMenu.Root
	closeFocus={false}
	onOpenChange={(state) => {
		if (!state) {
			onClose();
		}
	}}
	typeahead={false}
>
	<DropdownMenu.Trigger>
		<button
			class="bg-transparent hover:bg-gray-100 text-gray-800 dark:text-white dark:hover:bg-gray-800 transition rounded-full p-1.5 outline-hidden focus:outline-hidden"
			type="button"
			aria-label="More"
		>
			<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="size-5">
				<path d="M13 3 L7 17" stroke="currentColor" stroke-width="2"/>
			</svg>
		</button>
	</DropdownMenu.Trigger>

	<DropdownMenu.Content
		class="w-full max-w-[220px] rounded-xl px-1 py-1  border-gray-300/30 dark:border-gray-700/50 z-50 bg-white dark:bg-gray-850 dark:text-white shadow-sm"
		sideOffset={15}
		alignOffset={-8}
		side="top"
		align="start"
		transition={flyAndScale}
	>
		{#each commands as command}
			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl"
				on:click={() => {
				onChoose(command.content || command.command)
			}}
			>
				<div class="line-clamp-1">{command.title}</div>
			</DropdownMenu.Item>
		{/each}
	</DropdownMenu.Content>
</DropdownMenu.Root>
