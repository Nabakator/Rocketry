# DRIFT Design Specification

**Deployment and Recovery Integrated Flight Tool**
Version 0.4 — Design Concept for Codex Implementation

---

## 1. Design Direction

DRIFT is a desktop engineering tool for amateur rocketry recovery systems. The UI must feel like instrumentation software — sober, information-dense, trustworthy, and fast to scan. Think MATLAB sidebars, Bloomberg Terminal data density, or avionics GUIs — not consumer SaaS.

**Core principles:**

- Engineering-first: every pixel earns its place through information value
- Low cognitive load: strong visual hierarchy, grouped inputs, readable tables
- Transparent: assumptions are always visible, not hidden behind tooltips
- State-aware: the user always knows whether a configuration is draft, valid, or analysed
- Colour is semantic, never decorative: warnings are amber, phases are colour-coded, valid/invalid states are distinct
- British English throughout all copy

**Visual language:** Dark neutral surfaces (warm slate, not pure black), monospace numerals for all data, compact spacing, sharp corners (border-radius ≤ 6px), thin 1px borders for structure. No gradients, no shadows, no rounded cards. Modern and restrained.

---

## 2. Layout Structure

The application uses a fixed three-panel layout with a thin top bar. No routing, no pages — it is a single workspace.

```
┌──────────────────────────────────────────────────────────────────────┐
│ TOP BAR (40px)                                                       │
│ [DRIFT v0.4] │ [Project ▾] │ [Save][Load][Export][Reset]   [STATE] │
├────────────┬─────────────────────────────┬───────────────────────────┤
│ LEFT PANEL │ CENTRE PANEL                │ RIGHT PANEL               │
│ 320px      │ flex (fills remaining)      │ 280px                     │
│            │                             │                           │
│ Config     │ Results / Compare           │ Recovery Schematic        │
│ Inputs     │ Warnings                    │ Event Timeline            │
│ Atmosphere │ Phase Breakdown             │ Assumptions               │
│            │ Parachute Sizing            │                           │
│            │                             │                           │
│ [Analyse]  │                             │                           │
└────────────┴─────────────────────────────┴───────────────────────────┘
```

**Panel behaviour:**

- Panels are separated by 1px borders (`hsl(220, 12%, 18%)`)
- Left and right panels have fixed widths; centre panel is flexible
- All panels scroll independently (vertical only)
- Minimum centre panel width: 400px
- In PySide6: use `QSplitter` with three child widgets; set minimum widths

---

## 3. Top Bar

Height: 40px. Background: `surface-0`. Bottom border: `panel-border`.

**Contents (left to right):**

| Element | Type | Notes |
|---------|------|-------|
| `DRIFT` | Logo text | Monospace, semibold, `primary` colour |
| `v0.4` | Version | 10px mono, `muted-foreground` |
| Divider | 1px vertical line | 20px tall |
| Project name | Dropdown button | Shows current project, e.g. "Prometheus III" |
| Divider | 1px vertical line | |
| Save | Icon button | `Save` icon, tooltip "Save project" |
| Load | Icon button | `Upload` icon, tooltip "Load project" |
| Export | Icon button | `Download` icon, tooltip "Export summary" |
| Reset | Icon button | `RotateCcw` icon, tooltip "Reset configuration" |
| *(spacer)* | flex | Pushes state badge right |
| State badge | Status indicator | See State Model below |

**PySide6 mapping:** `QToolBar` or custom `QWidget` with `QHBoxLayout`. Icon buttons are `QToolButton` with flat style.

---

## 4. Left Panel — Configuration & Inputs

Background: `surface-1`. Width: 320px. Scrollable.

### 4.1 Section Structure

The panel is divided into collapsible sections separated by 1px bottom borders. Each section has:

- **Section heading:** 11px uppercase, `muted-foreground`, letter-spacing 0.05em
- **Content area:** 16px horizontal padding, 12px vertical padding
- **Input rows:** Label left, input+unit right, stacked vertically with 8px gap

### 4.2 Configuration Selector

