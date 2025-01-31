<script lang="ts">
	// We use DOMPurify to sanitize HTML, so we can safely use {@html}
	/* eslint-disable svelte/no-at-html-tags */
	import { createEventDispatcher } from 'svelte';
	import { marked } from 'marked';
	import DOMPurify from 'isomorphic-dompurify';

	const dispatch = createEventDispatcher();

	export let prompt: {
		name: string;
		content: string;
	};

	let markdownContent = '';

	$: {
		try {
			const html = marked(prompt.content);
			markdownContent = DOMPurify.sanitize(html);
		} catch (error) {
			console.error('Failed to render markdown:', error);
			markdownContent = prompt.content;
		}
	}
</script>

<div class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 p-4">
	<div class="max-h-[80vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-gray-800 p-6">
		<div class="mb-4 flex items-center justify-between">
			<h2 class="text-xl font-semibold">{prompt.name}</h2>
			<button class="text-gray-400 hover:text-white" on:click={() => dispatch('close')}> ✕ </button>
		</div>
		<div class="prose prose-invert max-w-none">
			<div class="markdown-content" role="article">
				<div>{@html markdownContent}</div>
			</div>
		</div>
	</div>
</div>

<style>
	.markdown-content :global(pre) {
		background-color: #1a1a1a;
		padding: 1rem;
		border-radius: 0.5rem;
		overflow-x: auto;
	}

	.markdown-content :global(code) {
		background-color: #2d2d2d;
		padding: 0.2rem 0.4rem;
		border-radius: 0.25rem;
	}

	.markdown-content :global(h1),
	.markdown-content :global(h2),
	.markdown-content :global(h3),
	.markdown-content :global(h4),
	.markdown-content :global(h5),
	.markdown-content :global(h6) {
		color: #fff;
		margin-top: 1.5rem;
		margin-bottom: 1rem;
	}

	.markdown-content :global(p) {
		margin-bottom: 1rem;
		line-height: 1.6;
	}

	.markdown-content :global(ul),
	.markdown-content :global(ol) {
		margin-left: 1.5rem;
		margin-bottom: 1rem;
	}

	.markdown-content :global(li) {
		margin-bottom: 0.5rem;
	}

	.markdown-content :global(blockquote) {
		border-left: 4px solid #4a5568;
		padding-left: 1rem;
		margin: 1rem 0;
		color: #a0aec0;
	}
</style>
