# OpenEnv: Customer Support Ticket Environment

This OpenEnv implementation simulates a real-world **Customer Support Environment** where an AI agent can learn to manage, triage, and resolve support tickets.

## Real-World Simulation
This environment evaluates AI agents on processing genuine user support requests. It is structured around the `step()`, `reset()`, and `state()` API as defined by the OpenEnv spec. Agents must select the proper tool and arguments to move tasks forward. There are 3 tasks (Easy, Medium, Hard) representing increasingly difficult customer support scenarios.

## Tasks and Graders
- **Easy**: Password Reset Request. The agent identifies the user and sends a reset link.
- **Medium**: Refund Request. The agent must verify the purchase date against a 30-day refund policy and process or deny the refund accordingly.
- **Hard**: Technical Troubleshooting. A multi-step flow where the agent must first ask the user for system logs, parse the provided error code, and supply the correct resolution to close the ticket.

Graders track whether the agent successfully completes the task and provides a deterministic `0.0` - `1.0` score with partial progress signals and penalties for bad actions (e.g. issuing a refund outside policy limits).

## Observation & Action Spaces (Pydantic Typed)

### Observation Space
- `ticket_id` (str): Identifier.
- `user_name` / `user_email` (str): User profiling.
- `subject` / `body` (str): Content of the ticket.
- `history` (List[Dict]): The message trajectory so far.
- `system_data` (Dict): Internal data the agent can consult (e.g. account active state, purchase dates, internal known issues).

### Action Space
The agent responds by selecting a tool:
- `tool_name` (str): E.g. `reply_to_customer`, `send_password_reset`, `issue_refund`, `request_logs`, `close_ticket`.
- `tool_args` (Dict): The argument for the chosen tool (e.g. `{"content": "..."}`).

### Reward Space
- `value` (float): The final score (0.0 to 1.0).
- `is_complete` (bool): Whether the episode should terminate.
- `info` (str): Debug info for the taken action or penalty.

## Setup Instructions

### Prerequisites
- Python 3.10+
- OpenAI API Key

### Installation

```bash
git clone <repository>
cd OpenEnv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Baseline Script (Inference)
The baseline uses `gpt-4o-mini` via the `openai` Python client to interact with the environment and reproducible scores are calculated at the end.

```bash
export OPENAI_API_KEY="your-sk-key"
python scripts/baseline.py
```

### Hugging Face Space Deployment
The project is configured so that it can be dropped into a Docker-based Hugging Face Space. The `app.py` script starts a lightweight FastAPI server on port `7860` to comply with Spaces container health checks.

```bash
docker build -t openenv:latest .
docker run -p 7860:7860 openenv:latest
```
Access `http://localhost:7860/` to ensure the Space is running.
