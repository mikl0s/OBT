<script lang="ts">
	import { onMount } from 'svelte';
	import {
		Card,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Button,
		Spinner,
		Accordion,
		AccordionItem
	} from 'flowbite-svelte';
	import BenchmarkComparison from '../benchmarks/BenchmarkComparison.svelte';

	interface BenchmarkResult {
		id: string;
		status: 'running' | 'completed' | 'failed';
		start_time: string;
		end_time?: string;
		config: {
			client_id: string;
			model_name: string;
			hardware: {
				use_gpu: boolean;
				gpu_id: number | null;
				threads: number;
			};
		};
		metrics: Array<{
			timestamp: number;
			tokens_per_second: number;
			memory_usage_mb: number;
			gpu_memory_usage_mb?: number;
			cpu_usage_percent: number;
			gpu_usage_percent?: number;
			cpu_temperature?: number;
			gpu_temperature?: number;
		}>;
		average_tokens_per_second: number;
		average_latency_ms: number;
		average_power_usage?: number;
		error?: string;
	}

	let results: BenchmarkResult[] = [];
	let loading = true;
	let error: string | null = null;
	let refreshInterval: number;

	async function fetchResults() {
		try {
			const response = await fetch('http://localhost:8881/api/v1/benchmarks');
			if (!response.ok) throw new Error('Failed to fetch benchmark results');
			results = await response.json();

			// Continue polling if any benchmarks are still running
			const hasRunning = results.some((r) => r.status === 'running');
			if (!hasRunning && refreshInterval) {
				clearInterval(refreshInterval);
				refreshInterval = 0;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load benchmark results';
			if (refreshInterval) {
				clearInterval(refreshInterval);
				refreshInterval = 0;
			}
		} finally {
			loading = false;
		}
	}

	function startPolling() {
		if (refreshInterval) return;
		refreshInterval = setInterval(fetchResults, 2000) as unknown as number;
	}

	onMount(async () => {
		await fetchResults();
		startPolling();
		return () => {
			if (refreshInterval) clearInterval(refreshInterval);
		};
	});

	function formatDuration(start: string, end?: string): string {
		if (!end) return 'Running...';
		const duration = new Date(end).getTime() - new Date(start).getTime();
		return `${(duration / 1000).toFixed(2)}s`;
	}

	function formatDate(date: string): string {
		return new Date(date).toLocaleString();
	}
</script>

<div class="container mx-auto space-y-6 p-4">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold">Benchmark Results</h1>
		<Button color="blue" on:click={fetchResults}>Refresh</Button>
	</div>

	{#if loading && results.length === 0}
		<div class="flex justify-center p-8">
			<Spinner size="12" />
		</div>
	{:else if error}
		<Card color="red">
			<p class="text-red-500">{error}</p>
			<Button color="red" class="mt-4" on:click={fetchResults}>Retry</Button>
		</Card>
	{:else if results.length === 0}
		<Card>
			<p class="text-center text-gray-500">No benchmark results found</p>
		</Card>
	{:else}
		<!-- Comparison View -->
		<BenchmarkComparison {results} />

		<!-- Detailed Results -->
		{#each results as result}
			<Card>
				<div class="mb-4 flex items-start justify-between">
					<div>
						<h2 class="text-xl font-bold">{result.config.model_name}</h2>
						<p class="text-sm text-gray-400">
							Client: {result.config.client_id}
						</p>
						<p class="text-sm text-gray-400">
							Started: {formatDate(result.start_time)}
						</p>
						<p class="text-sm text-gray-400">
							Duration: {formatDuration(result.start_time, result.end_time)}
						</p>
					</div>
					<div class="text-right">
						<p class="text-sm font-semibold">
							Status:
							<span
								class={result.status === 'completed'
									? 'text-green-400'
									: result.status === 'failed'
										? 'text-red-400'
										: 'text-yellow-400'}
							>
								{result.status}
							</span>
						</p>
						<p class="text-sm text-gray-400">
							Hardware: {result.config.hardware.use_gpu ? 'GPU' : 'CPU'}
							{#if result.config.hardware.use_gpu && result.config.hardware.gpu_id !== null}
								#{result.config.hardware.gpu_id}
							{/if}
						</p>
					</div>
				</div>

				{#if result.error}
					<div class="mb-4 rounded border border-red-700 bg-red-900/20 p-4">
						<p class="text-red-400">{result.error}</p>
					</div>
				{:else}
					<div class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
						<div class="rounded-lg bg-gray-800 p-4">
							<h3 class="mb-2 font-semibold">Performance</h3>
							<p><strong>Tokens/s:</strong> {result.average_tokens_per_second.toFixed(2)}</p>
							<p><strong>Latency:</strong> {result.average_latency_ms.toFixed(2)}ms</p>
						</div>

						<div class="rounded-lg bg-gray-800 p-4">
							<h3 class="mb-2 font-semibold">Memory Usage</h3>
							<p><strong>CPU:</strong> {result.metrics[0].memory_usage_mb.toFixed(0)}MB</p>
							{#if result.metrics[0].gpu_memory_usage_mb}
								<p><strong>GPU:</strong> {result.metrics[0].gpu_memory_usage_mb.toFixed(0)}MB</p>
							{/if}
						</div>

						<div class="rounded-lg bg-gray-800 p-4">
							<h3 class="mb-2 font-semibold">Resource Usage</h3>
							<p><strong>CPU:</strong> {result.metrics[0].cpu_usage_percent.toFixed(1)}%</p>
							{#if result.metrics[0].gpu_usage_percent}
								<p><strong>GPU:</strong> {result.metrics[0].gpu_usage_percent.toFixed(1)}%</p>
							{/if}
							{#if result.average_power_usage}
								<p><strong>Power:</strong> {result.average_power_usage.toFixed(1)}W</p>
							{/if}
						</div>
					</div>

					<Accordion>
						<AccordionItem>
							<span slot="header" class="text-sm font-semibold">View Metrics Timeline</span>
							<div class="space-y-4">
								<Table noborder={true} color="custom" class="w-full text-sm">
									<TableHead>
										<TableHeadCell>Time</TableHeadCell>
										<TableHeadCell>Tokens/s</TableHeadCell>
										<TableHeadCell>Memory (CPU/GPU)</TableHeadCell>
										<TableHeadCell>Usage (CPU/GPU)</TableHeadCell>
										<TableHeadCell>Temperature</TableHeadCell>
									</TableHead>
									<TableBody>
										{#each result.metrics as metric}
											<TableBodyRow>
												<TableBodyCell>
													{new Date(metric.timestamp * 1000).toLocaleTimeString()}
												</TableBodyCell>
												<TableBodyCell>
													{metric.tokens_per_second.toFixed(2)}
												</TableBodyCell>
												<TableBodyCell>
													{metric.memory_usage_mb.toFixed(0)}MB
													{#if metric.gpu_memory_usage_mb}
														/ {metric.gpu_memory_usage_mb.toFixed(0)}MB
													{/if}
												</TableBodyCell>
												<TableBodyCell>
													{metric.cpu_usage_percent.toFixed(1)}%
													{#if metric.gpu_usage_percent}
														/ {metric.gpu_usage_percent.toFixed(1)}%
													{/if}
												</TableBodyCell>
												<TableBodyCell>
													{#if metric.cpu_temperature || metric.gpu_temperature}
														{metric.cpu_temperature?.toFixed(1) || '-'}°C
														{#if metric.gpu_temperature}
															/ {metric.gpu_temperature.toFixed(1)}°C
														{/if}
													{:else}
														-
													{/if}
												</TableBodyCell>
											</TableBodyRow>
										{/each}
									</TableBody>
								</Table>
							</div>
						</AccordionItem>
					</Accordion>
				{/if}
			</Card>
		{/each}
	{/if}
</div>

<style>
	:global(.table-custom) {
		--table-color: transparent;
		--table-header-bg: transparent;
		--table-color-hover: #374151;
		--table-color-striped: transparent;
	}
</style>
