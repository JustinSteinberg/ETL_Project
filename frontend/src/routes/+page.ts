import { getStats, getData } from '$lib/api';

export const load = async ({ fetch, url }) => {
  // Check if URL has filter parameters
  const region = url.searchParams.get('state');
  const startWeek = url.searchParams.get('startWeek');
  const endWeek = url.searchParams.get('endWeek');
  
  // Only fetch data if filters are present in URL
  if (region && startWeek && endWeek) {
    // Convert weeks to dates (you'll need this helper function)
    const startDate = weekToMonday(startWeek);
    const endDate = weekToMonday(endWeek);
    
    const [stats, data] = await Promise.all([
      getStats(fetch, { region, start_date: startDate, end_date: endDate }),
      getData(fetch, { limit: 50, region, start_date: startDate, end_date: endDate })
    ]);
    
    return { stats, initialRows: data.rows };
  }
  
  // No filters in URL - return empty data
  return { 
    stats: {
      count: 0,
      min: null,
      max: null,
      start: null,
      end: null,
      regions: []
    },
    initialRows: []
  };
};

function weekToMonday(weekStr: string): string {
  if (!weekStr) return '';
  const [yPart, wPart] = weekStr.split('-W');
  const year = Number(yPart);
  const week = Number(wPart);
  if (!year || !week) return '';
  const d = new Date(Date.UTC(year, 0, 4));
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() - (day - 1) + (week - 1) * 7);
  return d.toISOString().slice(0, 10);
}