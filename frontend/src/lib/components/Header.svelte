<script lang="ts">
  import { page } from '$app/stores';
  $: pathname = $page.url.pathname;
  const isActive = (p: string) => pathname === p ? 'text-black font-medium' : 'text-gray-500';
</script>

<header class="w-full border-b bg-white sticky top-0 z-10">
  <div class="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="font-semibold text-lg">Disease ETL Dashboard</div>
      <nav class="flex items-center gap-6 text-sm">
          <a href="/" class="hover:text-black transition-colors {isActive('/')}">
              Dashboard
          </a>
          <a href="/about" class="hover:text-black transition-colors {isActive('/about')}">
              About
          </a>
      </nav>
  </div>
</header>