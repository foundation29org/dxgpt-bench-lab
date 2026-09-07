# Work Routing

How to decide who handles what.

## Routing Table

| Work Type | Route To | Examples |
|-----------|----------|----------|
| Dataset profiling and cleanup | Bishop | Schema drift, duplicates, prompt leakage, language distribution, preprocessing risks |
| Clinical validity review | Lambert | Unsafe labels, diagnostic ambiguity, symptom phrasing, medically misleading examples |
| Evaluation pipeline and metrics | Dallas | Prompt flow, translation steps, scoring logic, benchmark methodology |
| Testing and adversarial cases | Parker | Edge cases, robustness checks, failure modes, benchmark QA |
| Scope, prioritization, review | Ripley | Trade-offs, final recommendations, reviewer gate, synthesis |
| Session logging | Scribe | Automatic — never needs routing |
| Work monitoring | Ralph | Backlog checks, issue watch, keep-alive execution |

## Issue Routing

| Label | Action | Who |
|-------|--------|-----|
| `squad` | Triage: analyze issue, evaluate @copilot fit, assign `squad:{member}` label | Lead |
| `squad:{name}` | Pick up issue and complete the work | Named member |

### How Issue Assignment Works

1. When a GitHub issue gets the `squad` label, Ripley triages it and assigns the primary `squad:{member}` label.
2. Bishop owns data curation and dataset hygiene issues.
3. Dallas owns evaluation logic, pipeline wiring, and metric correctness issues.
4. Lambert owns clinical safety and label quality issues.
5. Parker owns testing, reproducibility, and adversarial benchmark issues.
6. The `squad` label is the inbox for untriaged work.

## Rules

1. **Eager by default** — spawn all agents who could usefully start work, including anticipatory downstream work.
2. **Scribe always runs** after substantial work, always as `mode: "background"`. Never blocks.
3. **Quick facts → coordinator answers directly.** Don't spawn an agent for "what port does the server run on?"
4. **When two agents could handle it**, pick the one whose domain is the primary concern.
5. **"Team, ..." → fan-out.** Spawn all relevant agents in parallel as `mode: "background"`.
6. **Anticipate downstream work.** If a feature is being built, spawn the tester to write test cases from requirements simultaneously.
7. **Issue-labeled work** — when a `squad:{member}` label is applied to an issue, route to that member. Ripley handles all `squad` (base label) triage.
8. **Evaluation integrity first** — dataset leakage, language contamination, and medically unsafe labels outrank metric tuning.