Two (or more) tab-style buttons for switching between configurations.

```
[ Config A ]  [ Config B ]  [ + ]
   ↑ active      ↑ inactive    ↑ add new
```

- Active: `primary/15%` background, `primary/30%` border, `primary` text
- Inactive: `surface-2` background, `panel-border` border, `muted-foreground` text
- "+" button: same as inactive, adds a new configuration

### 4.3 Deployment Type Toggle

A segmented control with two options:

```
[ Single | Dual ]
```

Below it, a single line of helper text that changes with the selection:

- **Single:** "Single parachute deploys at apogee. No staging."
- **Dual:** "Drogue deploys at apogee, main deploys at a set altitude."

This is the primary mechanism for making single vs dual deployment easy to understand. The toggle immediately shows/hides the Drogue section.

### 4.4 Input Sections

Each section follows the same input row pattern:

```
Label                    [  value  ] unit
Helper text (if any)
```

**Input row specs:**

| Property | Value |
|----------|-------|
| Label | 11px, `muted-foreground` |
| Input field | 64px wide, right-aligned, monospace, `input` background, `panel-border` border |
| Unit | 10px, `muted-foreground`, 40px wide, right-aligned |
| Helper text | 10px, `muted-foreground` at 70% opacity |

**Sections and their fields:**

#### Rocket
| Field | Unit | Helper |
|-------|------|--------|
| Dry mass | kg | — |
| Apogee (AGL) | m | — |
| Velocity at apogee | m/s | "Assumed zero unless known" |

#### Drogue *(dual deployment only)*
Phase indicator: 8px circle, `phase-drogue` colour.

| Field | Unit | Helper |
|-------|------|--------|
| Diameter | m | — |
| Cd | — | "Coefficient of drag" |
| Deploy altitude | — | "Apogee (automatic)" *(disabled field)* |

#### Main
Phase indicator: 8px circle, `phase-main` colour.

| Field | Unit | Helper |
|-------|------|--------|
| Diameter | m | — |
| Cd | — | "Coefficient of drag" |
| Deploy altitude | m AGL | *(dual only)* |
| Target descent rate | m/s | "Recommended ≤ 6.1 m/s for safe landing" |

#### Atmosphere

Header row has a right-aligned link: "Override density" (primary colour, underline on hover).

| Field | Unit | Helper |
|-------|------|--------|
| Launch altitude (MSL) | m | — |
| Temperature | °C | — |
| Pressure | hPa | — |
| *Computed ρ* | kg/m³ | *(read-only display, not input)* |

#### Wind (Drift Estimate)

| Field | Unit | Helper |
|-------|------|--------|
| Wind speed | km/h | — |
| Wind direction | ° (from) | — |

Below fields, an info note with icon:
> ℹ Drift is a first-order estimate. It assumes constant wind and vertical descent only.

### 4.5 Analyse Button

Pinned to the bottom of the panel (sticky). Full width, 32px height.

- Label: **"Analyse Configuration"**
- Style: `primary` background, `primary-foreground` text, semibold
- On hover: `primary` at 90% opacity

**PySide6 mapping:** Each section is a `QGroupBox` or custom collapsible widget. Input rows use `QHBoxLayout` with `QLabel`, `QLineEdit` (right-aligned, monospace font), and unit `QLabel`. The analyse button is pinned with a stretch spacer above it.

---

## 5. Centre Panel — Results, Warnings & Comparison

Background: `surface-0`. Flexible width (min 400px). Scrollable.

### 5.1 Tab Bar

Two tabs at the top, separated by a bottom border:

| Tab | Icon | Notes |
|-----|------|-------|
| Results | — | Default active tab |
| Compare | ↔ icon | Side-by-side comparison |

Active tab: `primary` text, 2px `primary` bottom border.
Inactive tab: `muted-foreground` text, transparent bottom border.

### 5.2 Warning Cards

Displayed at the top of the results area. Three severity levels:

