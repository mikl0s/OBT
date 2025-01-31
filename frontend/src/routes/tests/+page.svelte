<script lang="ts">
	import { onMount } from 'svelte';
	import { Button, Card, Input, Label, Select, Checkbox, Spinner } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	interface Prompt {
		id: string;
		name: string;
		content: string;
	}

	interface Client {
		id: string;
		name: string;
		model_count: number;
	}

	interface GPU {
		id: string;
		name: string;
		memory: number;
	}

	let prompts: Prompt[] = [];
	let selectedPrompts: string[] = [];
	let loading = true;
	let error: string | null = null;
	let selectedModels: string[] = [];
	let selectedClient = '';
	let clients: Client[] = [];
	let hardwareConfig = {
		use_gpu: false,
		gpu_id: null as string | null,
		threads: 4 // Default value
	};
	let availableGPUs: GPU[] = [];

	// Parse models from URL
	$: {
		const modelsParam = $page.url.searchParams.get('models');
		if (modelsParam) {
			try {
				selectedModels = JSON.parse(decodeURIComponent(modelsParam));
			} catch (e) {
				console.error('Failed to parse models from URL:', e);
			}
		}
	}

	onMount(async () => {
		// Set hardware concurrency if in browser environment
		if (typeof navigator !== 'undefined') {
			hardwareConfig.threads = navigator.hardwareConcurrency || 4;
		}

		try {
			console.log('Fetching data from backend...');
			// Fetch clients, prompts, and hardware info in parallel
			const [clientsRes, promptsRes, gpusRes] = await Promise.all([
				fetch('http://localhost:8881/api/v1/models/clients'),
				fetch('http://localhost:8881/api/v1/prompts/test-suites'),
				fetch('http://localhost:8881/api/v1/hardware/gpu')
			]);

			console.log('Clients response status:', clientsRes.status);
			console.log('Prompts response status:', promptsRes.status);
			console.log('GPUs response status:', gpusRes.status);

			if (!clientsRes.ok) {
				throw new Error(`Failed to fetch clients: ${clientsRes.status} ${await clientsRes.text()}`);
			}
			if (!promptsRes.ok) {
				throw new Error(`Failed to fetch prompts: ${promptsRes.status} ${await promptsRes.text()}`);
			}
			if (!gpusRes.ok) {
				throw new Error(`Failed to fetch GPUs: ${gpusRes.status} ${await gpusRes.text()}`);
			}

			// Parse responses
			const [clientsData, promptsData, gpusData] = await Promise.all([
				clientsRes.json(),
				promptsRes.json(),
				gpusRes.json()
			]).catch((e) => {
				console.error('Failed to parse response data:', e);
				throw e;
			});

			console.log('Received clients:', clientsData);
			console.log('Received prompts:', promptsData);
			console.log('Received GPUs:', gpusData);

			clients = clientsData;
			prompts = promptsData;
			availableGPUs = gpusData;

			// Auto-select first available client
			if (clients.length > 0) {
				selectedClient = clients[0].id;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	});

	async function startTest() {
		if (!selectedClient) {
			error = 'Please select a client';
			return;
		}
		if (selectedModels.length === 0) {
			error = 'Please select at least one model';
			return;
		}

		try {
			const response = await fetch('http://localhost:8881/api/v1/benchmarks/start', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					client_id: selectedClient,
					models: selectedModels,
					prompts: selectedPrompts.length > 0 ? selectedPrompts : undefined,
					hardware: hardwareConfig
				})
			});

			if (!response.ok) throw new Error('Failed to start benchmark');
			await goto('/results');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to start benchmark';
		}
	}
</script>

