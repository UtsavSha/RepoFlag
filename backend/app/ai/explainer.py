import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


def generate_finding_explanation(finding_desc: str, severity: str, filepath: str) -> str:
    """
    Uses Google Gemini to explain a security vulnerability and suggest a fix.
    """
    # Check for the Google API key instead of OpenAI
    if not os.getenv("GOOGLE_API_KEY"):
        return "AI Explanations require a GOOGLE_API_KEY environment variable."

    # Initialize the free Gemini 1.5 Flash model
    llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0.2)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are AUSPEX, an elite application security assistant. 
        Explain the provided vulnerability to a developer in plain English. 
        Do not use markdown headers. Structure your response exactly like this:
        
        **The Risk:** (Explain why this is dangerous in 2 sentences)
        **The Fix:** (Give a specific, actionable remediation step)"""),

        ("user",
         "File: {filepath}\nSeverity: {severity}\nFinding: {finding_desc}")
    ])

    chain = prompt | llm

    try:
        response = chain.invoke({
            "filepath": filepath,
            "severity": severity,
            "finding_desc": finding_desc
        })
        return response.content
    except Exception as e:
        return f"AI Generation failed: {str(e)}"
