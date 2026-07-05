// EvolveAgent desktop shell.
//
// Deliberately minimal: this wraps the existing web frontend in a native
// window. It registers NO extra native capabilities (no shell, no filesystem,
// no arbitrary network) — see capabilities/default.json. That keeps the desktop
// build aligned with EvolveAgent's safety model (no unrestricted shell access,
// no destructive autonomous file operations). Add capabilities explicitly and
// narrowly if a feature ever needs them.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running the EvolveAgent desktop app");
}
