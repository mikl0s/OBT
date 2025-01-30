<script lang="ts">
	import { onMount } from 'svelte';
	import {
		Button,
		Card,
		Input,
		Label,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell
	} from 'flowbite-svelte';
	import { selectedModels } from '$lib/stores/modelStore';
	import type { Model } from '$lib/types/model';
	import { toast } from '$lib/utils/toast';

	let newModelName = '';
	let newModelPath = '';
	let loading = false;

	async function addModel() {
		if (!newModelName.trim() || !newModelPath.trim()) {
			toast.error('Please provide both model name and path');
			return;
		}

		loading = true;
		try {
			const response = await fetch('/api/v1/models', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					name: newModelName.trim(),
					path: newModelPath.trim()
				})
			});

			if (!response.ok) throw new Error('Failed to add model');

			const model = await response.json();
			$selectedModels = [...$selectedModels, model];
			newModelName = '';
			newModelPath = '';
			toast.success('Model added successfully');
		} catch (error) {
			toast.error('Failed to add model');
			console.error('Error adding model:', error);
		} finally {
			loading = false;
		}
	}

	async function removeModel(model: Model) {
		try {
			await fetch(`/api/v1/models/${encodeURIComponent(model.name)}`, {
				method: 'DELETE'
			});

			$selectedModels = $selectedModels.filter((m) => m.name !== model.name);
			toast.success('Model removed successfully');
		} catch (error) {
			toast.error('Failed to remove model');
			console.error('Error removing model:', error);
		}
	}

	onMount(async () => {
		try {
			const response = await fetch('/api/v1/models');
			const models = await response.json();
			$selectedModels = models;
		} catch (error) {
			toast.error('Failed to load models');
			console.error('Error loading models:', error);
		}
	});
</script>

<Card>
	<h2 class="mb-4 text-xl font-semibold">Models</h2>

	<div class="mb-6">
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<div>
				<Label for="model-name" class="mb-2">Model Name</Label>
				<Input id="model-name" bind:value={newModelName} placeholder="Enter model name" />
			</div>
			<div>
				<Label for="model-path" class="mb-2">Model Path</Label>
				<Input id="model-path" bind:value={newModelPath} placeholder="Enter model path" />
			</div>
		</div>
		<Button class="mt-4" on:click={addModel} disabled={loading}>Add Model</Button>
	</div>

	<Table striped={true}>
		<TableHead>
			<TableHeadCell>Name</TableHeadCell>
			<TableHeadCell>Path</TableHeadCell>
			<TableHeadCell>Actions</TableHeadCell>
		</TableHead>
		<TableBody>
			{#each $selectedModels as model}
				<TableBodyRow>
					<TableBodyCell>{model.name}</TableBodyCell>
					<TableBodyCell>{model.path}</TableBodyCell>
					<TableBodyCell>
						<Button size="xs" color="red" on:click={() => removeModel(model)}>Remove</Button>
					</TableBodyCell>
				</TableBodyRow>
			{/each}
		</TableBody>
	</Table>
</Card>
