<script lang="ts">
	import { onMount } from 'svelte';
	import { Card } from 'flowbite-svelte';
	import Chart from 'chart.js/auto';
	import type { BenchmarkResult } from '$lib/types/benchmark';

	export let results: BenchmarkResult[] = [];
	let selectedMetric = 'tokens_per_second';
	let canvas: HTMLCanvasElement;
	let chart: Chart;

	const metrics = [
		{ id: 'tokens_per_second', label: 'Tokens per Second' },
		{ id: 'first_token_ms', label: 'First Token Latency (ms)' },
		{ id: 'average_token_ms', label: 'Average Token Latency (ms)' },
		{ id: 'memory_usage_mb', label: 'CPU Memory Usage (MB)' },
		{ id: 'gpu_memory_usage_mb', label: 'GPU Memory Usage (MB)' },
		{ id: 'cpu_usage_percent', label: 'CPU Usage (%)' },
		{ id: 'gpu_usage_percent', label: 'GPU Usage (%)' },
		{ id: 'power_usage_watts', label: 'Power Usage (W)' }
	];

	function getMetricValue(result: BenchmarkResult, metricId: string): number {
		if (metricId === 'tokens_per_second') {
			return result.average_tokens_per_second;
		}
		if (metricId === 'first_token_ms') {
			return result.average_latency_ms;
		}
		if (metricId === 'power_usage_watts' && result.average_power_usage) {
			return result.average_power_usage;
		}
		const firstMetric = result.metrics[0];
		return firstMetric[metricId] || 0;
	}

	function updateChart() {
		if (!canvas) return;

		const ctx = canvas.getContext('2d');
		if (!ctx) return;

		if (chart) {
			chart.destroy();
		}

		const labels = results.map((r) => {
			const model = r.config.model_name;
			const hardware = r.config.hardware.use_gpu
				? `GPU${r.config.hardware.gpu_id !== null ? ' #' + r.config.hardware.gpu_id : ''}`
				: 'CPU';
			return `${model} (${hardware})`;
		});

		const values = results.map((r) => getMetricValue(r, selectedMetric));

		chart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels,
				datasets: [
					{
						label: metrics.find((m) => m.id === selectedMetric)?.label || '',
						data: values,
						backgroundColor: 'rgba(75, 192, 192, 0.2)',
						borderColor: 'rgba(75, 192, 192, 1)',
						borderWidth: 1
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					title: {
						display: true,
						text: 'Benchmark Comparison'
					},
					legend: {
						display: true,
						position: 'bottom'
					}
				},
				scales: {
					y: {
						beginAtZero: true
					}
				}
			}
		});
	}

	$: if (results && canvas && selectedMetric) {
		updateChart();
	}

	onMount(() => {
		if (results.length > 0) {
			updateChart();
		}
		return () => {
			if (chart) {
				chart.destroy();
			}
		};
	});
</script>

<Card class="p-4">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-xl font-semibold">Benchmark Comparison</h2>
		<select
			class="rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-500 dark:focus:ring-blue-500"
			bind:value={selectedMetric}
		>
			{#each metrics as metric}
				<option value={metric.id}>{metric.label}</option>
			{/each}
		</select>
	</div>

	<div class="h-64 w-full">
		<canvas bind:this={canvas}></canvas>
	</div>
</Card>
