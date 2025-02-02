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
		if (selectedClient) {
			benchmarkStore.getModels(selectedClient);
		}
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

	// Handle prompt selection
	function handlePromptSelection(promptId: string) {
		benchmarkStore.togglePromptSelection(promptId);
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
			await Promise.all([benchmarkStore.getClients(), benchmarkStore.getPrompts()]);
		} catch (error) {
			console.error('Failed to initialize benchmark data:', error);
		}
	});
</script>

<div class="container mx-auto max-w-6xl p-6">
	<!-- Client Selection -->
	<div class="mb-8">
		<h2 class="mb-4 text-xl font-semibold">Client Selection</h2>
		<div class="max-w-md">
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
		</div>

		{#if selectedClientData}
			<div class="mt-4 grid grid-cols-1 gap-6 rounded bg-gray-800 p-4 md:grid-cols-3">
				<!-- CPU Section -->
				<div class="space-y-3">
					<h3 class="font-medium text-purple-400">CPU</h3>
					<div class="space-y-2 text-sm">
						<div>
							<span class="text-gray-400">Model:</span>
							<span class="ml-2 font-medium">{selectedClientData.hardware.cpu.name}</span>
						</div>
						<div>
							<span class="text-gray-400">Architecture:</span>
							<span class="ml-2">{selectedClientData.hardware.cpu.architecture}</span>
						</div>
						<div>
							<span class="text-gray-400">Clock Speed:</span>
							<span class="ml-2">
								{selectedClientData.hardware.cpu.base_clock} GHz
								{#if selectedClientData.hardware.cpu.boost_clock}
									(Boost: {selectedClientData.hardware.cpu.boost_clock} GHz)
								{/if}
							</span>
						</div>
						<div>
							<span class="text-gray-400">Cores/Threads:</span>
							<span class="ml-2">
								{selectedClientData.hardware.cpu.cores}/{selectedClientData.hardware.cpu.threads}
								{#if selectedClientData.hardware.cpu.core_types}
									({selectedClientData.hardware.cpu.core_types.performance_cores}P+
									{selectedClientData.hardware.cpu.core_types.efficiency_cores}E)
								{/if}
							</span>
						</div>
						{#if selectedClientData.hardware.cpu.features?.length}
							<div>
								<span class="text-gray-400">AI Features:</span>
								<span class="ml-2">{selectedClientData.hardware.cpu.features.join(', ')}</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- GPU Section -->
				{#if selectedClientData.hardware.gpu}
					<div class="space-y-3">
						<h3 class="font-medium text-green-400">GPU</h3>
						<div class="space-y-2 text-sm">
							<div>
								<span class="text-gray-400">Model:</span>
								<span class="ml-2 font-medium">{selectedClientData.hardware.gpu.name}</span>
							</div>
							<div>
								<span class="text-gray-400">VRAM:</span>
								<span class="ml-2"
									>{selectedClientData.hardware.gpu.vram_size}MB {selectedClientData.hardware.gpu
										.vram_type}</span
								>
							</div>
							{#if selectedClientData.hardware.gpu.tensor_cores}
								<div>
									<span class="text-gray-400">Tensor Cores:</span>
									<span class="ml-2">{selectedClientData.hardware.gpu.tensor_cores}</span>
								</div>
							{/if}
							{#if selectedClientData.hardware.gpu.compute_capability}
								<div>
									<span class="text-gray-400">Compute:</span>
									<span class="ml-2">{selectedClientData.hardware.gpu.compute_capability}</span>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- NPU Section -->
				{#if selectedClientData.hardware.npu}
					<div class="space-y-3">
						<h3 class="font-medium text-blue-400">NPU</h3>
						<div class="space-y-2 text-sm">
							{#if selectedClientData.hardware.npu.name}
								<div>
									<span class="text-gray-400">Model:</span>
									<span class="ml-2 font-medium">{selectedClientData.hardware.npu.name}</span>
								</div>
							{/if}
							{#if selectedClientData.hardware.npu.compute_power}
								<div>
									<span class="text-gray-400">Performance:</span>
									<span class="ml-2">{selectedClientData.hardware.npu.compute_power} TOPS</span>
								</div>
							{/if}
							{#if selectedClientData.hardware.npu.precision_support?.length}
								<div>
									<span class="text-gray-400">Precision:</span>
									<span class="ml-2"
										>{selectedClientData.hardware.npu.precision_support.join(', ')}</span
									>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- System Memory -->
				<div class="col-span-3 mt-2 text-sm">
					<span class="text-gray-400">System Memory:</span>
					<span class="ml-2">{Math.round(selectedClientData.hardware.total_memory / 1024)} GB</span>
				</div>
			</div>
		{/if}
	</div>

	<!-- Model Selection -->
	{#if selectedClient && models.length > 0}
		<div class="mb-8">
			<h2 class="mb-4 text-xl font-semibold">Available Models</h2>
			<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
				{#each models as model}
					<label class="flex items-center gap-2 rounded bg-gray-800 p-2">
						<input
							type="checkbox"
							bind:group={selectedModels}
							value={model.name}
							class="form-checkbox rounded text-purple-500 focus:ring-purple-500"
						/>
						<div class="flex flex-col">
							<span class="font-medium">{model.name}</span>
							<span class="text-sm text-gray-400">{Math.round(model.size / 1024 / 1024)} MB</span>
						</div>
					</label>
				{/each}
			</div>
		</div>
	{:else if selectedClient}
		<div class="mb-8 text-center text-gray-400">No models available for this client</div>
	{/if}

	<!-- Test Prompts -->
	<div class="mb-8">
		<h2 class="mb-4 text-xl font-semibold">Test Prompts</h2>
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
			{#each testPrompts as prompt}
				<div
					class="flex flex-col justify-between rounded-lg border border-gray-700 bg-gray-800 p-4"
				>
					<div>
						<h3 class="mb-2 font-medium text-gray-200">{prompt.name}</h3>
						<p class="mb-4 line-clamp-2 text-sm text-gray-400">{prompt.description}</p>
					</div>
					<div class="flex items-center justify-between">
						<button
							class="text-sm text-purple-400 hover:text-purple-300"
							on:click={() => viewPrompt(prompt)}
						>
							View Details
						</button>
						<label class="relative inline-flex cursor-pointer items-center">
							<input
								type="checkbox"
								class="peer sr-only"
								checked={prompt.selected}
								on:change={() => handlePromptSelection(prompt.id)}
							/>
							<div class="peer h-6 w-11 rounded-full bg-gray-700">
								<div
									class="absolute left-[2px] top-[2px] h-5 w-5 rounded-full border border-gray-300 bg-white transition-all peer-checked:translate-x-full peer-checked:border-white peer-checked:bg-purple-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-800"
								></div>
							</div>
						</label>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- Start Button -->
	<div class="mb-8 flex justify-center">
		<button
			class="inline-flex min-w-[200px] items-center justify-center rounded bg-purple-600 px-6 py-2 font-medium text-white transition-colors hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
			disabled={!canStartBenchmark}
			on:click={startBenchmark}
		>
			Start Benchmark
		</button>
	</div>

	<!-- Active Benchmarks -->
	<div class="mb-8">
		<h2 class="mb-4 text-xl font-semibold">Active Benchmarks</h2>
		{#if $benchmarkStore.activeBenchmarks.length === 0}
			<p class="text-gray-400">No active benchmarks</p>
		{:else}
			<div class="space-y-4">
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
			</div>
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
