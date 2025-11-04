<script lang="ts">
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card'
    export let stats: {count:number; min:number|null; max:number|null; start:string|null; end:string|null; regions:string[]} | null = null
  </script>
  
  <Card>
    <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
    <CardContent>
      {#if stats}
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div><div class="text-gray-500">Count</div><div class="font-mono">{stats.count}</div></div>
          <div><div class="text-gray-500">Min</div><div class="font-mono">{stats.min ?? '—'}</div></div>
          <div><div class="text-gray-500">Max</div><div class="font-mono">{stats.max ?? '—'}</div></div>
          <div><div class="text-gray-500">Range</div><div class="font-mono">{stats.start ?? '—'} → {stats.end ?? '—'}</div></div>
        </div>
      {:else}
        <div class="text-sm text-gray-500">No stats yet.</div>
      {/if}
    </CardContent>
  </Card>
  