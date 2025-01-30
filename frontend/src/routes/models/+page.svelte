<script lang="ts">
  import { onMount } from 'svelte';
  import { Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell, Spinner, Alert, Input, Checkbox, Select } from 'flowbite-svelte';

  interface Client {
    id: string;
    version: string;
    available: boolean;
    model_count: number;
    last_heartbeat: string;
  }

  interface Model {
    name: string;
    size: number;
    digest: string;
    modified_at: number;
  }

  let clients: Client[] = [];
  let selectedClient: string | null = null;
  let models: Model[] = [];
  let filteredModels: Model[] = [];
  let loading = true;
  let error: string | null = null;
  let searchTerm = '';
  let sortField: 'name' | 'size' | 'modified_at' = 'name';
  let sortDirection: 'asc' | 'desc' = 'asc';
  let selectedModels: Set<string> = new Set();

  const API_URL = 'http://localhost:8881/api/v1';

  async function fetchClients() {
    try {
      const response = await fetch(`${API_URL}/models/clients`);
      if (!response.ok) {
        throw new Error(`Failed to fetch clients: ${await response.text()}`);
      }
      clients = await response.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load clients';
      console.error('Error:', e);
    }
  }

  async function fetchModels(clientId: string) {
    try {
      const response = await fetch(`${API_URL}/models?client_id=${clientId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${await response.text()}`);
      }
      models = await response.json();
      selectedModels.clear();
      filterAndSortModels();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load models';
      console.error('Error:', e);
    }
  }

  async function handleClientChange(event: Event) {
    const select = event.target as HTMLSelectElement;
    selectedClient = select.value || null;
    if (selectedClient) {
      await fetchModels(selectedClient);
    } else {
      models = [];
      filteredModels = [];
      selectedModels.clear();
    }
  }

  function filterAndSortModels() {
    // First filter
    filteredModels = models.filter(model => 
      model.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Then sort
    filteredModels.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      return sortDirection === 'asc'
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });
  }

  function handleSort(field: typeof sortField) {
    if (sortField === field) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortField = field;
      sortDirection = 'asc';
    }
    filterAndSortModels();
  }

  function toggleSelectAll() {
    if (selectedModels.size === filteredModels.length) {
      selectedModels.clear();
    } else {
      selectedModels = new Set(filteredModels.map(model => model.name));
    }
    selectedModels = selectedModels; // Trigger reactivity
  }

  function toggleModelSelection(modelName: string) {
    if (selectedModels.has(modelName)) {
      selectedModels.delete(modelName);
    } else {
      selectedModels.add(modelName);
    }
    selectedModels = selectedModels; // Trigger reactivity
  }

  $: {
    if (searchTerm !== undefined && models) {
      filterAndSortModels();
    }
  }

  onMount(async () => {
    try {
      await fetchClients();
    } finally {
      loading = false;
    }
  });

  function formatSize(bytes: number): string {
    if (!bytes) return '0 B';
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
    if (!timestamp) return 'Unknown';
    try {
      return new Date(timestamp * 1000).toLocaleString();
    } catch (e) {
      return 'Invalid Date';
    }
  }

  function getSortIcon(field: typeof sortField) {
    if (sortField !== field) return '↕';
    return sortDirection === 'asc' ? '↑' : '↓';
  }
</script>

<div class="container mx-auto p-4 space-y-6">
  {#if loading}
    <div class="flex justify-center items-center min-h-[200px]">
      <Spinner size="xl" />
    </div>
  {:else if error}
    <Alert color="red">
      {error}
    </Alert>
  {:else}
    <div class="w-full max-w-md">
      <label for="client-select" class="block mb-2 text-sm font-medium text-gray-400">
        Select Ollama Client ({clients.length} available)
      </label>
      <Select
        id="client-select"
        class="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 hover:bg-gray-600 transition-colors"
        on:change={handleClientChange}
        value={selectedClient}
      >
        <option value="">Select a client...</option>
        {#each clients as client}
          <option value={client.id}>
            {client.id} (v{client.version}) - {client.model_count} models
          </option>
        {/each}
      </Select>
    </div>

    {#if selectedClient}
      <div class="w-full max-w-md mb-4">
        <label for="search" class="block mb-2 text-sm font-medium text-gray-400">
          Search Models
        </label>
        <Input
          id="search"
          type="search"
          placeholder="Type to filter models..."
          bind:value={searchTerm}
          class="bg-gray-700 border-gray-600 text-white"
        />
      </div>

      {#if filteredModels.length > 0}
        <div class="flex justify-between items-center mb-4">
          <div class="text-sm text-gray-400">
            {selectedModels.size} of {filteredModels.length} models selected
          </div>
          {#if selectedModels.size > 0}
            <div class="flex gap-2">
              <button class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500">
                Run Selected Models
              </button>
            </div>
          {/if}
        </div>

        <div class="relative overflow-x-auto shadow-md sm:rounded-lg">
          <Table noborder={true} color="custom" class="w-full text-sm text-left">
            <TableHead class="text-xs uppercase bg-gray-800 text-gray-400 sticky top-0">
              <TableHeadCell class="!bg-gray-800 w-8">
                <Checkbox checked={selectedModels.size === filteredModels.length && filteredModels.length > 0} on:change={toggleSelectAll} />
              </TableHeadCell>
              <TableHeadCell class="!bg-gray-800 cursor-pointer select-none" on:click={() => handleSort('name')}>
                Model Name <span class="ml-1">{getSortIcon('name')}</span>
              </TableHeadCell>
              <TableHeadCell class="!bg-gray-800 cursor-pointer select-none" on:click={() => handleSort('size')}>
                Size <span class="ml-1">{getSortIcon('size')}</span>
              </TableHeadCell>
              <TableHeadCell class="!bg-gray-800 cursor-pointer select-none" on:click={() => handleSort('modified_at')}>
                Modified <span class="ml-1">{getSortIcon('modified_at')}</span>
              </TableHeadCell>
              <TableHeadCell class="!bg-gray-800">Digest</TableHeadCell>
            </TableHead>
            <TableBody class="divide-y divide-gray-700">
              {#each filteredModels as model}
                <TableBodyRow class="bg-gray-800 border-gray-700 hover:bg-gray-700 transition-colors">
                  <TableBodyCell class="w-8">
                    <Checkbox checked={selectedModels.has(model.name)} on:change={() => toggleModelSelection(model.name)} />
                  </TableBodyCell>
                  <TableBodyCell class="font-medium text-gray-200">{model.name}</TableBodyCell>
                  <TableBodyCell class="text-gray-300">{formatSize(model.size)}</TableBodyCell>
                  <TableBodyCell class="text-gray-300">{formatDate(model.modified_at)}</TableBodyCell>
                  <TableBodyCell class="font-mono text-xs text-gray-400">{model.digest ? model.digest.substring(0, 12) : 'N/A'}</TableBodyCell>
                </TableBodyRow>
              {/each}
            </TableBody>
          </Table>
        </div>
      {:else}
        <div class="text-center text-gray-400 py-12 bg-gray-800 rounded-lg">
          {searchTerm ? 'No models match your search' : 'No models found for this client'}
        </div>
      {/if}
    {/if}
  {/if}
</div>

<style>
  :global(.table-custom) {
    --table-color: transparent;
    --table-header-bg: transparent;
    --table-color-hover: #374151;
    --table-color-striped: transparent;
  }
  
  /* Override Flowbite's default table styles */
  :global(th) {
    text-transform: uppercase !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
  }
  
  :global(td, th) {
    padding-top: 0.75rem !important;
    padding-bottom: 0.75rem !important;
  }
</style>
