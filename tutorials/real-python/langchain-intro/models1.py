import dotenv
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

chat_model = ChatOpenAI(model="gpt-4o", temperature=0)

print(chat_model.invoke("What is blood pressure?"))
