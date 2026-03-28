# OpenEnv Specification & Requirements

## Problem Statement

Build a complete, real-world OpenEnv environment that an AI agent can learn from through the standard `step()` / `reset()` / `state()` API.

---

## Key Requirements at a Glance

- ✅ Must simulate a **real-world task** (not games or toys)
- ✅ Implement **full OpenEnv spec**: typed models, `step()`/`reset()`/`state()`, `openenv.yaml`
- ✅ **Minimum 3 tasks** with agent graders (easy → medium → hard, scores 0.0–1.0)
- ✅ **Meaningful reward function** with partial progress signals
- ✅ **Baseline inference script** with reproducible scores
- ✅ **Deploy to Hugging Face Spaces** + working `Dockerfile`
- ✅ **README** with environment description, action/observation spaces, setup instructions

---

## Detail Requirements

### Functional Requirements

#### Real-world Task Simulation

The environment must simulate a task humans actually do. **Not games, not toys.**

**Examples:**
- Email triage
- Code review
- Data cleaning
- Scheduling
- Customer support
- Content moderation

#### OpenEnv Spec Compliance

Implement the full OpenEnv interface:
- Typed `Observation`, `Action`, and `Reward` Pydantic models
- `step(action)` → returns `observation`, `reward`, `done`, `info`
- `reset()` → returns initial observation
- `state()` → returns current state
- `openenv.yaml` with metadata
- Tested via `openenv validate`

#### Minimum 3 Tasks with Agent Graders

Each task defines a concrete objective an agent must accomplish, with a programmatic grader that scores performance (0.0–1.0).

**Requirements:**
- Tasks should range from **easy** → **medium** → **hard**
- Graders must have **clear, deterministic success/failure criteria**

#### Meaningful Reward Function

The reward function should:
- Provide signal over the **full trajectory** (not just binary end-of-episode)
- **Reward partial progress** toward task completion
- **Penalize undesirable behavior** (e.g., infinite loops, destructive actions)

#### Baseline Inference Script

The baseline script should:
- Use the **OpenAI API client** to run a model against the environment
- Read API credentials from **environment variables** (`OPENAI_API_KEY`)
- Produce **reproducible baseline scores** on all 3 tasks

---

### Non-Functional Requirements

#### Deploys to a Hugging Face Space

Environment must run as a **containerized HF Space** tagged with `openenv`.

#### Containerized Execution

Must include a **working `Dockerfile`**. The environment should start cleanly with:
```bash
docker build && docker run
```

#### Documentation

**README** must include:
- Environment description and motivation
- Action and observation space definitions
- Task descriptions with expected difficulty
- Setup and usage instructions
- Baseline scores

---

## Scoring Breakdown

### Real-world Utility (30%)

| Score | Description |
|:-----:|-------------|
| **0–5** | Toy/artificial problem with no practical application |
| **6–15** | Valid domain but shallow modeling of the real task |
| **16–25** | Good domain modeling, would be useful for agent evaluation |
| **26–30** | **Excellent** — fills a real gap, immediate value for the RL/agent community |

### Task & Grader Quality (25%)

- ✓ 3+ tasks with difficulty range?
- ✓ Graders produce scores between 0.0–1.0?
- ✓ Graders deterministic and reproducible?
- ✓ Hard task genuinely challenges frontier models?

### Environment Design (20%)

- ✓ `reset()` produces clean state?
- ✓ Action/observation types well-designed and documented?
- ✓ Reward function provides useful varying signal (not just sparse)?
- ✓ Episode boundaries sensible?

### Code Quality & Spec Compliance (15%)

- ✓ `openenv validate` passes?
- ✓ `docker build && docker run` works?
- ✓ HF Space deploys and responds?
- ✓ Baseline script runs and reproduces scores?

### Creativity & Novelty (10%)

- ✓ Domain we haven't seen in OpenEnv before?
- ✓ Reward design has interesting properties?
- ✓ Clever mechanics that make the environment engaging?

---

## Evaluation Criteria Summary

| Parameter | Weight | Description |
|:----------|:------:|:-----------|
| **Real-world utility** | 30% | Does the environment model a genuine task? Would someone actually use this to train or evaluate agents? |
| **Task & grader quality** | 25% | Are tasks well-defined with clear objectives? Do graders accurately and fairly measure success? Meaningful difficulty progression? |
| **Environment design** | 20% | Clean state management, sensible action/observation spaces, good reward shaping, proper episode boundaries. |
| **Code quality & spec compliance** | 15% | Follows OpenEnv spec, clean project structure, typed models, documented, tested, Dockerfile works. |
| **Creativity & novelty** | 10% | Novel problem domain, interesting mechanics, clever reward design, original approach. |
