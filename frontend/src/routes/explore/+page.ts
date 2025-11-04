import { getData } from '$lib/api';

export const load = async ({ fetch, url }) => {
  const region = url.searchParams.get('region') ?? 'MA';
  const limit = Number(url.searchParams.get('limit') ?? 50);
  const offset = Number(url.searchParams.get('offset') ?? 0);
  const data = await getData(fetch, { limit, offset, region });
  return { region, limit, offset, total: data.total, rows: data.rows };
};
