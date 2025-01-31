import { writable } from 'svelte/store';

export interface Client {
	id: string;
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
}

export interface Model {
	name: string;
	size: number;
	digest: string;
	modified_at: number;
	client_id: string;
}

export interface Prompt {
	id: string;
	name: string;
	content: string;
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
	selectedClients: Set<string>;
	models: Model[];
	filteredModels: Model[];
	selectedModels: Set<string>;
	prompts: Prompt[];
	selectedPrompts: Set<string>;
	availableGPUs: GPU[];
	hardwareConfig: HardwareConfig;
	testConfig: TestConfig;
	searchTerm: string;
	sortField: 'name' | 'size' | 'modified_at';
	sortDirection: 'asc' | 'desc';
	loading: boolean;
	error: string | null;
	activeTests: Map<string, string>;
}

const initialState: BenchmarkState = {
	clients: [],
	selectedClients: new Set(),
	models: [],
	filteredModels: [],
	selectedModels: new Set(),
	prompts: [],
	selectedPrompts: new Set(),
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
	activeTests: new Map()
};

function createBenchmarkStore() {
	const { subscribe, set, update } = writable<BenchmarkState>(initialState);

	return {
		subscribe,
		set,
		update,
		reset: () => set(initialState),
		toggleClient: (clientId: string) =>
			update((state) => {
				const newSelected = new Set(state.selectedClients);
				if (newSelected.has(clientId)) {
					newSelected.delete(clientId);
				} else {
					newSelected.add(clientId);
				}
				return { ...state, selectedClients: newSelected };
			}),
		setModels: (models: Model[]) =>
			update((state) => ({ ...state, models, filteredModels: models })),
		toggleModel: (modelName: string) =>
			update((state) => {
				const newSelected = new Set(state.selectedModels);
				if (newSelected.has(modelName)) {
					newSelected.delete(modelName);
				} else {
					newSelected.add(modelName);
				}
				return { ...state, selectedModels: newSelected };
			}),
		togglePrompt: (promptId: string) =>
			update((state) => {
				const newSelected = new Set(state.selectedPrompts);
				if (newSelected.has(promptId)) {
					newSelected.delete(promptId);
				} else {
					newSelected.add(promptId);
				}
				return { ...state, selectedPrompts: newSelected };
			}),
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

				return { ...state, filteredModels: filtered };
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
			})
	};
}

export const benchmarkStore = createBenchmarkStore();
