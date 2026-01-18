
This continuation completes **`docs/FRAMEWORKS.md`**, then introduces the **next major documentation file: `docs/FEATURE_FLOW.md`**, which will provide a visual and stepwise walkthrough of how CodexCockpit takes a user request from idea → scaffold → validation → completion.

---

# 📗 **docs/FRAMEWORKS.md (continued)**

---

### 7. Adding a New Framework (continued)

To register and execute a new framework within CodexCockpit, follow these steps:

1. **Create the framework file**

   * Add a new YAML definition in `/frameworks/<framework_name>.yaml` (for example: `feature_refactor.yaml`).

   Example:

   ```yaml
   framework: feature_refactor
   description: "Iteratively analyze and refactor code for performance improvements."
   trigger: "codex run refactor:<target>"
   model: openai:codex
   steps:
     - name: Analyze
       action: analyze_target
       prompt: "Identify optimization opportunities in the specified code path."
     - name: Refactor
       action: apply_refactor
       depends_on: [Analyze]
     - name: Validate
       action: run_tests
       depends_on: [Refactor]
     - name: Iterate
       action: iterate_until_optimized
       depends_on: [Validate]
   ```

2. **Register it in `codex.json`**

   * Open the configuration file at the root of the repository:

     ```json
     {
       "frameworks": {
         "feature_development": "./frameworks/feature_development.yaml",
         "bug_fixing": "./frameworks/bug_fixing.yaml",
         "rule_enforcer": "./frameworks/rule_enforcer.yaml",
         "feature_refactor": "./frameworks/feature_refactor.yaml"
       }
     }
     ```

3. **Define Step Handlers**

   * In `backend/core/framework_engine.py`, implement the logic for each action referenced in your framework.
     Example:

     ```python
     from backend.core.codex_runner import CodexRunner

     def analyze_target(context):
         CodexRunner.run("Analyze performance issues", context)
         return context

     def apply_refactor(context):
         CodexRunner.run("Implement optimized changes", context)
         return context
     ```

4. **Document in `docs/FRAMEWORKS.md`**

   * Add a new subsection describing the framework, including:

     * Its intent and expected inputs.
     * Output artifacts.
     * Dependencies and Codex Agents involved.

5. **Test Execution**

   * Run your new framework using:

     ```
     codex run framework:feature_refactor --input "Optimize backend/api/routes response latency"
     ```
   * Verify output logs in `backend/logs/`.

---

### 8. Framework Validation Layer

Each framework execution undergoes multi-stage validation to ensure correctness and consistency.

**Validation Phases:**

| Phase                     | Description                                                           | Implemented In                                |
| ------------------------- | --------------------------------------------------------------------- | --------------------------------------------- |
| **Schema Validation**     | Checks that the framework YAML structure conforms to required fields. | `framework_engine.validate_schema()`          |
| **Dependency Validation** | Ensures all `depends_on` steps exist and are properly ordered.        | `iteration_controller.resolve_dependencies()` |
| **Runtime Validation**    | Validates output after each step (syntax checks, tests, etc.).        | `codex_runner.validate_output()`              |

---

### 9. Built-in Validation Hooks

Each step can optionally define validation hooks.
Example:

```yaml
steps:
  - name: Scaffold
    action: scaffold_code
    depends_on: [Plan]
    validate:
      - run_pytest
      - check_syntax
      - ensure_no_todo_comments
```

**Hooks are Python functions** implemented in `backend/utils/validation_hooks.py`.
If any validation fails, the framework automatically re-enters the iteration loop for correction.

---

### 10. Multi-Agent Support

Frameworks can specify which Codex Agent (from `AGENTS.md`) should execute each step.
Example:

```yaml
steps:
  - name: Plan
    action: generate_plan
    agent: ArchitectAgent
  - name: Scaffold
    action: scaffold_code
    agent: BuilderAgent
  - name: Review
    action: review_output
    agent: ReviewerAgent
```

Agents are loaded dynamically via the **Agent Registry** in `backend/core/agent_loader.py`.
This allows specialization of behavior — for example, a ReviewerAgent may be tuned to enforce `RULES.md` standards automatically.

---

### 11. Framework Execution Logs

Every framework run generates a structured log file:

**Path:**
`/backend/logs/framework_<timestamp>.json`

**Example:**

```json
{
  "framework": "feature_development",
  "run_id": "2026-01-16T21:45:00Z",
  "initiator": "CLI",
  "model": "openai:codex",
  "steps": [
    {
      "name": "Outline",
      "status": "complete",
      "agent": "ArchitectAgent",
      "duration": "00:01:20",
      "output": "outline.yaml"
    },
    {
      "name": "Plan",
      "status": "complete",
      "agent": "ArchitectAgent",
      "duration": "00:02:14",
      "output": "plan.md"
    },
    {
      "name": "Scaffold",
      "status": "complete",
      "agent": "BuilderAgent",
      "output": "backend/api/routes/logging_middleware.py"
    },
    {
      "name": "Review",
      "status": "iterating",
      "agent": "ReviewerAgent"
    }
  ],
  "final_state": "iterating",
  "next_action": "iterate_until_complete"
}
```

---

### 12. Framework Visualization (GUI Integration)

The GUI component (`codex-cockpit-desktop/src/components/FrameworkView.jsx`) renders frameworks in a **node-based diagram**:

```
[Outline] → [Plan] → [Scaffold] → [Review] ↻ [Iterate]
```

Each node’s state color:

* **Gray:** Pending
* **Blue:** Running
* **Green:** Complete
* **Orange:** Iterating
* **Red:** Failed

