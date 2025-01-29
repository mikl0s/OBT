<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell, Button, Spinner, Accordion, AccordionItem } from 'flowbite-svelte';

  let sessions: any[] = [];
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/tests');
      if (!response.ok) throw new Error('Failed to fetch test sessions');
      sessions = await response.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load test sessions';
    } finally {
      loading = false;
    }
  });

  function formatDuration(start: string, end: string): string {
    const duration = new Date(end).getTime() - new Date(start).getTime();
    return `${(duration / 1000).toFixed(2)}s`;
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold">Test Results</h1>
    <Button color="blue">Refresh</Button>
  </div>

  {#if loading}
    <div class="flex justify-center p-8">
      <Spinner size="12" />
    </div>
  {:else if error}
    <Card color="red">
      <p class="text-red-500">{error}</p>
      <Button color="red" class="mt-4">Retry</Button>
    </Card>
  {:else if sessions.length === 0}
    <Card>
      <p class="text-center text-gray-500">No test sessions found</p>
    </Card>
  {:else}
    {#each sessions as session}
      <Card>
        <div class="flex justify-between items-start mb-4">
          <div>
            <h2 class="text-xl font-bold">Test Session</h2>
            <p class="text-sm text-gray-400">
              Started: {new Date(session.start_time).toLocaleString()}
            </p>
            {#if session.end_time}
              <p class="text-sm text-gray-400">
                Duration: {formatDuration(session.start_time, session.end_time)}
              </p>
            {/if}
          </div>
          <div class="text-right">
            <p class="text-sm font-semibold">Status: {session.status}</p>
            <p class="text-sm text-gray-400">Hardware ID: {session.hardware_config_id}</p>
          </div>
        </div>

        <Accordion>
          {#each session.models as modelEntry}
            {#each Object.entries(modelEntry) as [modelName, results]}
              <AccordionItem>
                <span slot="header" class="text-lg font-semibold">{modelName}</span>
                <div class="space-y-4">
                  {#each results as result}
                    <Card>
                      <h3 class="font-bold mb-2">Prompt: {result.prompt}</h3>
                      <div class="space-y-2">
                        {#each result.responses as response}
                          <div class="border-l-4 border-blue-500 pl-4">
                            {#if response.reasoning}
                              <div class="mb-2">
                                <p class="text-sm text-gray-400">Reasoning:</p>
                                <p class="text-gray-300">{response.reasoning}</p>
                              </div>
                            {/if}
                            <div>
                              <p class="text-sm text-gray-400">Response:</p>
                              <p>{response.response}</p>
                            </div>
                          </div>
                        {/each}
                      </div>
                    </Card>
                  {/each}
                </div>
              </AccordionItem>
            {/each}
          {/each}
        </Accordion>
      </Card>
    {/each}
  {/if}
</div>
