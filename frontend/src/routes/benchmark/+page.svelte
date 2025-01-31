<script lang="ts">
	import { onMount } from 'svelte';
	import { benchmarkStore } from '$lib/stores/benchmark';
	import PromptModal from '$lib/components/PromptModal.svelte';
	import type { Prompt, ClientData } from '$lib/types/benchmark';

	// State
	let selectedClient = '';
	let selectedClientData: ClientData | null = null;
	let isDropdownOpen = false;
	let clientPollInterval: ReturnType<typeof setInterval>;
	let promptModalVisible = false;
	let selectedPrompt: Prompt | null = null;

	// Initialize stores
	$: clients = $benchmarkStore.clients;
	$: testPrompts = $benchmarkStore.prompts;
	$: models = $benchmarkStore.models;
	$: selectedModels = $benchmarkStore.selectedModels;

	// Handle client selection
	function handleClientChange(): void {
		selectedClientData = clients.find((c) => c.id === selectedClient) || null;
	}

	// Handle dropdown open/close
	function handleDropdownOpen() {
		isDropdownOpen = true;
		// Fetch clients immediately when opening dropdown
		benchmarkStore.getClients();
		// Start polling while dropdown is open
		clientPollInterval = setInterval(() => {
			benchmarkStore.getClients();
		}, 5000);
	}

	function handleDropdownClose() {
		isDropdownOpen = false;
		if (clientPollInterval) {
			clearInterval(clientPollInterval);
		}
	}

	// Handle prompt view
	function viewPrompt(prompt: Prompt): void {
		selectedPrompt = prompt;
		promptModalVisible = true;
	}

	// Check if benchmark can start
	$: canStartBenchmark =
		selectedClient &&
		selectedClientData?.models?.length > 0 &&
		testPrompts.some((p) => p.selected) &&
		selectedModels.length > 0;

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
				hardware: selectedClientData?.hardware,
				models: selectedModels
			});
		} catch (error) {
			console.error('Failed to start benchmark:', error);
		}
	}

	onMount(async () => {
		try {
			await Promise.all([
				benchmarkStore.getClients(),
				benchmarkStore.getPrompts(),
				benchmarkStore.getModels()
			]);
		} catch (error) {
			console.error('Failed to initialize benchmark data:', error);
		}
	});
</script>

<div class="grid grid-cols-4 gap-6 p-6">
	<!-- Client Selection -->
	<div class="col-span-4 space-y-4">
		<h2 class="text-xl font-semibold">Client Selection</h2>
		<select
			bind:value={selectedClient}
			on:change={handleClientChange}
			on:focus={handleDropdownOpen}
			on:blur={handleDropdownClose}
			class="w-full rounded border border-purple-700 bg-gray-800 p-2 text-gray-100 focus:border-purple-500 focus:ring-2 focus:ring-purple-500"
			aria-expanded={isDropdownOpen}
		>
			<option value="">Select Client</option>
			{#each clients as client}
				<option value={client.id}>
					{client.id} - {client.hardware?.gpu_name || 'CPU Only'}
				</option>
			{/each}
		</select>

		{#if selectedClientData}
			<div class="space-y-4 rounded bg-gray-800 p-4">
				<h3 class="font-medium">Client Details</h3>
				<div class="grid grid-cols-2 gap-4 text-sm">
					<div>
						<span class="text-gray-400">Version:</span>
						<span class="ml-2">{selectedClientData.version}</span>
					</div>
					<div>
						<span class="text-gray-400">Models:</span>
						<span class="ml-2">{selectedClientData.model_count}</span>
					</div>
					<div>
						<span class="text-gray-400">CPU Threads:</span>
						<span class="ml-2">{selectedClientData.hardware?.cpu_threads || 'N/A'}</span>
					</div>
					{#if selectedClientData.hardware?.gpu_name}
						<div>
							<span class="text-gray-400">GPU:</span>
							<span class="ml-2">{selectedClientData.hardware.gpu_name}</span>
						</div>
						<div>
							<span class="text-gray-400">GPU Memory:</span>
							<span class="ml-2">{selectedClientData.hardware.gpu_memory}GB</span>
						</div>
					{/if}
				</div>

				<!-- Model Selection -->
				<div class="space-y-2">
					<h3 class="font-medium">Available Models</h3>
					<div class="grid grid-cols-2 gap-4">
						{#each models.filter((m) => m.client_id === selectedClient) as model}
							<label class="flex items-center space-x-2 rounded bg-gray-800 p-2 hover:bg-gray-700">
								<input
									type="checkbox"
									bind:group={selectedModels}
									value={model.name}
									class="form-checkbox rounded text-purple-500 focus:ring-purple-500"
								/>
								<span>{model.name}</span>
							</label>
						{/each}
					</div>
				</div>
			</div>
		{/if}
	</div>

	<!-- Test Prompts -->
	<div class="col-span-4 space-y-4">
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
{#if promptModalVisible && selectedPrompt}
	<PromptModal
		prompt={selectedPrompt}
		on:close={() => {
			promptModalVisible = false;
			selectedPrompt = null;
		}}
	/>
{/if}
