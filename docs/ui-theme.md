# Cockpit UI Theme Tokens

CodexCockpit's desktop UI uses a shared theme stylesheet to provide a modular,
terminal-inspired foundation with dark/light support and extensible layout
utilities. The theme lives in `codex-cockpit-desktop/src/styles/theme.css` and
is loaded globally in `codex-cockpit-desktop/src/main.ts`.

## Theme Modes

Theme selection is driven by the `data-theme` attribute on the root element.
Supported values are:

- `dark`: Force the dark palette.
- `light`: Force the light palette.
- `gruvbox`: Warm, retro terminal palette.
- `dracula`: Neon purple/teal palette inspired by Dracula.
- `nord`: Cool arctic palette with muted blues.
- `system`: Remove the attribute to honor `prefers-color-scheme`.

The top bar provides a theme selector that writes the preference to
`localStorage` and updates the root attribute.

TODO: Add automated UI coverage for theme switching once a frontend test harness
is in place.

## Design Tokens

The theme provides CSS custom properties for layout, typography, spacing, and
status colors. The most commonly used tokens are:

- `--bg`, `--panel`, `--panel-2`, `--panel-3` for layered surfaces.
- `--text`, `--muted` for primary and secondary text.
- `--font-sans`, `--font-mono` for theme-specific typography stacks.
- `--accent`, `--accent-soft`, `--good`, `--warn`, `--bad`, `--info` for status
  messaging.
- `--radius-*`, `--space-*`, `--shadow` for shape and rhythm.

Dark mode also applies a subtle animated glow overlay (`body::before`) and
scanline texture (`body::after`) to add terminal-style movement. Animations are
disabled automatically when `prefers-reduced-motion` is set.

## Utility Classes

`theme.css` defines reusable utility classes so future UI sections can adopt a
consistent terminal cockpit style:

- Layout: `.panel`, `.panel-header`, `.panel-body`, `.panel-footer`,
  `.panel-subheader`, `.card`, `.layout-grid`, `.layout-split`, `.stack`.
- Controls: `.btn`, `.btn.primary`, `.btn.danger`, `.input`, `.select`,
  `.textarea`, `.btn.compact`, `.input.compact`, `.select.compact`,
  `.toggle.compact`, `.toolbar.compact`.
- Indicators: `.pill`, `.badge`, `.status-dot`, `.progress`.
- Data views: `.table`, `.diff-viewer`, `.log-stream`, `.timeline`.

When adding new UI modules, prefer these utilities over introducing new
one-off styles.

## Workflow Sidebar Guidance

The cockpit sidebar uses step-labeled headers to clarify the workflow order.
Keep the session creation button as the primary call-to-action, and only
emphasize execution controls once a session exists. Secondary controls (stop
stream, clear console) should retain reduced visual weight to avoid competing
with the primary flow.
