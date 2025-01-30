<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell, Button, Spinner, Alert } from 'flowbite-svelte';

  let models: any[] = [];
  let loading = true;
  let error: string | null = null;
  let showClientError = false;

  const API_URL = 'http://localhost:8001/api/v1';
  const CLIENT_ID = 'frontend-client';
  const CLIENT_URL = 'http://localhost:8002';

  onMount(async () => {
    try {
      // Register client first
      const registerResponse = await fetch(`${API_URL}/models/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          client_url: CLIENT_URL,
          client_id: CLIENT_ID
        })
      });
      if (!registerResponse.ok) {
        showClientError = true;
        throw new Error('Failed to register client. Please make sure the Ollama client is running on port 8002.');
      }

      // Then fetch models
      const modelsResponse = await fetch(`${API_URL}/models?client_id=${CLIENT_ID}`);
      if (!modelsResponse.ok) {
        const errorText = await modelsResponse.text();
        throw new Error(`Failed to fetch models: ${errorText}`);
      }
      models = await modelsResponse.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load models';
      console.error('Error:', e);
    } finally {
      loading = false;
    }
  });

  function formatSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  function formatDate(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleString();
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold">Ollama Models</h1>
    <Button color="blue">Refresh Models</Button>
  </div>

  {#if loading}
    <div class="flex justify-center p-8">
      <Spinner size="12" />
    </div>
  {:else if error}
    <div class="space-y-4">
      {#if showClientError}
        <Alert color="red">
          <span class="font-medium">Ollama Client Not Running!</span>
          <p class="mt-2">Please start the Ollama client by running:</p>
          <pre class="mt-2 p-2 bg-gray-800 rounded">cd ollama-client && python -m uvicorn main.py:app --reload --port 8002</pre>
        </Alert>
      {:else}
        <Alert color="red">
          <span class="font-medium">Error Loading Models</span>
          <p class="mt-2">{error}</p>
        </Alert>
      {/if}
    </div>
  {:else}
    <Card>
      <Table>
        <TableHead>
          <TableHeadCell>Model Name</TableHeadCell>
          <TableHeadCell>Size</TableHeadCell>
          <TableHeadCell>Modified</TableHeadCell>
          <TableHeadCell>Actions</TableHeadCell>
        </TableHead>
        <TableBody>
          {#each models as model}
            <TableBodyRow>
              <TableBodyCell>{model.name}</TableBodyCell>
              <TableBodyCell>{formatSize(model.size)}</TableBodyCell>
              <TableBodyCell>{formatDate(model.modified)}</TableBodyCell>
              <TableBodyCell>
                <div class="flex space-x-2">
                  <Button size="xs" color="blue">Test</Button>
                  <Button size="xs" color="red">Remove</Button>
                </div>
              </TableBodyCell>
            </TableBodyRow>
          {/each}
        </TableBody>
      </Table>
    </Card>
  {/if}
</div>
