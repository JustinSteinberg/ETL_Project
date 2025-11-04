<script lang="ts">
    import Header from '$lib/components/Header.svelte'
    import RowsTable from '$lib/components/RowsTable.svelte'
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card'
    import { Button } from '$lib/components/ui/button'
    import { Input } from '$lib/components/ui/input'
    import { Badge } from '$lib/components/ui/badge'
    import { goto } from '$app/navigation'
  
    export let data: { region: string, limit: number, offset: number, total: number, rows: any[] }
    let { region, limit, offset, total, rows } = data
  
    async function applyFilter() {
      goto(`/explore?region=${encodeURIComponent(region)}&limit=${limit}&offset=0`)
    }
    function nextPage(){ if (offset + limit < total) goto(`/explore?region=${region}&limit=${limit}&offset=${offset+limit}`) }
    function prevPage(){ if (offset - limit >= 0) goto(`/explore?region=${region}&limit=${limit}&offset=${offset-limit}`) }
  </script>
  
  <Header />
  
  <main class="max-w-5xl mx-auto p-4">
    <Card>
      <CardHeader class="flex items-center justify-between gap-3">
        <CardTitle class="text-lg">Explore</CardTitle>
        <div class="flex items-center gap-2">
          <Input bind:value={region} placeholder="Region e.g., MA" class="w-36" />
          <Button variant="outline" on:click={applyFilter}>Filter</Button>
          <Badge variant="secondary">Total: {total}</Badge>
        </div>
      </CardHeader>
      <CardContent class="space-y-3">
        <RowsTable {rows} />
        <div class="flex items-center justify-between">
          <Button variant="outline" on:click={prevPage} disabled={offset===0}>Prev</Button>
          <div class="text-sm text-gray-500">Showing {offset+1}-{Math.min(offset+limit, total)} of {total}</div>
          <Button variant="outline" on:click={nextPage} disabled={offset+limit>=total}>Next</Button>
        </div>
      </CardContent>
    </Card>
  </main>
  