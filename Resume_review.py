# =============================================================================

# Resume vs Job Description Matcher -- LangGraph Project

# =============================================================================

import sys
import operator
import json
import os
from typing import Annotated

from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from PyPDF2 import PdfReader
import docx

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

# =============================================================================

# STATE

# =============================================================================

class ResumeMatchState(BaseModel):
    job_description: str = ""   # initially file path → later replaced with text
    resume_text: str = ""       # initially file path → later replaced with text

    skill_match: str = ""
    experience_match: str = ""
    keyword_match: str = ""

    match_score: float = 0.0
    missing_skills: str = ""
    decision: str = ""
    final_report: str = ""

    messages: Annotated[list, operator.add] = []


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# =============================================================================

# HELPERS

# =============================================================================

def extract_text(file_path: str) -> str:
    try:
        if file_path.endswith(".pdf"):
            reader = PdfReader(file_path)
            return " ".join([p.extract_text() or "" for p in reader.pages])

        elif file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])

        else:
            return ""

    except Exception as e:
        return f"Error reading file: {e}"

# =============================================================================

# NODES

# =============================================================================

def load_documents(state: ResumeMatchState) -> dict:
    jd_text = extract_text(state.job_description)
    resume_text = extract_text(state.resume_text)
    return {
        "job_description": jd_text,
        "resume_text": resume_text,
        "messages": ["[load_documents] JD + Resume loaded"]
    }

def match_skills(state: ResumeMatchState) -> dict:
    response = llm.invoke(
    f"You are a recruiter.\n\n"
    f"JOB DESCRIPTION:\n{state.job_description}\n\n"
    f"RESUME:\n{state.resume_text}\n\n"
    f"Compare required skills vs candidate skills.\n"
    f"List matched skills and missing skills clearly."
    )

  
    return {
        "skill_match": response.content,
        "messages": ["[match_skills] Done"]
    }
  

def match_experience(state: ResumeMatchState) -> dict:
    response = llm.invoke(
    f"Compare experience level between job and resume.\n\n"
    f"JOB:\n{state.job_description}\n\n"
    f"RESUME:\n{state.resume_text}"
    )

   
    return {
        "experience_match": response.content,
        "messages": ["[match_experience] Done"]
    }
    

def match_keywords(state: ResumeMatchState) -> dict:
    response = llm.invoke(
    f"Find keyword overlap between job description and resume.\n\n"
    f"JOB:\n{state.job_description}\n\n"
    f"RESUME:\n{state.resume_text}"
    )

    return {
        "keyword_match": response.content,
        "messages": ["[match_keywords] Done"]
    }
 

def compute_score(state: ResumeMatchState) -> dict:
    response = llm.invoke(
    f"You are an expert hiring system.\n\n"
    f"SKILLS:\n{state.skill_match}\n\n"
    f"EXPERIENCE:\n{state.experience_match}\n\n"
    f"KEYWORDS:\n{state.keyword_match}\n\n"
    f"Return ONLY JSON:\n"
    f'{{"match_score": number (0-100), "missing_skills": "text"}}'
    )

    try:
        data = json.loads(response.content)
        score = data["match_score"]
        missing = data["missing_skills"]
    except:
        score = 50
        missing = "Parsing failed"

    return {
        "match_score": score,
        "missing_skills": missing,
        "messages": [f"[compute_score] score={score}"]
    }


def final_decision(state: ResumeMatchState) -> dict:
    if state.match_score >= 70:
        decision = "SELECTED"
    else:
        decision = "REJECTED"

    response = llm.invoke(
        f"You are a hiring manager.\n"
        f"Score: {state.match_score}\n"
        f"Missing: {state.missing_skills}\n\n"
        f"Explain clearly why the candidate is {decision}.\n"
        f"If rejected, explain what is missing.\n"
        f"If selected, explain strengths."
    )

    report = f"""

    ============================================================
    MATCH SCORE: {state.match_score}%

    DECISION: {decision}

    MISSING SKILLS:
    {state.missing_skills}

    REASON:
    {response.content}
    ==================

    """

    return {
        "decision": decision,
        "final_report": report,
        "messages": [f"[final_decision] {decision}"]
    }
   

# =============================================================================

# GRAPH

# =============================================================================

graph = StateGraph(ResumeMatchState)

graph.add_node("load_documents", load_documents)
graph.add_node("match_skills", match_skills)
graph.add_node("match_experience", match_experience)
graph.add_node("match_keywords", match_keywords)
graph.add_node("compute_score", compute_score)
graph.add_node("final_decision", final_decision)

graph.add_edge(START, "load_documents")

# parallel execution

graph.add_edge("load_documents", "match_skills")
graph.add_edge("load_documents", "match_experience")
graph.add_edge("load_documents", "match_keywords")

# fan-in

graph.add_edge("match_skills", "compute_score")
graph.add_edge("match_experience", "compute_score")
graph.add_edge("match_keywords", "compute_score")

graph.add_edge("compute_score", "final_decision")
graph.add_edge("final_decision", END)

app = graph.compile()

# =============================================================================

# RUNNER

# =============================================================================

def run_resume_match(jd_path: str, resume_path: str):
    print("=" * 60)
    print("  RESUME vs JOB MATCHER")
    print("=" * 60)

    # validation
    if not os.path.exists(jd_path):
        print("❌ JD file not found")
        return

    if not os.path.exists(resume_path):
        print("❌ Resume file not found")
        return

    result = app.invoke({
        "job_description": jd_path,
        "resume_text": resume_path,
        "messages": [],
    })

    print("\n" + "=" * 60)
    print("  RESULT")
    print("=" * 60)
    print(result["final_report"])

    print("\n" + "-" * 60)
    print("  MESSAGE LOG")
    print("-" * 60)
    for msg in result["messages"]:
        print(msg)

    return result


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  RESUME MATCHING SYSTEM")
    print("=" * 60)

    jd_path = input("\nEnter JD file path (.pdf/.docx):\n").strip()
    resume_path = input("\nEnter Resume file path (.pdf/.docx):\n").strip()

    run_resume_match(jd_path, resume_path)

