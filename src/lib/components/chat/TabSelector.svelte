<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { flyAndScale } from '$lib/utils/transitions';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';

	export let selectedTab = 'Coding';
	export let onChoose: Function;
	export let initNewChat: Function;
	// let show = false;
</script>

<DropdownMenu.Root
	closeFocus={false}
	onOpenChange={(state) => {
						if (!state) {
							console.log(state)
							// onClose();
						}
					}}
	typeahead={false}
>
	<DropdownMenu.Trigger>
		<button
			class="flex mr-4 bg-transparent text-gray-800 dark:text-white x	transition rounded-full p-1.5 outline-hidden focus:outline-hidden"
			type="button"
			aria-label="More"
		>
			<span>
				{selectedTab}
			</span>
			<ChevronDown className=" self-center ml-2 size-3" strokeWidth="2.5" />
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
		<DropdownMenu.Item
			class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl"
			on:click={() => {
				onChoose(`Coding`);
				initNewChat();
		}}
		>
			<div class="line-clamp-1">Coding</div>
		</DropdownMenu.Item>
		<DropdownMenu.Item
			class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl"
			on:click={() => {
				onChoose(`Requirement`);
				initNewChat();
		}}
		>
			<div class="line-clamp-1">Requirement</div>
		</DropdownMenu.Item>
	</DropdownMenu.Content>
</DropdownMenu.Root>