| Severity | Border | Background | Text | Icon |
|----------|--------|------------|------|------|
| Error | `destructive/30%` | `destructive/5%` | `destructive` | ⚠ triangle |
| Warning | `warning/30%` | `warning/5%` | `warning` | ⚠ triangle |
| Info | `info/20%` | `info/5%` | `info` | ℹ circle |

**Example warning messages:**

- ⚠ "Main descent rate exceeds 6.1 m/s at the given mass. Consider a larger canopy."
- ⚠ "Drogue descent rate exceeds 30 m/s. Confirm structural margins for main deployment shock."
- ℹ "Drift estimate assumes constant wind speed and direction throughout descent."
- ✕ "Invalid input: parachute diameter must be greater than zero."

### 5.3 Result Cards

2×2 grid of key metrics. Each card:

```
┌─────────────────────┐
│ Label               │  ← 11px, muted-foreground
│ 87.3 s              │  ← 20px mono semibold + 11px unit
│ Apogee to ground    │  ← 10px, muted-foreground
└─────────────────────┘
```

- Background: `surface-1`, 1px `panel-border` border
- Alert state: `warning/40%` border, value text in `warning` colour

**The four result cards:**

| Label | Sublabel | Alert condition |
|-------|----------|-----------------|
| Total Descent Time | Apogee to ground | — |
| Estimated Drift | Downwind from launch pad | — |
| Main Descent Rate | At landing | > 6.1 m/s |
| Drogue Descent Rate | Before main deploy | > 30 m/s |

### 5.4 Phase Breakdown Table

Compact table with header row and one row per phase.

| Column | Alignment | Format |
|--------|-----------|--------|
| Phase | Left | Phase name + 8px colour dot |
| Alt. Start | Right | Mono, with "m" suffix |
| Alt. End | Right | Mono, with "m" suffix |
| Duration | Right | Mono, with "s" suffix |
| Avg. Rate | Right | Mono, with "m/s" suffix |

- Header row: `surface-2` background, `muted-foreground` text, 11px font-weight medium
- Body rows: `surface-1` background, separated by 1px `panel-border` dividers
- All numeric cells: monospace, tabular-nums

### 5.5 Parachute Sizing Summary

Two cards side by side (one per chute), each showing:

- Phase indicator (coloured dot + label: "Drogue" or "Main")
- Data lines: Diameter, Area, Cd, Descent rate
- Each data line: label left, monospace value+unit right

### 5.6 Comparison View (Compare Tab)

When the Compare tab is active, show two configurations side by side:

```
┌─────────── Config A ───────────┬─────────── Config B ───────────┐
│ Result cards (2×2)             │ Result cards (2×2)              │
│ Phase breakdown table          │ Phase breakdown table           │
│                                │                                 │
│ Differences highlighted        │ Differences highlighted         │
└────────────────────────────────┴─────────────────────────────────┘
```

- Highlight cells where values differ (subtle `accent` background)
- Show delta values in parentheses: e.g. "87.3s (−4.1s)"
- If only one config exists, show empty state: "Create a second configuration to compare."

**PySide6 mapping:** `QTabWidget` for Results/Compare. Result cards are custom `QFrame` widgets in a `QGridLayout`. Table is `QTableWidget` with custom delegate for phase colour dots. Comparison uses a horizontal `QSplitter`.

---

## 6. Right Panel — Schematic & Timeline

Background: `surface-1`. Width: 280px. Scrollable.

### 6.1 Recovery Schematic

An SVG (or QPainter-drawn) diagram showing the recovery trajectory in profile view.

**Elements:**

| Element | Colour | Style |
|---------|--------|-------|
| Ascent path | `phase-ascent` (red) | Dashed curve from ground to apogee |
| Apogee marker | `phase-freefall` (orange) | Circle with filled centre |
| Drogue descent | `phase-drogue` (blue) | Solid line, slight lateral drift |
| Drogue chute icon | `phase-drogue` | Small canopy shape |
| Main deploy marker | `phase-main` (teal) | Circle with filled centre |
| Main descent | `phase-main` | Thicker solid line |
| Main chute icon | `phase-main` | Larger canopy shape |
| Ground line | `muted` | Dashed horizontal line, "GND" label |
| Altitude markers | `muted-foreground` | Monospace labels: "1524m", "300m", "0m" |
| Wind arrow | `muted-foreground` | Arrow with "wind" label |
| Drift distance | `muted-foreground` | Bracket with "≈194m" label |
| Phase labels | Phase colours | Rotated text along descent paths |

