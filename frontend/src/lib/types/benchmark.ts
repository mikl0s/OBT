export interface CPUInfo {
	name: string;
	architecture: string;
	base_clock: number;
	boost_clock?: number;
	cores: number;
	threads: number;
	core_types?: {
		performance_cores?: number;
		efficiency_cores?: number;
	};
	features: string[]; // AVX-512, AMX, etc.
}

export interface GPUInfo {
	name: string;
	vram_size: number; // in MB
	vram_type: string; // GDDR6X, HBM2, etc.
	tensor_cores?: number;
	cuda_cores?: number;
	compute_capability?: string;
}

export interface NPUInfo {
	name?: string;
	compute_power?: number; // TOPS
	precision_support?: string[]; // INT8, FP16, etc.
	dedicated?: boolean;
}

export interface HardwareInfo {
	cpu: CPUInfo;
	gpu?: GPUInfo;
	npu?: NPUInfo;
	total_memory: number; // System RAM in MB
}

export interface BenchmarkConfig {
	model_name: string;
	prompt_tokens: number;
	completion_tokens: number;
	num_iterations: number;
	temperature: number;
	top_p: number;
	top_k: number;
	repeat_penalty: number;
}

export interface BenchmarkMetrics {
	tokens_per_second: number;
	latency_ms: number;
	memory_usage_mb: number;
	gpu_memory_usage_mb?: number;
	cpu_usage_percent: number;
	gpu_usage_percent?: number;
}

export interface Client {
	id: string;
	name: string;
	hardware: HardwareInfo;
	models: Model[];
}

export interface Model {
	name: string;
	client_id: string;
	size: number;
	modified: number;
	digest: string;
	version?: string;
	tags?: string[];
}

export interface Prompt {
	id: string;
	name: string;
	content: string;
	selected?: boolean;
}

export interface BenchmarkResult {
	id: string;
	clientId: string;
	promptId: string;
	startTime: Date;
	endTime?: Date;
	status: 'pending' | 'running' | 'completed' | 'failed';
	metrics: {
		tokensPerSecond?: number;
		peakMemory?: number;
	};
}

export interface OriginalBenchmarkResult {
	id: string;
	client_id: string;
	config: BenchmarkConfig;
	hardware_info: HardwareInfo;
	metrics: BenchmarkMetrics[];
	start_time: string;
	end_time: string;
	status: 'running' | 'completed' | 'failed';
	error?: string;
	average_tokens_per_second: number;
	average_latency_ms: number;
}
