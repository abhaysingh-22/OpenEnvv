# Customer Support Ticket Environment (OpenEnv)

A fully compliant [OpenEnv](https://github.com/meta-pytorch/OpenEnv) testbed simulating an interactive customer support helpdesk where an AI agent attempts to resolve customer issues by using tools (reply, send password reset, check logs, issue refund).

### Task Breakdown

We support 3 distinct difficulty tasks designed to push Frontier LLMs:

1. **Easy (`easy_ticket_1`)**: Password Reset Request. The agent must verify the customer's identity and correctly send a password reset loop using `send_password_reset` to the right email, without taking destructive actions.
2. **Medium (`medium_ticket_1`)**: Refund Request & Policy Check. The agent must successfully recognize a customer is past a 30-day refund window by requesting internal system logs `request_logs`. If the agent ignores policy and clicks `issue_refund`, it earns a massive ERROR penalty.
3. **Hard (`hard_ticket_1`)**: API Troubleshooting. The customer reports an unknown internal 500 API error. The agent must `request_logs`, find the underlying system stack trace, diagnose the problem, and provide the exact required fix (update to v2.1) without leaking internal code names.

---

### Project Structure

This project conforms strictly to the `meta-pytorch/OpenEnv` architecture.

```text
├── support_env/                 # Core Environment Package
│   ├── models.py                # Action, Observation, State extending openenv types
│   ├── client.py                # EnvClient Wrapper
│   └── server/
│       └── support_environment.py # Encapsulated Task & Grader Logic
├── server/                      # OpenEnv standardized entry point
│   └── app.py                   # FastAPI create_app wrapper
├── data/                        # Sample offline logs and references
├── skills/                      # Instruction sets for the LLM
├── openenv.yaml                 # OpenEnv Deployment Spec
├── pyproject.toml               # Package Definition
├── Dockerfile                   # Deployment container
└── inference.py                 # Multi-Agent Baseline Inference Engine
```

### Setup & Usage

**1. Install Dependencies**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e . uv 
uv lock
uv sync
```

**2. Run Locally With `openenv` CLI**
```bash
openenv validate  # Ensure everything respects the latest framework spec!
```

**3. Run Inference Benchmark**
Tests the environment utilizing 3 local scripted agents (Perfect, Imperfect, Random) and if an API key is present, tests the `MODEL_NAME` you provide against the system.

```bash
export OPENAI_API_KEY="sk-..."
export MODEL_NAME="gpt-4o-mini"
python inference.py
```

### Docker 

Built securely using `appuser` (non-root) on port 7860 to match standard Hugging Face Spaces rules.

```bash
docker build -t sst_openenv .
docker run -p 7860:7860 sst_openenv:latest
```
