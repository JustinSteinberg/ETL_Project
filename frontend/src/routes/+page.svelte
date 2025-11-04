<script lang="ts">
    import Header from '$lib/components/Header.svelte'
    import SummaryCard from '$lib/components/SummaryCard.svelte'
    import RowsTable from '$lib/components/RowsTable.svelte'
    import USChoropleth from '$lib/components/USChoropleth.svelte'
    import { Badge } from '$lib/components/ui/badge'
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card'
    import { Tabs, TabsList, TabsTrigger, TabsContent } from '$lib/components/ui/tabs'
    import { runETL } from '$lib/api'
    import { browser } from '$app/environment'

    import { onMount, onDestroy } from 'svelte'
    import { page } from '$app/stores'
    import { goto } from '$app/navigation'
    import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, Title } from 'chart.js'
    Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, Title)
  
    // ---- loader data ----
    export let data: { stats: any; initialRows: any[] }
    let stats = data.stats
    let rows: any[] = data.initialRows
  
    // ---- UI state ----
    const STATES = ['AL','AK','AZ','AR','CA','CO','CT','DE','DC','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
  
    // Region + week inputs (persisted via URL)
    let region = 'MA'         // two-letter code
    let startWeek = ''        // "YYYY-Www"
    let endWeek = ''          // "YYYY-Www"
  
    // Derived dates (YYYY-MM-DD Monday of ISO week)
    let start = ''
    let end   = ''
  
    // Busy / errors
    let busy = false
    let errorMsg = ''
    let lastResult: { rows_loaded?: number; first_week?: string; last_week?: string } | null = null
    let view = 'chart' // chart | table
  
    // Convert "YYYY-Www" -> Monday YYYY-MM-DD
    function weekToMonday(weekStr: string): string | '' {
      if (!weekStr) return ''
      const [yPart, wPart] = weekStr.split('-W')
      const year = Number(yPart)
      const week = Number(wPart)
      if (!year || !week) return ''
      const d = new Date(Date.UTC(year, 0, 4)) // Jan 4 is in ISO week 1
      const day = d.getUTCDay() || 7
      d.setUTCDate(d.getUTCDate() - (day - 1) + (week - 1) * 7)
      return d.toISOString().slice(0, 10)
    }
  
    // Keep derived dates in sync with week inputs
    $: start = weekToMonday(startWeek)
    $: end   = weekToMonday(endWeek)
  
    // validity: require state + both weeks (and order)
    $: filtersValid = Boolean(region && startWeek && endWeek && (!start || !end || start <= end))
    $: if (start && end && start > end) errorMsg = 'Start week must be before end week.'
  
    // qs helper
    function qs(params: Record<string, string | number | undefined>) {
      const u = new URLSearchParams()
      for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== '') u.set(k, String(v))
      return u.toString()
    }
  
    // --- URL <-> state sync ---
    // On mount, read current URL params into state
    onMount(() => {
        if (!browser) return
        const sp = $page.url.searchParams
        const urlState  = sp.get('state')
        const urlStartW = sp.get('startWeek')
        const urlEndW   = sp.get('endWeek')
        if (urlState && STATES.includes(urlState.toUpperCase())) region = urlState.toUpperCase()
        if (urlStartW) startWeek = urlStartW
        if (urlEndW)   endWeek = urlEndW
    })
    // Whenever region/startWeek/endWeek change, write them to the URL (replaceState to avoid history spam)
    let syncingURL = false

    $: if (browser && !syncingURL) {                    // ← add browser guard
        const sp = $page.url.searchParams
        const curState  = sp.get('state') || ''
        const curStartW = sp.get('startWeek') || ''
        const curEndW   = sp.get('endWeek') || ''

        const nextState  = region || ''
        const nextStartW = startWeek || ''
        const nextEndW   = endWeek || ''

        const changed = curState !== nextState || curStartW !== nextStartW || curEndW !== nextEndW
        if (changed) {
            const newParams = new URLSearchParams(sp)
            if (nextState)  newParams.set('state', nextState);   else newParams.delete('state')
            if (nextStartW) newParams.set('startWeek', nextStartW); else newParams.delete('startWeek')
            if (nextEndW)   newParams.set('endWeek', nextEndW);     else newParams.delete('endWeek')

            syncingURL = true
            goto(`?${newParams.toString()}`, { replaceState: true, keepFocus: true, noScroll: true })
            .finally(() => setTimeout(() => { syncingURL = false }, 0))
        }

    }

    async function fetchRows(limit = 50, offset = 0) {
      if (!filtersValid) throw new Error('Choose state and week range first.')
      const r = await fetch(`/data?${qs({ limit, offset, region, start_date: start, end_date: end })}`)
      if (!r.ok) throw new Error(`Data failed: ${r.status}`)
      return r.json() as Promise<{ total: number; rows: any[] }>
    }
  
    async function fetchStats() {
      if (!filtersValid) throw new Error('Choose state and week range first.')
      const r = await fetch(`/stats?${qs({ region, start_date: start, end_date: end })}`)
      if (!r.ok) throw new Error(`Stats failed: ${r.status}`)
      return r.json()
    }
  
    // ---- Chart bits ----
    let canvas: HTMLCanvasElement
    let chart: Chart | null = null
  
    function fmtDateLabel(dVal: any): string {
      try {
        if (typeof dVal === 'string' && /^\d{4}-\d{2}-\d{2}/.test(dVal)) return dVal.slice(0, 10)
        const d = new Date(dVal)
        if (Number.isNaN(d.getTime())) return String(dVal ?? '')
        return d.toISOString().slice(0, 10)
      } catch {
        return String(dVal ?? '')
      }
    }
  
    function renderChart() {
      if (!canvas) return
      if (chart) chart.destroy()
      const labels = rows.map(r => fmtDateLabel(r.date))
      const values = rows.map(r => Number(r.value))
  
      chart = new Chart(canvas.getContext('2d')!, {
        type: 'line',
        data: { labels, datasets: [{ label: 'ILI (%)', data: values, borderWidth: 2, tension: 0.25, pointRadius: 0 }] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: {
              title: (items) => items[0]?.label ?? '',
              label: (item) => ` ILI: ${values[item.dataIndex].toFixed(3)}%`
            }},
            title: { display: true, text: 'Weighted ILI (%) by Epiweek' }
          },
          scales: {
            x: { ticks: { maxTicksLimit: 8 } },
            y: { beginAtZero: true, title: { display: true, text: 'ILI (%)' } }
          }
        }
      })
    }
  
    onMount(renderChart)
    onDestroy(() => { if (chart) chart?.destroy() })
    $: rows, renderChart()
  
    // ---- Extra summary (client-side) ----
    type ExtraStats = {
      mean?: number
      median?: number
      stdev?: number
      latestValue?: number
      latestDate?: string
      weeks?: number
      region?: string
    }
    function computeExtraStats(rs: any[]): ExtraStats {
      if (!rs || rs.length === 0) return {}
      const vals = rs.map(r => Number(r.value)).filter(v => Number.isFinite(v)).sort((a,b)=>a-b)
      const n = vals.length
      const mean = vals.reduce((a,b)=>a+b,0) / n
      const median = n % 2 ? vals[(n-1)/2] : (vals[n/2-1] + vals[n/2]) / 2
      const varPop = vals.reduce((a,b)=>a + (b-mean)*(b-mean), 0) / n
      const stdev = Math.sqrt(varPop)
      const sorted = [...rs].sort((a,b)=> new Date(a.date).getTime() - new Date(b.date).getTime())
      const last = sorted[sorted.length-1]
      return {
        mean, median, stdev,
        latestValue: Number(last?.value),
        latestDate: fmtDateLabel(last?.date),
        weeks: n,
        region
      }
    }
    $: extra = computeExtraStats(rows)

    let mapValues: Record<string, number> = {}

    // helper to fetch all-states aggregate for selected weeks
    async function fetchMapValues() {
        if (!filtersValid) { mapValues = {}; return }
        const r = await fetch(`/map?${qs({ start_date: start, end_date: end })}`)
        if (!r.ok) throw new Error(`Map failed: ${r.status}`)
        mapValues = await r.json() // e.g., { MA: 1.23, NY: 0.87, ... }
    }
  
    // ---- actions ----
    async function handleRun() {
        errorMsg = ''
        lastResult = null
        if (!filtersValid) { errorMsg = 'Please select a state and a start/end week.'; return }
        busy = true
        try {
            // 1) Load ALL states for range (fuel the map)
            const res = await runETL(fetch, 'all', start, end)
            lastResult = res

            // 2) Refresh selected state's table & stats
            const dataRes = await fetchRows(50, 0)
            rows = dataRes.rows
            stats = await fetchStats()

            // 3) Refresh the choropleth values for ALL states
            await fetchMapValues()
        } catch (e) {
            errorMsg = e instanceof Error ? e.message : String(e)
        } finally {
            busy = false
        }
        }

        async function reloadRows() {
        try {
            if (!filtersValid) { errorMsg = 'Please select a state and a start/end week.'; return }
            const dataRes = await fetchRows(50, 0)
            rows = dataRes.rows
            stats = await fetchStats()
            await fetchMapValues()
        } catch (e) {
            errorMsg = e instanceof Error ? e.message : String(e)
        }
        }

    // Using mean ILI (%) over the selected period.
    function computeStateMeans(rs: any[]): Record<string, number> {
    const sums: Record<string, number> = {}
    const counts: Record<string, number> = {}
    for (const r of rs) {
        const st = (r.region || '').toUpperCase()
        const v = Number(r.value)
        if (!st || !Number.isFinite(v)) continue
        sums[st] = (sums[st] ?? 0) + v
        counts[st] = (counts[st] ?? 0) + 1
    }
    const out: Record<string, number> = {}
    for (const st of Object.keys(sums)) out[st] = sums[st] / counts[st]
    return out
    }
    $: mapValues = computeStateMeans(rows)

    // Label for the chosen time span
    $: mapLabel = stats?.start && stats?.end ? `Epiweeks ${stats.start} → ${stats.end}` : ''
  </script>
  
  <Header />
  
  <main class="max-w-5xl mx-auto p-4 space-y-4">
    <Card>
      <CardHeader class="flex items-center justify-between gap-3">
        <CardTitle class="text-lg">Run ETL</CardTitle>
  
        <div class="flex flex-wrap items-center gap-2">
          <!-- State -->
          <select bind:value={region} class="rounded-md border px-3 py-2 text-sm">
            {#each STATES as s}<option value={s}>{s}</option>{/each}
          </select>
  
          <!-- Week range -->
          <input type="week" bind:value={startWeek} class="rounded-md border px-3 py-2 text-sm" />
          <span class="text-gray-400 text-sm">→</span>
          <input type="week" bind:value={endWeek} class="rounded-md border px-3 py-2 text-sm" />
  
          <!-- Run -->
          <button
            type="button"
            on:click={handleRun}
            disabled={busy || !filtersValid}
            class="inline-flex items-center justify-center rounded-md bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            title={!filtersValid ? 'Pick a state and weeks first' : ''}
          >
            {#if busy}
              <svg class="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.25" />
                <path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" stroke-width="4" fill="none" />
              </svg>
            {/if}
            {busy ? 'Running…' : 'Run ETL'}
          </button>
  
          <!-- Download (respects filters) -->
          <a href={`/download.csv?${qs({ region, start_date: start, end_date: end })}`}>
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md border px-4 py-2 text-sm font-medium hover:bg-gray-50"
              disabled={!filtersValid}
              title={!filtersValid ? 'Pick a state and weeks first' : ''}
            >
              Download CSV
            </button>
          </a>
        </div>
      </CardHeader>
  
      {#if !filtersValid}
        <CardContent>
          <div class="text-gray-600 bg-gray-50 p-2 rounded text-sm">
            Select a <b>state</b> and a <b>start/end week</b> (ISO week), then click <i>Run ETL</i>.
          </div>
        </CardContent>
      {/if}
  
      {#if errorMsg}
        <CardContent>
          <div class="text-red-700 bg-red-50 p-2 rounded" aria-live="polite">
            {errorMsg}
          </div>
        </CardContent>
      {/if}
  
      {#if lastResult}
        <CardContent>
          <Badge variant="secondary">
            Loaded {lastResult.rows_loaded ?? 0} {lastResult.rows_loaded === 1 ? 'row' : 'rows'}
          </Badge>
        </CardContent>
      {/if}
    </Card>
  
    <!-- Existing summary -->
    <SummaryCard {stats} />
  
    <!-- Extra summary (client-side) -->
    <Card>
      <CardHeader>
        <CardTitle>Other Stats</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-2">
          <div><div class="text-sm text-gray-500">State</div><div class="font-medium">{region}</div></div>
          <div><div class="text-sm text-gray-500">Weeks</div><div class="font-medium">{extra.weeks ?? 0}</div></div>
          <div><div class="text-sm text-gray-500">Mean ILI</div><div class="font-medium">{extra.mean?.toFixed(3) ?? '—'}</div></div>
          <div><div class="text-sm text-gray-500">Median ILI</div><div class="font-medium">{extra.median?.toFixed(3) ?? '—'}</div></div>
          <div><div class="text-sm text-gray-500">Std Dev</div><div class="font-medium">{extra.stdev?.toFixed(3) ?? '—'}</div></div>
          <div><div class="text-sm text-gray-500">Latest (date)</div><div class="font-medium">{extra.latestValue?.toFixed?.(3) ?? '—'}{extra.latestDate ? ` on ${extra.latestDate}` : ''}</div></div>
        </div>
      </CardContent>
    </Card>
  
    <Card>
      <CardHeader class="flex items-center justify-between">
        <CardTitle>Explore</CardTitle>
        <button
          type="button"
          class="rounded-md border px-3 py-1.5 text-sm hover:bg-gray-50"
          on:click={reloadRows}
          disabled={!filtersValid || busy}
          title={!filtersValid ? 'Pick a state and weeks first' : ''}
        >
          Reload
        </button>
      </CardHeader>
  
      <CardContent class="space-y-3">
        <Tabs value={view} on:change={(e: CustomEvent) => (view = (e as any).detail.value)}>
          <TabsList>
            <TabsTrigger value="chart">Chart</TabsTrigger>
            <TabsTrigger value="table">Table</TabsTrigger>
            <TabsTrigger value="map">Map</TabsTrigger>
          </TabsList>
  
          <TabsContent value="chart">
            <div class="text-xs text-gray-500 mb-1">Mode: <span class="font-medium">Weighted ILI (%) by epiweek</span></div>
            <div class="h-64">
              <canvas bind:this={canvas} aria-label="ILI line chart"></canvas>
            </div>
            <div class="mt-2 text-xs text-gray-500">
              {#if stats?.start && stats?.end}
                Showing {rows.length} rows for {region}, {stats.start} → {stats.end}.
              {:else}
                Choose a state and week range to render the chart.
              {/if}
            </div>
          </TabsContent>
  
          <TabsContent value="table">
            <!-- Optional: add your pagination controls here if you implemented them -->
            <RowsTable {rows} />
          </TabsContent>
          <TabsContent value="map">
            <USChoropleth
              values={mapValues}
              title="Influenza-Like Illness — State Heat Map"
              legendLabel="Weighted ILI (%)"
              weekLabel={mapLabel}
              fmt={(n)=>`${n.toFixed(2)}%`}
            />
            <div class="mt-2 text-xs text-gray-500">
              Colors show the average ILI (%) per state across the selected weeks.
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  </main>
  