**Key design rules:**

- The schematic is *not* a simulation plot — it is a stylised profile showing deployment events
- Altitude markers use reference dashed lines
- Wind direction is shown as a simple arrow
- Drift distance is indicated by a bracket at ground level

**PySide6 mapping:** Custom `QWidget` with `paintEvent` using `QPainter`. All coordinates are computed from the input data. Use `QPen` with appropriate colours and dash patterns.

### 6.2 Event Timeline

A vertical timeline with coloured dots and connecting lines.

```
● T+0.0    1524m   Apogee — drogue deploy
│
● T+54.6   300m    Main deploy
│
● T+87.3   0m      Touchdown
```

- Dot: 8px, filled with phase colour
- Connecting line: 1px, `panel-border`
- Time: monospace, 10px, `muted-foreground`
- Altitude: monospace, 10px, `muted-foreground`
- Event label: 12px, `foreground`

**PySide6 mapping:** Custom `QWidget` or `QListWidget` with custom delegate.

### 6.3 Assumptions Panel

Always visible at the bottom of the right panel. Lists the model assumptions:

- Vertical descent only
- Constant air density per phase
- Instant parachute inflation
- No coupling between wind and descent rate

Style: 10px, `muted-foreground`, bullet list.

---

## 7. State Model

Every configuration has one of four states:

| State | Colour Token | Meaning |
|-------|-------------|---------|
| Draft | `state-draft` (`hsl(220, 12%, 40%)`) | Inputs have been edited but not analysed |
| Valid | `state-valid` (`hsl(210, 70%, 55%)`) | All inputs pass validation |
| Analysed | `state-analysed` (`hsl(142, 50%, 45%)`) | Analysis has been run; results are current |
| Invalid | `state-invalid` (`hsl(0, 65%, 55%)`) | One or more inputs fail validation |

**State badge format:** Compact pill with:
- 6px filled circle (state colour)
- State name in uppercase monospace, 10px
- Background: state colour at 15-20% opacity
- Border: state colour at 30% opacity

**State transitions:**

```
[New config] → Draft
Draft → (validate) → Valid or Invalid
Valid → (analyse) → Analysed
Analysed → (edit any input) → Draft
```

---

## 8. Colour System

### Surface Hierarchy

| Token | HSL | Usage |
|-------|-----|-------|
| `surface-0` | `220 14% 10%` | App background, centre panel |
| `surface-1` | `220 13% 13%` | Left panel, right panel, cards |
| `surface-2` | `220 12% 16%` | Table headers, inactive buttons |
| `surface-3` | `220 11% 20%` | Hover states |

### Text

| Token | HSL | Usage |
|-------|-----|-------|
| `foreground` | `210 20% 90%` | Primary text |
| `muted-foreground` | `215 15% 55%` | Labels, secondary text, units |

### Semantic Colours

| Token | HSL | Usage |
|-------|-----|-------|
| `primary` | `210 70% 55%` | Active states, links, primary actions |
| `warning` | `38 92% 50%` | Warning cards, alert values |
| `destructive` | `0 65% 55%` | Error states, invalid inputs |
| `success` | `142 50% 45%` | Analysed state |
| `info` | `210 70% 55%` | Informational notes |

### Phase Colours

| Token | HSL | Phase |
|-------|-----|-------|
| `phase-ascent` | `0 60% 55%` | Ascent (red) |
| `phase-freefall` | `30 80% 55%` | Freefall / apogee (orange) |
| `phase-drogue` | `200 65% 55%` | Drogue descent (blue) |
| `phase-main` | `170 55% 45%` | Main descent (teal) |

### Borders

