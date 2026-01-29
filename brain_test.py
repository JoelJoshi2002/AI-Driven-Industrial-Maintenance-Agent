import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# 1. Load Secrets
load_dotenv()

# 2. Initialize the Brain (Llama 3 via Groq)
llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.3-70b-versatile", # The big, smart open-source model
    api_key=os.getenv("GROQ_API_KEY")
)

# 3. Test Reasoning
question = "I have a Prusa MK3S+ printer. It is making a clicking sound. What is the most likely mechanical cause?"

print("🧠 Thinking...")
response = llm.invoke(question)

print("\n--- AGENT RESPONSE ---")
print(response.content)