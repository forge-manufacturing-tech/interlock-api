import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


def get_tech_transfer_agent():
    """Returns a configured LangChain runnable"""
    if "GEMINI_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview", google_api_key=os.environ["GEMINI_API_KEY"]
    )
    prompt = ChatPromptTemplate.from_template(
        "You are an expert in manufacturing tech transfer. "
        "Answer this concisely: {question}"
    )
    return prompt | llm | StrOutputParser()
