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

  // ---- Props from SvelteKit page loader ----
  export let data: { stats: any; initialRows: any[] }
  
  // ---- UI State Variables ----
  const ALL_US_STATES = ['AL','AK','AZ','AR','CA','CO','CT','DE','DC','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']

  // User-selected filters (synced with URL)
  let selectedRegion = 'MA'              // Two-letter USPS state code
  let selectedStartWeek = ''             // ISO week format: "YYYY-Www"
  let selectedEndWeek = ''               // ISO week format: "YYYY-Www"

  // Derived ISO date strings from week inputs
  let selectedStartDate = ''             // "YYYY-MM-DD" format
  let selectedEndDate = ''               // "YYYY-MM-DD" format

  // Data and UI state
  let observationRows: any[] = data.initialRows
  let summaryStatistics = data.stats
  let isLoadingData = false
  let userErrorMessage = ''
  let lastETLResult: { rows_loaded?: number; first_week?: string; last_week?: string } | null = null
  let activeTabView = 'chart'            // chart | table | map

  // Chart.js instance management
  let chartCanvasElement: HTMLCanvasElement
  let chartInstance: Chart | null = null

  // Map data for choropleth visualization
  let stateILIAverages: Record<string, number> = {}

  /**
   * Convert ISO week string "YYYY-Www" to the Monday date of that week in "YYYY-MM-DD" format.
   * ISO weeks start on Monday and the first week contains January 4th.
   * 
   * @param isoWeekString - ISO week format like "2024-W01"
   * @returns Monday date string "YYYY-MM-DD" or empty string if invalid
   */
  function convertISOWeekToMondayDate(isoWeekString: string): string | '' {
    if (!isoWeekString) return ''
    
    const [yearPart, weekPart] = isoWeekString.split('-W')
    const year = Number(yearPart)
    const week = Number(weekPart)
    
    if (!year || !week) return ''
    
    // January 4th is always in ISO week 1
    const januaryFourth = new Date(Date.UTC(year, 0, 4))
    const dayOfWeek = januaryFourth.getUTCDay() || 7 // Sunday=7, Monday=1
    
    // Calculate the Monday of week 1
    januaryFourth.setUTCDate(januaryFourth.getUTCDate() - (dayOfWeek - 1) + (week - 1) * 7)
    
    return januaryFourth.toISOString().slice(0, 10)
  }

  // Reactively update derived dates when week inputs change
  $: selectedStartDate = convertISOWeekToMondayDate(selectedStartWeek)
  $: selectedEndDate = convertISOWeekToMondayDate(selectedEndWeek)

  // Form validation: ensure all required fields are filled and dates are in correct order
  $: areFiltersValid = Boolean(
      selectedRegion && 
      selectedStartWeek && 
      selectedEndWeek && 
      (!selectedStartDate || !selectedEndDate || selectedStartDate <= selectedEndDate)
  )
  
  // Show error if dates are out of order
  $: if (selectedStartDate && selectedEndDate && selectedStartDate > selectedEndDate) {
      userErrorMessage = 'Start week must be before or equal to end week.'
  }

  /**
   * Build a clean URL query string from parameters, omitting empty/undefined values.
   * 
   * @param parameters - Object with key-value pairs for query string
   * @returns URL-encoded query string
   */
  function buildQueryString(parameters: Record<string, string | number | undefined>): string {
    const urlParams = new URLSearchParams()
    
    for (const [key, value] of Object.entries(parameters)) {
      if (value !== undefined && value !== '') {
        urlParams.set(key, String(value))
      }
    }
    
    return urlParams.toString()
  }

  /**
   * Initialize component by restoring filter state from URL parameters.
   * Runs once when component mounts in the browser.
   * Loads data if valid filters are present in the URL.
   */
  onMount(async () => {
      if (!browser) return
      
      // Restore filter state from URL query parameters
      const currentURLParams = $page.url.searchParams
      const urlStateCode = currentURLParams.get('state')
      const urlStartWeek = currentURLParams.get('startWeek')
      const urlEndWeek = currentURLParams.get('endWeek')
      
      if (urlStateCode && ALL_US_STATES.includes(urlStateCode.toUpperCase())) {
          selectedRegion = urlStateCode.toUpperCase()
      }
      if (urlStartWeek) selectedStartWeek = urlStartWeek
      if (urlEndWeek) selectedEndWeek = urlEndWeek
      
      // If filters are valid from URL, load the data
      if (areFiltersValid) {
          await loadDataForCurrentFilters()
      }
  })

  // Track URL sync state to prevent infinite loops
  let isSyncingURLState = false

  /**
   * Reactively sync filter state to URL parameters without adding to browser history.
   * Updates URL whenever selectedRegion, selectedStartWeek, or selectedEndWeek changes.
   */
  $: if (browser && !isSyncingURLState) {
      const currentURLParams = $page.url.searchParams
      const currentURLState = currentURLParams.get('state') || ''
      const currentURLStartWeek = currentURLParams.get('startWeek') || ''
      const currentURLEndWeek = currentURLParams.get('endWeek') || ''

      const newURLState = selectedRegion || ''
      const newURLStartWeek = selectedStartWeek || ''
      const newURLEndWeek = selectedEndWeek || ''

      const hasURLChanged = 
          currentURLState !== newURLState || 
          currentURLStartWeek !== newURLStartWeek || 
          currentURLEndWeek !== newURLEndWeek
          
      if (hasURLChanged) {
          const updatedParams = new URLSearchParams(currentURLParams)
          
          if (newURLState) {
              updatedParams.set('state', newURLState)
          } else {
              updatedParams.delete('state')
          }
          
          if (newURLStartWeek) {
              updatedParams.set('startWeek', newURLStartWeek)
          } else {
              updatedParams.delete('startWeek')
          }
          
          if (newURLEndWeek) {
              updatedParams.set('endWeek', newURLEndWeek)
          } else {
              updatedParams.delete('endWeek')
          }

          isSyncingURLState = true
          goto(`?${updatedParams.toString()}`, { 
              replaceState: true, 
              keepFocus: true, 
              noScroll: true 
          }).finally(() => {
              setTimeout(() => { isSyncingURLState = false }, 0)
          })
      }
  }

  /**
   * Fetch paginated observation rows from the database with applied filters.
   * Queries local SQLite database (fast operation, no external API call).
   * 
   * @param rowLimit - Maximum number of rows to return
   * @param rowOffset - Number of rows to skip for pagination
   * @returns Promise with total row count and data array
   */
  async function fetchObservationRowsFromDatabase(
      rowLimit = 50, 
      rowOffset = 0
  ): Promise<{ total: number; rows: any[] }> {
      if (!areFiltersValid) {
          throw new Error('Please select a state and valid week range.')
      }
      
      const queryString = buildQueryString({ 
          limit: rowLimit, 
          offset: rowOffset, 
          region: selectedRegion, 
          start_date: selectedStartDate, 
          end_date: selectedEndDate 
      })
      
      const response = await fetch(`/data?${queryString}`)
      
      if (!response.ok) {
          throw new Error(`Failed to fetch data: ${response.status}`)
      }
      
      return response.json()
  }

  /**
   * Fetch summary statistics from the database with applied filters.
   * Returns aggregated metrics like min, max, count, date range, and regions.
   * Queries local SQLite database (fast operation, no external API call).
   * 
   * @returns Promise with statistics object
   */
  async function fetchSummaryStatisticsFromDatabase(): Promise<any> {
      if (!areFiltersValid) {
          throw new Error('Please select a state and valid week range.')
      }
      
      const queryString = buildQueryString({ 
          region: selectedRegion, 
          start_date: selectedStartDate, 
          end_date: selectedEndDate 
      })
      
      const response = await fetch(`/stats?${queryString}`)
      
      if (!response.ok) {
          throw new Error(`Failed to fetch statistics: ${response.status}`)
      }
      
      return response.json()
  }

  /**
   * Fetch aggregated ILI values for all states to populate the choropleth map.
   * Returns mean ILI percentage per state within the selected date range.
   * Queries local SQLite database (fast operation, no external API call).
   */
  async function fetchStateAveragesForMap(): Promise<void> {
      if (!areFiltersValid) { 
          stateILIAverages = {}
          return 
      }
      
      const queryString = buildQueryString({ 
          start_date: selectedStartDate, 
          end_date: selectedEndDate 
      })
      
      const response = await fetch(`/map?${queryString}`)
      
      if (!response.ok) {
          throw new Error(`Failed to fetch map data: ${response.status}`)
      }
      
      stateILIAverages = await response.json()
  }

  /**
   * Check if database contains data for the current filter selection.
   * If data is missing, automatically fetches it from the CDC API.
   * This is the "smart gap detection" - prevents empty results by fetching on-demand.
   * 
   * @returns true if data exists or was successfully fetched, false otherwise
   */
  async function ensureDatabaseHasDataForSelection(): Promise<boolean> {
      if (!areFiltersValid) return false
      
      try {
          // Check if database already has data for this selection
          const existingStats = await fetchSummaryStatisticsFromDatabase()
          
          if (existingStats.count > 0) {
              console.log(`✓ Database has ${existingStats.count} rows for ${selectedRegion} ${selectedStartDate} to ${selectedEndDate}`)
              return true
          }
          
          // No data found - need to fetch from API
          console.log(`✗ No data in database for ${selectedRegion} ${selectedStartDate} to ${selectedEndDate}`)
          console.log('→ Fetching from CDC API...')
          
          userErrorMessage = `Fetching ${selectedRegion} data from CDC API for ${selectedStartDate} to ${selectedEndDate}...`
          isLoadingData = true
          
          // Fetch missing data from external API
          const etlResult = await runETL(fetch, selectedRegion, selectedStartDate, selectedEndDate)
          console.log('✓ API fetch complete:', etlResult)
          
          userErrorMessage = ''
          
          // Check if API actually returned data
          if (etlResult.rows_loaded === 0) {
              userErrorMessage = `No data available from CDC for ${selectedRegion} in this date range.`
              return false
          }
          
          return true
          
      } catch (error) {
          console.error('Failed to ensure data exists:', error)
          userErrorMessage = `Could not fetch data: ${error instanceof Error ? error.message : String(error)}`
          return false
      } finally {
          isLoadingData = false
      }
  }

  /**
   * Load all data (rows, statistics, map values) for the current filter selection.
   * First ensures database has the data (fetches from API if missing).
   * Then queries the database to populate the UI.
   * This is the primary data loading function called when filters change.
   */
  async function loadDataForCurrentFilters(): Promise<void> {
      try {
          if (!areFiltersValid) { 
              userErrorMessage = 'Please select a state and valid week range.'
              return 
          }
          
          // Ensure database has data for this selection (fetches if missing)
          const hasDataAvailable = await ensureDatabaseHasDataForSelection()
          
          if (!hasDataAvailable) {
              // Error message already set by ensureDatabaseHasDataForSelection()
              return
          }
          
          // Query database for the data we now know exists
          const dataResponse = await fetchObservationRowsFromDatabase(50, 0)
          observationRows = dataResponse.rows
          
          summaryStatistics = await fetchSummaryStatisticsFromDatabase()
          await fetchStateAveragesForMap()
          
          // Verify we actually got data
          if (observationRows.length === 0) {
              userErrorMessage = `No data found for ${selectedRegion} between ${selectedStartDate} and ${selectedEndDate}.`
          }
          
      } catch (error) {
          userErrorMessage = error instanceof Error ? error.message : String(error)
      }
  }

  /**
   * Manually trigger a fresh data fetch from the CDC API for all states.
   * This bypasses the cache and always calls the external API.
   * Used when user explicitly wants the latest data from CDC.
   * Shows confirmation dialog to prevent accidental expensive API calls.
   */
  async function manuallyRefreshDataFromAPI(): Promise<void> {
      userErrorMessage = ''
      lastETLResult = null
      
      if (!areFiltersValid) { 
          userErrorMessage = 'Please select a state and valid week range.'
          return 
      }
      
      // Confirm before making expensive API call
      const userConfirmedRefresh = confirm(
          'This will fetch the latest data from the CDC API for all states. ' +
          'It may take 30-60 seconds. Continue?'
      )
      
      if (!userConfirmedRefresh) return
      
      isLoadingData = true
      
      try {
          // Fetch fresh data from API for ALL states (enables map view)
          const apiResult = await runETL(fetch, 'all', selectedStartDate, selectedEndDate)
          lastETLResult = apiResult

          // Reload the current view with fresh data
          await loadDataForCurrentFilters()
          
      } catch (error) {
          userErrorMessage = error instanceof Error ? error.message : String(error)
      } finally {
          isLoadingData = false
      }
  }

  /**
   * Format various date value types into consistent "YYYY-MM-DD" string format.
   * Handles string dates, Date objects, and invalid inputs gracefully.
   * Used for chart labels and display formatting.
   * 
   * @param dateValue - Date in various formats
   * @returns Formatted date string "YYYY-MM-DD" or stringified value if invalid
   */
  function formatDateAsISOString(dateValue: any): string {
      try {
          // If already a valid ISO date string, return first 10 characters
          if (typeof dateValue === 'string' && /^\d{4}-\d{2}-\d{2}/.test(dateValue)) {
              return dateValue.slice(0, 10)
          }
          
          const parsedDate = new Date(dateValue)
          
          if (Number.isNaN(parsedDate.getTime())) {
              return String(dateValue ?? '')
          }
          
          return parsedDate.toISOString().slice(0, 10)
      } catch {
          return String(dateValue ?? '')
      }
  }

  /**
   * Render or re-render the Chart.js line chart with current observation data.
   * Destroys existing chart instance before creating new one to prevent memory leaks.
   * Displays weighted ILI percentage over time for selected region and date range.
   */
  function renderLineChart(): void {
      if (!chartCanvasElement) return
      
      // Destroy existing chart to prevent memory leaks
      if (chartInstance) {
          chartInstance.destroy()
      }
      
      const chartLabels = observationRows.map(row => formatDateAsISOString(row.date))
      const chartDataValues = observationRows.map(row => Number(row.value))

      chartInstance = new Chart(chartCanvasElement.getContext('2d')!, {
          type: 'line',
          data: { 
              labels: chartLabels, 
              datasets: [{ 
                  label: 'ILI (%)', 
                  data: chartDataValues, 
                  borderWidth: 2, 
                  tension: 0.25, 
                  pointRadius: 0 
              }] 
          },
          options: {
              responsive: true,
              maintainAspectRatio: false,
              interaction: { mode: 'index', intersect: false },
              plugins: {
                  legend: { display: false },
                  tooltip: { 
                      callbacks: {
                          title: (tooltipItems) => tooltipItems[0]?.label ?? '',
                          label: (tooltipItem) => ` ILI: ${chartDataValues[tooltipItem.dataIndex].toFixed(3)}%`
                      }
                  },
                  title: { display: true, text: 'Weighted ILI (%) by Epiweek' }
              },
              scales: {
                  x: { ticks: { maxTicksLimit: 8 } },
                  y: { 
                      beginAtZero: true, 
                      title: { display: true, text: 'ILI (%)' } 
                  }
              }
          }
      })
  }

  // Initialize chart on mount and clean up on unmount
  onMount(renderLineChart)
  onDestroy(() => { 
      if (chartInstance) {
          chartInstance.destroy()
      }
  })
  
  // Re-render chart whenever observation data changes
  $: observationRows, renderLineChart()

  // ---- Client-side statistical calculations ----
  
  type ClientSideStatistics = {
      meanValue?: number
      medianValue?: number
      standardDeviation?: number
      latestObservationValue?: number
      latestObservationDate?: string
      numberOfWeeks?: number
      regionCode?: string
  }
  
  /**
   * Compute additional statistics from current observation data on the client side.
   * Calculates mean, median, standard deviation, and latest value/date.
   * These supplement the server-side stats with more detailed metrics.
   * 
   * @param rows - Array of observation rows from database
   * @returns Object with calculated statistics or empty object if no data
   */
  function calculateClientSideStatistics(rows: any[]): ClientSideStatistics {
      if (!rows || rows.length === 0) return {}
      
      // Extract and sort numeric values
      const numericValues = rows
          .map(row => Number(row.value))
          .filter(value => Number.isFinite(value))
          .sort((a, b) => a - b)
      
      const totalCount = numericValues.length
      
      // Calculate mean
      const sumOfValues = numericValues.reduce((sum, value) => sum + value, 0)
      const meanValue = sumOfValues / totalCount
      
      // Calculate median
      const medianValue = totalCount % 2 
          ? numericValues[(totalCount - 1) / 2] 
          : (numericValues[totalCount / 2 - 1] + numericValues[totalCount / 2]) / 2
      
      // Calculate population standard deviation
      const variancePopulation = numericValues.reduce(
          (sum, value) => sum + (value - meanValue) * (value - meanValue), 
          0
      ) / totalCount
      const standardDeviation = Math.sqrt(variancePopulation)
      
      // Find latest observation by date
      const sortedByDate = [...rows].sort((a, b) => 
          new Date(a.date).getTime() - new Date(b.date).getTime()
      )
      const latestObservation = sortedByDate[sortedByDate.length - 1]
      
      return {
          meanValue,
          medianValue,
          standardDeviation,
          latestObservationValue: Number(latestObservation?.value),
          latestObservationDate: formatDateAsISOString(latestObservation?.date),
          numberOfWeeks: totalCount,
          regionCode: selectedRegion
      }
  }
  
  $: clientStatistics = calculateClientSideStatistics(observationRows)

  /**
   * Compute mean ILI percentage for each state from current observation data.
   * Used to populate the choropleth map with color-coded state values.
   * 
   * @param rows - Array of observation rows
   * @returns Object mapping state codes to mean ILI percentages
   */
  function calculateStateMeanILIValues(rows: any[]): Record<string, number> {
      const stateSums: Record<string, number> = {}
      const stateCounts: Record<string, number> = {}
      
      for (const row of rows) {
          const stateCode = (row.region || '').toUpperCase()
          const iliValue = Number(row.value)
          
          if (!stateCode || !Number.isFinite(iliValue)) continue
          
          stateSums[stateCode] = (stateSums[stateCode] ?? 0) + iliValue
          stateCounts[stateCode] = (stateCounts[stateCode] ?? 0) + 1
      }
      
      const stateMeans: Record<string, number> = {}
      
      for (const stateCode of Object.keys(stateSums)) {
          stateMeans[stateCode] = stateSums[stateCode] / stateCounts[stateCode]
      }
      
      return stateMeans
  }
  
  $: stateILIAverages = calculateStateMeanILIValues(observationRows)

  // Generate human-readable label for map showing the date range
  $: mapDateRangeLabel = summaryStatistics?.start && summaryStatistics?.end 
      ? `Epiweeks ${summaryStatistics.start} → ${summaryStatistics.end}` 
      : ''
