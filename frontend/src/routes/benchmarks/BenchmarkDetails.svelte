<script lang="ts">
	import {
		Card,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell
	} from 'flowbite-svelte';
	import type { BenchmarkResult } from '$lib/types/benchmark';

	export let result: BenchmarkResult;

	$: hardwareInfo = [
		{ label: 'CPU Model', value: result.hardware_info.cpu.name },
		{ label: 'CPU Architecture', value: result.hardware_info.cpu.architecture },
		{ label: 'CPU Base Clock', value: `${result.hardware_info.cpu.base_clock} GHz` },
		...(result.hardware_info.cpu.boost_clock
			? [{ label: 'CPU Boost Clock', value: `${result.hardware_info.cpu.boost_clock} GHz` }]
			: []),
		{ label: 'CPU Cores', value: result.hardware_info.cpu.cores },
		{ label: 'CPU Threads', value: result.hardware_info.cpu.threads },
		...(result.hardware_info.cpu.core_types?.performance_cores
			? [
					{
						label: 'Performance Cores',
						value: result.hardware_info.cpu.core_types.performance_cores
					}
				]
			: []),
		...(result.hardware_info.cpu.core_types?.efficiency_cores
			? [{ label: 'Efficiency Cores', value: result.hardware_info.cpu.core_types.efficiency_cores }]
			: []),
		{ label: 'CPU Features', value: result.hardware_info.cpu.features.join(', ') },
		{ label: 'RAM Total (GB)', value: (result.hardware_info.total_memory / 1024).toFixed(2) },
		...(result.hardware_info.gpu
			? [
					{ label: 'GPU Model', value: result.hardware_info.gpu.name },
					{
						label: 'GPU Memory',
						value: `${(result.hardware_info.gpu.vram_size / 1024).toFixed(2)} GB ${result.hardware_info.gpu.vram_type}`
					},
					...(result.hardware_info.gpu.tensor_cores
						? [{ label: 'Tensor Cores', value: result.hardware_info.gpu.tensor_cores }]
						: []),
					...(result.hardware_info.gpu.cuda_cores
						? [{ label: 'CUDA Cores', value: result.hardware_info.gpu.cuda_cores }]
						: []),
					...(result.hardware_info.gpu.compute_capability
						? [{ label: 'Compute Capability', value: result.hardware_info.gpu.compute_capability }]
						: [])
				]
			: []),
		...(result.hardware_info.npu
			? [
					{ label: 'NPU Model', value: result.hardware_info.npu.name || 'Unknown' },
					...(result.hardware_info.npu.compute_power
						? [
								{
									label: 'NPU Compute Power',
									value: `${result.hardware_info.npu.compute_power} TOPS`
								}
							]
						: []),
					...(result.hardware_info.npu.precision_support
						? [
								{
									label: 'NPU Precision Support',
									value: result.hardware_info.npu.precision_support.join(', ')
								}
							]
						: [])
				]
			: [])
	];

	$: configInfo = [
		{ label: 'Model', value: result.config.model_name },
		{ label: 'Hardware', value: result.config.hardware.use_gpu ? 'GPU' : 'CPU' },
		{ label: 'Iterations', value: result.config.num_iterations },
		{ label: 'Temperature', value: result.config.temperature },
		{ label: 'Top P', value: result.config.top_p },
		{ label: 'Top K', value: result.config.top_k },
		{ label: 'Repeat Penalty', value: result.config.repeat_penalty }
	];

	function formatMetric(value: number, precision: number = 2): string {
		return value.toFixed(precision);
	}
</script>

<div class="space-y-6">
	<Card>
		<h3 class="mb-4 text-xl font-semibold">Hardware Information</h3>
		<Table striped={true}>
			<TableHead>
				<TableHeadCell>Metric</TableHeadCell>
				<TableHeadCell>Value</TableHeadCell>
			</TableHead>
			<TableBody>
				{#each hardwareInfo as info}
					<TableBodyRow>
						<TableBodyCell>{info.label}</TableBodyCell>
						<TableBodyCell>{info.value}</TableBodyCell>
					</TableBodyRow>
				{/each}
			</TableBody>
		</Table>
	</Card>

	<Card>
		<h3 class="mb-4 text-xl font-semibold">Configuration</h3>
		<Table striped={true}>
			<TableHead>
				<TableHeadCell>Parameter</TableHeadCell>
				<TableHeadCell>Value</TableHeadCell>
			</TableHead>
			<TableBody>
				{#each configInfo as info}
					<TableBodyRow>
						<TableBodyCell>{info.label}</TableBodyCell>
						<TableBodyCell>{info.value}</TableBodyCell>
					</TableBodyRow>
				{/each}
			</TableBody>
		</Table>
	</Card>

	<Card>
		<h3 class="mb-4 text-xl font-semibold">Performance Metrics</h3>
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<div>
				<h4 class="mb-2 font-semibold">Throughput</h4>
				<p class="text-2xl">{formatMetric(result.average_tokens_per_second)} tokens/s</p>
			</div>
			<div>
				<h4 class="mb-2 font-semibold">Latency</h4>
				<p class="text-2xl">{formatMetric(result.average_latency_ms)} ms</p>
			</div>
			<div>
				<h4 class="mb-2 font-semibold">Memory Usage</h4>
				<p class="text-2xl">
					{formatMetric(result.metrics[0].memory_usage_mb)} MB
					{#if result.metrics[0].gpu_memory_usage_mb}
						/ {formatMetric(result.metrics[0].gpu_memory_usage_mb)} MB GPU
					{/if}
				</p>
			</div>
			{#if result.average_power_usage}
				<div>
					<h4 class="mb-2 font-semibold">Power Usage</h4>
					<p class="text-2xl">{formatMetric(result.average_power_usage)} W</p>
				</div>
			{/if}
		</div>
	</Card>
</div>
