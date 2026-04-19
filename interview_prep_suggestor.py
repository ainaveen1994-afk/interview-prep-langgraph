# =============================================================================

# Interview Prep Suggester -- A LangGraph Learning Project

# =============================================================================
# WHAT THIS DOES:
# A user enters their interview role and preparation level
# (e.g. "I have a senior backend interview tomorrow and feel underprepared").
# The system runs 3 suggestion engines in PARALLEL:
# - Technical topics
# - Behavioral stories
# - Confidence habits
# Then a decision node chooses:
# - QUICK PREP (1 hour)
# - DEEP PREP (3 hours)
# =============================================================================
import sys
import operator
import json
from typing import Annotated

from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

# =============================================================================

# STATE

# =============================================================================

class InterviewPrepState(BaseModel):
    user_input: str = ""
    technical_suggestion: str = ""
    behavioral_suggestion: str = ""
    confidence_suggestion: str = ""
    needs_deep_prep: bool = False
    prep_reason: str = ""
    final_plan: str = ""
    messages: Annotated[list, operator.add] = []

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# =============================================================================

# NODES

# =============================================================================

def understand_context(state: InterviewPrepState) -> dict:
    response = llm.invoke(
    f"You are an interview coach. "
    f"A user says: '{state.user_input}'. "
    f"Acknowledge their situation briefly in 1-2 sentences. "
    f"Then classify urgency as LOW, MEDIUM, or HIGH in one line like: Urgency: HIGH"
    )
    return {
    "messages": [f"[understand_context] {response.content}"]
    }

def suggest_technical(state: InterviewPrepState) -> dict:
    response = llm.invoke(
    f"You are a senior technical interviewer. "
    f"The user says: '{state.user_input}'. "
    f"Suggest 3-5 high-impact technical topics to review "
    f"(data structures, system design, etc). Keep it concise."
    )
    return {
    "technical_suggestion": response.content,
    "messages": ["[suggest_technical] Done"]
    }

def suggest_behavioral(state: InterviewPrepState) -> dict:
    response = llm.invoke(
    f"You are a behavioral interview coach. "
    f"The user says: '{state.user_input}'. "
    f"Suggest 3-4 strong behavioral story prompts using the STAR method."
    )
    return {
    "behavioral_suggestion": response.content,
    "messages": ["[suggest_behavioral] Done"]
    }

def suggest_confidence(state: InterviewPrepState) -> dict:
    response = llm.invoke(
    f"You are a mindset coach. "
    f"The user says: '{state.user_input}'. "
    f"Suggest 3 quick confidence-building habits before the interview."
    )
    return {
    "confidence_suggestion": response.content,
    "messages": ["[suggest_confidence] Done"]
    }

def pick_prep_strategy(state: InterviewPrepState) -> dict:
    response = llm.invoke(
    f"You are a decision system. The user says: '{state.user_input}'.\n\n"
    f"TECHNICAL:\n{state.technical_suggestion}\n\n"
    f"BEHAVIORAL:\n{state.behavioral_suggestion}\n\n"
    f"CONFIDENCE:\n{state.confidence_suggestion}\n\n"
    f"Decide if they need QUICK PREP (1 hour) or DEEP PREP (3 hours).\n\n"
    f"Reply ONLY in JSON:\n"
    f'{{"needs_deep_prep": true/false, "reason": "one sentence"}}'
    )

    try:
        result = json.loads(response.content)
        needs_deep = result["needs_deep_prep"]
        reason = result["reason"]
    except:
        needs_deep = False
        reason = "Defaulted to quick prep."

    return {
        "needs_deep_prep": needs_deep,
        "prep_reason": reason,
        "messages": [f"[pick_prep_strategy] deep_prep={needs_deep}"]
    }