</script>

<Header />

<main class="max-w-5xl mx-auto p-4 space-y-4">

  <!-- ETL control panel: filters and actions -->
  <Card>
      <CardHeader class="flex items-center justify-between gap-3">
          <CardTitle class="text-lg">Data Filters</CardTitle>

          <div class="flex flex-wrap items-center gap-2">
              <!-- State selector dropdown -->
              <select 
                  bind:value={selectedRegion} 
                  class="rounded-md border px-3 py-2 text-sm"
                  aria-label="Select state"
              >
                  {#each ALL_US_STATES as stateCode}
                      <option value={stateCode}>{stateCode}</option>
                  {/each}
              </select>

              <!-- Week range selector -->
              <input 
                  type="week" 
                  bind:value={selectedStartWeek} 
                  class="rounded-md border px-3 py-2 text-sm"
                  aria-label="Start week"
              />
              <span class="text-gray-400 text-sm">→</span>
              <input 
                  type="week" 
                  bind:value={selectedEndWeek} 
                  class="rounded-md border px-3 py-2 text-sm"
                  aria-label="End week"
              />

              <!-- Load data button (with smart gap detection) -->
              <button
                  type="button"
                  on:click={loadDataForCurrentFilters}
                  disabled={isLoadingData || !areFiltersValid}
                  class="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                  title={!areFiltersValid ? 'Select a state and valid week range first' : 'Load data (fetches from API if not cached)'}
              >
                  {#if isLoadingData}
                      <svg class="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.25" />
                          <path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" stroke-width="4" fill="none" />
                      </svg>
                  {/if}
                  {isLoadingData ? 'Loading…' : 'Load Data'}
              </button>

              <!-- Manual API refresh button -->
              <button
                  type="button"
                  on:click={manuallyRefreshDataFromAPI}
                  disabled={isLoadingData || !areFiltersValid}
                  class="inline-flex items-center justify-center rounded-md bg-black px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
                  title={!areFiltersValid ? 'Select a state and valid week range first' : 'Refresh data from CDC API (all states)'}
              >
                  Refresh from API
              </button>

              <!-- CSV download link (respects current filters) -->
              <a href={`/download.csv?${buildQueryString({ region: selectedRegion, start_date: selectedStartDate, end_date: selectedEndDate })}`}>
                  <button
                      type="button"
                      class="inline-flex items-center justify-center rounded-md border px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
                      disabled={!areFiltersValid}
                      title={!areFiltersValid ? 'Select a state and valid week range first' : 'Download filtered data as CSV'}
                  >
                      Download CSV
                  </button>
              </a>
          </div>
      </CardHeader>

      <!-- Instructional message when filters are incomplete -->
      {#if !areFiltersValid}
          <CardContent>
              <div class="text-gray-600 bg-gray-50 p-2 rounded text-sm">
                  Select a <b>state</b> and a <b>start/end week</b> (ISO week format), then click <b>Load Data</b>.
                  Data will be fetched from the API only if not already cached.
              </div>
          </CardContent>
      {/if}

      <!-- Error message display -->
      {#if userErrorMessage}
          <CardContent>
              <div class="text-red-700 bg-red-50 p-2 rounded" aria-live="polite">
                  {userErrorMessage}
              </div>
          </CardContent>
      {/if}

      <!-- ETL result summary badge -->
      {#if lastETLResult}
          <CardContent>
              <Badge variant="secondary">
                  Loaded {lastETLResult.rows_loaded ?? 0} {lastETLResult.rows_loaded === 1 ? 'row' : 'rows'} from API
              </Badge>
          </CardContent>
      {/if}
  </Card>

  <!-- Server-side summary statistics card -->
  <SummaryCard stats={summaryStatistics} />

  <!-- Client-side calculated statistics card -->
  <Card>
      <CardHeader>
          <CardTitle>Additional Statistics</CardTitle>
      </CardHeader>
      <CardContent>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-y-2">
              <div>
                  <div class="text-sm text-gray-500">State</div>
                  <div class="font-medium">{selectedRegion}</div>
              </div>
              <div>
                  <div class="text-sm text-gray-500">Weeks</div>
                  <div class="font-medium">{clientStatistics.numberOfWeeks ?? 0}</div>
              </div>
              <div>
                  <div class="text-sm text-gray-500">Mean ILI</div>
                  <div class="font-medium">{clientStatistics.meanValue?.toFixed(3) ?? '—'}</div>
              </div>
              <div>
                  <div class="text-sm text-gray-500">Median ILI</div>
                  <div class="font-medium">{clientStatistics.medianValue?.toFixed(3) ?? '—'}</div>
              </div>
              <div>
                  <div class="text-sm text-gray-500">Std Dev</div>
                  <div class="font-medium">{clientStatistics.standardDeviation?.toFixed(3) ?? '—'}</div>
              </div>
              <div>
                  <div class="text-sm text-gray-500">Latest (date)</div>
                  <div class="font-medium">
                      {clientStatistics.latestObservationValue?.toFixed?.(3) ?? '—'}
                      {#if clientStatistics.latestObservationDate}
                          on {clientStatistics.latestObservationDate}
                      {/if}
                  </div>
              </div>
          </div>
      </CardContent>
  </Card>

  <!-- Main data exploration panel with tabs -->
  <Card>
      <CardHeader>
          <CardTitle>Explore Data</CardTitle>
      </CardHeader>

      <CardContent class="space-y-3">
          <Tabs value={activeTabView} on:change={(e: CustomEvent) => (activeTabView = (e as any).detail.value)}>
              <TabsList>
                  <TabsTrigger value="chart">Chart</TabsTrigger>
                  <TabsTrigger value="table">Table</TabsTrigger>
                  <TabsTrigger value="map">Map</TabsTrigger>
              </TabsList>

              <!-- Line chart visualization tab -->
              <TabsContent value="chart">
                  <div class="text-xs text-gray-500 mb-1">
                      Mode: <span class="font-medium">Weighted ILI (%) by epiweek</span>
                  </div>
                  <div class="h-64">
                      <canvas bind:this={chartCanvasElement} aria-label="ILI line chart"></canvas>
                  </div>
                  <div class="mt-2 text-xs text-gray-500">
                      {#if summaryStatistics?.start && summaryStatistics?.end}
                          Showing {observationRows.length} rows for {selectedRegion}, {summaryStatistics.start} → {summaryStatistics.end}.
                      {:else}
                          Choose a state and week range, then click "Load Data" to render the chart.
                      {/if}
                  </div>
              </TabsContent>

              <!-- Table view of raw observation data -->
              <TabsContent value="table">
                  <RowsTable rows={observationRows} />
              </TabsContent>
              
              <!-- US choropleth heat map visualization -->
              <TabsContent value="map">
                  <USChoropleth
                      values={stateILIAverages}
                      title="Influenza-Like Illness — State Heat Map"
                      legendLabel="Weighted ILI (%)"
                      weekLabel={mapDateRangeLabel}
                      fmt={(numericValue) => `${numericValue.toFixed(2)}%`}
                  />
                  <div class="mt-2 text-xs text-gray-500">
                      Colors show the average ILI (%) per state across the selected weeks.
                  </div>
              </TabsContent>
          </Tabs>
      </CardContent>
  </Card>
</main>