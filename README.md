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

Each task represents a realistic customer support scenario. Tasks are designed to require **increasing amounts of reasoning** and **multi-step interactions**.

### Easy: Password Reset Request ⭐
**Objective:** Identify the user and initiate a password reset.

**Difficulty:** Straightforward single-step task with clear success criteria.
- User initializes with email
- Agent sends reset link via `send_password_reset` tool
- Agent closes ticket via `close_ticket` tool
- Expected score if completed correctly: **1.0**

### Medium: Refund Request Processing ⭐⭐
**Objective:** Evaluate refund eligibility based on company policy and process accordingly.

**Difficulty:** Requires policy knowledge and decision-making logic.
- User requests refund for a past purchase
- Agent must request purchase logs to verify purchase date
- Agent must apply the **30-day refund policy** rule
  - Within 30 days → approve refund via `issue_refund`
  - After 30 days → deny refund and explain policy
- Agent replies to customer with decision
- Expected score if completed correctly: **1.0**

### Hard: Technical Troubleshooting ⭐⭐⭐
**Objective:** Diagnose and resolve a technical issue through multi-step investigation.

**Difficulty:** Multi-turn conversation with error diagnosis and solution matching.
- User reports a technical error (e.g., connection timeout)
- Agent must request system logs via `request_logs` tool
- Agent receives error code from logs
- Agent must match error code to known issue in `system_data`
- Agent provides correct resolution via `reply_to_customer`
- Agent closes ticket
- Expected score if completed correctly: **1.0**

### Grading System
Each task has a **deterministic grader** that:
- Awards partial credit for intermediate steps (e.g., 0.33 for requesting logs, 1.0 for correct reply)
- Penalizes policy violations (e.g., approving refund outside policy)
- Provides **0.0–1.0 scores** with meaningful differentiation
- Tracks step progression and tool usage

## Observation & Action Spaces (Pydantic Typed)

### Observation Space: `Observation(Pydantic Model)`

```python
{
    "ticket_id": "easy_ticket_1",           # str: Unique identifier
    "user_name": "John Doe",                # str: Customer name
    "user_email": "john@example.com",       # str: Customer email
    "subject": "Password Reset",            # str: Ticket subject
    "body": "I need to reset my password",  # str: Issue description
    "history": [                            # List[Dict]: Conversation log
        {"role": "customer", "content": "...", "tool_used": null},
        {"role": "agent", "content": "...", "tool_used": "send_password_reset", "tool_args": {...}}
    ],
    "system_data": {                        # Dict: Backend knowledge base
        "purchase_date": "2024-01-15",
        "account_status": "active",
        "known_issues": {...}
    }
}
```

### Action Space: `Action(Pydantic Model)`

An agent responds by selecting a **tool** with corresponding arguments:

```python
{
    "tool_name": "send_password_reset",  # str: One of the available tools
    "tool_args": {                       # Dict: Arguments for the tool
        "email": "john@example.com"
    }
}
```

**Available Tools:**
- `send_password_reset(email: str)` → Initiate password reset
- `request_logs(user_id: str)` → Get system logs from user
- `issue_refund(amount: float, reason: str)` → Process refund
- `reply_to_customer(content: str)` → Send message to customer
- `close_ticket(resolution: str)` → Mark ticket as resolved

### Reward Space: `Reward(Pydantic Model)`

```python
{
    "value": 0.75,                       # float: Score [0.0, 1.0]
    "is_complete": False,                # bool: Episode termination flag
    "info": "Partial progress: sent password reset email"  # str: Debug info
}
```

**Reward Structure:**
- **Sparse/Partial Rewards:** Progress signals at each step (0.33, 0.75, 1.0)
- **Penalties:** Negative scores for policy violations or incorrect actions
- **Terminal Rewards:** Final score only awarded when `is_complete=True`

## Setup Instructions

### Prerequisites
- **Python 3.10+**
- **OpenAI API Key** (for running baseline/inference)
- **pip** or **conda** for dependency management

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
# Required: OpenAI API Configuration
OPENAI_API_KEY=sk-your-api-key-here
MODEL_NAME=gpt-4o-mini  # or gpt-4, gpt-4-turbo, etc.

# Optional: Custom API Endpoint
API_BASE_URL=https://api.openai.com/v1  # For custom endpoints (e.g., Azure)

