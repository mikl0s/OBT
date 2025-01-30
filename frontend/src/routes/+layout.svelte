<script lang="ts">
	import '../app.css';
	import { Navbar, NavBrand, NavLi, NavUl, NavHamburger } from 'flowbite-svelte';
	let { children } = $props();
</script>

<Navbar let:hidden let:toggle color="dark">
	<NavBrand href="/">
		<span class="self-center whitespace-nowrap text-xl font-semibold dark:text-white">
			Ollama Benchmark Tool
		</span>
	</NavBrand>
	<NavHamburger on:click={toggle} />
	<NavUl {hidden}>
		<NavLi href="/">Home</NavLi>
		<NavLi href="/models">Models</NavLi>
		<NavLi href="/tests">Tests</NavLi>
		<NavLi href="/results">Results</NavLi>
	</NavUl>
</Navbar>

<main class="container mx-auto px-4 py-8">
	{@render children()}
</main>
