<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>

<script>
  import { Card } from 'flowbite-svelte';
</script>

<div class="grid gap-8">
  <div class="text-center">
    <h1 class="text-4xl font-bold mb-4">Ollama Benchmark Tool</h1>
    <p class="text-xl text-gray-400">
      Test and analyze Ollama models with comprehensive benchmarks
    </p>
  </div>

  <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
    <Card href="/models">
      <h5 class="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
        Models
      </h5>
      <p class="font-normal text-gray-700 dark:text-gray-400 leading-tight">
        View and manage your installed Ollama models
      </p>
    </Card>

    <Card href="/tests">
      <h5 class="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
        Tests
      </h5>
      <p class="font-normal text-gray-700 dark:text-gray-400 leading-tight">
        Run benchmarks with customizable test prompts
      </p>
    </Card>

    <Card href="/results">
      <h5 class="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
        Results
      </h5>
      <p class="font-normal text-gray-700 dark:text-gray-400 leading-tight">
        Analyze test results and model performance
      </p>
    </Card>
  </div>
</div>
