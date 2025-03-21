<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { flyAndScale } from '$lib/utils/transitions';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import { chatTabSettings } from '$lib/stores';

	export let initNewChat: Function;

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
				{$chatTabSettings.tabs.find(t => t.tab === $chatTabSettings.selected)?.title ?? '[Unknown]'}
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
		{#each $chatTabSettings.tabs as tab}
		<DropdownMenu.Item
			class="flex gap-2 items-center px-3 py-2 my-1 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl {tab.tab === $chatTabSettings.selected ? 'bg-gray-50 dark:bg-gray-800' : ''}"
			on:click={() => {
				chatTabSettings.update(last => ({...last, selected: tab.tab}))
				localStorage.setItem('_tab', tab.tab);
				initNewChat();
		}}
		>
			<div class="line-clamp-1">{tab.title}</div>
		</DropdownMenu.Item>
		{/each}
	</DropdownMenu.Content>
</DropdownMenu.Root>
