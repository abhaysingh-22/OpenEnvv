# 🚀 FINAL REFACTOR PROMPT (FOR COPILOT)

You are refactoring an OpenEnv-based customer support environment.

⚠️ IMPORTANT:

* DO NOT overengineer
* DO NOT add unnecessary abstractions
* DO NOT increase code size significantly
* Focus ONLY on fixing scoring logic and agent differentiation

---

# 🎯 OBJECTIVE

Fix the environment so that:

* Perfect Agent > Imperfect Agent > Random Agent
* Scores are clearly separated
* Reward system is simple, consistent, and deterministic

---

# ❗ CURRENT PROBLEMS TO FIX

1. Perfect and Imperfect agents get similar scores
2. Random agent sometimes gets high score
3. Easy task scores too low for perfect agent
4. Reward system inconsistent (step vs cumulative confusion)
5. Tasks sometimes complete too easily (2 steps only)

---

# ✅ REQUIRED FIXES (STRICT)

## 1. SIMPLIFY REWARD SYSTEM

Use ONLY these components:

* Correct action → +0.4
* Correct response → +0.3
* Good tone → +0.2
* Efficiency penalty → -0.1 per extra step
* Wrong action → -0.5

👉 DO NOT add more reward types

---

## 2. REMOVE REWARD CONFUSION

* Maintain ONLY one variable: `total_reward`
* Do NOT mix:

  * step reward
  * cumulative reward
  * average reward

Final score must be:

```python
final_score = max(0.0, min(1.0, total_reward / MAX_REWARD))
```

---

## 3. ADD BASIC ACTION VALIDATION (MINIMAL)

Ensure correct sequence in hard task:

* Step 1: request_logs
* Step 2: reply_to_customer
* Step 3: close_ticket

If wrong order:

```python
reward -= 0.5
```

👉 Keep this logic SIMPLE (no complex state machines)

---

## 4. PREVENT RANDOM SUCCESS

If agent makes too many wrong actions:

```python
if wrong_action_count >= 3:
    done = True
```

---

## 5. PREVENT REPEATED ACTION SPAM

If same action repeated:

```python
reward -= 0.3
```

---

## 6. ENSURE MULTI-STEP TASKS

* Easy → minimum 2 steps
* Medium → minimum 2–3 steps
* Hard → minimum 3 steps

DO NOT allow 1-step completion

---

## 7. KEEP CODE CLEAN

* Modify ONLY:

  * environment.py
  * rewards.py (if needed)
* DO NOT touch project structure
* DO NOT add new files

---

# 🎯 EXPECTED OUTPUT AFTER FIX

| Agent Type | Expected Score Range |
| ---------- | -------------------- |
| Perfect    | 0.8 – 1.0            |
| Imperfect  | 0.4 – 0.7            |
| Random     | 0.0 – 0.3            |

---

# 🧠 FINAL RULE

This is a MOCK environment.

👉 Keep logic:

* simple
* deterministic
* readable

❌ NO complex AI logic
❌ NO unnecessary abstractions
❌ NO long code

---

# 🚀 TASK

Refactor the environment to meet ALL conditions above.

Ensure:

* scoring is correct
* agents are distinguishable
* code remains simple and clean

Return updated code only.