| Token | HSL | Usage |
|-------|-----|-------|
| `border` | `220 12% 22%` | General borders |
| `panel-border` | `220 12% 18%` | Panel separators, section dividers |
| `input` | `220 13% 15%` | Input field backgrounds |

---

## 9. Typography

| Role | Font | Size | Weight | Notes |
|------|------|------|--------|-------|
| UI text | Inter | 12px (default) | 400 | All labels, descriptions, body |
| Section headings | Inter | 11px | 600 | Uppercase, letter-spacing 0.05em |
| Input values | JetBrains Mono | 12px | 400 | Right-aligned, tabular-nums |
| Result values | JetBrains Mono | 20px | 600 | Large metric display |
| Units | Inter or Mono | 10-11px | 400 | `muted-foreground` |
| Helper text | Inter | 10px | 400 | `muted-foreground` at 70% |
| State badge | JetBrains Mono | 10px | 500 | Uppercase |
| Schematic labels | JetBrains Mono | 7-8px | 400 | SVG/QPainter text |

**PySide6 font setup:**

```python
from PySide6.QtGui import QFont, QFontDatabase

# Load fonts
QFontDatabase.addApplicationFont("fonts/Inter-VariableFont.ttf")
QFontDatabase.addApplicationFont("fonts/JetBrainsMono-Regular.ttf")

# Define font constants
FONT_UI = QFont("Inter", 12)
FONT_HEADING = QFont("Inter", 11, QFont.DemiBold)
FONT_MONO = QFont("JetBrains Mono", 12)
FONT_MONO_LARGE = QFont("JetBrains Mono", 20, QFont.DemiBold)
FONT_MONO_SMALL = QFont("JetBrains Mono", 10)
```

---

## 10. Spacing System

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Tight gaps (icon to label) |
| `sm` | 8px | Input row vertical gap |
| `md` | 12px | Section padding vertical |
| `lg` | 16px | Section padding horizontal, card padding |
| `xl` | 24px | Between major sections |

---

## 11. Component Patterns

### 11.1 Input Row

```
┌─────────────────────────────────────────────┐
│ Dry mass                    [ 4.2 ] kg      │
└─────────────────────────────────────────────┘
```

- `QHBoxLayout`: stretch label, fixed-width `QLineEdit` (64px), fixed-width unit label (40px)
- Input: right-aligned, monospace, `input` background, `panel-border` border, 1px
- On focus: 1px `ring` (primary blue) border

### 11.2 Section Heading

```
ROCKET
```

- 11px, uppercase, semibold, `muted-foreground`, letter-spacing 0.05em
- Bottom margin: 8px

### 11.3 Warning Card

```
┌ ⚠ Main descent rate exceeds 6.1 m/s at the given mass. ──────────┐
│   Consider a larger canopy.                                        │
└────────────────────────────────────────────────────────────────────┘
```

- Left icon + text, 12px
- Rounded corners: 6px
- Padding: 8px horizontal, 8px vertical
- Severity determines border, background, and text colour

### 11.4 Result Card

```
┌─────────────────────┐
│ Total Descent Time  │
│ 87.3 s              │
│ Apogee to ground    │
└─────────────────────┘
```

- 12px padding
- 6px border-radius
- `surface-1` background
- Alert variant: `warning/40%` border, `warning` value colour

### 11.5 Phase Table Row

```
│ ● Drogue  │  1524m  │  300m  │  54.6s  │  22.4 m/s  │
```

- 8px coloured dot before phase name
- All numeric cells: monospace, tabular-nums, right-aligned
- Row height: ~28px
- Alternating: not needed (section borders provide enough structure)

### 11.6 Timeline Event

```
● T+0.0    1524m
│ Apogee — drogue deploy
│
```

- Vertical layout: dot → line → dot → line → dot
- Dot: 8px filled circle
- Line: 1px, `panel-border`

---

## 12. Copy Conventions

### Section Headings

Use single nouns or noun phrases. Uppercase, short.

