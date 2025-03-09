<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { flyAndScale } from '$lib/utils/transitions';
	import { getContext, onMount, tick } from 'svelte';

	import { config, user, tools as _tools, mobile } from '$lib/stores';


	const i18n = getContext('i18n');

	export let onClose: Function;

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
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 20 20"
				fill="currentColor"
				class="size-5"
			>
				<path
					d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z"
				/>
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

		<DropdownMenu.Item
			class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl"
			on:click={() => {
			}}
		>
			<div class="line-clamp-1">{$i18n.t('Upload Files')}</div>
		</DropdownMenu.Item>
	</DropdownMenu.Content>
</DropdownMenu.Root>
