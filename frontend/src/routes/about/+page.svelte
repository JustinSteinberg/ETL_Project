<script lang="ts">
    import Header from '$lib/components/Header.svelte'
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card'
    import { Badge } from '$lib/components/ui/badge'
    import { Separator } from '$lib/components/ui/separator'
</script>

<svelte:head>
    <title>About - Disease ETL Dashboard</title>
    <meta name="description" content="Learn about Influenza-Like Illness data, epiweeks, and how to use the Disease ETL Dashboard" />
</svelte:head>

<Header />

<main class="max-w-5xl mx-auto p-4 space-y-6">
    
    <!-- Hero Section -->
    <div class="pt-8 pb-6">
        <h1 class="text-3xl font-bold tracking-tight">About This Dashboard</h1>
        <p class="text-muted-foreground mt-2">
            Understanding Influenza-Like Illness surveillance and how to use this tool
        </p>
    </div>

    <!-- What is ILI? -->
    <Card>
        <CardHeader>
            <div class="flex items-center gap-2">
                <div class="h-2 w-2 rounded-full bg-blue-500"></div>
                <CardTitle>What is ILI (Influenza-Like Illness)?</CardTitle>
            </div>
        </CardHeader>
        <CardContent class="space-y-4">
            <p class="text-sm text-muted-foreground leading-relaxed">
                Influenza-Like Illness (ILI) is a syndromic surveillance measure used by the CDC to track 
                the spread of flu-like symptoms across the United States.
            </p>
            
            <div class="rounded-lg border bg-card p-4">
                <p class="text-sm font-medium mb-1">Clinical Definition</p>
                <p class="text-sm text-muted-foreground">
                    Fever (≥100°F or 37.8°C) <span class="font-medium">AND</span> cough or sore throat, 
                    without a known cause other than influenza
                </p>
            </div>

            <div class="space-y-2">
                <p class="text-sm font-medium">Weighted ILI Percentage (%ILI)</p>
                <p class="text-sm text-muted-foreground leading-relaxed">
                    The weighted ILI percentage represents the number of ILI patient visits divided by 
                    the total number of patient visits, adjusted for differences in state population 
                    and healthcare reporting practices.
                </p>
            </div>

            <Separator />

            <div class="space-y-2">
                <p class="text-sm font-medium">Why Track ILI?</p>
                <ul class="text-sm text-muted-foreground space-y-1.5 ml-4">
                    <li class="flex items-start gap-2">
                        <span class="text-primary mt-0.5">•</span>
                        <span>Early detection of flu outbreaks</span>
                    </li>
                    <li class="flex items-start gap-2">
                        <span class="text-primary mt-0.5">•</span>
                        <span>Monitor seasonal patterns and trends</span>
                    </li>
                    <li class="flex items-start gap-2">
                        <span class="text-primary mt-0.5">•</span>
                        <span>Allocate healthcare resources effectively</span>
                    </li>
                    <li class="flex items-start gap-2">
                        <span class="text-primary mt-0.5">•</span>
                        <span>Track effectiveness of interventions (vaccines, campaigns)</span>
                    </li>
                </ul>
            </div>
        </CardContent>
    </Card>

    <!-- What are Epiweeks? -->
    <Card>
        <CardHeader>
            <div class="flex items-center gap-2">
                <div class="h-2 w-2 rounded-full bg-green-500"></div>
                <CardTitle>What are Epiweeks?</CardTitle>
            </div>
        </CardHeader>
        <CardContent class="space-y-4">
            <p class="text-sm text-muted-foreground leading-relaxed">
                Epiweeks (epidemiological weeks) are a standardized way to count weeks in a year 
                for disease surveillance. They follow the ISO 8601 week date system.
            </p>

            <div class="grid md:grid-cols-2 gap-4">
                <div class="rounded-lg border bg-card p-4">
                    <p class="text-sm font-medium mb-3">Key Rules</p>
                    <ul class="text-sm text-muted-foreground space-y-2">
                        <li class="flex items-start gap-2">
                            <Badge variant="outline" class="text-xs">📅</Badge>
                            <span>Weeks start on Monday</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <Badge variant="outline" class="text-xs">📌</Badge>
                            <span>Week 1 contains January 4th</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <Badge variant="outline" class="text-xs">🔢</Badge>
                            <span>Each year has 52 or 53 weeks</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <Badge variant="outline" class="text-xs">💾</Badge>
                            <span>Format: YYYYWW (e.g., 202401)</span>
                        </li>
                    </ul>
                </div>

                <div class="rounded-lg border bg-muted p-4">
                    <p class="text-sm font-medium mb-3">Examples</p>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="font-mono">2024-W01</span>
                            <span class="text-muted-foreground">Dec 31 - Jan 6</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="font-mono">2024-W26</span>
                            <span class="text-muted-foreground">Jun 24 - Jun 30</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="font-mono">2024-W52</span>
                            <span class="text-muted-foreground">Dec 23 - Dec 29</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="rounded-lg border bg-card p-4">
                <p class="text-sm text-muted-foreground">
                    Using epiweeks instead of calendar months provides more consistent time periods 
                    for analyzing disease patterns, since each epiweek is exactly 7 days.
                </p>
            </div>
        </CardContent>
    </Card>

    <!-- Data Source -->
    <Card>
        <CardHeader>
            <div class="flex items-center gap-2">
                <div class="h-2 w-2 rounded-full bg-purple-500"></div>
                <CardTitle>Data Source</CardTitle>
            </div>
        </CardHeader>
        <CardContent class="space-y-4">
            <div class="flex items-center gap-3 p-4 rounded-lg border bg-card">
                <div class="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <span class="text-xl">🏥</span>
                </div>
                <div>
                    <p class="font-medium text-sm">Carnegie Mellon Delphi Research Group</p>
                    <p class="text-xs text-muted-foreground">Epidata API - FluView Dataset</p>
                </div>
            </div>

            <p class="text-sm text-muted-foreground leading-relaxed">
                This dashboard uses data from the Delphi Epidata API, which aggregates influenza 
                surveillance data from the CDC's FluView system.
            </p>

            <div class="space-y-3">
                <div class="flex gap-3">
                    <Badge variant="secondary" class="text-xs">ILINet</Badge>
                    <div class="flex-1">
                        <p class="text-sm font-medium">U.S. Outpatient ILI Surveillance Network</p>
                        <p class="text-xs text-muted-foreground">
                            ~3,000 healthcare providers across all 50 states reporting weekly
                        </p>
                    </div>
                </div>
                
                <div class="flex gap-3">
                    <Badge variant="secondary" class="text-xs">📊</Badge>
                    <div class="flex-1">
                        <p class="text-sm font-medium">Weekly Reporting Cycle</p>
                        <p class="text-xs text-muted-foreground">
                            Published Friday afternoons for the previous epiweek
                        </p>
                    </div>
                </div>
                
                <div class="flex gap-3">
                    <Badge variant="secondary" class="text-xs">📚</Badge>
                    <div class="flex-1">
                        <p class="text-sm font-medium">Historical Data</p>
                        <p class="text-xs text-muted-foreground">
                            Records dating back to 2010 available through the API
                        </p>
                    </div>
                </div>
            </div>

            <div class="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 p-3">
                <p class="text-xs text-amber-900 dark:text-amber-100">
                    <span class="font-medium">Note:</span> Data may be revised retroactively as late reports 
                    are received. The most recent 1-2 weeks are considered provisional.
                </p>
            </div>

            <div class="flex flex-wrap gap-3 pt-2">
                <a 
                    href="https://cmu-delphi.github.io/delphi-epidata/api/fluview.html" 
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-xs text-primary hover:underline inline-flex items-center gap-1"
                >
                    <span>Delphi API Docs</span>
                    <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                </a>
                <a 
                    href="https://www.cdc.gov/flu/weekly/overview.htm" 
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-xs text-primary hover:underline inline-flex items-center gap-1"
                >
                    <span>CDC FluView Portal</span>
                    <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                </a>
            </div>
        </CardContent>
    </Card>

    <!-- How to Use -->
    <Card>
        <CardHeader>
            <div class="flex items-center gap-2">
                <div class="h-2 w-2 rounded-full bg-orange-500"></div>
                <CardTitle>How to Use This Dashboard</CardTitle>
            </div>
        </CardHeader>
        <CardContent class="space-y-4">
            <p class="text-sm text-muted-foreground leading-relaxed">
                This dashboard follows an ETL (Extract-Transform-Load) workflow with smart caching 
                to provide fast access to ILI data.
            </p>

            <div class="space-y-4">
                {#each [
                    { num: 1, title: 'Select Your Filters', desc: 'Choose a state and date range using the ISO week picker. Example: MA from 2024-W01 to 2024-W52.' },
                    { num: 2, title: 'Click "Load Data"', desc: 'The system checks the local database first. If data exists, it loads instantly. If missing, it fetches from the CDC API (2-5 seconds).' },
                    { num: 3, title: 'Explore the Data', desc: 'View as a line chart, data table, or US choropleth map showing state-level averages.' },
                    { num: 4, title: 'Download or Refresh', desc: 'Export filtered data as CSV or force refresh the latest data from CDC API.' }
                ] as step}
                    <div class="flex gap-3">
                        <div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-medium">
                            {step.num}
                        </div>
                        <div class="flex-1 space-y-1">
                            <p class="text-sm font-medium leading-none">{step.title}</p>
                            <p class="text-xs text-muted-foreground leading-relaxed">{step.desc}</p>
                        </div>
                    </div>
                {/each}
            </div>

            <Separator />

            <div class="rounded-lg border bg-muted p-4">
                <p class="text-sm font-medium mb-2">💡 Pro Tips</p>
                <ul class="text-xs text-muted-foreground space-y-1.5">
                    <li class="flex items-start gap-2">
                        <span class="text-primary mt-0.5">•</span>
                        <span>Your filters are saved in the URL - bookmark specific views!</span>
                    </li>
                    <li class="flex items-start gap-2">
                        <span class="text-primary mt-0.5">•</span>
                        <span>Data is cached locally for fast repeated access</span>
                    </li>
                    <li class="flex items-start gap-2">
                        <span class="text-primary mt-0.5">•</span>
                        <span>The map view requires data for multiple states</span>
                    </li>
                    <li class="flex items-start gap-2">
                        <span class="text-primary mt-0.5">•</span>
                        <span>Statistics update automatically as you change filters</span>
                    </li>
                </ul>
            </div>
        </CardContent>
    </Card>

    <!-- Understanding the Metrics -->
    <Card>
        <CardHeader>
            <div class="flex items-center gap-2">
                <div class="h-2 w-2 rounded-full bg-pink-500"></div>
                <CardTitle>Understanding the Metrics</CardTitle>
            </div>
        </CardHeader>
        <CardContent class="space-y-4">
            <div class="grid md:grid-cols-2 gap-4">
                <div class="space-y-3">
                    <p class="text-sm font-medium">Summary Statistics</p>
                    <div class="space-y-2 text-xs">
                        <div class="flex justify-between py-1 border-b">
                            <span class="text-muted-foreground">Count</span>
                            <span>Total epiweeks with data</span>
                        </div>
                        <div class="flex justify-between py-1 border-b">
                            <span class="text-muted-foreground">Min / Max</span>
                            <span>Lowest and highest ILI %</span>
                        </div>
                        <div class="flex justify-between py-1 border-b">
                            <span class="text-muted-foreground">Start / End</span>
                            <span>Date range of data</span>
                        </div>
                    </div>
                </div>

                <div class="space-y-3">
                    <p class="text-sm font-medium">Additional Statistics</p>
                    <div class="space-y-2 text-xs">
                        <div class="flex justify-between py-1 border-b">
                            <span class="text-muted-foreground">Mean ILI</span>
                            <span>Average across all weeks</span>
                        </div>
                        <div class="flex justify-between py-1 border-b">
                            <span class="text-muted-foreground">Median ILI</span>
                            <span>Middle value (robust to outliers)</span>
                        </div>
                        <div class="flex justify-between py-1 border-b">
                            <span class="text-muted-foreground">Std Dev</span>
                            <span>Measure of variability</span>
                        </div>
                    </div>
                </div>
            </div>

            <Separator />

            <div class="space-y-2">
                <p class="text-sm font-medium">Interpreting ILI Percentages</p>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <div class="flex items-center gap-2 text-xs">
                        <Badge variant="outline" class="bg-green-50 text-green-700 border-green-200">0-2%</Badge>
                        <span class="text-muted-foreground">Low activity</span>
                    </div>
                    <div class="flex items-center gap-2 text-xs">
                        <Badge variant="outline" class="bg-yellow-50 text-yellow-700 border-yellow-200">2-5%</Badge>
                        <span class="text-muted-foreground">Moderate activity</span>
                    </div>
                    <div class="flex items-center gap-2 text-xs">
                        <Badge variant="outline" class="bg-orange-50 text-orange-700 border-orange-200">5-10%</Badge>
                        <span class="text-muted-foreground">High activity</span>
                    </div>
                    <div class="flex items-center gap-2 text-xs">
                        <Badge variant="outline" class="bg-red-50 text-red-700 border-red-200">10%+</Badge>
                        <span class="text-muted-foreground">Very high activity</span>
                    </div>
                </div>
            </div>
        </CardContent>
    </Card>

    <!-- Technical Stack -->
    <Card>
        <CardHeader>
            <div class="flex items-center gap-2">
                <div class="h-2 w-2 rounded-full bg-cyan-500"></div>
                <CardTitle>Technical Details</CardTitle>
            </div>
        </CardHeader>
        <CardContent class="space-y-4">
            <p class="text-sm text-muted-foreground leading-relaxed">
                Built as a full-stack ETL (Extract-Transform-Load) pipeline:
            </p>

            <div class="grid md:grid-cols-3 gap-3">
                <div class="rounded-lg border bg-card p-3">
                    <Badge variant="secondary" class="mb-2 text-xs">Extract</Badge>
                    <p class="text-xs text-muted-foreground">
                        Fetch raw ILI data from Delphi API
                    </p>
                </div>
                <div class="rounded-lg border bg-card p-3">
                    <Badge variant="secondary" class="mb-2 text-xs">Transform</Badge>
                    <p class="text-xs text-muted-foreground">
                        Clean, normalize, calculate fields
                    </p>
                </div>
                <div class="rounded-lg border bg-card p-3">
                    <Badge variant="secondary" class="mb-2 text-xs">Load</Badge>
                    <p class="text-xs text-muted-foreground">
                        Store in SQLite for fast queries
                    </p>
                </div>
            </div>

            <div class="rounded-lg border bg-muted p-4">
                <p class="text-sm font-medium mb-3">Technology Stack</p>
                <div class="grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-muted-foreground">
                    <div>
                        <span class="font-medium">Frontend</span>
                        <p>SvelteKit, TypeScript, Tailwind</p>
                    </div>
                    <div>
                        <span class="font-medium">Backend</span>
                        <p>FastAPI (Python), SQLite</p>
                    </div>
                    <div>
                        <span class="font-medium">Charts</span>
                        <p>Chart.js, D3 Geo</p>
                    </div>
                    <div>
                        <span class="font-medium">UI Components</span>
                        <p>shadcn/ui</p>
                    </div>
                </div>
            </div>
        </CardContent>
    </Card>

    <!-- Footer -->
    <div class="text-center py-8 text-xs text-muted-foreground space-y-2">
        <p>
            Data provided by the 
            <a href="https://delphi.cmu.edu/" target="_blank" rel="noopener noreferrer" class="text-primary hover:underline">
                CMU Delphi Research Group
            </a>
            and 
            <a href="https://www.cdc.gov/" target="_blank" rel="noopener noreferrer" class="text-primary hover:underline">
                CDC
            </a>
        </p>
        <p>This dashboard is for educational and research purposes.</p>
    </div>

</main>