- CONFIGURATION
- DEPLOYMENT TYPE
- ROCKET
- DROGUE
- MAIN
- ATMOSPHERE
- WIND (DRIFT ESTIMATE)
- RESULTS
- PHASE BREAKDOWN
- PARACHUTE SIZING
- RECOVERY SCHEMATIC
- EVENT TIMELINE
- ASSUMPTIONS

### Button Labels

| Action | Label |
|--------|-------|
| Run analysis | Analyse Configuration |
| Save | Save (icon only in top bar) |
| Load | Load (icon only in top bar) |
| Export | Export Summary |
| Reset | Reset Configuration |
| Add config | + |
| Override density | Override density |

### Validation Messages

- "Parachute diameter must be greater than zero."
- "Mass must be a positive number."
- "Apogee altitude must be greater than main deploy altitude."
- "Deploy altitude must be between 0 and apogee."
- "Coefficient of drag must be positive."

### Warning Messages

- "Main descent rate exceeds 6.1 m/s at the given mass. Consider a larger canopy."
- "Drogue descent rate exceeds 30 m/s. Confirm structural margins for main deployment shock."
- "Estimated drift exceeds 500 m. Recovery may be difficult in this wind."
- "Main deploy altitude is below 150 m AGL. Allow adequate time for canopy inflation."

### Helper Text

- "Assumed zero unless known"
- "Coefficient of drag"
- "Apogee (automatic)"
- "Recommended ≤ 6.1 m/s for safe landing"

### Empty States

- Compare tab, no second config: "Create a second configuration to compare."
- No analysis run: "Enter parameters and press Analyse to see results."
- No project loaded: "Create or load a project to begin."

### Info Notes

- "Drift is a first-order estimate. It assumes constant wind and vertical descent only."
- "Atmospheric density is computed from the ISA model using the inputs above."

---

## 13. PySide6 Implementation Notes

### QSS (Qt Style Sheet) Skeleton

```css
/* Global */
QWidget {
    background-color: hsl(220, 14%, 10%);
    color: hsl(210, 20%, 90%);
    font-family: "Inter";
    font-size: 12px;
}

/* Panels */
QWidget#leftPanel {
    background-color: hsl(220, 13%, 13%);
    border-right: 1px solid hsl(220, 12%, 18%);
}

QWidget#rightPanel {
    background-color: hsl(220, 13%, 13%);
    border-left: 1px solid hsl(220, 12%, 18%);
}

/* Input fields */
QLineEdit {
    background-color: hsl(220, 13%, 15%);
    border: 1px solid hsl(220, 12%, 22%);
    border-radius: 3px;
    padding: 2px 6px;
    color: hsl(210, 20%, 90%);
    font-family: "JetBrains Mono";
    font-size: 12px;
}

QLineEdit:focus {
    border-color: hsl(210, 70%, 55%);
}

QLineEdit:disabled {
    opacity: 0.4;
}

/* Buttons */
QPushButton#analyseButton {
    background-color: hsl(210, 70%, 55%);
    color: hsl(210, 20%, 98%);
    border: none;
    border-radius: 3px;
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton#analyseButton:hover {
    background-color: hsl(210, 70%, 50%);
}

/* Section headings */
QLabel.sectionHeading {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: hsl(215, 15%, 55%);
}

/* Tables */
QTableWidget {
    background-color: hsl(220, 13%, 13%);
    border: 1px solid hsl(220, 12%, 22%);
    gridline-color: hsl(220, 12%, 18%);
    font-family: "JetBrains Mono";
    font-size: 12px;
}

QHeaderView::section {
    background-color: hsl(220, 12%, 16%);
    color: hsl(215, 15%, 55%);
    border: none;
    border-bottom: 1px solid hsl(220, 12%, 18%);
    padding: 4px 12px;
    font-family: "Inter";
    font-weight: 500;
}
```

### Colour Constants (Python)

