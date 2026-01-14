

---

## Codex GUI - CodexCockpit — Development Rules

### 1. Architectural Boundaries (Non-Negotiable)

* The GUI **must never** communicate directly with any model (local or remote).
* The GUI **must never** execute shell commands or touch the filesystem directly.
* All intelligence, tools, and execution flow through the **Codex Control API**.
* Codex is treated as a **service**, not a helper library.

Violations of these rules are considered architectural bugs, not shortcuts.

---

### 2. Codex Isolation Rule

* Codex execution is **session-scoped**, not request-scoped.
* Codex lifecycle must be abstracted behind a driver interface.
* The API layer must not depend on whether Codex is:

  * in-process
  * a subprocess
  * a daemon
  * remote

Codex must be swappable without changing GUI or API contracts.

---

### 3. Driver Interface Rule (Critical)

All Codex interaction goes through a single internal interface (example responsibilities):

* create session
* send input
* stream events
* stop session
* report status

No API endpoint may call Codex logic directly.
No GUI feature may assume Codex implementation details.

---

### 4. Event-First Communication

* Codex outputs **structured events**, not raw text blobs.
* Events are typed (e.g. `plan`, `tool`, `diff`, `thought`, `status`, `final`, `cancelled`, `error`).
* The GUI renders events; it does not interpret model intent.

Free-form text is allowed only as event payloads, never as protocol.

---

### 5. Streaming Is the Default

* Long-running tasks **must stream** progress.
* Blocking requests are forbidden for execution endpoints.
* Backpressure and cancellation must be supported.

If something can take more than one second, it must stream.

---

### 6. Model Neutrality Rule

* No logic may assume a specific model family or vendor.
* Model capabilities are **declared**, not inferred.
* Unsupported features must degrade gracefully (UI disables, API rejects).

Local and remote models are peers.

---

### 7. Explicit Capability Declaration

Each model definition must specify:

* context length
* tool support
* function / JSON reliability
* latency class
* cost class (even if zero)

The system must never “try and see” in production paths.

---

### 8. Workspace Transparency

* All filesystem operations occur inside an explicit workspace.
* The GUI must be able to see:

  * file changes
  * diffs
  * created / deleted files
* Silent mutations are forbidden.

If Codex edits something, the user must be able to inspect it.

---

### 9. Deterministic Sessions

* Sessions have IDs and explicit state.
* Sessions can be:

  * resumed
  * stopped
  * inspected
  * replayed (where possible)
* The system must not rely on global mutable state.

Stateless APIs, stateful sessions.

---

### 10. Failure Is a First-Class Outcome

* Codex crashes must not crash the API.
* Partial failures must surface as structured error events.
* Restarting Codex must not require restarting the GUI or API.

Failure is expected. Design accordingly.

---

### 11. No Hidden Magic

* No implicit environment variables.
* No reliance on shell PATHs.
* No undocumented side effects.

If something is required, it must be declared, validated, and logged.

---

### 12. Debuggability Over Cleverness

* Prefer explicit code paths over abstractions that hide flow.
* Prefer readable logs over compact ones.
* Prefer boring solutions that survive refactors.

This system is a **workbench**, not a demo.

---

### 13. Migration Rule

* In-process Codex is allowed **only** if it conforms to the driver interface.
* The system must be migratable to a Codex daemon without API or GUI changes.

Design as if the migration is inevitable.

---

### 14. GUI Philosophy

* The GUI displays **process**, not just results.
* Users must be able to see what the system is doing and why.
* Chat-style UX is insufficient for this system.

This is an execution cockpit, not a chatbot.
