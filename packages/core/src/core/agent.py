from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def get_tech_transfer_agent():
    """Returns a configured LangChain runnable"""
    llm = ChatOpenAI(model_name="gpt-4o")
    prompt = ChatPromptTemplate.from_template(
        "You are an expert in manufacturing tech transfer. "
        "Answer this concisely: {question}"
    )
    return prompt | llm | StrOutputParser()
