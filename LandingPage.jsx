<!DOCTYPE html>

<html class="dark" lang="en" style=""><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>DeltaDCF | Institutional Terminal</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600&amp;family=JetBrains+Mono:wght@400;500;700&amp;display=swap" rel="stylesheet"/>
<!-- Lucide Icons -->
<script src="https://unpkg.com/lucide@latest"></script>
<!-- Framer Motion -->
<script src="https://unpkg.com/framer-motion@10.16.4/dist/framer-motion.js"></script>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    "colors": {
                        "on-primary-fixed": "#001a42",
                        "on-surface": "#e2e2e2",
                        "primary": "#adc6ff",
                        "on-surface-variant": "#c2c6d6",
                        "primary-fixed-dim": "#adc6ff",
                        "on-primary-fixed-variant": "#004395",
                        "on-secondary-fixed-variant": "#005236",
                        "surface-container-high": "#282a2b",
                        "secondary-fixed-dim": "#4edea3",
                        "inverse-primary": "#005ac2",
                        "on-tertiary-fixed": "#410004",
                        "on-secondary-fixed": "#002113",
                        "surface": "#121414",
                        "surface-variant": "#333535",
                        "on-primary": "#002e6a",
                        "on-secondary-container": "#00311f",
                        "error": "#ffb4ab",
                        "surface-dim": "#121414",
                        "surface-tint": "#adc6ff",
                        "on-error": "#690005",
                        "primary-fixed": "#d8e2ff",
                        "background": "#121414",
                        "inverse-surface": "#e2e2e2",
                        "primary-container": "#4d8eff",
                        "surface-container-highest": "#333535",
                        "tertiary-container": "#ff5451",
                        "secondary": "#4edea3",
                        "secondary-fixed": "#6ffbbe",
                        "tertiary-fixed-dim": "#ffb3ad",
                        "on-error-container": "#ffdad6",
                        "outline-variant": "#424754",
                        "on-tertiary-container": "#5c0008",
                        "on-secondary": "#003824",
                        "on-background": "#e2e2e2",
                        "surface-container": "#1e2020",
                        "surface-container-low": "#1a1c1c",
                        "surface-bright": "#38393a",
                        "error-container": "#93000a",
                        "surface-container-lowest": "#0c0f0f",
                        "tertiary": "#ffb3ad",
                        "on-tertiary": "#68000a",
                        "on-tertiary-fixed-variant": "#930013",
                        "on-primary-container": "#00285d",
                        "secondary-container": "#00a572",
                        "outline": "#8c909f",
                        "inverse-on-surface": "#2f3131",
                        "tertiary-fixed": "#ffdad7"
                    },
                    "fontFamily": {
                        "body-md": ["Hanken Grotesk"],
                        "data-md": ["JetBrains Mono"],
                        "label-xs": ["Hanken Grotesk"],
                        "data-lg": ["JetBrains Mono"],
                        "data-sm": ["JetBrains Mono"],
                        "headline-sm": ["Hanken Grotesk"]
                    }
                },
            },
        }
    </script>
