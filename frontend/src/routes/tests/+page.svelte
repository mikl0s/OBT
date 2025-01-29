<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell, Button, Spinner, Checkbox } from 'flowbite-svelte';

  let models: any[] = [];
  let prompts: any[] = [];
  let selectedModels: string[] = [];
  let selectedPrompts: string[] = [];
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      const [modelsRes, promptsRes] = await Promise.all([
        fetch('http://localhost:8000/api/v1/models'),
        fetch('http://localhost:8000/api/v1/tests/prompts')
      ]);
      
      if (!modelsRes.ok) throw new Error('Failed to fetch models');
      if (!promptsRes.ok) throw new Error('Failed to fetch prompts');
      
      models = await modelsRes.json();
      prompts = await promptsRes.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load data';
    } finally {
      loading = false;
    }
  });

  async function startTest() {
    if (selectedModels.length === 0) {
      error = 'Please select at least one model';
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/v1/tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_names: selectedModels,
          prompt_ids: selectedPrompts.length > 0 ? selectedPrompts : undefined
        })
      });

      if (!response.ok) throw new Error('Failed to start test');
      const result = await response.json();
      // TODO: Redirect to test results page
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to start test';
    }
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold">Run Tests</h1>
  </div>

  {#if loading}
    <div class="flex justify-center p-8">
      <Spinner size="12" />
    </div>
  {:else if error}
    <Card color="red">
      <p class="text-red-500">{error}</p>
      <Button color="red" class="mt-4" on:click={() => error = null}>Dismiss</Button>
    </Card>
  {:else}
    <div class="grid md:grid-cols-2 gap-6">
      <!-- Models Selection -->
      <Card>
        <h2 class="text-xl font-bold mb-4">Select Models</h2>
        <div class="space-y-2">
          {#each models as model}
            <div class="flex items-center">
              <Checkbox 
                value={model.name}
                bind:group={selectedModels}
              >
                {model.name}
              </Checkbox>
            </div>
          {/each}
        </div>
      </Card>

      <!-- Prompts Selection -->
      <Card>
        <h2 class="text-xl font-bold mb-4">Select Prompts</h2>
        <p class="text-sm text-gray-400 mb-4">Leave empty to run all prompts</p>
        <div class="space-y-2">
          {#each prompts as prompt}
            <div class="flex items-center">
              <Checkbox 
                value={prompt.id}
                bind:group={selectedPrompts}
              >
                {prompt.name}
              </Checkbox>
            </div>
          {/each}
        </div>
      </Card>
    </div>

    <div class="flex justify-end">
      <Button color="blue" on:click={startTest}>Start Test</Button>
    </div>
  {/if}
</div>
