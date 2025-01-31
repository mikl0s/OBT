<script lang="ts">
	import { Button } from 'flowbite-svelte';
	import { goto } from '$app/navigation';
</script>

<div class="px-4 py-16">
	<!-- Hero Section -->
	<div class="mb-16 text-center">
		<h1
			class="mb-6 bg-gradient-to-r from-purple-300 via-fuchsia-200 to-purple-300 bg-clip-text text-6xl font-bold text-transparent"
		>
			Ollama Benchmark Tool
		</h1>
		<p class="mx-auto mb-8 max-w-2xl text-lg text-purple-200/90">
			Comprehensive performance testing for Ollama models. Compare, analyze, and optimize your AI
			models with precision.
		</p>
		<Button
			size="xl"
			class="mr-4 bg-purple-600 hover:bg-purple-700"
			on:click={() => goto('/benchmark')}
		>
			Start Benchmarking
		</Button>
		<Button
			size="xl"
			color="light"
			class="text-purple-200 hover:bg-purple-900/50"
			on:click={() => goto('/results')}
		>
			View Results
		</Button>
	</div>

	<!-- Features Grid -->
	<div class="grid gap-8 md:grid-cols-3">
		<!-- Feature 1: Benchmarking -->
		<div class="group rounded-xl bg-purple-900/20 p-6 transition-all hover:bg-purple-800/20">
			<div class="mb-4 inline-block rounded-lg bg-purple-700/20 p-3">
				<svg class="h-6 w-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
					/>
				</svg>
			</div>
			<h3 class="mb-2 text-xl font-semibold text-purple-100">Comprehensive Testing</h3>
			<p class="text-purple-200/80">
				Test your models across multiple dimensions including speed, accuracy, and resource usage.
			</p>
		</div>

		<!-- Feature 2: Analysis -->
		<div class="group rounded-xl bg-purple-900/20 p-6 transition-all hover:bg-purple-800/20">
			<div class="mb-4 inline-block rounded-lg bg-purple-700/20 p-3">
				<svg class="h-6 w-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
					/>
				</svg>
			</div>
			<h3 class="mb-2 text-xl font-semibold text-purple-100">Detailed Analytics</h3>
			<p class="text-purple-200/80">
				Get in-depth performance metrics and visualizations to understand your models better.
			</p>
		</div>

		<!-- Feature 3: Optimization -->
		<div class="group rounded-xl bg-purple-900/20 p-6 transition-all hover:bg-purple-800/20">
			<div class="mb-4 inline-block rounded-lg bg-purple-700/20 p-3">
				<svg class="h-6 w-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
					/>
				</svg>
			</div>
			<h3 class="mb-2 text-xl font-semibold text-purple-100">Hardware Optimization</h3>
			<p class="text-purple-200/80">
				Fine-tune hardware settings for optimal performance across different configurations.
			</p>
		</div>
	</div>

	<!-- Stats Section -->
	<div class="mt-16 grid gap-8 rounded-xl bg-purple-900/20 p-8 md:grid-cols-3">
		<div class="text-center">
			<div class="mb-2 text-3xl font-bold text-purple-300">Fast</div>
			<p class="text-purple-200/80">Efficient benchmarking process</p>
		</div>
		<div class="text-center">
			<div class="mb-2 text-3xl font-bold text-purple-300">Precise</div>
			<p class="text-purple-200/80">Accurate performance metrics</p>
		</div>
		<div class="text-center">
			<div class="mb-2 text-3xl font-bold text-purple-300">Insightful</div>
			<p class="text-purple-200/80">Detailed analysis and reports</p>
		</div>
	</div>
</div>

<style>
	:global(body) {
		@apply bg-gray-900;
	}
</style>
