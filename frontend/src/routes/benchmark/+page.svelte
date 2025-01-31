<script lang="ts">
	import { onMount } from 'svelte';
	import { benchmarkStore } from '$lib/stores/benchmark';
	import PromptModal from '$lib/components/PromptModal.svelte';
	import type { Client, Prompt } from '$lib/types/benchmark';

	// State
	let selectedClient = '';
	let selectedClientData: Client | null = null;
	let promptModalVisible = false;
	let selectedPrompt: Prompt | null = null;

	// Initialize stores
	$: clients = $benchmarkStore.clients;
	$: testPrompts = $benchmarkStore.prompts;

	// Handle client selection
	function handleClientChange(): void {
		if (!selectedClient) {
			selectedClientData = null;
			return;
		}

		// Find client data
		selectedClientData = clients.find((c) => c.id === selectedClient) || null;
	}

	// Handle prompt view
	function viewPrompt(prompt: Prompt): void {
		selectedPrompt = prompt;
		promptModalVisible = true;
	}

	// Check if benchmark can start
	$: canStartBenchmark =
		selectedClient && selectedClientData?.models?.length > 0 && testPrompts.some((p) => p.selected);

	// Start benchmark
	async function startBenchmark(): Promise<void> {
		if (!canStartBenchmark) return;

		const selectedPrompts = testPrompts.filter((p) => p.selected);
		if (!selectedPrompts.length) {
			alert('Please select at least one test prompt.');
			return;
		}

		try {
			await benchmarkStore.startBenchmark({
				client_id: selectedClient,
				prompts: selectedPrompts.map((p) => p.content),
				hardware: selectedClientData?.hardware
			});
		} catch (error) {
			console.error('Failed to start benchmark:', error);
		}
	}

	onMount(async () => {
		await benchmarkStore.fetchClients();
	});
</script>

<div class="space-y-6 p-6">
	<!-- Client Selection -->
	<div class="space-y-4">
		<h2 class="text-xl font-semibold">Client Selection</h2>
		<div class="form-control">
			<label for="client-select" class="label">
				<span class="label-text">Select Client</span>
			</label>
			<select
				id="client-select"
				bind:value={selectedClient}
				on:change={handleClientChange}
				class="select select-bordered w-full"
			>
				<option value="">Select a client</option>
				{#each clients as client}
					<option value={client.id}>{client.id}</option>
				{/each}
			</select>
		</div>
	</div>

	<!-- Hardware Info -->
	{#if selectedClientData?.hardware}
		<div class="space-y-4">
			<h2 class="text-xl font-semibold">Hardware Configuration</h2>
			<div class="grid grid-cols-2 gap-4">
				{#each [{ id: 'cpu', label: 'CPU', key: 'cpu_name' }, { id: 'cpu-threads', label: 'CPU Threads', key: 'cpu_threads' }, { id: 'memory', label: 'Memory (MB)', key: 'total_memory' }, { id: 'gpu', label: 'GPU', key: 'gpu_name' }] as control}
					<div class="form-control">
						<label for={control.id} class="label">
							<span class="label-text">{control.label}</span>
						</label>
						<input
							id={control.id}
							type="text"
							class="input input-bordered"
							value={selectedClientData.hardware[control.key] || 'N/A'}
							disabled
						/>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Test Prompts -->
	<div class="space-y-4">
		<h2 class="text-xl font-semibold">Test Prompts</h2>
		<div class="space-y-2">
			{#each testPrompts as prompt}
				<div class="flex items-center gap-4 rounded bg-gray-800 p-2">
					<input
						type="checkbox"
						class="form-checkbox"
						bind:checked={prompt.selected}
						disabled={!selectedClient}
					/>
					<span class="flex-grow">{prompt.name}</span>
					<button
						class="rounded bg-purple-600 px-3 py-1 text-white hover:bg-purple-700"
						on:click={() => viewPrompt(prompt)}
					>
						View
					</button>
				</div>
			{/each}
		</div>
	</div>

	<!-- Start Button -->
	<button
		class="w-full rounded bg-purple-600 px-4 py-2 text-white transition-colors hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
		disabled={!canStartBenchmark}
		on:click={startBenchmark}
	>
		Start Benchmark
	</button>

	<!-- Active Benchmarks -->
	<div class="col-span-4 space-y-6">
		<h2 class="text-xl font-semibold">Active Benchmarks</h2>
		{#if $benchmarkStore.activeBenchmarks.length === 0}
			<p class="text-gray-400">No active benchmarks</p>
		{:else}
			{#each $benchmarkStore.activeBenchmarks as benchmark}
				<div class="space-y-2 rounded bg-gray-800 p-4">
					<div class="flex items-center justify-between">
						<span class="font-medium">{benchmark.client_id}</span>
						<span class="text-sm text-gray-400">{benchmark.status}</span>
					</div>
					<div class="text-sm text-gray-400">
						Progress: {benchmark.completed_prompts}/{benchmark.total_prompts}
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>

<!-- Prompt Modal -->
{#if promptModalVisible}
	<PromptModal
		prompt={selectedPrompt}
		on:close={() => {
			promptModalVisible = false;
			selectedPrompt = null;
		}}
	/>
{/if}
