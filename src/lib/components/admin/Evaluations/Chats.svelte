<script lang="ts">
	import { toast } from 'svelte-sonner';
	import fileSaver from 'file-saver';
	const { saveAs } = fileSaver;

	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';

	dayjs.extend(relativeTime);
	import { onMount, getContext } from 'svelte';

	const i18n = getContext('i18n');
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Download from '$lib/components/icons/Download.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import { getAllChatsAdmin, getAllUserChats } from '$lib/apis/chats';

	let limit = 20;
	let page = 1;
	let count = 0;
	let chats = [];

	// Function to load chats
	const loadChats = async () => {
		const res = await getAllChatsAdmin(localStorage.token, limit, page);
		count = res.count;
		chats = res.list;
	};

	// Load chats when the component is first mounted
	onMount(() => {
		loadChats();
	});

	// Watch for changes to `page` and reload chats
	$: if (page) {
		loadChats();
	}

	const exportAllUserChats = async () => {
		toast.message('Exporting... Please wait a bit.');
		let blob = new Blob([JSON.stringify(await getAllUserChats(localStorage.token))], {
			type: 'application/json'
		});
		saveAs(blob, `all-chats-export-${Date.now()}.json`);
	};
</script>

<div class="mt-0.5 mb-2 gap-1 flex flex-row justify-between">
	<div class="flex md:self-center text-lg font-medium px-0.5">
		Chats
		{#if (count)}
			<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />
			<span class="text-lg font-medium text-gray-500 dark:text-gray-300">{count}</span>
		{/if}
	</div>
	<div>
		<div>
			<Tooltip content={$i18n.t('Export')}>
				<button
					class="p-2 rounded-xl hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition font-medium text-sm flex items-center space-x-1"
					on:click={exportAllUserChats}
				>
					<Download class="size-3" />
				</button>
			</Tooltip>
		</div>
	</div>
</div>

<div class="scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm pt-0.5">
	{#if (chats ?? []).length === 0}
		<div class="text-center text-xs text-gray-500 dark:text-gray-400 py-1">
			{'No chats found'}
		</div>
	{:else}
		<table class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-auto max-w-full rounded-sm">
			<thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5">
			<tr>
				<th scope="col" class="px-3 text-left cursor-pointer select-none w-0">
					{$i18n.t('Title')}
				</th>
				<th scope="col" class="px-3 py-1.5 text-right cursor-pointer select-none w-0">
					{$i18n.t('Updated At')}
				</th>
			</tr>
			</thead>
			<tbody>
			{#each chats as chat (chat.id)}
				<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs">
					<td class="py-1 pl-3 flex flex-col">
						<a  href="/s/{chat.id}" target="_blank" class="flex flex-col items-start gap-0.5 h-full">
							<div class="flex flex-col h-full">
								<div class="text-sm font-medium text-gray-600 dark:text-gray-400 flex-1 py-1.5">
									{chat.title}
								</div>
							</div>
						</a>
					</td>
					<td class="px-3 py-1 text-right font-medium">
						{dayjs(chat.updated_at * 1000).fromNow()}
					</td>
				</tr>
			{/each}
			</tbody>
		</table>
	{/if}
</div>

{#if count > limit}
	<Pagination bind:page={page} count={count} perPage={limit} />
{/if}