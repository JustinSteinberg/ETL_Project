<script lang="ts">
    import { page } from '$app/stores';
    $: pathname = $page.url.pathname;
    const isActive = (p: string) => pathname === p ? 'text-black' : 'text-gray-500';
  </script>
  
  <header class="w-full border-b bg-white sticky top-0 z-10">
    <div class="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="font-semibold">Disease ETL</div>
      <nav class="flex items-center gap-4 text-sm">
        <a href="/" class="hover:text-black {isActive('/')}">Dashboard</a>
      </nav>
    </div>
  </header>
  