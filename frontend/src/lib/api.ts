/**
 * Build a querystring from a params object, skipping empty/undefined values.
 * Example: q({ a: 1, b: undefined }) -> "a=1"
 */
function q(params: Record<string, string | number | undefined>) {
    const usp = new URLSearchParams()
    for (const [k,v] of Object.entries(params)) if (v !== undefined && v !== '') usp.set(k, String(v))
    return usp.toString()
  }

  /**
  * Trigger the backend ETL job.
  *
  * @param fetcher - Injected fetch (use the browser's fetch in components; SvelteKit passes one in load functions)
  * @param region  - Two-letter state code ('ma', 'ny', ...). Use 'all' to ETL all states.
  * @param start   - Optional start date (YYYY-MM-DD). Backend converts to epiweek.
  * @param end     - Optional end date (YYYY-MM-DD).
  * @throws Error  - If the server returns non-2xx, includes status and backend 'error' detail when present.
  * @returns       - JSON payload like { rows_loaded: number, ... }
  */
  export async function runETL(fetcher: typeof fetch, region='ma', start?: string, end?: string) {
    const q = new URLSearchParams()
    q.set('region', region)
    if (start) q.set('start_date', start)
    if (end) q.set('end_date', end)
  
    const r = await fetcher(`/etl/run?${q.toString()}`, { method: 'POST' })
    if (!r.ok) {
      let details = ''
      try { const j = await r.json(); details = j?.error || '' } catch {}
      throw new Error(`ETL failed: ${r.status}${details ? ` — ${details}` : ''}`)
    }
    return r.json() as Promise<{ rows_loaded: number }>
  }

  /**
   * Fetch summary statistics for the selected filters.
   *
   * @param fetcher - Injected fetch
   * @param params  - Optional filters { region, start, end }
   *                  Dates are YYYY-MM-DD (the server converts to epiweeks).
   * @returns       - { count, min, max, start, end, regions }
   */
  export async function getStats(fetcher: typeof fetch, params: { region?: string, start?: string, end?: string } = {}) {
    const r = await fetcher(`/stats?${q({ region: params.region, start_date: params.start, end_date: params.end })}`)
    if (!r.ok) throw new Error(`Stats failed: ${r.status}`)
    return r.json() as Promise<{ count:number; min:number|null; max:number|null; start:string|null; end:string|null; regions:string[] }>
  }
  
  /**
   * Fetch a page of row data for the table.
   *
   * @param fetcher - Injected fetch
   * @param params  - { limit, offset, region, start, end }
   * @returns       - { total, rows }
   */
  export async function getData(fetcher: typeof fetch, params: { limit?: number; offset?: number; region?: string; start?: string; end?: string } = {}) {
    const r = await fetcher(`/data?${q({ limit: params.limit, offset: params.offset, region: params.region, start_date: params.start, end_date: params.end })}`)
    if (!r.ok) throw new Error(`Data failed: ${r.status}`)
    return r.json() as Promise<{ total:number; rows:any[] }>
  }
  
  /**
   * Fetch a simplified series (labels + values) for charting.
   * (Only needed if you have a dedicated /series endpoint on the backend.
   *  Otherwise your chart can derive from getData().)
   *
   * @param fetcher - Injected fetch
   * @param params  - { region, start, end, limit }
   * @returns       - { labels, values, region? }
   */
  export async function getSeries(fetcher: typeof fetch, params: { region?: string; start?: string; end?: string; limit?: number } = {}) {
    const r = await fetcher(`/series?${q({ region: params.region, start_date: params.start, end_date: params.end, limit: params.limit })}`)
    if (!r.ok) throw new Error(`Series failed: ${r.status}`)
    return r.json() as Promise<{ labels: string[]; values: number[]; region?: string }>
  }
  