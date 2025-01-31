<script lang="ts">
	import '../app.css';
	import { Navbar, NavBrand, NavLi, NavUl, NavHamburger } from 'flowbite-svelte';
	let { children } = $props();
</script>

<div class="min-h-screen bg-gradient-to-br from-gray-900 via-purple-950 to-gray-900">
	<Navbar let:hidden let:toggle color="transparent" class="border-none">
		<NavBrand href="/">
			<span class="self-center whitespace-nowrap text-xl font-semibold text-purple-200">
				Ollama Benchmark Tool
			</span>
		</NavBrand>
		<NavHamburger on:click={toggle} class="text-purple-200 hover:text-purple-100" />
		<NavUl {hidden} class="text-purple-300">
			<NavLi href="/" class="hover:text-purple-100">Home</NavLi>
			<NavLi href="/benchmark" class="hover:text-purple-100">Benchmark</NavLi>
			<NavLi href="/results" class="hover:text-purple-100">Results</NavLi>
		</NavUl>
	</Navbar>

	<main class="container mx-auto">
		{@render children()}
	</main>
</div>

<style>
	:global(body) {
		@apply bg-gray-900;
	}
</style>