Framework progress and logs are streamed via the API endpoint:
`GET /api/frameworks/:run_id/status`

---

### 13. Future Framework Features

| Feature                          | Description                                                                    |
| -------------------------------- | ------------------------------------------------------------------------------ |
| **Dynamic Step Injection**       | Allow Codex to add new steps during execution if it deems necessary.           |
| **Parallel Branch Execution**    | Run independent steps concurrently (e.g., code generation + doc generation).   |
| **Auto-Tuning Parameters**       | Adjust temperature, max tokens, or model choice dynamically based on progress. |
| **Recursive Frameworks**         | Frameworks that can call themselves for sub-features or nested components.     |
| **Multi-Agent Consensus Review** | Require consensus among multiple reviewer agents before marking complete.      |

---

# 📘 **docs/FEATURE_FLOW.md**

---

# CodexCockpit Feature Flow

**Version:** 0.1
**Purpose:** To describe, step-by-step, how CodexCockpit converts a user’s feature request into a fully implemented, reviewed, and merged feature using the iterative Codex framework.

---

## 1. Overview

The **Feature Flow** is the complete lifecycle of a Codex-guided development process.
It begins when a user submits a feature request (via GUI or CLI) and ends when the generated code is committed and validated.

Each stage corresponds to a framework step defined in `/frameworks/feature_development.yaml`.

---

## 2. Process Diagram

```
┌────────────┐
│ User Input │
└──────┬─────┘
       │
       ▼
┌────────────────────┐
│ 1. Outline         │
│ (Generate feature  │
│ description + goals)│
└──────┬─────────────┘
       ▼
┌────────────────────┐
│ 2. Plan            │
│ (Define steps,     │
│ file targets, tests)│
└──────┬─────────────┘
       ▼
┌────────────────────┐
│ 3. Scaffold        │
│ (Generate initial  │
│ code structures)   │
└──────┬─────────────┘
       ▼
┌────────────────────┐
│ 4. Review          │
│ (Analyze output,   │
│ enforce RULES.md)  │
└──────┬─────────────┘
       ▼
┌────────────────────┐
│ 5. Iterate         │
│ (Refine until done)│
└──────┬─────────────┘
       ▼
┌────────────────────┐
│ 6. Commit + Merge  │
│ (Git integration)  │
└────────────────────┘
```

---

## 3. Example Flow (based on current repo)

**Feature Request:**

> “Add analytics tracking to the codex-cockpit-desktop GUI.”

### Step 1: Outline

Codex generates:

```
1. Add analytics.js under codex-cockpit-desktop/src/utils.
2. Create AnalyticsProvider context.
3. Wrap Dashboard.jsx in AnalyticsProvider.
4. Send event logs to backend API route /api/logs.
```

→ Output saved as `/backend/memory/outline_analytics.json`

---

### Step 2: Plan

Codex expands the outline into a step plan:

```markdown
## Development Plan
- Modify `main.js` to initialize analytics.
- Create new file `src/utils/analytics.js`.
- Add environment config to `codex.json`.
- Update `backend/api/routes/logs.py` to accept POST payloads.
```

---

### Step 3: Scaffold

Codex scaffolds:

* `codex-cockpit-desktop/src/utils/analytics.js`
* `backend/api/routes/logs.py`

Each file is written atomically and committed to a feature branch:

```
git branch feature/add-analytics
git commit -m "Scaffold analytics integration"
```

---

### Step 4: Review

The ReviewerAgent runs:

* **Code style checks**
* **RULES.md compliance audit**
* **Sanity review** of logic completeness

Detected issue example:

> “Missing error handling for failed POST requests in analytics.js.”

Framework re-enters iteration cycle.

---

### Step 5: Iterate

Codex re-runs with updated prompt:

```
"Fix missing error handling for failed POST requests in analytics.js"
```

Once resolved and review confidence > 0.9, step is marked complete.

---

### Step 6: Commit + Merge

The final iteration produces:

```
commit: Implemented analytics tracking and backend log API
```

If configured, CodexCockpit automatically opens a PR via GitHub API.

---

## 4. Monitoring in GUI

In the GUI:

* The active framework appears as a timeline in the **FrameworkView**.
* LogPanel streams the Codex outputs in real-time.
* Each step’s progress is color-coded (pending, active, complete, iterating).
* Developers can pause or inject manual edits mid-run.

---

## 5. Termination Criteria

CodexCockpit marks a feature as complete when:

* All framework steps have `status: complete`
* Validation hooks return true
* Git commit successful
* Optional test suite passes

---

## 6. Example Output Artifacts

| Artifact              | Path               | Description                  |
| --------------------- | ------------------ | ---------------------------- |
| `outline.yaml`        | `/backend/memory/` | Step-by-step feature outline |
| `plan.md`             | `/backend/memory/` | Development plan             |
| `scaffold_diff.patch` | `/backend/logs/`   | Generated code diff          |
| `review_report.md`    | `/backend/logs/`   | Self-review results          |
| `iteration_log.json`  | `/backend/logs/`   | Iteration metadata           |

---

## 7. Next Extensions

* Add multi-feature batch support
* Integrate real-time token and cost tracking
* Connect analytics telemetry to `codex-cockpit-desktop` metrics dashboard
* Build model-comparison mode (Codex vs Local LLM vs Cached)

---

Would you like me to continue by writing the next piece — `docs/MODEL_SUPPORT.md`, detailing how CodexCockpit abstracts between OpenAI, Ollama, LM Studio, and offline backends (including configuration examples, model capabilities table, and adapter interface design)?
