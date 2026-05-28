from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()

messages = [
    SystemMessage(content="You are a helpful health care assistant. only answer questions about health care. If you don't know the answer, say you don't know."),
    HumanMessage(content="What is an ideal blood pressure?"),
]

chat_model = ChatOpenAI(model="gpt-4o", temperature=0)
response = chat_model.invoke(messages)
print(response.content)