# EvolveAgent — native macOS app (Tauri)

Phase 5. Wraps the existing EvolveAgent web frontend in a native macOS window
using [Tauri v2](https://tauri.app) — a real app icon, a Mac-style overlay title
bar, and no browser tab. **Additive:** this lives entirely under `desktop/` and
does not change the web app or its CI. The web app keeps working exactly as
before; this is just a native shell around it.

## What it is (and isn't)

- **Is:** a thin, locked-down native window that loads the same React frontend
  (`frontend/dist` in release, the Vite dev server in development) and talks to
  your local backend at `http://127.0.0.1:8000`.
- **Isn't:** a new backend, a second copy of the UI, or anything with elevated
  privileges. It registers **no** shell, filesystem, or arbitrary-network
  capabilities (see `src-tauri/capabilities/default.json`). This keeps it aligned
  with EvolveAgent's safety model.

## Prerequisites (one-time, on your Mac)

Tauri compiles a native binary, so it needs a Rust toolchain and Apple's build
tools — these are **not** required for the web app.

```bash
xcode-select --install                                   # Xcode Command Line Tools
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # Rust
cd desktop && npm install                                # Tauri CLI + API
npm run tauri icon ../assets/logo.png                    # generate app icons (any square PNG ≥ 512px)
```

> Icons are generated locally into `src-tauri/icons/` (git-ignored so we never
> commit binaries). Point the command at any square logo; it produces every size
> Tauri needs, including the `.icns`.

## Run it

Make sure the backend is running (`uvicorn app.main:app` on :8000), then:

```bash
cd desktop
npm run dev      # launches the native window; hot-reloads from the Vite dev server
npm run build    # produces EvolveAgent.app + a .dmg in src-tauri/target/release/bundle/
```

`npm run dev`/`build` automatically start the frontend dev/build for you (see
`beforeDevCommand` / `beforeBuildCommand` in `src-tauri/tauri.conf.json`).

## Security posture

- **CSP** restricts the webview to `'self'`, the local backend
  (`http://127.0.0.1:8000` and its websocket), and the local Vite dev server
  (`localhost:5173` + HMR) — no external hosts. `script-src` includes
  `'unsafe-inline'` because Vite's dev-mode React-refresh preamble is injected
  inline; connect-src stays limited to localhost so nothing can be exfiltrated.
- **Capabilities** grant only `core:default`. No `shell`, `fs`, or `http`
  plugins are enabled, so the native layer cannot run commands, read/write
  arbitrary files, or reach arbitrary hosts.
- Add capabilities **explicitly and narrowly** if a future feature needs them;
  never widen to blanket access.

## Layout

```
desktop/
├── package.json              # Tauri tooling (isolated from frontend/)
└── src-tauri/
    ├── tauri.conf.json       # window, CSP, bundle config; points at ../../frontend/dist
    ├── Cargo.toml
    ├── build.rs
    ├── capabilities/default.json
    └── src/{main.rs,lib.rs}   # minimal shell — no extra native APIs
```
