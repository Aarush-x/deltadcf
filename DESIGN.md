---
name: Delta Terminal
colors:
  surface: '#121414'
  surface-dim: '#121414'
  surface-bright: '#38393a'
  surface-container-lowest: '#0d0e0f'
  surface-container-low: '#1a1c1c'
  surface-container: '#1e2020'
  surface-container-high: '#282a2b'
  surface-container-highest: '#333535'
  on-surface: '#e2e2e2'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#e2e2e2'
  inverse-on-surface: '#2f3131'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb3ad'
  on-tertiary: '#68000a'
  tertiary-container: '#ff5451'
  on-tertiary-container: '#5c0008'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdad7'
  tertiary-fixed-dim: '#ffb3ad'
  on-tertiary-fixed: '#410004'
  on-tertiary-fixed-variant: '#930013'
  background: '#000000'
  on-background: '#e2e2e2'
  surface-variant: '#333535'
  border-terminal: '#1F1F1F'
  widget-bg: '#000000'
  nested-bg: '#0A0A0A'
  text-dim: '#8c909f'
  critical: '#ef4444'
  warning: '#fbbf24'
  success: '#34d399'
typography:
  headline-sm:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  data-lg:
    fontFamily: JetBrains Mono
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 16px
  data-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.02em
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-xs:
    fontFamily: Hanken Grotesk
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
spacing:
  container-padding: 1.25rem
  module-gap: 1rem
  cell-padding-x: 0.75rem
  cell-padding-y: 0.5rem
  stack-tight: 0.25rem
---

## Brand & Style

Delta Terminal is a high-density, data-centric design system tailored for institutional finance and quantitative analysis. The aesthetic is "Bloomberg-modern"—it prioritizes information density and high-speed legibility over decorative whitespace.

The style is a hybrid of **Brutalism** and **Modern Corporate**. It uses sharp, 0px borders and a rigid grid to evoke a sense of precision and "terminal-like" efficiency. The dark, high-contrast environment reduces eye strain for power users while highlighting critical risk indicators through aggressive use of semantic color. The emotional response is one of clinical authority, professional rigor, and technical depth.

## Colors

The palette is anchored by a "True Black" (`#000000`) background to maximize contrast for data points. 

- **Primary & Actions:** A vibrant blue (`#3B82F6`) is used sparingly for primary actions and focused inputs.
- **Semantic Logic:** Color is strictly functional. Red (`#EF4444`) denotes "Fail" or "Critical" states; Amber (`#FBBF24`) denotes "Warning"; Green/Emerald denotes "Pass" or "Growth."
- **Surfaces:** Depth is created through subtle shifts in dark grays. The main background is absolute black, while widgets and containers use a slightly elevated charcoal (`#121414`) or dark slate.
- **Typography:** Primary text is a high-contrast off-white (`#E2E2E2`), while labels and metadata use a muted silver-gray (`#8C909F`).

## Typography

Typography is split between two distinct roles:
1.  **Hanken Grotesk:** Used for UI chrome, headings, and descriptive prose. It provides a clean, modern readable base.
2.  **JetBrains Mono:** Used for all quantitative data, tickers, and financial parameters. The monospaced nature ensures that numbers align perfectly in tables and lists, facilitating rapid scanning of values.

All labels should be uppercase with slight letter spacing to differentiate them from interactive data points.

## Layout & Spacing

The layout follows a **Fluid Bento Grid** model. The screen is divided into functional modules separated by 1px borders (`#1F1F1F`) rather than margins. This maximizes every pixel for data display.

- **Grid:** A multi-column structure that reflows from 2-column (desktop) to 1-column (mobile). 
- **Rhythm:** Spacing is tight and systematic. A base unit of 4px is used, with standard cell padding at 12px (0.75rem) and container padding at 20px (1.25rem).
- **Alignment:** Data labels are typically left-aligned, while numerical values in tables are right-aligned to allow for easy comparison of magnitudes.

## Elevation & Depth

Delta Terminal avoids shadows entirely to maintain a flat, technical aesthetic. Depth is achieved via **Tonal Layering**:

- **Floor (Level 0):** Absolute black (`#000000`).
- **Containers (Level 1):** Dark gray (`#121414`) with 1px solid borders.
- **Active/Hover States (Level 2):** Subtle brightening of the background (`#111111`) or nested surfaces (`#0A0A0A`).

The hierarchy is communicated through structural lines rather than lighting effects, creating a "blueprint" feel.

## Shapes

The shape language is strictly **Sharp (0px)**. All buttons, input fields, and container corners have zero border-radius. This reinforces the "Terminal" metaphor and the institutional, non-consumer nature of the product. The only exception is the `full` radius used for icons or specific toggle status indicators if necessary.

## Components

- **Buttons:** Sharp corners. Primary buttons use a solid blue background with white text. Secondary buttons are ghost-style with 1px borders.
- **Inputs:** Dark backgrounds (`#111111`) with 1px borders that change color on focus. Use JetBrains Mono for input text.
- **Tables/Lists:** Use "Terminal Rows"—1px bottom borders, no zebra striping. Hover states should trigger a subtle background tint.
- **Collapsibles:** Indicate expansion with simple chevron icons. Expanded content should have a slightly darker background (`#0A0A0A`) to provide a nested visual cue.
- **Status Badges:** Small, uppercase text using JetBrains Mono. Color should be applied only to the text or a very subtle background tint, never a heavy fill, to avoid visual clutter.