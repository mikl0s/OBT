<script lang="ts">
	import { onMount } from 'svelte';
	import Chart from 'chart.js/auto';
	import type { BenchmarkResult } from '$lib/types/benchmark';

	export let results: BenchmarkResult[] = [];
	export let metric: 'tokens_per_second' | 'latency_ms' = 'tokens_per_second';
	export let chartTitle: string;

	let canvas: HTMLCanvasElement;
	let chart: Chart;

	$: if (results && canvas) {
		updateChart();
	}

	onMount(() => {
		if (results.length > 0) {
			createChart();
		}
		return () => {
			if (chart) {
				chart.destroy();
			}
		};
	});

	function createChart() {
		const ctx = canvas.getContext('2d');
		if (!ctx) return;

		const data = processData();

		chart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: data.labels,
				datasets: [
					{
						label: metric === 'tokens_per_second' ? 'Tokens per Second' : 'Latency (ms)',
						data: data.values,
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
						text: chartTitle
					},
					legend: {
						display: true,
						position: 'bottom'
					}
				},
				scales: {
					y: {
						beginAtZero: true,
						title: {
							display: true,
							text: metric === 'tokens_per_second' ? 'Tokens/s' : 'Latency (ms)'
						}
					}
				}
			}
		});
	}

	function processData() {
		const labels = results.map((r) => r.config.model_name);
		const values = results.map((r) =>
			metric === 'tokens_per_second' ? r.average_tokens_per_second : r.average_latency_ms
		);
		return { labels, values };
	}

	function updateChart() {
		if (!chart) {
			createChart();
			return;
		}

		const data = processData();
		chart.data.labels = data.labels;
		chart.data.datasets[0].data = data.values;
		chart.update();
	}
</script>

<div class="h-64 w-full">
	<canvas bind:this={canvas}></canvas>
</div>
