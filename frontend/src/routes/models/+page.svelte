<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell, Button, Spinner } from 'flowbite-svelte';

  let models: any[] = [];
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/models');
      if (!response.ok) throw new Error('Failed to fetch models');
      models = await response.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load models';
    } finally {
      loading = false;
    }
  });
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
              <TableBodyCell>{model.size}</TableBodyCell>
              <TableBodyCell>{new Date(model.modified).toLocaleString()}</TableBodyCell>
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