def quick_prep(state: InterviewPrepState) -> dict:
    response = llm.invoke(
    f"You are an interview coach. The user says: '{state.user_input}'.\n\n"
    f"Create a 1-HOUR focused prep plan covering ONLY top 3 gaps.\n\n"
    f"TECHNICAL: {state.technical_suggestion}\n"
    f"BEHAVIORAL: {state.behavioral_suggestion}\n"
    f"CONFIDENCE: {state.confidence_suggestion}\n\n"
    f"Format as a simple step-by-step checklist."
    )


    return {
        "final_plan": f"QUICK PREP PLAN (1 Hour)\n{'='*45}\n{response.content}",
        "messages": ["[quick_prep] Generated quick prep"]
    }


def deep_prep(state: InterviewPrepState) -> dict:
    response = llm.invoke(
    f"You are an expert interview coach. The user says: '{state.user_input}'.\n\n"
    f"Create a structured 3-HOUR prep plan.\n\n"
    f"Include:\n"
    f"- Technical block\n"
    f"- Behavioral block\n"
    f"- Confidence block\n\n"
    f"Use time slots and step-by-step instructions.\n\n"
    f"TECHNICAL: {state.technical_suggestion}\n"
    f"BEHAVIORAL: {state.behavioral_suggestion}\n"
    f"CONFIDENCE: {state.confidence_suggestion}"
    )

    return {
        "final_plan": f"DEEP PREP PLAN (3 Hours)\n{'='*45}\n{response.content}",
        "messages": ["[deep_prep] Generated deep prep"]
    }

def route_after_decision(state: InterviewPrepState) -> str:
    if state.needs_deep_prep:
        return "deep"
    else:
        return "quick"
  
# =============================================================================

# GRAPH

# =============================================================================

graph = StateGraph(InterviewPrepState)

graph.add_node("understand_context", understand_context)
graph.add_node("suggest_technical", suggest_technical)
graph.add_node("suggest_behavioral", suggest_behavioral)
graph.add_node("suggest_confidence", suggest_confidence)

graph.add_node("pick_prep_strategy", pick_prep_strategy)
graph.add_node("quick_prep", quick_prep)
graph.add_node("deep_prep", deep_prep)

graph.add_edge(START, "understand_context")

graph.add_edge("understand_context", "suggest_technical")
graph.add_edge("understand_context", "suggest_behavioral")
graph.add_edge("understand_context", "suggest_confidence")

graph.add_edge("suggest_technical", "pick_prep_strategy")
graph.add_edge("suggest_behavioral", "pick_prep_strategy")
graph.add_edge("suggest_confidence", "pick_prep_strategy")

graph.add_conditional_edges(
"pick_prep_strategy",
route_after_decision,
{
"quick": "quick_prep",
"deep": "deep_prep",
}
)

graph.add_edge("quick_prep", END)
graph.add_edge("deep_prep", END)

app = graph.compile()

# =============================================================================

# RUNNER

# =============================================================================

def run_wellness_check(interviewsuggestion: str):
    print("=" * 55)
    print("  MENTAL WELLNESS PRACTICE SUGGESTER")
    print(f"  You said: \"{interviewsuggestion}\"")
    print("=" * 55)

    result = app.invoke({
        "user_input": interviewsuggestion,
        "messages": [],
    })

    print("\n" + "=" * 55)
    print("   YOUR PREP PLAN")
    print("=" * 55)
    print(f"\n{result['final_plan']}")

    print("\n" + "-" * 55)
    print("  MESSAGE LOG")
    print("-" * 55)
    for msg in result["messages"]:
        print(f"  {msg}")

    return result


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  INTERVIEW PREP SUGGESTER")
    print("=" * 55)
    print("\n  Tell me your interview situation")
    print("  Type 'quit' to exit.\n")

    while True:
        interviewsuggestion = input("   Your situation ? > ").strip()

        if interviewsuggestion.lower() in ("quit", "exit", "q"):
            print("\n  Take care of yourself. Goodbye!\n")
            break

        if not interviewsuggestion:
            continue

        run_wellness_check(interviewsuggestion)
        print("\n")
       