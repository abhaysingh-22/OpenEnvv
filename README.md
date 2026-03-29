# OpenEnv: Customer Support Ticket Environment

A production-ready **OpenEnv implementation** for customer support ticket resolution. This environment simulates a real-world support operation where AI agents learn to triage, prioritize, and resolve customer tickets using domain-specific tools.

## Motivation & Real-World Utility

Customer support is a multi-billion dollar industry with high operational costs. Automating ticket handling can:
- **Reduce response times** from hours/days to minutes
- **Improve resolution rates** by applying consistent policies
- **Lower operational costs** by handling routine requests automatically
- **Enable scaling** without proportional increase in support staff

This environment provides a realistic benchmark for evaluating agent capabilities on **multi-step reasoning**, **policy compliance**, and **customer communication**.

## Environment Overview

This environment is structured around the OpenEnv spec (`step()`, `reset()`, `state()`). Agents interact with support tickets by selecting appropriate tools and providing arguments. The environment provides:

- **Typed Pydantic models** for observations, actions, and rewards
- **3 difficulty levels** of tasks with deterministic graders
- **Realistic reward signals** with partial progress tracking
- **Tool-based action interface** (similar to ReAct/function calling)
- **Policy-aware evaluation** (e.g., 30-day refund policy enforcement)

## Tasks & Difficulty Levels

Each task represents a realistic customer support scenario with increasing reasoning requirements.

### Easy: Password Reset Request ⭐
**Objective:** Identify the user and initiate a password reset.

- User initializes with email
- Agent sends reset link via `send_password_reset` tool
- Agent closes ticket via `close_ticket` tool
- Expected score if completed correctly: **1.0**

### Medium: Refund Request Processing ⭐⭐
**Objective:** Evaluate refund eligibility based on company policy and process accordingly.

- User requests refund for a past purchase
- Agent must check purchase date against the **30-day refund policy**
  - Within 30 days → approve refund via `issue_refund`
  - After 30 days → deny refund and explain policy
- Agent replies to customer with decision
- Expected score if completed correctly: **1.0**

### Hard: Technical Troubleshooting ⭐⭐⭐
**Objective:** Diagnose and resolve a technical issue through multi-step investigation.

- User reports a technical error (API 500)
- Agent must request system logs via `request_logs` tool
- Agent receives error code (ERR-99) from logs
- Agent must match error code to known fix (update client to v2.1)
- Agent provides correct resolution via `reply_to_customer`
- Expected score if completed correctly: **1.0**

### Grading System
Each task has a **deterministic grader** that:
- Awards partial credit for intermediate steps
- Penalizes policy violations and repeated actions
- Provides **0.0–1.0 scores** with meaningful differentiation

## Observation & Action Spaces (Pydantic Typed)

### Observation Space

```python
{
    "ticket_id": "easy_ticket_1",
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "subject": "Password Reset",
    "body": "I need to reset my password",
    "history": [
        {"role": "customer", "content": "..."},
        {"role": "agent", "content": "...", "tool_used": "send_password_reset"}
    ],
    "system_data": {
        "purchase_date": "2024-01-15",
        "account_status": "active",
        "known_issues": {...}
    }
}
```

### Action Space

```python
{
    "tool_name": "send_password_reset",
    "tool_args": {"email": "john@example.com"}
}
```

**Available Tools:**
- `send_password_reset(email)` — Initiate password reset
- `request_logs()` — Get system/diagnostic logs
- `issue_refund(amount, reason)` — Process refund
- `reply_to_customer(content)` — Send message to customer
- `close_ticket()` — Mark ticket as resolved

### Reward Space

```python
{
    "value": 0.75,
    "is_complete": false,
    "info": "Sent password reset (+0.9)"
}
```

**Reward structure:** Partial rewards at each step (0.3–0.9), penalties for wrong/repeated actions (-0.3 to -0.5), normalized final score ∈ [0.0, 1.0].

## Setup Instructions

