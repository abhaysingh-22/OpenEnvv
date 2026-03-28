# 🚀 Customer Support OpenEnv Environment

## 🎯 Goal

Build a **real-world AI evaluation environment** where agents simulate handling customer support tickets using a structured `step() / reset() / state()` API.

The system must produce **meaningful performance differences**:

* Perfect Agent → **~0.9–1.0**
* Imperfect Agent → **~0.4–0.7**
* Random Agent → **~0.0–0.3**

---

## 🧠 Project Overview

This environment simulates a **customer support operations system** where an AI agent must:

1. Understand a support ticket
2. Decide the correct action
3. Respond appropriately
4. Follow company policy
5. Maintain proper tone

---

## ⚙️ Core Environment API

### `reset()`

* Initializes a new task
* Loads ticket data
* Resets internal state

### `step(action)`

Returns:

```
observation, reward, done, info
```

* Applies agent action
* Calculates reward
* Updates state

### `state()`

* Returns full internal state (for debugging)

---

## 📊 Action Space

Agents can perform:

* `route_ticket`
* `reply_to_customer`
* `request_logs`
* `escalate`
* `request_more_info`

---

## 👁️ Observation Space

```json
{
  "ticket": {
    "message": "...",
    "category": "...",
    "history": "...",
    "sentiment": "..."
  },
  "step_count": 1,
  "pending_actions": []
}
```

---

## 🧪 Tasks

### 🟢 Easy

* Simple classification
* Clear intent
* 1–2 steps

---

### 🟡 Medium

* Policy-based decisions
* Requires reasoning
* 2–3 steps

---

### 🔴 Hard

* Multi-step workflow
* Ambiguous inputs
* Emotional tone handling
* Requires:

  * routing
  * investigation
  * response

---

## 💰 Reward System (IMPORTANT)

Rewards are **NOT binary**.

### Components:

* Routing accuracy → `±0.4`
* Response quality → `0 → +0.3`
* Tone quality → `0 → +0.2`
* Efficiency penalty → `-0.05 per step`

---

### Example:

```
Step Reward = routing + response + tone - penalty
```

Final score normalized:

```
0.0 → 1.0
```

---

## ❗ Critical Design Rules

### 1. Multi-step tasks required

Tasks must NOT finish in 1 step.

---

### 2. Include penalties

Agent must be punished for:

* wrong actions
* bad tone
* unnecessary steps

---

### 3. Deterministic grading

* Uses `answer_keys.json`
* Same input → same score

---

### 4. Reward shaping

* Gradual reward accumulation
* No instant 1.0 scoring

---

## 🤖 Agents (Testing Setup)

### ✅ Dummy Agent (Perfect)

* Always correct
* Score ≈ 1.0

---

### ⚠️ Imperfect Agent

* Sometimes wrong
* Mixed tone
* Score ≈ 0.4–0.7

---

### ❌ Random Agent

* Random actions
* Score ≈ 0.0–0.3

---

## 🧪 Baseline Script

Run:

```bash
python scripts/baseline.py
```

Expected Output:

```
Perfect Agent: ~0.95
Imperfect Agent: ~0.55
Random Agent: ~0.2
```

---

## 🧠 Development Workflow

### Step 1

Implement:

* models.py
* environment.py

---

### Step 2

Add:

* reward system
* multi-step logic

---

### Step 3

Test with:

* dummy agent
* imperfect agent
* random agent

---

### Step 4

Verify:

* score distribution exists
* hard task is actually hard

---

### Step 5

Then integrate OpenAI API

---

## ⚠️ Common Mistakes (Avoid)

❌ Binary reward (0 or 1 only)
❌ Tasks finishing in 1 step
❌ No penalty system
❌ All agents scoring same
❌ Hard task not actually hard

---

## 🧠 Key Philosophy

This is NOT:

* a chatbot
* a UI app
* a frontend project

This IS:
👉 an **AI evaluation environment**

---

## 🚀 Next Steps

* Improve reward shaping
* Add more realistic tickets
* Introduce ambiguity
* Integrate OpenAI agent
* Deploy via Docker + HF Spaces

---

## 🏁 Final Note

A good environment:

✔ differentiates between good vs bad agents
✔ provides meaningful feedback
✔ simulates real-world complexity

If everything scores **1.0**, your system is broken.

---