<div class="container mx-auto space-y-6 p-4">
	<h1 class="mb-4 text-2xl font-bold">Configure Benchmark</h1>

	{#if loading}
		<div class="flex justify-center p-8">
			<Spinner size="12" />
		</div>
	{:else if error}
		<Card color="red">
			<p class="text-red-500">{error}</p>
			<Button color="red" class="mt-4" on:click={() => (error = null)}>Dismiss</Button>
		</Card>
	{:else}
		<div class="grid gap-6 md:grid-cols-2">
			<!-- Client Selection -->
			<Card>
				<h2 class="mb-4 text-xl font-bold">Ollama Client</h2>
				<div class="flex flex-col gap-4">
					<div>
						<Label for="client-select">Select a client...</Label>
						<Select id="client-select" bind:value={selectedClient}>
							<option value="">Select a client...</option>
							{#each clients as client}
								<option value={client.id}>
									{client.id} (v{client.version}) - {client.model_count} models
								</option>
							{/each}
						</Select>
					</div>
				</div>
			</Card>

			<!-- Hardware Configuration -->
			<Card>
				<h2 class="mb-4 text-xl font-bold">Hardware Configuration</h2>
				<div class="space-y-4">
					<div class="flex items-center">
						<Checkbox bind:checked={hardwareConfig.use_gpu} disabled={availableGPUs.length === 0}>
							<Label for="use-gpu-checkbox">Use GPU</Label>
						</Checkbox>
					</div>

					{#if hardwareConfig.use_gpu && availableGPUs.length > 0}
						<div>
							<Label for="gpu-select">Select GPU</Label>
							<Select id="gpu-select" bind:value={hardwareConfig.gpu_id}>
								<option value={null}>Auto-select</option>
								{#each availableGPUs as gpu}
									<option value={gpu.id}>
										GPU #{gpu.id} - {gpu.name} ({gpu.memory}GB)
									</option>
								{/each}
							</Select>
						</div>
					{/if}

					<div>
						<Label for="cpu-threads-input">CPU Threads</Label>
						<Input
							type="number"
							min="1"
							max={navigator.hardwareConcurrency || 8}
							class="block w-full rounded-lg border border-gray-600 bg-gray-700 p-2.5 text-sm text-white focus:border-blue-500 focus:ring-blue-500"
							bind:value={hardwareConfig.threads}
							id="cpu-threads-input"
						/>
					</div>
				</div>
			</Card>

			<!-- Models Selection -->
			<Card>
				<h2 class="mb-4 text-xl font-bold">Selected Models</h2>
				{#if selectedModels.length === 0}
					<p class="text-gray-400">
						No models selected. Go back to the Models page to select models.
					</p>
				{:else}
					<div class="space-y-2">
						{#each selectedModels as model}
							<div class="flex items-center justify-between rounded bg-gray-700 p-2">
								<span>{model}</span>
								<button
									class="text-red-400 hover:text-red-300"
									on:click={() => (selectedModels = selectedModels.filter((m) => m !== model))}
								>
									Remove
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</Card>

			<!-- Prompts Selection -->
			<Card>
				<h2 class="mb-4 text-xl font-bold">Select Prompts</h2>
				<p class="mb-4 text-sm text-gray-400">Leave empty to run all prompts</p>
				<div class="max-h-[300px] space-y-2 overflow-y-auto">
					{#each prompts as prompt}
						<div class="flex items-center justify-between rounded bg-gray-700 p-2">
							<div class="flex items-center">
								<Checkbox value={prompt.id} bind:group={selectedPrompts}>
									<Label for={`prompt-${prompt.id}`}>{prompt.name}</Label>
								</Checkbox>
							</div>
							<button
								class="text-sm text-blue-400 hover:text-blue-300"
								on:click={() => {
									/* TODO: Show prompt content */
								}}
							>
								View
							</button>
						</div>
					{/each}
				</div>
			</Card>
		</div>

		<div class="mt-6 flex justify-end gap-4">
			<Button color="alternative" on:click={() => goto('/models')}>Back to Models</Button>
			<Button
				color="blue"
				disabled={selectedModels.length === 0 || !selectedClient}
				on:click={startTest}
			>
				Start Benchmark
			</Button>
		</div>
	{/if}
</div>
