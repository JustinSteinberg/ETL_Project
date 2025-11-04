<script>
    import Header from '$lib/components/Header.svelte'
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card'
    import { Separator } from '$lib/components/ui/separator'
  </script>
  
  <Header />
  
  <main class="max-w-5xl mx-auto p-4">
    <Card>
      <CardHeader><CardTitle>Download</CardTitle></CardHeader>
      <CardContent class="space-y-3">
        <a href="/download.csv" class="text-blue-600 underline">Download cleaned.csv</a>
        <Separator />
        <div class="text-sm text-gray-600">
          <div class="font-semibold">Schema (columns):</div>
          <ul class="list-disc pl-5">
            <li><code>date</code> (DATE)</li>
            <li><code>region</code> (TEXT)</li>
            <li><code>value</code> (REAL)</li>
            <li><code>metric</code> (TEXT)</li>
            <li><code>source_id</code> (TEXT, PK)</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  </main>
  