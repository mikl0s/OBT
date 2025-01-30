<script lang="ts">
	import { Button } from 'flowbite-svelte';
	import { onMount } from 'svelte';
	import type { TestPrompt } from '$lib/types/benchmark';
	import { testSuites, selectedPromptIds, loadTestSuites } from '$lib/stores/promptStore';

	onMount(async () => {
		await loadTestSuites();
	});

	function handlePromptSelect(prompt: TestPrompt): void {
		selectedPromptIds.update((ids) => [...ids, prompt.id]);
	}
</script>

<div class="space-y-4">
	{#each $testSuites as suite}
		<div>
			<h3 class="mb-2 text-lg font-semibold">{suite.name}</h3>
			<div class="space-y-2">
				{#each suite.prompts as prompt}
					<div class="flex items-center justify-between rounded bg-gray-700 p-2">
						<span class="text-sm">{prompt.name}</span>
						<Button
							size="xs"
							on:click={() => handlePromptSelect(prompt)}
							disabled={$selectedPromptIds.includes(prompt.id)}
						>
							{$selectedPromptIds.includes(prompt.id) ? 'Added' : 'Add'}
						</Button>
					</div>
				{/each}
			</div>
		</div>
	{/each}
</div>
