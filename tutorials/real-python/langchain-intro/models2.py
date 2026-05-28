import dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

dotenv.load_dotenv()

chat_model = ChatOpenAI(model="gpt-4o", temperature=0)

messages = [
    SystemMessage(
        content="""You're an assistant knowledgeable about
        healthcare. Only answer healthcare-related questions."""
    ),
    # HumanMessage(content="What is blood pressure?"),
    HumanMessage(content="How do I change a tire?"),
]
print(chat_model.invoke(messages))
