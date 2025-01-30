<script lang="ts">
	import { Radio, Select } from 'flowbite-svelte';
	import type { GPUInfo } from '$lib/types/benchmark';
	import { hardwarePreferences } from '$lib/stores/hardwareStore';

	export let gpus: GPUInfo[] = [];

	let useGpu = $hardwarePreferences.use_gpu;
	let selectedGpuId = $hardwarePreferences.gpu_id;

	$: $hardwarePreferences = {
		use_gpu: useGpu,
		gpu_id: useGpu ? selectedGpuId : null
	};
</script>

<div class="space-y-4">
	<div class="flex gap-4">
		<Radio name="hardware" value={false} bind:group={useGpu}>CPU</Radio>
		<Radio name="hardware" value={true} bind:group={useGpu} disabled={gpus.length === 0}>GPU</Radio>
	</div>

	{#if useGpu && gpus.length > 0}
		<div>
			<Select
				items={gpus.map((gpu) => ({ value: gpu.id, name: gpu.name }))}
				bind:value={selectedGpuId}
			/>
		</div>
	{/if}
</div>