<style>
        body {
            background-color: var(--bg-color, #000000);
            color: var(--text-color, #e2e2e2);
            margin: 0;
            overflow-x: hidden;
            transition: background-color 0.3s, color 0.3s;
        }
        
        .dark {
            --bg-color: #000000;
            --text-color: #e2e2e2;
            --border-color: #1F1F1F;
            --surface-color: #000000;
            --surface-nested: #0A0A0A;
            --surface-hover: #111111;
            --text-muted: #8c909f;
            --fail-color: #ef4444; /* red-500 */
            --pass-color: #10b981; /* emerald-500 */
            --warning-color: #fbbf24; /* amber-400 */
        }

        .light {
            --bg-color: #FFFFFF;
            --text-color: #0A0A0A;
            --border-color: #E0E0E0;
            --surface-color: #F5F5F5;
            --surface-nested: #FFFFFF;
            --surface-hover: #EAEAEA;
            --text-muted: #999999;
            --fail-color: #dc2626; /* red-600 */
            --pass-color: #059669; /* emerald-600 */
            --warning-color: #d97706; /* amber-600 */
        }

        .border-terminal { border-color: var(--border-color); }
        .bg-terminal-widget { background-color: var(--surface-color); }
        .bg-terminal-nested { background-color: var(--surface-nested); }
        .hover-bg-terminal:hover { background-color: var(--surface-hover); }
        .text-terminal-muted { color: var(--text-muted); }
        
        .text-fail { color: var(--fail-color); }
        .text-pass { color: var(--pass-color); }
        .text-warning { color: var(--warning-color); }

        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: var(--bg-color); }
        ::-webkit-scrollbar-thumb { background: var(--border-color); }
        .ticker-input:focus { outline: none; border-color: #3B82F6; }
        
        .collapsible-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.15s ease-out;
        }
        .collapsible-trigger[aria-expanded="true"] + .collapsible-content {
            max-height: 200px;
        }
        
        /* App State Toggles */
        .page-landing { display: flex; }
        .page-analysis { display: none; }
        
        body[data-page="analysis"] .page-landing { display: none; }
        body[data-page="analysis"] .page-analysis { display: block; }
    </style>
</head>
<body class="font-body-md" data-page="landing">
<!-- LANDING PAGE -->
<div class="page-landing min-h-screen flex flex-col items-center justify-center p-5" id="landing-container"><button class="fixed top-8 right-8 text-[var(--text-muted)] hover:text-[var(--text-color)] transition-colors p-2 z-50" onclick="toggleTheme()">
<i class="w-6 h-6" data-lucide="moon"></i>
</button>
<div class="text-center w-full max-w-[520px]">
<h1 class="font-data-lg text-4xl tracking-widest uppercase mb-2 text-[var(--text-color)]">DELTADCF</h1>
<p class="font-data-sm text-[var(--text-muted)] mb-8">AI-powered DCF analysis and management audit.</p>
<div class="relative w-full flex items-center bg-[var(--surface-color)] border border-terminal">
<input class="ticker-input w-full bg-transparent border-none text-[var(--text-color)] font-data-md text-data-md h-12 px-4 placeholder:text-[var(--text-muted)]" id="landing-search" placeholder="Enter ticker... e.g. AAPL, ETERNAL.NS" type="text"/>
<button class="bg-[#3B82F6] text-[#FFFFFF] font-data-md text-data-md px-6 h-12 whitespace-nowrap hover:bg-blue-600 transition-colors" onclick="goToAnalysis()">
                ANALYZE →
            </button>
</div>
</div>
</div>
<!-- ANALYSIS PAGE -->
<div class="page-analysis min-h-screen">
<!-- TOP NAVIGATION SHELL -->
<header class="fixed top-0 left-0 right-0 h-14 flex items-center justify-between px-5 bg-[var(--bg-color)] border-b border-terminal z-50">
<div class="flex items-center gap-8 w-48 cursor-pointer" onclick="goToLanding()">
<span class="font-data-lg text-xl tracking-widest uppercase text-[var(--text-color)]">DELTADCF</span>
</div>
<div class="flex flex-1 max-w-2xl mx-10">
<div class="relative w-full flex items-center bg-[var(--surface-color)] border border-terminal">
<input class="ticker-input w-full bg-transparent border-none text-[var(--text-color)] font-data-md text-data-md h-9 px-3 placeholder:text-[var(--text-muted)]" placeholder="Enter ticker... e.g. AAPL, ETERNAL.NS" type="text" value="ETERNAL.NS"/>
<button class="bg-[#3B82F6] text-[#FFFFFF] font-data-md text-data-md px-4 h-9 whitespace-nowrap hover:bg-blue-600 transition-colors">
                    ANALYZE →
                </button>
</div>
</div>
<div class="flex items-center justify-end w-48">
<button class="text-[var(--text-muted)] hover:text-[var(--text-color)] transition-colors p-2" id="theme-toggle" onclick="toggleTheme()">
<svg aria-hidden="true" class="lucide lucide-moon w-5 h-5" data-lucide="moon" fill="none" height="24" id="moon-icon" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401"></path></svg>
<svg aria-hidden="true" class="lucide lucide-sun w-5 h-5 hidden" data-lucide="sun" fill="none" height="24" id="sun-icon" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path></svg>
</button>
</div>
</header>
<main class="pt-14 min-h-screen">
<!-- GLOBAL TICKER HEADER -->
<div class="p-5 border-b border-terminal flex items-end justify-between bg-[var(--bg-color)]">
<div>
<div class="flex items-center gap-3 mb-1">
<h1 class="font-data-lg text-2xl tracking-tight text-[var(--text-color)]">ETERNAL INC.</h1>
<span class="font-data-md text-data-md text-[var(--text-muted)]">NSE: ETERNAL.NS</span>
</div>
</div>
</div>
<!-- BENTO GRID LAYOUT -->
<div class="grid grid-cols-1 md:grid-cols-[1.5fr_1fr] border-b border-terminal bg-[var(--bg-color)]">
<!-- LEFT COLUMN: QUANT & BUSINESS -->
<div class="border-r border-terminal flex flex-col">
<!-- WIDGET: Quantitative Checklist -->
<section class="bg-terminal-widget border-b border-terminal p-5">
<header class="flex justify-between items-center border-b border-terminal pb-2 mb-4">
<span class="font-data-sm text-data-sm uppercase text-terminal-muted">INTRINSIC VALUE / SHARE</span>
</header>
<div class="flex flex-col">
<div class="flex items-center justify-between py-3 border-b border-terminal">
<span class="font-data-md text-[var(--text-muted)]">Gross Profit Margin &gt; 40%</span>
<div class="flex items-center gap-4">
<span class="font-data-md text-[var(--text-color)]">12.4%</span>
<div class="flex items-center gap-1.5 text-fail"><span class="font-data-sm uppercase tracking-wider">FAIL</span></div>
</div>
</div>
<div class="flex items-center justify-between py-3 border-b border-terminal">
<span class="font-data-md text-[var(--text-muted)]">Debt Level (D/E &lt; 0.5)</span>
<div class="flex items-center gap-4">
<span class="font-data-md text-[var(--text-color)]">1.8x</span>
<div class="flex items-center gap-1.5 text-fail"><span class="font-data-sm uppercase tracking-wider">FAIL</span></div>
</div>
</div>
<div class="flex items-center justify-between py-3 border-b border-terminal">
<span class="font-data-md text-[var(--text-muted)]">Positive Cash Flow from Ops</span>
<div class="flex items-center gap-4">
<span class="font-data-md text-[var(--text-color)]">-₹45M</span>
<div class="flex items-center gap-1.5 text-fail"><span class="font-data-sm uppercase tracking-wider">FAIL</span></div>
</div>
</div>
<div class="flex items-center justify-between py-3 border-b border-terminal">
<span class="font-data-md text-[var(--text-muted)]">Return on Equity &gt; 15%</span>
<div class="flex items-center gap-4">
<span class="font-data-md text-[var(--text-color)]">-8.2%</span>
<div class="flex items-center gap-1.5 text-fail"><span class="font-data-sm uppercase tracking-wider">FAIL</span></div>
</div>
</div>
</div>
</section>
<!-- WIDGET: Core Business Audit -->
<section class="bg-terminal-widget p-5 flex-1">
<header class="border-b border-terminal pb-2 mb-4">
<span class="font-data-sm text-data-sm uppercase text-terminal-muted">CORE BUSINESS AUDIT</span>
</header>
<div class="space-y-2">
<!-- Row 1 -->
<div class="border border-terminal bg-[var(--surface-color)]">
<button aria-expanded="false" class="collapsible-trigger w-full flex items-center justify-between p-3 hover-bg-terminal transition-colors focus:outline-none text-left">
<div class="flex items-center gap-3">
<span class="font-data-sm text-[var(--text-muted)] w-6">01</span>
<span class="font-data-md text-[var(--text-color)] font-medium">GPM Compression</span>
</div>
<div class="flex items-center gap-1.5 text-fail"><span class="font-data-sm uppercase tracking-wider">CRITICAL</span></div>
</button>
<div class="collapsible-content border-t border-terminal bg-terminal-nested">
<div class="p-3 text-[var(--text-muted)] font-body-md text-sm">
                                    Gross margins have compressed from 28% to 12.4% over the last 3 years, indicating severe loss of pricing power or escalating input costs not passed to consumers.
                                </div>
</div>
</div>
<!-- Row 2 -->
<div class="border border-terminal bg-[var(--surface-color)]">
<button aria-expanded="false" class="collapsible-trigger w-full flex items-center justify-between p-3 hover-bg-terminal transition-colors focus:outline-none text-left">
<div class="flex items-center gap-3">
<span class="font-data-sm text-[var(--text-muted)] w-6">02</span>
<span class="font-data-md text-[var(--text-color)] font-medium">Revenue vs Gross Profit Divergence</span>
</div>
<div class="flex items-center gap-1.5 text-warning"><span class="font-data-sm uppercase tracking-wider">WARNING</span></div>
</button>
<div class="collapsible-content border-t border-terminal bg-terminal-nested">
<div class="p-3 text-[var(--text-muted)] font-body-md text-sm">
                                    While top-line revenue shows artificial 15% growth, gross profit has declined by 8%, suggesting low-quality revenue acquisition and fundamentally broken unit economics.
                                </div>
</div>
</div>
<!-- Row 3 -->
<div class="border border-terminal bg-[var(--surface-color)]">
<button aria-expanded="false" class="collapsible-trigger w-full flex items-center justify-between p-3 hover-bg-terminal transition-colors focus:outline-none text-left">
<div class="flex items-center gap-3">
<span class="font-data-sm text-[var(--text-muted)] w-6">03</span>
<span class="font-data-md text-[var(--text-color)] font-medium">Severe EPS Dilution</span>
</div>
<div class="flex items-center gap-1.5 text-fail"><span class="font-data-sm uppercase tracking-wider">CRITICAL</span></div>
</button>
<div class="collapsible-content border-t border-terminal bg-terminal-nested">
<div class="p-3 text-[var(--text-muted)] font-body-md text-sm">
                                    Outstanding shares have increased by 45% over 5 years. Any perceived net income growth is completely negated on a per-share basis, destroying shareholder value.
                                </div>
</div>
</div>
<!-- Row 4 -->
<div class="border border-terminal bg-[var(--surface-color)]">
<button aria-expanded="false" class="collapsible-trigger w-full flex items-center justify-between p-3 hover-bg-terminal transition-colors focus:outline-none text-left">
<div class="flex items-center gap-3">
<span class="font-data-sm text-[var(--text-muted)] w-6">04</span>
<span class="font-data-md text-[var(--text-color)] font-medium">Unsustainable Debt Burden</span>
</div>
<div class="flex items-center gap-1.5 text-fail"><span class="font-data-sm uppercase tracking-wider">CRITICAL</span></div>
</button>
<div class="collapsible-content border-t border-terminal bg-terminal-nested">
<div class="p-3 text-[var(--text-muted)] font-body-md text-sm">
                                    Interest coverage ratio is below 1.0x. Operating income is insufficient to service current debt obligations, drastically increasing restructuring or default risk.
                                </div>
</div>
</div>
</div>
</section>
</div>
<!-- RIGHT COLUMN: INTRINSIC & MANAGEMENT -->
<div class="flex flex-col">
<!-- WIDGET: Intrinsic Value + DCF Parameters -->
<section class="bg-terminal-widget border-b border-terminal p-5">
<header class="border-b border-terminal pb-2 mb-4">
<span class="font-data-sm text-data-sm uppercase text-terminal-muted">INTRINSIC VALUE / SHARE</span>
</header>
<div class="flex flex-col items-center justify-center py-8 border border-terminal bg-[var(--surface-color)] mb-6">
<span class="font-data-lg text-5xl text-fail mb-2">-61.65</span>
<span class="font-data-sm text-data-sm text-terminal-muted uppercase tracking-widest">NEGATIVE EQUITY VALUE</span>
</div>
<div class="w-full">
<table class="w-full text-left font-data-md">
<thead>
<tr class="border-b border-terminal">
<th class="py-2 text-terminal-muted font-normal uppercase text-xs">Parameter</th>
<th class="py-2 text-terminal-muted font-normal uppercase text-xs text-right">Base</th>
<th class="py-2 text-terminal-muted font-normal uppercase text-xs text-right">Adj</th>
<th class="py-2 text-terminal-muted font-normal uppercase text-xs text-right">Final</th>
</tr>
</thead>
<tbody>
<tr class="border-b border-terminal">
<td class="py-2 text-[var(--text-muted)]">Stage 1 Gr</td>
<td class="py-2 text-right text-[var(--text-muted)]">5.0%</td>
<td class="py-2 text-right text-fail">-8.0%</td>
<td class="py-2 text-right text-[var(--text-color)] font-bold">-3.0%</td>
</tr>
<tr class="border-b border-terminal">
<td class="py-2 text-[var(--text-muted)]">Stage 2 Gr</td>
<td class="py-2 text-right text-[var(--text-muted)]">3.0%</td>
<td class="py-2 text-right text-fail">-5.0%</td>
<td class="py-2 text-right text-[var(--text-color)] font-bold">-2.0%</td>
</tr>
<tr class="border-b border-terminal">
<td class="py-2 text-[var(--text-muted)]">Discount Rate</td>
<td class="py-2 text-right text-[var(--text-muted)]">10.0%</td>
<td class="py-2 text-right text-pass">+5.0%</td>
<td class="py-2 text-right text-[var(--text-color)] font-bold">15.0%</td>
</tr>
</tbody>
</table>
</div>
</section>
<!-- WIDGET: Management Integrity Alerts -->
<section class="bg-terminal-widget p-5 flex-1">
<header class="border-b border-terminal pb-2 mb-4 flex items-center gap-2">
<span class="font-data-sm text-data-sm uppercase text-terminal-muted">INTEGRITY ALERTS</span>
</header>
<div class="space-y-4">
<div class="border border-terminal bg-terminal-nested flex flex-col gap-2 p-3">
<div class="flex items-center mb-1"><span class="font-data-sm font-bold uppercase text-fail">RED FLAG</span></div>
<p class="font-body-md text-[var(--text-muted)] text-sm mt-1">
                                Management focuses on "EBITDA adjustments" in investor presentations, masking the underlying cash burn and deteriorating gross margins.
                            </p>
</div>
<div class="border border-terminal bg-terminal-nested flex flex-col gap-2 p-3">
<div class="flex items-center mb-1"><span class="font-data-sm font-bold uppercase text-warning">CAUTION</span></div>
<p class="font-body-md text-[var(--text-muted)] text-sm mt-1">
                                Frequent Qualified Institutional Placements (QIPs) are used to plug operational cash deficits, continually diluting retail shareholders without generating ROI.
                            </p>
</div>
</div>
</section>
</div>
</div>
</main>
</div>
<script>
    lucide.createIcons();

    // Theme Toggle Logic
    const htmlEl = document.documentElement;
    
    // Check local storage for persistent theme state
    const savedTheme = localStorage.getItem('deltadcf-theme');
    if (savedTheme === 'light') {
        htmlEl.classList.remove('dark');
        htmlEl.classList.add('light');
    } else if (savedTheme === 'dark') {
        htmlEl.classList.remove('light');
        htmlEl.classList.add('dark');
    }
    
    function updateThemeIcons() {
        const isDark = htmlEl.classList.contains('dark');
        const moonIcon = document.getElementById('moon-icon');
        const sunIcon = document.getElementById('sun-icon');
        
        // Update analysis page icons
        if (moonIcon && sunIcon) {
            if (isDark) {
                moonIcon.classList.remove('hidden');
                sunIcon.classList.add('hidden');
            } else {
                moonIcon.classList.add('hidden');
                sunIcon.classList.remove('hidden');
            }
        }
        
        // Update landing page icon
        const landingBtn = document.querySelector('.page-landing button[onclick="toggleTheme()"]');
        if (landingBtn) {
            landingBtn.innerHTML = isDark 
                ? '<i class="w-6 h-6" data-lucide="moon"></i>'
                : '<i class="w-6 h-6" data-lucide="sun"></i>';
            lucide.createIcons();
        }
    }

    function toggleTheme() {
        if (htmlEl.classList.contains('dark')) {
            htmlEl.classList.remove('dark');
            htmlEl.classList.add('light');
            localStorage.setItem('deltadcf-theme', 'light');
        } else {
            htmlEl.classList.remove('light');
            htmlEl.classList.add('dark');
            localStorage.setItem('deltadcf-theme', 'dark');
        }
        updateThemeIcons();
    }
    
    // Page Transitions
    const landingContainer = document.getElementById('landing-container');
    
    function goToAnalysis() {
        const { animate } = window.Motion;
        
        // Simple fade out on landing
        animate(landingContainer, { opacity: 0, scale: 0.98 }, { duration: 0.3 })
            .then(() => {
                document.body.setAttribute('data-page', 'analysis');
                landingContainer.style.opacity = '1'; // reset for back nav
                landingContainer.style.transform = 'scale(1)';
            });
    }

    function goToLanding() {
        document.body.setAttribute('data-page', 'landing');
    }

    // Ticker focus simulation
    document.querySelectorAll('.ticker-input').forEach(input => {
        input.addEventListener('keydown', (e) => {
            if(e.key === 'Enter') {
                const button = input.nextElementSibling;
                button.classList.add('bg-white', 'text-black');
                setTimeout(() => {
                    button.classList.remove('bg-white', 'text-black');
                    if (document.body.getAttribute('data-page') === 'landing') {
                        goToAnalysis();
                    } else {
                        alert('Executing query for: ' + input.value.toUpperCase());
                    }
                }, 150);
            }
        });
    });

    // Collapsible interactions
    document.querySelectorAll('.collapsible-trigger').forEach(btn => {
        btn.addEventListener('click', () => {
            const expanded = btn.getAttribute('aria-expanded') === 'true';
            btn.setAttribute('aria-expanded', !expanded);
        });
    });
    
    updateThemeIcons();
</script>
</body></html>