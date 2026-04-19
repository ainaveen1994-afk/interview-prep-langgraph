# 🧠 Interview Prep Suggester — Architecture

## 📌 Overview

This project is a **LangGraph-based AI workflow** that generates a personalized interview preparation plan based on a user’s input.

The system:

* Understands user context (role + preparedness)
* Runs **3 expert suggestion engines in parallel**
* Uses a **decision node** to choose prep depth
* Outputs a **Quick (1-hour)** or **Deep (3-hour)** plan

---

## 🏗️ High-Level Architecture

```
            START
              |
      understand_context
              |
    -------------------------
    |          |           |
suggest_technical  suggest_behavioral  suggest_confidence
    |          |           |
    -----------|-----------
              |
      pick_prep_strategy
              |
        (conditional)
         /        \
     quick       deep
      |            |
 quick_prep   deep_prep
      |            |
      END          END
```

---

## 🧩 Core Components

### 1. State Management

The system uses a shared state object:

```python
class InterviewPrepState(BaseModel):
```

#### Fields:

* `user_input` → raw user input
* `technical_suggestion` → DSA/system design topics
* `behavioral_suggestion` → STAR-based prompts
* `confidence_suggestion` → mindset tips
* `needs_deep_prep` → routing decision (bool)
* `prep_reason` → explanation for decision
* `final_plan` → final output
* `messages` → execution trace/log

👉 This state flows through all nodes.

---

### 2. LLM Layer

All nodes use:

```python
ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
```

Each node has a **specialized prompt role**:

* Interview coach
* Technical interviewer
* Behavioral coach
* Confidence coach
* Decision system

---

### 3. Nodes (Processing Units)

#### 🔹 `understand_context`

* Acknowledges user input
* Extracts urgency level (LOW/MEDIUM/HIGH)

---

#### 🔹 `suggest_technical`

* Suggests key technical topics
* Focus: DSA, system design

---

#### 🔹 `suggest_behavioral`

* Generates STAR-based story prompts
* Focus: past achievements

---

#### 🔹 `suggest_confidence`

* Provides confidence-building habits
* Focus: mindset, breathing, posture

---

### ⚡ Parallel Execution (Fan-Out)

These three nodes run **simultaneously**:

* technical
* behavioral
* confidence

---

### 🔹 `pick_prep_strategy`

* Aggregates all suggestions
* Decides:

  * Quick Prep (1 hour)
  * Deep Prep (3 hours)
* Returns JSON:

```json
{
  "needs_deep_prep": true/false,
  "reason": "..."
}
```

---

### 🔀 Conditional Routing

```python
route_after_decision()
```

* `True` → deep_prep
* `False` → quick_prep

---

### 🔹 `quick_prep`

* Generates **1-hour focused plan**
* Covers top 3 gaps only

---

### 🔹 `deep_prep`

* Generates **3-hour structured plan**
* Includes:

  * Technical block
  * Behavioral block
  * Confidence block

---

## 🔄 Execution Flow

1. User provides input
2. Context is understood
3. 3 expert suggestions run in parallel
4. Results are merged
5. Decision node selects prep depth
6. Final plan is generated

---

## 🧠 Key LangGraph Concepts Used

| Concept            | Usage                            |
| ------------------ | -------------------------------- |
| State              | Shared data across nodes         |
| Nodes              | Independent functions            |
| Parallel Execution | Multiple suggestion engines      |
| Fan-in             | Merge outputs into decision node |
| Conditional Edges  | Route based on decision          |
| Graph Compilation  | Convert to runnable app          |

---

## 🖥️ Runtime (CLI)

The script runs in a loop:

```
Your situation ? >
```

Example input:

```
"I have a backend interview tomorrow and feel underprepared"
```

Output:

* Personalized prep plan
* Execution log

---

## ⚠️ Known Improvements

* Urgency extraction not explicitly stored in state
* Minor naming inconsistency (`run_wellness_check`)
* Could add:

  * Resume-based personalization
  * Company-specific prep
  * Mock interview simulation

---

## 🚀 Future Enhancements

* 🌐 Web UI (Streamlit)
* 📊 Readiness scoring system
* 🎯 Role-specific pipelines
* 🧪 Unit testing for nodes

---

## 📦 Dependencies

* langgraph
* langchain-openai
* python-dotenv
* pydantic

---

## 🧾 Summary

This project demonstrates a **modular, scalable AI workflow** using LangGraph, combining:

* Parallel reasoning
* Decision-making
* Personalized output generation

---