# Optional: Hugging Face Integration
HF_TOKEN=hf_your-token-here
```

**For local testing**, you can also export variables:
```bash
export OPENAI_API_KEY="sk-..."
export MODEL_NAME="gpt-4o-mini"
```

### Running the Environment Locally

#### Run the Web Server
```bash
python app.py
# Server will start on http://localhost:7860
```

#### Run the Baseline Inference Script
```bash
python inference.py
# Expected output:
# ================================================================================
# INFERENCE SUMMARY
# ================================================================================
# 1. Password Reset Request    Score: 1.000  Steps: 2  Time: ~2s
# 2. Refund Request            Score: 1.000  Steps: 2  Time: ~1s
# 3. Technical Error           Score: 1.000  Steps: 3  Time: ~1s
# 
# ================================================================================
# TOTAL INFERENCE SCORE: 3.000 / 3
# AVERAGE SCORE: 1.000
# ================================================================================
```

#### Run Unit Tests
```bash
pytest tests/ -v
# Expected: 15/15 tests passing
```

### Baseline Scores

The baseline uses `gpt-4o-mini` to demonstrate environment functionality:

| Task | Difficulty | Expected Score | Notes |
|:-----|:----------:|:---------------:|:-----|
| Password Reset | Easy ⭐ | 1.000 | Single-step, straightforward |
| Refund Request | Medium ⭐⭐ | 1.000 | Policy-aware, multi-step |
| Tech Support | Hard ⭐⭐⭐ | 1.000 | Complex diagnosis required |
| **Average** | - | **1.000** | Perfect baseline on all tasks |

**Runtime:** ~3-4 seconds total (well under 20-minute limit)

## API Endpoints

The FastAPI web server exposes the following endpoints:

### `GET /`
Health check endpoint. Returns "OK" to confirm the server is running.
```bash
curl http://localhost:7860/
# Response: "OK"
```

### `POST /reset`
Resets the environment and returns initial observation for a new task.
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_ticket_1"}'
# Response: { "ticket_id": "easy_ticket_1", "user_name": "John Doe", ... }
```

### `POST /step`
Steps through an action and returns observation, reward, done flag, and info.
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "send_password_reset", "tool_args": {"email": "john@example.com"}}'
# Response: { "observation": {...}, "reward": 0.75, "done": false, "info": "..." }
```

### `GET /health`
Health check endpoint that returns HTTP 200 for container orchestration tools.
```bash
curl http://localhost:7860/health
# Response: 200 OK
```

## Project Structure

```
OpenEnv/
├── app.py                          # FastAPI web server (port 7860)
├── inference.py                    # Baseline inference script (CRITICAL)
├── Dockerfile                      # Docker container definition
├── openenv.yaml                    # OpenEnv metadata specification
├── requirements.txt                # Python dependencies
├── .env.example                    # Example environment configuration
├── README.md                       # This file
│
├── env/                            # Core environment module
│   ├── __init__.py
│   ├── environment.py              # Main SupportTicketEnv class
│   ├── models.py                   # Pydantic models (Observation, Action, Reward)
│   └── constants.py                # Configuration and constants
│
├── tasks/                          # Task definitions
│   ├── __init__.py
│   ├── base_task.py               # Abstract task base class
│   ├── easy.py                    # Easy task (password reset)
│   ├── medium.py                  # Medium task (refund request)
│   └── hard.py                    # Hard task (technical troubleshooting)
│
├── graders/                        # Reward/grading logic
│   ├── __init__.py
│   ├── base_grader.py             # Abstract grader base class
│   ├── support_grader.py          # SupportTicket grader implementation
│   └── rewards.py                  # Reward function definitions
│
├── agents/                         # Agent implementations (examples)
│   ├── __init__.py
│   ├── base_agent.py              # Abstract agent base class
│   ├── dummy_agent.py             # Random/dummy baseline agent
│   └── hf_agent.py                # Hugging Face model agent
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration and fixtures
│   ├── test_environment.py        # Environment tests
│   ├── test_graders.py            # Grader tests
│   ├── test_models.py             # Model tests
│   ├── test_rewards.py            # Reward tests
│   └── __pycache__/
│
├── data/                           # Static data files
│   ├── tickets_easy.json          # Easy task definitions
│   ├── tickets_medium.json        # Medium task definitions
│   ├── tickets_hard.json          # Hard task definitions
│   ├── company_policy.json        # Business rules (refund policy, etc.)
│   ├── answer_keys.json           # Grading reference answers
│   └── forbidden_phrases.txt      # Customer service guardrails
│
├── scripts/                        # Utility scripts
│   ├── baseline.py                # Legacy baseline script
│   └── run_env.py                 # Environment test script
│
├── config/                         # Configuration
│   └── settings.py                # Application settings
│
├── skills/                         # Skills documentation
│   └── SKILLS.md                  # Available skills documentation
│
└── docs/                           # Documentation
    ├── ARCHITECTURE.md            # System design
    ├── openenv.md                 # OpenEnv spec details
    └── SUBMISSION_CHECKLIST.md    # Pre-submission verification
```

## OpenEnv Specification Compliance

This environment fully implements the OpenEnv specification:

- ✅ **Typed Models:** Pydantic models for `Observation`, `Action`, `Reward`
- ✅ **Core Functions:** `step()`, `reset()`, `state()` 
- ✅ **YAML Metadata:** `openenv.yaml` with task definitions
- ✅ **Task Graders:** Deterministic scoring (0.0–1.0 range)
- ✅ **Environment Variables:** Support for `OPENAI_API_KEY`, `MODEL_NAME`, `API_BASE_URL`, `HF_TOKEN`
- ✅ **Reproducible Baseline:** `inference.py` produces consistent scores

**Validate compliance:**
```bash
openenv validate
```

## Contributing

To add new tasks or modify graders:

1. **Create a new task:** Extend `base_task.py` in the `tasks/` directory
2. **Implement a grader:** Extend `base_grader.py` in the `graders/` directory
3. **Add test coverage:** Create test file in `tests/`
4. **Update documentation:** Modify README and relevant docs

## License

This project is provided as-is for educational and research purposes.
