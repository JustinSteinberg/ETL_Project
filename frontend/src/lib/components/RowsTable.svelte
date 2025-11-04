<script lang="ts">
    export let rows: Array<{ date: string; region: string; value: number; metric?: string }> = []
  </script>
  
  <div class="overflow-x-auto rounded-md border">
    <table class="min-w-full text-sm">
      <caption class="text-left p-3 text-gray-500">
        Each row is a weekly observation (epiweek → Monday date) for the selected state.
        <br />Value = weighted influenza-like illness percentage (ILI %).
      </caption>
      <thead class="bg-gray-50 text-gray-700">
        <tr>
          <th class="px-3 py-2 text-left font-medium">Week (Monday)</th>
          <th class="px-3 py-2 text-left font-medium">State</th>
          <th class="px-3 py-2 text-left font-medium">Weighted ILI (%)</th>
          <th class="px-3 py-2 text-left font-medium">Metric</th>
        </tr>
      </thead>
      <tbody>
        {#if rows.length === 0}
          <tr><td colspan="4" class="px-3 py-4 text-center text-gray-500">No data for the current filters.</td></tr>
        {:else}
          {#each rows as r}
            <tr class="border-t">
              <td class="px-3 py-2 tabular-nums">{r.date?.slice(0,10)}</td>
              <td class="px-3 py-2">{r.region}</td>
              <td class="px-3 py-2 tabular-nums">{Number(r.value).toFixed(3)}</td>
              <td class="px-3 py-2">{r.metric ?? 'ili'}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
  