import { writable, derived } from 'svelte/store';

export interface TestPrompt {
	id: string;
	name: string;
	prompt: string;
}

export interface TestSuite {
	name: string;
	prompts: TestPrompt[];
}

export const testSuites = writable<TestSuite[]>([]);
export const selectedPromptIds = writable<string[]>([]);

export const selectedPrompts = derived(
	[testSuites, selectedPromptIds],
	([$testSuites, $selectedPromptIds]) => {
		const allPrompts = $testSuites.flatMap((suite) => suite.prompts);
		return allPrompts.filter((prompt) => $selectedPromptIds.includes(prompt.id));
	}
);

export async function loadTestSuites() {
	try {
		const response = await fetch('/api/v1/prompts/test-suites');
		if (!response.ok) {
			throw new Error('Failed to load test suites');
		}
		const data = await response.json();
		testSuites.set(data);
	} catch (error) {
		console.error('Failed to load test suites:', error);
		throw error;
	}
}
