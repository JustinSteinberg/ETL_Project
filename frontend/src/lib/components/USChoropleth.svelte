<script lang="ts">
    import * as d3 from 'd3'
    import { feature, mesh } from 'topojson-client'
    // @ts-ignore
    import us from 'us-atlas/states-10m.json'
  
    export let values: Record<string, number> = {}
    export let title = 'US Heat Map'
    export let legendLabel = 'Intensity'
    export let domain: [number, number] | null = null
    export let fmt: (n: number) => string = (n) => (Number.isFinite(n) ? n.toFixed(3) : '—')
    export let weekLabel = ''
  
    const USPS2FIPS: Record<string, string> = {
      AL:'01', AK:'02', AZ:'04', AR:'05', CA:'06', CO:'08', CT:'09', DE:'10', DC:'11',
      FL:'12', GA:'13', HI:'15', ID:'16', IL:'17', IN:'18', IA:'19', KS:'20', KY:'21',
      LA:'22', ME:'23', MD:'24', MA:'25', MI:'26', MN:'27', MS:'28', MO:'29', MT:'30',
      NE:'31', NV:'32', NH:'33', NJ:'34', NM:'35', NY:'36', NC:'37', ND:'38', OH:'39',
      OK:'40', OR:'41', PA:'42', RI:'44', SC:'45', SD:'46', TN:'47', TX:'48', UT:'49',
      VT:'50', VA:'51', WA:'53', WV:'54', WI:'55', WY:'56'
    }
  
    // Topology → features (static)
    const states = feature(us as any, (us as any).objects.states) as any
    const nation = mesh(us as any, (us as any).objects.nation) as any
  
    let width = 880
    let height = 540
  
    // Projection/path (static)
    const projection = d3.geoAlbersUsa().fitSize([width, height], states)
    const path = d3.geoPath(projection)
  
    // Reactive: convert values → byFips
    let byFips: Record<string, number> = {}
    $: {
      const tmp: Record<string, number> = {}
      for (const [abbr, v] of Object.entries(values || {})) {
        const f = USPS2FIPS[abbr.toUpperCase()]
        if (f && Number.isFinite(v as number)) tmp[f] = Number(v)
      }
      byFips = tmp
    }
  
    // Reactive: domain and color scale
    let vmin = 0, vmax = 1
    $: {
      const dataVals = Object.values(byFips)
      const dmin = dataVals.length ? d3.min(dataVals)! : 0
      const dmax = dataVals.length ? d3.max(dataVals)! : 1
      ;[vmin, vmax] = domain ?? [dmin, dmax]
      if (vmin === vmax) { vmin = 0; vmax = vmin + 1e-6 } // avoid NaN gradient
    }
    $: color = d3.scaleSequential(d3.interpolateYlOrRd).domain([vmin, vmax])
  
    // Tooltip
    let tipVisible = false
    let tipX = 0
    let tipY = 0
    let tipText = ''
  
    function onEnter(e: MouseEvent, f: any) {
      const fips: string = f.id?.toString().padStart(2, '0')
      const name: string = f.properties?.name ?? 'Unknown'
      const val = byFips[fips]
      tipText = `${name}: ${Number.isFinite(val) ? fmt(val) : '—'}`
      tipVisible = true
      onMove(e)
    }
    function onMove(e: MouseEvent) {
      const box = (e.currentTarget as SVGElement).getBoundingClientRect()
      tipX = e.clientX - box.left + 10
      tipY = e.clientY - box.top + 10
    }
    function onLeave() { tipVisible = false }
  </script>
  
  <div class="space-y-1">
    <div class="text-sm text-gray-500">Mode: <span class="font-medium">{legendLabel} by state</span></div>
    <div class="text-xl font-semibold">{title}</div>
    {#if weekLabel}<div class="text-xs text-gray-500">{weekLabel}</div>{/if}
  </div>
  
  <div class="relative overflow-hidden rounded-lg border">
    <svg {width} {height} on:mousemove={onMove}>
      {#each states.features as f}
        {@const fips = (f.id ?? '').toString().padStart(2, '0')}
        {@const v = byFips[fips]}
        <path
          d={path(f) || ''}
          fill={Number.isFinite(v) ? color(v) : '#eee'}
          stroke="white"
          stroke-width="0.5"
          on:mouseenter={(e)=>onEnter(e, f)}
          on:mouseleave={onLeave}
        />
      {/each}
      <path d={path(nation) || ''} fill="none" stroke="#333" stroke-width="0.8" />
    </svg>
  
    {#if tipVisible}
      <div class="pointer-events-none absolute rounded bg-black/80 px-2 py-1 text-xs text-white"
           style={`left:${tipX}px; top:${tipY}px`}>
        {tipText}
      </div>
    {/if}
  </div>
  
  <div class="mt-2 flex items-center gap-3">
    <div class="text-xs text-gray-600 shrink-0">{legendLabel}</div>
    <div class="h-3 w-56 rounded"
         style={`background: linear-gradient(90deg, ${d3.ticks(0, 1, 10).map(t => color(vmin + t*(vmax-vmin))).join(',')});`}>
    </div>
    <div class="text-xs text-gray-600 tabular-nums">{fmt(vmin)}</div>
    <div class="text-xs text-gray-600 ml-auto tabular-nums">{fmt(vmax)}</div>
  </div>
  
  <style>
    .tabular-nums { font-variant-numeric: tabular-nums; }
  </style>
  