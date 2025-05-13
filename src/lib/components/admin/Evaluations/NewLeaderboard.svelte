<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { models } from '$lib/stores';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import { getFeedbacksEvaluate } from '$lib/apis/evaluations';

	const i18n = getContext('i18n');

	let rankedModels = [];

	let loadingLeaderboard = true;

	onMount(async () => {
		const feedbacksEvaluate: FeedbackEvaluate[] = await getFeedbacksEvaluate(localStorage.token);
		rankedModels = $models
			.filter((m) => m?.owned_by !== 'arena' && (m?.info?.meta?.hidden ?? false) !== true)
			.map((model) => {
				const stats = feedbacksEvaluate.find((e) => e.model_id == model.id);
				return {
					...model,
					stats: {
						count: stats ? stats.count : 0,
						possible: stats ? stats.possible : 0,
						negative: stats ? stats.negative : 0,
						won: stats ? stats.possible.toString() : '-',
						lost: stats ? stats.negative.toString() : '-'
					}
				};
			})
			.sort((a, b) => {
				return (b.stats.count == 0 && a.stats.count != 0 ? -1 : b.stats.count != 0 && a.stats.count == 0 ? 1 : 0) || (b.stats.possible - a.stats.possible)
					|| (a.stats.negative - b.stats.negative)
					|| (b.stats.count - a.stats.count)
					|| a.name.localeCompare(b.name);
			});
		loadingLeaderboard = false;
	});
</script>

<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
	<div class="flex md:self-center text-lg font-medium px-0.5 shrink-0 items-center">
		<div class=" gap-1">
			{$i18n.t('Leaderboard')}
		</div>

		<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />

		<span class="text-lg font-medium text-gray-500 dark:text-gray-300 mr-1.5"
		>{rankedModels.length}</span
		>
	</div>
</div>

<div
	class="scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm pt-0.5"
>
	{#if loadingLeaderboard}
		<div class=" absolute top-0 bottom-0 left-0 right-0 flex">
			<div class="m-auto">
				<Spinner />
			</div>
		</div>
	{/if}
	{#if (rankedModels ?? []).length === 0}
		<div class="text-center text-xs text-gray-500 dark:text-gray-400 py-1">
			{$i18n.t('No models found')}
		</div>
	{:else}
		<table
			class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-auto max-w-full rounded {loadingLeaderboard
				? 'opacity-20'
				: ''}"
		>
			<thead
				class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5"
			>
			<tr class="">
				<th scope="col" class="px-3 py-1.5 cursor-pointer select-none w-3">
					{$i18n.t('RK')}
				</th>
				<th scope="col" class="px-3 py-1.5 cursor-pointer select-none">
					{$i18n.t('Model')}
				</th>
				<th scope="col" class="px-3 py-1.5 text-right cursor-pointer select-none w-5">
					{$i18n.t('Won')}
				</th>
				<th scope="col" class="px-3 py-1.5 text-right cursor-pointer select-none w-5">
					{$i18n.t('Lost')}
				</th>
			</tr>
			</thead>
			<tbody class="">
			{#each rankedModels as model, modelIdx (model.id)}
				<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs group">
					<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit">
						<div class=" line-clamp-1">
							{model?.stats?.count ? modelIdx + 1 : '-'}
						</div>
					</td>
					<td class="px-3 py-1.5 flex flex-col justify-center">
						<div class="flex items-center gap-2">
							<div class="shrink-0">
								<img
									src={model?.info?.meta?.profile_image_url ?? '/favicon.png'}
									alt={model.name}
									class="size-5 rounded-full object-cover shrink-0"
								/>
							</div>

							<div class="font-medium text-gray-800 dark:text-gray-200 pr-4">
								{model.name}
							</div>
						</div>
					</td>
					<td class=" px-3 py-1.5 text-right font-semibold text-green-500">
						<div class=" w-10">
							{#if model.stats.won === '-'}
								-
							{:else}
									<span class="hidden group-hover:inline"
									>{((model.stats.won / model.stats.count) * 100).toFixed(1)}%</span
									>
								<span class=" group-hover:hidden">{model.stats.won}</span>
							{/if}
						</div>
					</td>

					<td class="px-3 py-1.5 text-right font-semibold text-red-500">
						<div class=" w-10">
							{#if model.stats.lost === '-'}
								-
							{:else}
									<span class="hidden group-hover:inline"
									>{((model.stats.lost / model.stats.count) * 100).toFixed(1)}%</span
									>
								<span class=" group-hover:hidden">{model.stats.lost}</span>
							{/if}
						</div>
					</td>
				</tr>
			{/each}
			</tbody>
		</table>
	{/if}
</div>
