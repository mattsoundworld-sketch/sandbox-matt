import dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

dotenv.load_dotenv()

template_str = """You're an expert on {topic}. ...

Here is some context to help you respond to the prompt:
{context}

Here is the prompt you need to respond to:
{question}"""

prompt_template = PromptTemplate.from_template(template_str)
filled_prompt = prompt_template.format(
    topic="User feedback", context="I love it here!", question="Any positives?"
)

chat_model = ChatOpenAI(model="gpt-4o", temperature=0)
print(chat_model.invoke(filled_prompt))
