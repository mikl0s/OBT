<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell, Button, Spinner } from 'flowbite-svelte';

  let models: any[] = [];
  let loading = true;
  let error: string | null = null;

  const API_URL = 'http://localhost:8001/api/v1';
  const CLIENT_ID = 'frontend-client';
  const CLIENT_URL = 'http://localhost:8002';

  onMount(async () => {
    try {
      // Register client first
      const registerResponse = await fetch(
        `${API_URL}/models/register?client_url=${encodeURIComponent(CLIENT_URL)}&client_id=${encodeURIComponent(CLIENT_ID)}`,
        { method: 'POST' }
      );
      if (!registerResponse.ok) throw new Error('Failed to register client');

      // Then fetch models
      const modelsResponse = await fetch(`${API_URL}/models?client_id=${encodeURIComponent(CLIENT_ID)}`);
      if (!modelsResponse.ok) throw new Error('Failed to fetch models');
      models = await modelsResponse.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load models';
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
    <Card color="red">
      <p class="text-red-500">{error}</p>
      <Button color="red" class="mt-4">Retry</Button>
    </Card>
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
