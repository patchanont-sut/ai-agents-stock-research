---
name: Luminous Fintech
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#bbcabf'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#86948a'
  outline-variant: '#3c4a42'
  surface-tint: '#4edea3'
  primary: '#4edea3'
  on-primary: '#003824'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#006c49'
  secondary: '#bec6e0'
  on-secondary: '#283044'
  secondary-container: '#3f465c'
  on-secondary-container: '#adb4ce'
  tertiary: '#45dfa4'
  on-tertiary: '#003825'
  tertiary-container: '#00b982'
  on-tertiary-container: '#00422c'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#68fcbf'
  tertiary-fixed-dim: '#45dfa4'
  on-tertiary-fixed: '#002114'
  on-tertiary-fixed-variant: '#005137'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

The design system is engineered for a high-trust, growth-oriented fintech environment. It projects stability through a deep navy foundation while signaling upward momentum and prosperity with vibrant emerald accents. 

The aesthetic is **Glassmorphic-Corporate**, blending the reliability of traditional finance with the innovative feel of modern wealth management. It utilizes frosted-glass containers and subtle background blurs to create a sense of depth and transparency—metaphorically aligning with the brand's commitment to clear financial insights. The interface should feel premium, focused, and technologically advanced, evoking an emotional response of confidence and calm control over one's financial future.

## Colors

The palette is optimized for a dark-mode-first experience, prioritizing legibility and visual hierarchy through luminous accents.

- **Primary (Emerald):** Used for growth indicators, successful states, and primary actions. It is often applied as a linear gradient (Emerald 500 to Emerald 600) to create a "glowing" effect.
- **Secondary (Deep Navy):** The core background color. It provides a sophisticated, high-contrast base that reduces eye strain during long-term data monitoring.
- **Tertiary (Mint/Spring):** Used for subtle highlights, secondary data points, or "upward" trend lines that require less visual weight than the primary emerald.
- **Neutral (Slate/Steel):** Used for secondary text, borders, and inactive states to ensure the interface remains clean and structured.

Backgrounds should utilize a radial gradient transition from `#1E293B` (center-top) to `#0F172A` (bottom) to provide subtle depth beneath the glass layers.

## Typography

The typography system uses **Hanken Grotesk** for its sharp, contemporary, and highly legible characteristics. Its geometric construction feels modern yet professional, perfect for a fintech dashboard. 

For technical data, currency values, and timestamps, **JetBrains Mono** is utilized. This monospaced font ensures that numerical values align perfectly in tables and charts, facilitating quick scanning of financial data. Headlines use tighter tracking and heavier weights to establish a strong visual anchor, while labels are set in uppercase with slight letter spacing to differentiate them from body content.

## Layout & Spacing

The design system employs a **fluid grid** with fixed-width constraints for maximum readability on large displays. 

- **Desktop:** A 12-column grid with a 1440px max-width. Content is organized into modular "glass" tiles that snap to the grid.
- **Tablet:** An 8-column grid with reduced margins (24px).
- **Mobile:** A 4-column grid with 16px margins. Heavy use of vertical stacking for card-based components.

Spacing follows a strict 4px base unit. Component internal padding should favor generous whitespace (usually 24px or 32px) to prevent the data-dense fintech environment from feeling cluttered. Modular containers are separated by a consistent 16px gutter.

## Elevation & Depth

Hierarchy is established through **Glassmorphism** and tonal layering rather than traditional heavy shadows.

1.  **Base Layer:** The deepest Navy (`#0F172A`), serving as the canvas.
2.  **Card Layer:** Semi-transparent containers (`rgba(30, 41, 59, 0.7)`) with a `backdrop-filter: blur(12px)`. These cards feature a thin, 1px semi-transparent border (`rgba(255, 255, 255, 0.1)`) to define their edges against the dark background.
3.  **Active/Floating Layer:** Elements like dropdowns or modals use a higher opacity glass and a soft, emerald-tinted glow (`0 8px 32px rgba(16, 185, 129, 0.15)`) to indicate they are closer to the user.

Depth is further enhanced by placing subtle, large-scale blurred "blobs" of emerald and navy in the background, which peek through the glass layers.

## Shapes

The design system uses a **Rounded** shape language to soften the "hard" feel of financial data and make the interface feel more approachable.

- **Cards/Containers:** Use a 1rem (`rounded-lg`) radius to create a modern, friendly structure.
- **Buttons/Inputs:** Standardized at 0.5rem (`rounded-md`) to maintain a professional, clickable appearance.
- **Charts:** Line graphs should use smoothed Bézier curves rather than jagged points, and bar charts should have slightly rounded top corners (4px) to match the overall aesthetic.

## Components

- **Buttons:** Primary buttons are vibrant emerald gradients with white text. Secondary buttons are "ghost" style with an emerald border. Use a subtle hover scale effect (1.02x) to provide tactile feedback.
- **Glass Cards:** The fundamental building block. Every card must have a 1px top-oriented border highlight to simulate light catching the "glass" edge.
- **Data Tables:** Row separators use low-opacity slate lines. The "Amount" column always uses the monospaced font for alignment.
- **Growth Indicators:** Positive trends use the primary emerald with a small "up" arrow icon. Negative trends use a soft coral-red, but are styled with the same glow intensity to maintain system harmony.
- **Input Fields:** Dark backgrounds (`rgba(15, 23, 42, 0.5)`) with emerald bottom-borders on focus. Placeholder text uses a muted slate.
- **Status Chips:** Small, pill-shaped indicators with low-opacity emerald backgrounds and high-opacity emerald text for "Success" or "Active" states.