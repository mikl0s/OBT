import { writable } from 'svelte/store';

const API_URL = 'http://localhost:8881/api/v1';

export interface Client {
	id: string;
	name: string;
	version: string;
	available: boolean;
	model_count: number;
	last_heartbeat: string;
	hardware: {
		cpu_threads: number;
		gpu_count: number;
		gpu_name?: string;
		gpu_memory?: number;
	};
	models: Model[];
}

export interface Model {
	name: string;
	client_id: string;
	size: number;
	digest: string;
}

export interface Prompt {
	id: string;
	name: string;
	content: string;
	description: string;
	selected: boolean;
}

export interface GPU {
	id: string;
	name: string;
	memory: number;
	client_id: string;
}

export interface HardwareConfig {
	client_id: string;
	use_gpu: boolean;
	gpu_id: string | null;
	threads: number;
}

export interface TestConfig {
	iterations: number;
	parallel_clients: boolean;
}

interface BenchmarkState {
	clients: Client[];
	selectedClients: string[];
	models: Model[];
	selectedModels: string[];
	prompts: Prompt[];
	selectedPrompts: string[];
	availableGPUs: GPU[];
	hardwareConfig: HardwareConfig;
	testConfig: TestConfig;
	searchTerm: string;
	sortField: 'name' | 'size' | 'modified_at';
	sortDirection: 'asc' | 'desc';
	loading: boolean;
	error: string | null;
	activeTests: Map<string, string>;
	activeBenchmarks: Array<{
		client_id: string;
		status: string;
		completed_prompts: number;
		total_prompts: number;
	}>;
}

const initialState: BenchmarkState = {
	clients: [],
	selectedClients: [],
	models: [],
	selectedModels: [],
	prompts: [],
	selectedPrompts: [],
	availableGPUs: [],
	hardwareConfig: {
		client_id: '',
		use_gpu: false,
		gpu_id: null,
		threads: typeof navigator !== 'undefined' ? navigator.hardwareConcurrency || 4 : 4
	},
	testConfig: {
		iterations: 1,
		parallel_clients: false
	},
	searchTerm: '',
	sortField: 'name',
	sortDirection: 'asc',
	loading: true,
	error: null,
	activeTests: new Map(),
	activeBenchmarks: []
};

