# Base Power Install Requirement Checker

A pre-screening tool for whether a Texas home can host a Base Power home
battery unit (25 kWh single, 50 kWh double, or the 39.2 kWh beta unit),
built from two complementary data paths:

1. **Address-only screen** — pulls free public data (county appraisal
   records, parcel/lot geometry, building footprints, FEMA flood zone,
   USGS slope, PUCT utility-service territory, city permit records where
   available, Google Street View as a capped/paid fallback) and scores
   each address against Base's install requirements before anyone visits
   the site or requests drawings.
2. **Architectural-drawing reading** — when a plot plan, electrical
   riser, and elevation are available (from a builder, architect, or the
   homeowner), the checker reads them and answers the same requirements
   directly, then draws a to-scale install-envelope diagram from what
   the drawings actually show.

Both paths write into the same 6 core requirements (panel size, meter
location, wall space at the meter, side clearance, gas-meter separation,
and NEC working-space/closet/meter-condition checks), each shown as
YES / NO / MAYBE with its source and supporting note.

## Contents

- **`checker.html`** — the interactive checker itself (a single-file
  HTML/JS artifact). Drop it into an environment that supports the
  Claude Artifact runtime (`sample` + `db` capabilities) to run it, or
  open it standalone to see the UI (drawing reading needs `sample`; the
  shared address database needs `db`).
- **`tx-screen.mjs`** — Node script that runs the address-only screen for
  one Texas address end-to-end (geocode → parcel → utility → flood →
  slope → footprint → county appraisal record → optional Street View →
  city permits where a public API exists) and writes a scored record to
  `records/<address-key>.json`.
  ```
  node tx-screen.mjs "<address>" [--facts facts/<address-key>.json]
  ```
  `--facts` merges in manually-researched facts (e.g. from an agent
  research pass) that aren't yet wired into an automated source for that
  county.
- **`streetview.mjs`** — Street View capture with a hard monthly image
  budget (see below), called by `tx-screen.mjs`.
- **`records/`** — one JSON record per screened address (git-ignored:
  the `*_streetview/` image subfolders only).
- **`facts/`** — manually-supplied facts per address, consumed by
  `--facts`.
- **`demo/`** — illustrative architectural-drawing sets and the Python
  generators that produced them, used to test and demo the
  drawing-reading path. **These drawings are synthetic** (generated from
  public parcel/appraisal data plus reasonable assumptions about panel
  size, meter placement, etc.) and are watermarked "Illustrative sample
  · Not for construction" on every sheet — they are not the real
  builder/architect plans for those addresses.
- **`bulk/`** — scratch space for large county bulk-data downloads
  (git-ignored). Re-fetch from the county appraisal district's public
  data-export page as needed.

## Requirements this checker screens

| # | Requirement |
|---|---|
| C1 | Panel size — 100–200A main breaker, single main panel |
| C2 | Meter & panel location — exterior wall, ≤ 6 ft, panel same wall |
| C3 | Wall space at the meter — ≥ 6 ft clear wall, no windows/doors |
| C4 | Side clearance — ≥ 56 in wall-to-fence/lot-line |
| C5 | Gas-meter separation — ≥ 3 ft, or no gas service |
| C6 | NEC check — 110.26 working space, 240.24(D) not-in-closet, 110.12 meter/mast condition |

Scope is **Texas only** (Base's current service area); the address
lookup rejects out-of-state addresses.

## Data sources and costs

- **Free, unlimited:** US Census / Esri geocoding, TxGIO statewide
  parcels, FEMA NFHL flood zones, USGS 3DEP elevation, PUCT utility
  service-area boundaries, OpenStreetMap building footprints, city open
  permit-data APIs (Austin, Dallas — where they exist).
- **Free, semi-automated:** county appraisal-district current-roll data
  (wired for Hays County; others need a per-county bulk-export parser).
- **Paid, capped:** Google Street View Static API, used only as a last
  resort to help locate the meter wall. Capped at 3 images per address
  and 300 images/month total (tracked in `~/claude/google-usage.json`
  outside this repo). Metadata lookups (free) always run first to avoid
  spending on addresses with no imagery.

## Setup

```
GOOGLE_MAPS_API_KEY=...   # in ~/claude/.env — NOT in this repo, NOT in
                          # any repo. Restrict the key to Street View
                          # Static + (optionally) Solar/Map Tiles APIs.
```

## Status / known gaps

- Meter and gas-meter placement are **never** in public records — the
  address-only path can only flag likely trouble (e.g. a narrow side
  yard) or confirm a pass when a permit happens to state the amperage.
  Closing this gap needs one of: builder/architect drawings, a
  homeowner photo, or a utility service-location partnership.
- County appraisal current-roll parsing is implemented for Hays County
  only; Harris (Houston) and Travis (Austin) fall back to the (older,
  less complete) statewide parcel layer.
- City permit APIs are wired for Austin and Dallas; Houston and San
  Antonio permits are not exposed as a queryable API and would need
  scraping or a bulk file.
