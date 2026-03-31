# 🎧 Customer Support Ticket Environment

> An OpenEnv-compliant, real-world AI agent evaluation environment simulating interactive customer support, where agents must resolve tickets using tools — graded on correctness, efficiency, and policy compliance.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-blue)](https://github.com/meta-pytorch/OpenEnv)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

---

## Motivation

Customer support is one of the most common real-world tasks where AI agents must demonstrate:

- **Tool selection** — choosing the right action from a constrained set
- **Policy reasoning** — applying company rules correctly (e.g., 30-day refund windows)
- **Information gathering** — knowing when to request data before acting
- **Judgment under uncertainty** — diagnosing ambiguous technical issues

Unlike toy environments, this testbed evaluates whether an agent can follow **multi-step workflows** with **realistic constraints**, producing scores that meaningfully differentiate between optimal, suboptimal, and random behavior.

---

## Environment Design

### Action Space

The agent selects from **5 discrete tools** at each step. Each tool has specific arguments and conditions:

| Tool | Arguments | When to Use | Reward |
|:-----|:----------|:------------|:-------|
| `send_password_reset` | `{"email": "user@example.com"}` | Account recovery tasks (Easy) | +0.9 (correct email) / −0.5 (wrong) |
| `request_logs` | `{}` | Technical issues, policy verification | +0.4 to +0.7 |
| `reply_to_customer` | `{"content": "message"}` | Communicating solutions or denials | +0.3 to +0.9 (content-dependent) |
| `issue_refund` | `{}` | **Only** within 30-day policy window | −0.5 + instant failure if outside policy |
| `close_ticket` | `{}` | Final step after resolution | +0.3 to +0.4 |

### Observation Space

Each observation is a `SupportObservation` (Pydantic model) containing:

| Field | Type | Description |
|:------|:-----|:------------|
| `ticket_id` | `str` | Unique ticket identifier (e.g., `TKT-1001`) |
| `user_name` | `str` | Customer name |
| `user_email` | `str` | Customer email (critical for password reset) |
| `subject` | `str` | Ticket subject line |
| `body` | `str` | Customer's initial message |
| `history` | `List[Dict]` | Chronological log of agent/user/system interactions |
| `system_data` | `Dict` | Internal data (purchase dates, error codes, known issues) |
| `done` | `bool` | Whether the episode has terminated |
| `reward` | `float` | Cumulative normalized score [0.0, 1.0] |
| `metadata` | `Dict` | Step-level grading info (e.g., `{"info": "Sent password reset (+0.9)"}`) |

### Reward Function

The reward function provides **dense, partial-credit signals** — not just sparse end-of-episode feedback:

```
step_reward = action_reward + tone_bonus - penalties
final_score = clamp(total_accumulated_reward / task_normalization, 0.0, 1.0)
```

**Reward components:**
- ✅ **Correct actions**: +0.3 to +0.9 per step (higher for critical actions)
- ✅ **Partial progress**: Each correct step contributes positively, even if the episode isn't complete
- ⚠️ **Repeated action penalty**: −0.3 for taking the same action twice
- ⚠️ **Efficiency penalty**: −0.1 per step beyond the minimum required
- ❌ **Wrong action penalty**: −0.5 and `wrong_action_count++`
- ❌ **Policy violation** (e.g., refund outside 30 days): −0.5 and `wrong_action_count += 3` (instant failure)
- 💀 **Auto-termination**: Episode stops at 3 wrong actions or 20 total steps

### Episode Boundaries

- `reset(task_id)` → initializes clean state, returns first observation
- `step(action)` → executes action, returns updated observation with reward
- Episode ends when: task completed, 3+ wrong actions, or 20 steps reached
- `state` property → returns current `SupportState` snapshot

---

## Tasks

### Easy ⭐ — Password Reset (`easy_ticket_1`)

**Scenario:** Customer "John Doe" (john@example.com) forgot their password and cannot log in.

**Optimal Workflow (2 steps):**
1. `send_password_reset(email: "john@example.com")` → +0.9
2. `close_ticket()` → +0.3

**What makes it easy:** Single-tool resolution, clear email in observation, no policy ambiguity.

**Common failures:** Wrong email address, unnecessary actions before reset.

---

### Medium ⭐⭐ — Refund Policy Check (`medium_ticket_1`)

**Scenario:** Customer "Alice Smith" requests a refund for a product purchased **45 days ago** — exceeding the 30-day refund policy.

**Optimal Workflow (2 steps):**
1. `request_logs()` → +0.4 (verifies purchase date against policy)
2. `reply_to_customer("...cannot refund...30-day policy...")` → +0.9

**What makes it medium:** Agent must check `system_data.days_since_purchase` (45) against `refund_policy_days` (30), then correctly **deny** the refund with policy justification. Using `issue_refund` causes instant failure.

**Trap:** An eager agent that issues a refund without checking policy gets `wrong_action_count += 3` → immediate episode termination with score near 0.

---

### Hard ⭐⭐⭐ — API Troubleshooting (`hard_ticket_1`)

**Scenario:** Customer "Bob Jones" reports their integration is broken — the `/process` endpoint returns HTTP 500 errors.

**Optimal Workflow (2 steps):**
1. `request_logs()` → +0.7 (retrieves error code ERR-99 and client version v2.0.5)
2. `reply_to_customer("...update client to v2.1...")` → +0.9

**What makes it hard:** Agent must:
- Request logs **first** (mandatory — skipping gets −0.5)
- Correctly diagnose ERR-99 from the stack trace
- Provide the exact fix ("update to v2.1") without leaking internal code names
- Balance information from `system_data.known_issues` with the log output

**Common failures:** Guessing a fix without checking logs, providing a generic "try again later" response, or leaking internal system details.

---

## Baseline Scores

Evaluated using `inference.py` with three scripted agents and an optional LLM agent:

### Multi-Agent Baseline (Scripted — No LLM Required)

| Agent | Easy ⭐ | Medium ⭐⭐ | Hard ⭐⭐⭐ | Average |
|:------|:------:|:---------:|:--------:|:-------:|
| 🟢 **Perfect** | 0.960 | 0.929 | 0.889 | **0.926** |
| 🟡 **Imperfect** | 0.640 | 0.643 | 0.556 | **0.613** |
| 🔴 **Random** | 0.128 | 0.000 | 0.000 | **0.043** |

### Key Observations

- ✅ **Score differentiation**: Perfect >> Imperfect >> Random across all tasks
- ✅ **Difficulty scaling**: Perfect agent scores decrease with difficulty (0.960 → 0.929 → 0.889)
- ✅ **No perfect scores**: Even the optimal agent doesn't reach 1.0 — the environment is genuinely challenging
- ✅ **Meaningful gradients**: Imperfect agent shows clear degradation (0.640 → 0.643 → 0.556)
- ✅ **Reward shaping**: Partial credit at every step, not just binary pass/fail

### LLM Agent (gpt-4.1-mini, when API key available)

| Task | Score | Steps | Agent Mode |
|:-----|:-----:|:-----:|:----------:|
| Easy ⭐ | 0.960 | 2 | LLM |
| Medium ⭐⭐ | 0.500 | 1 | LLM |
| Hard ⭐⭐⭐ | 0.889 | 2 | LLM |

The LLM excels at Easy and Hard but scores lower on Medium because it takes a shortcut (direct denial without first checking logs), demonstrating that the environment rewards **thoroughness**, not just correctness.

---

## Setup & Usage

### Prerequisites

- Python 3.10+
- Docker (for containerized deployment)

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run Inference

The inference script runs **both phases automatically** and works with or without an API key:

```bash
# With OpenAI API (LLM agent + scripted baselines)
export OPENAI_API_KEY="sk-..."
export MODEL_NAME="gpt-4.1-mini"
python inference.py

# Without API key (scripted baselines + deterministic fallback)
python inference.py
```

When no API key is provided, the script clearly indicates this and uses a scripted fallback agent — **it never crashes**.

### Validate

```bash
openenv validate
```

### Docker

```bash
docker build -t sst_openenv .
docker run -p 7860:7860 sst_openenv
```

The container runs as `appuser` (non-root) on port 7860, compatible with Hugging Face Spaces.

---

## Environment Variables

| Variable | Required | Default | Description |
|:---------|:--------:|:--------|:------------|
| `OPENAI_API_KEY` | No | — | OpenAI API key for LLM agent (Phase 2). Falls back to scripted agent if missing. |
| `API_BASE_URL` | No | — | Custom API endpoint (for proxies or alternative providers) |
| `MODEL_NAME` | No | `gpt-4.1-mini` | Model identifier for the OpenAI client |
| `HF_TOKEN` | No | — | Hugging Face token for Space deployment |

---

## Project Structure

```
├── support_env/                     # Core Environment Package
│   ├── __init__.py                  # Package exports
│   ├── models.py                    # SupportAction, SupportObservation, SupportState (Pydantic)
│   ├── client.py                    # EnvClient wrapper for remote interaction
│   └── server/
│       ├── app.py                   # FastAPI create_app (openenv standard)
│       └── support_environment.py   # Environment class with step/reset/state + grading
├── server/
│   └── app.py                       # Uvicorn entry point (imports support_env.server.app)
├── data/                            # Reference data (tickets, policies, answer keys)
├── skills/
│   └── SKILLS.md                    # LLM agent instruction set (570 lines)
├── tests/                           # Pytest suite (environment, graders, models, rewards)
├── openenv.yaml                     # OpenEnv deployment specification
├── inference.py                     # Multi-agent evaluation engine (Phase 1 + Phase 2)
├── pyproject.toml                   # Package definition
├── Dockerfile                       # Production container
└── requirements.txt                 # Pip dependencies
```

---

## Technical Highlights

- **Full OpenEnv Spec Compliance**: Typed Pydantic models, `step()`/`reset()`/`state()` API, `openenv.yaml` metadata
- **Dense Reward Shaping**: Every step produces a reward signal — not just binary end-of-episode scoring
- **Multi-Agent Evaluation**: 4 agent types (Perfect, Imperfect, Random, LLM) demonstrate scoring validity
- **Graceful Degradation**: Runs correctly with or without OpenAI API key
- **SKILLS.md Integration**: 570-line instruction manual guides the LLM agent through optimal workflows
- **Production-Ready Container**: Non-root user, healthcheck, optimised image size (~380MB)