function createBenchmarkStore() {
	const { subscribe, set, update } = writable<BenchmarkState>(initialState);

	return {
		subscribe,
		set,
		update,
		reset: () => set(initialState),
		getClients: async () => {
			update((state) => ({ ...state, loading: true, error: null }));
			try {
				const response = await fetch(`${API_URL}/models/clients`);
				if (!response.ok) throw new Error('Failed to fetch clients');
				const clients = await response.json();
				update((state) => ({ ...state, clients, loading: false }));
				return clients;
			} catch (error) {
				update((state) => ({ ...state, error: error.message, loading: false }));
				return [];
			}
		},
		getPrompts: async () => {
			update((state) => ({ ...state, loading: true, error: null }));
			try {
				const response = await fetch(`${API_URL}/prompts/test-suites`);
				if (!response.ok) throw new Error('Failed to fetch prompts');
				const data = await response.json();
				// The API returns test suites, we want to flatten all prompts from all suites
				// and add the selected property
				const prompts = data.flatMap((suite) =>
					suite.prompts.map((prompt) => ({
						...prompt,
						selected: false
					}))
				);
				update((state) => ({ ...state, prompts, loading: false }));
				return prompts;
			} catch (error) {
				update((state) => ({ ...state, error: error.message, loading: false }));
				return [];
			}
		},
		getModels: async (clientId?: string) => {
			update((state) => ({ ...state, loading: true, error: null }));
			try {
				const url = clientId
					? `${API_URL}/models?client_id=${encodeURIComponent(clientId)}`
					: `${API_URL}/models`;
				const response = await fetch(url);
				if (!response.ok) throw new Error('Failed to fetch models');
				const models = await response.json();
				console.log('Fetched models:', models); // Debug log
				update((state) => ({ ...state, models: models || [], loading: false }));
				return models;
			} catch (error) {
				console.error('Error fetching models:', error); // Debug log
				update((state) => ({ ...state, error: error.message, loading: false }));
				return [];
			}
		},
		selectModel: (modelName: string) => {
			update((state) => ({
				...state,
				selectedModels: state.selectedModels.includes(modelName)
					? state.selectedModels.filter((m) => m !== modelName)
					: [...state.selectedModels, modelName]
			}));
		},
		clearSelectedModels: () => {
			update((state) => ({ ...state, selectedModels: [] }));
		},
		toggleClient: (clientId: string) => {
			update((state) => {
				const newSelected = state.selectedClients.includes(clientId)
					? state.selectedClients.filter((c) => c !== clientId)
					: [...state.selectedClients, clientId];
				return { ...state, selectedClients: newSelected };
			});
		},
		setModels: (models: Model[]) => {
			update((state) => ({ ...state, models }));
		},
		toggleModel: (modelName: string) => {
			update((state) => ({
				...state,
				selectedModels: state.selectedModels.includes(modelName)
					? state.selectedModels.filter((m) => m !== modelName)
					: [...state.selectedModels, modelName]
			}));
		},
		togglePromptSelection: (promptId: string) => {
			update((state) => ({
				...state,
				prompts: state.prompts.map((prompt) =>
					prompt.id === promptId ? { ...prompt, selected: !prompt.selected } : prompt
				)
			}));
		},
		setGPUs: (gpus: GPU[]) => update((state) => ({ ...state, availableGPUs: gpus })),
		setError: (error: string | null) => update((state) => ({ ...state, error })),
		setLoading: (loading: boolean) => update((state) => ({ ...state, loading })),
		updateHardware: (config: Partial<HardwareConfig>) =>
			update((state) => ({
				...state,
				hardwareConfig: { ...state.hardwareConfig, ...config }
			})),
		setIterations: (iterations: number) =>
			update((state) => ({
				...state,
				testConfig: { ...state.testConfig, iterations }
			})),
		setParallelClients: (parallel: boolean) =>
			update((state) => ({
				...state,
				testConfig: { ...state.testConfig, parallel_clients: parallel }
			})),
		filterAndSortModels: () =>
			update((state) => {
				let filtered = state.models;

				// Apply search filter if there's a search term
				if (state.searchTerm) {
					filtered = filtered.filter((model) =>
						model.name.toLowerCase().includes(state.searchTerm.toLowerCase())
					);
				}

				// Sort models
				filtered.sort((a, b) => {
					let comparison = 0;
					switch (state.sortField) {
						case 'name':
							comparison = a.name.localeCompare(b.name);
							break;
						case 'size':
							comparison = a.size - b.size;
							break;
						case 'modified_at':
							comparison = a.modified_at - b.modified_at;
							break;
					}
					return state.sortDirection === 'asc' ? comparison : -comparison;
				});

				return { ...state, models: filtered };
			}),
		setActiveTest: (id: string, status: string) =>
			update((state) => {
				const newTests = new Map(state.activeTests);
				newTests.set(id, status);
				return { ...state, activeTests: newTests };
			}),
		removeActiveTest: (id: string) =>
			update((state) => {
				const newTests = new Map(state.activeTests);
				newTests.delete(id);
				return { ...state, activeTests: newTests };
			}),
		startBenchmark: async (params: {
			client_id: string;
			prompts: string[];
			hardware: ClientHardware;
			models: string[];
		}) => {
			update((state) => ({ ...state, loading: true, error: null }));
			try {
				const response = await fetch(`${API_URL}/benchmarks/start`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify(params)
				});
				if (!response.ok) {
					const errorData = await response.json();
					throw new Error(errorData.detail || 'Failed to start benchmark');
				}
				// Assuming the API returns the benchmark ID
				const data = await response.json();
				console.log('Benchmark started:', data);
				// Optionally, update the store with the new benchmark ID
				// update(state => ({ ...state, activeBenchmarks: [...state.activeBenchmarks, {id: data.id, status: 'running'}] }));
			} catch (error) {
				console.error('Error starting benchmark:', error);
				update((state) => ({ ...state, error: error.message, loading: false }));
			} finally {
				update((state) => ({ ...state, loading: false }));
			}
		}
	};
}

export const benchmarkStore = createBenchmarkStore();