### Prerequisites
- **Python 3.10+**
- **OpenAI API Key** (for LLM-based inference; works without it via scripted fallback)
- **pip** for dependency management

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/abhaysingh-22/OpenEnvv.git
cd OpenEnv
```

#### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=sk-your-api-key-here
MODEL_NAME=gpt-4.1-mini
API_BASE_URL=                           # optional custom endpoint
HF_TOKEN=hf_your-token-here            # optional for HF Spaces
```

### Running the Environment

#### Start the Web Server
```bash
python app.py
# Server starts on http://localhost:7860
```

#### Run the Baseline Inference Script
```bash
python inference.py
```

#### Run Unit Tests
```bash
pytest tests/ -v
```

### Baseline Scores

| Task | Difficulty | Expected Score |
|:-----|:----------:|:-------------:|
| Password Reset | Easy ⭐ | 1.000 |
| Refund Request | Medium ⭐⭐ | 1.000 |
| Tech Support | Hard ⭐⭐⭐ | 1.000 |
| **Average** | - | **1.000** |

Runtime: ~3-4 seconds total (well under the 20-minute limit).

## API Endpoints

### `GET /`
Health check. Returns 200 to confirm the server is running.

### `GET /health`
Detailed health status including credential configuration.

### `GET /reset`
Simple reset confirmation (for HF Spaces ping validation).

### `POST /reset`
Initialize a new episode for a given task.
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_ticket_1"}'
```

### `POST /step`
Execute one action and return (observation, reward, done, info).
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "send_password_reset", "tool_args": {"email": "john@example.com"}}'
```

### `GET /state`
Return the current environment state snapshot.

### `GET /info`
Environment metadata and available endpoints.

## Project Structure

```
OpenEnv/
├── app.py                  # FastAPI server (port 7860)
├── inference.py            # Baseline inference script
├── Dockerfile              # Container definition
├── openenv.yaml            # OpenEnv metadata spec
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment config
├── README.md               # This file
│
├── env/                    # Core environment module
│   ├── __init__.py
│   ├── environment.py      # Main Environment class (step/reset/state)
│   ├── models.py           # Pydantic models (Observation, Action, Reward)
│   └── constants.py        # Configuration constants
│
├── tasks/                  # Task definitions
│   ├── __init__.py
│   ├── base_task.py        # Abstract task base class
│   ├── easy.py             # Easy: password reset
│   ├── medium.py           # Medium: refund request
│   └── hard.py             # Hard: technical troubleshooting
│
├── graders/                # Reward/grading logic
│   ├── __init__.py
│   ├── base_grader.py      # Abstract grader base class
│   ├── support_grader.py   # Deterministic grader implementation
│   └── rewards.py          # Reward accumulator
│
├── data/                   # Static data files
│   ├── tickets_easy.json
│   ├── tickets_medium.json
│   ├── tickets_hard.json
│   ├── company_policy.json
│   ├── answer_keys.json
│   └── forbidden_phrases.txt
│
├── skills/                 # Agent instruction document
│   └── SKILLS.md           # Comprehensive agent guidelines
│
├── tests/                  # Test suite
│   ├── conftest.py
│   ├── test_environment.py
│   ├── test_graders.py
│   ├── test_models.py
│   └── test_rewards.py
│
└── scripts/                # Utility scripts
    ├── baseline.py
    └── validate_scoring.py
```

## OpenEnv Specification Compliance

- ✅ **Typed Models:** Pydantic `Observation`, `Action`, `Reward`
- ✅ **Core Functions:** `step()`, `reset()`, `state()`
- ✅ **YAML Metadata:** `openenv.yaml`
- ✅ **Task Graders:** Deterministic scoring (0.0–1.0)
- ✅ **Environment Variables:** `OPENAI_API_KEY`, `MODEL_NAME`, `API_BASE_URL`, `HF_TOKEN`
- ✅ **Reproducible Baseline:** `inference.py` produces consistent scores
- ✅ **Skills Integration:** `SKILLS.md` loaded and injected into LLM prompts

## License

This project is provided as-is for educational and research purposes.
