<script lang="ts">
	import {
		Button,
		Card,
		Spinner,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell
	} from 'flowbite-svelte';
	import BenchmarkComparison from './BenchmarkComparison.svelte';
	import ModelManager from './ModelManager.svelte';
	import type { BenchmarkResult } from '$lib/types/benchmark';
	import { toast } from '$lib/utils/toast';

	interface BenchmarkConfig {
		model_name: string;
		prompt_config: {
			prompt: string;
			completion_tokens: number;
		};
		num_iterations: number;
		temperature: number;
		top_p: number;
		top_k: number;
		repeat_penalty: number;
	}

	let benchmarkResults: BenchmarkResult[] = [];
	let isRunning = false;

	// Load saved benchmark config from localStorage or use defaults
	const STORAGE_KEY = 'benchmark_config';
	const savedConfig =
		typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;

	let config: BenchmarkConfig = savedConfig
		? JSON.parse(savedConfig)
		: {
				model_name: '',
				prompt_config: {
					prompt: '',
					completion_tokens: 100
				},
				num_iterations: 3,
				temperature: 0.7,
				top_p: 1.0,
				top_k: 40,
				repeat_penalty: 1.1
			};

	// Save config whenever it changes
	$: if (config && typeof localStorage !== 'undefined') {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
	}

	async function loadResults() {
		try {
			const response = await fetch('/api/v1/benchmarks/results');
			benchmarkResults = await response.json();
		} catch {
			toast.error('Failed to load benchmark results');
		}
	}

	async function deleteBenchmark(id: string) {
		try {
			await fetch(`/api/v1/benchmarks/results/${id}`, { method: 'DELETE' });
			await loadResults();
			toast.success('Benchmark deleted successfully');
		} catch {
			toast.error('Failed to delete benchmark');
		}
	}
</script>

<div class="container mx-auto p-4">
	<h1 class="mb-6 text-3xl font-bold">Model Benchmarks</h1>

	<div class="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
		<ModelManager />
	</div>

	<Card>
		<h2 class="mb-4 text-xl font-semibold">Benchmark Results</h2>

		<Table striped={true}>
			<TableHead>
				<TableHeadCell>Model</TableHeadCell>
				<TableHeadCell>Status</TableHeadCell>
				<TableHeadCell>Tokens/s</TableHeadCell>
				<TableHeadCell>Latency (ms)</TableHeadCell>
				<TableHeadCell>Actions</TableHeadCell>
			</TableHead>
			<TableBody>
				{#each benchmarkResults as result}
					<TableBodyRow>
						<TableBodyCell>{result.config.model_name}</TableBodyCell>
						<TableBodyCell>
							{#if isRunning}
								<div class="flex items-center">
									<Spinner size="sm" class="mr-2" />
									Running...
								</div>
							{:else}
								{result.status}
							{/if}
						</TableBodyCell>
						<TableBodyCell>{result.average_tokens_per_second.toFixed(2)}</TableBodyCell>
						<TableBodyCell>{result.average_latency_ms.toFixed(2)}</TableBodyCell>
						<TableBodyCell>
							<Button size="xs" color="red" on:click={() => deleteBenchmark(result.id)}>
								Delete
							</Button>
						</TableBodyCell>
					</TableBodyRow>
				{/each}
			</TableBody>
		</Table>
	</Card>

	{#if benchmarkResults.length > 0}
		<div class="mt-6">
			<BenchmarkComparison results={benchmarkResults} />
		</div>
	{/if}
</div>
