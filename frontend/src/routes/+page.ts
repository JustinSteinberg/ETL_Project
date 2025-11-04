import { getStats, getData } from '$lib/api';

export const load = async ({ fetch }) => {
  const [stats, data] = await Promise.all([
    getStats(fetch),
    getData(fetch, { limit: 50 })
  ]);
  return { stats, initialRows: data.rows };
};