```python
class Colours:
    SURFACE_0 = "#181b20"     # hsl(220, 14%, 10%)
    SURFACE_1 = "#1e2127"     # hsl(220, 13%, 13%)
    SURFACE_2 = "#252930"     # hsl(220, 12%, 16%)
    SURFACE_3 = "#2d3139"     # hsl(220, 11%, 20%)

    FOREGROUND = "#dce1e8"    # hsl(210, 20%, 90%)
    MUTED = "#7a8494"         # hsl(215, 15%, 55%)

    PRIMARY = "#4a9be8"       # hsl(210, 70%, 55%)
    WARNING = "#f5a623"       # hsl(38, 92%, 50%)
    DESTRUCTIVE = "#d44a4a"   # hsl(0, 65%, 55%)
    SUCCESS = "#47a05c"       # hsl(142, 50%, 45%)

    PHASE_ASCENT = "#d44a4a"  # hsl(0, 60%, 55%)
    PHASE_FREEFALL = "#e8912a" # hsl(30, 80%, 55%)
    PHASE_DROGUE = "#3a9fd4"  # hsl(200, 65%, 55%)
    PHASE_MAIN = "#3d997a"    # hsl(170, 55%, 45%)

    BORDER = "#333a45"        # hsl(220, 12%, 22%)
    PANEL_BORDER = "#282d35"  # hsl(220, 12%, 18%)
    INPUT_BG = "#1c2027"      # hsl(220, 13%, 15%)
```

### Widget Hierarchy

```
QMainWindow
├── TopBarWidget (QWidget, fixed height 40px)
│   └── QHBoxLayout
│       ├── QLabel "DRIFT"
│       ├── QComboBox (project selector)
│       ├── QToolButton × 4 (save, load, export, reset)
│       ├── QSpacerItem (expanding)
│       └── StateBadgeWidget
│
└── QSplitter (horizontal)
    ├── LeftPanelWidget (QScrollArea, min-width 280, preferred 320)
    │   └── QVBoxLayout
    │       ├── ConfigSelectorWidget
    │       ├── DeploymentTypeToggle
    │       ├── SectionWidget "Rocket"
    │       │   └── InputRow × 3
    │       ├── SectionWidget "Drogue" (conditional)
    │       │   └── InputRow × 3
    │       ├── SectionWidget "Main"
    │       │   └── InputRow × 3-4
    │       ├── SectionWidget "Atmosphere"
    │       │   └── InputRow × 3 + DataLine × 1
    │       ├── SectionWidget "Wind"
    │       │   └── InputRow × 2 + InfoNote
    │       ├── QSpacerItem (expanding)
    │       └── QPushButton "Analyse Configuration"
    │
    ├── CentrePanelWidget (QWidget, min-width 400)
    │   └── QVBoxLayout
    │       ├── QTabWidget (Results / Compare)
    │       │   ├── ResultsTab
    │       │   │   ├── WarningCard × N
    │       │   │   ├── QGridLayout (2×2 ResultCards)
    │       │   │   ├── QTableWidget (Phase Breakdown)
    │       │   │   └── QHBoxLayout (Parachute Sizing × 2)
    │       │   └── CompareTab
    │       │       └── QSplitter (horizontal, two result columns)
    │
    └── RightPanelWidget (QScrollArea, min-width 240, preferred 280)
        └── QVBoxLayout
            ├── SchematicWidget (custom QPainter)
            ├── TimelineWidget (custom paint or QListWidget)
            └── AssumptionsWidget (QLabel list)
```

---

## 14. Verification Checklist

- [ ] Reads as a desktop engineering tool, not a web SaaS app
- [ ] Three-panel layout is intact and non-negotiable
- [ ] Dark theme with warm slate tones, not pure black
- [ ] Monospace for all numerical data
- [ ] Phase colours used consistently (ascent=red, freefall=orange, drogue=blue, main=teal)
- [ ] State model clearly distinguishes draft/valid/analysed/invalid
- [ ] Warnings use amber, errors use red, info uses blue
- [ ] Assumptions are visible, not hidden
- [ ] British English throughout
- [ ] No fake precision — the tool provides first-order estimates only
- [ ] Single vs dual deployment toggle shows/hides drogue section
- [ ] Copy is engineering-appropriate, not marketing copy
- [ ] All input fields have appropriate units displayed
- [ ] Helper text guides without patronising
