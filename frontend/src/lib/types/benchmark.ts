export interface HardwareInfo {
	cpu_model: string;
	cpu_cores: number;
	cpu_threads: number;
	ram_total: number;
	gpu_model?: string;
	gpu_memory?: number;
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
	hardware: {
		cpu: string;
		threads: number;
		memory: number;
		gpu?: string;
	};
	models: Model[];
}

export interface Model {
	id: string;
	name: string;
	parameters: string;
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
