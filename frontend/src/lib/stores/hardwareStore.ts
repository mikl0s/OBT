import { writable } from 'svelte/store';
import type { HardwareSelection } from '$lib/types/benchmark';

const STORAGE_KEY = 'hardware_preferences';

function createHardwareStore() {
	// Load saved preferences or use defaults
	const savedPrefs = typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;

	const initial: HardwareSelection = savedPrefs
		? JSON.parse(savedPrefs)
		: { use_gpu: true, gpu_id: null };

	const { subscribe, set, update } = writable<HardwareSelection>(initial);

	return {
		subscribe,
		setPreferences: (prefs: HardwareSelection) => {
			set(prefs);
			if (typeof localStorage !== 'undefined') {
				localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
			}
		},
		toggleGPU: () => {
			update((prefs) => {
				const newPrefs = {
					...prefs,
					use_gpu: !prefs.use_gpu,
					gpu_id: !prefs.use_gpu ? 0 : null
				};
				if (typeof localStorage !== 'undefined') {
					localStorage.setItem(STORAGE_KEY, JSON.stringify(newPrefs));
				}
				return newPrefs;
			});
		},
		setGPU: (id: number) => {
			update((prefs) => {
				const newPrefs = { ...prefs, gpu_id: id, use_gpu: true };
				if (typeof localStorage !== 'undefined') {
					localStorage.setItem(STORAGE_KEY, JSON.stringify(newPrefs));
				}
				return newPrefs;
			});
		}
	};
}

export const hardwarePreferences = createHardwareStore();
