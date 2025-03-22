import streamlit as st
import requests
import feedparser
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMMathChain, LLMChain
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import Tool, DuckDuckGoSearchRun
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# Title
st.title(" Cybersecurity Intelligence Chatbot")

groq_api_key = st.sidebar.text_input("Enter your Groq API Key", type="password")

if not groq_api_key:
    st.info("⚠️ Please provide the Groq API Key.")
    st.stop()

llm = ChatGroq(groq_api_key=groq_api_key, model="Gemma2-9b-It")

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


prompt_template = """
You are a cybersecurity expert with knowledge of cyber threats, malware, and hacking incidents.
If a question is related to cybersecurity threats, attacks, or live updates, provide a **detailed report**
including the latest findings from security sources.

If it's a math-related query, solve it step-by-step.

If it's a general query, answer concisely but informatively.

Question: {question}
Answer:
"""

prompt = PromptTemplate(input_variables=['question'], template=prompt_template)

def fetch_latest_threats(_=None):
    url = "https://www.bleepingcomputer.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    news_items = []
    for article in soup.select(".bc_latest_news a")[:5]: 
        title = article.text.strip()
        link = article['href']
        news_items.append(f"🔹 **{title}**\n📌 [Read More]({link})\n")

    return "\n".join(news_items) if news_items else "⚠️ No latest threats found."

def fetch_rss_threats(_=None):
    feed = feedparser.parse("https://threatpost.com/feed/")
    news_items = []
    for entry in feed.entries[:5]:  # Top 5 latest articles
        news_items.append(f"🔹 **{entry.title}**\n📌 [Read More]({entry.link})\n")

    return "\n".join(news_items) if news_items else "⚠️ No recent news found."

# Creating Tools for the Agent
wiki_wrap = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=300)
wiki_tool = Tool(
    name="Wikipedia",
    func=wiki_wrap.run,
    description="Search for information on Wikipedia."
)

math_chain = LLMMathChain.from_llm(llm=llm)
math_tool = Tool(
    name="Math Solver",
    func=math_chain.run,
    description="Solve mathematical problems step-by-step."
)

search_tool = DuckDuckGoSearchRun(name="Threat Search")

# Adding Cybersecurity Tools
threat_tool = Tool(
    name="Latest Cyber Threats",
    func=fetch_latest_threats,
    description="Fetches the latest cybersecurity threats from BleepingComputer."
)

rss_threat_tool = Tool(
    name="Cyber Threat Intelligence",
    func=fetch_rss_threats,
    description="Fetches the latest cyber attack news from ThreatPost."
)

# Creating the Reasoning Chain
chain = LLMChain(llm=llm, prompt=prompt)

reasoning_tool = Tool(
    name="General Knowledge",
    func=chain.run,
    description="Provides answers to general questions."
)

# Initializing the Agent
agent = initialize_agent(
    tools=[wiki_tool, math_tool, search_tool, threat_tool, rss_threat_tool, reasoning_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=False,
    handle_parsing_errors=True
)

# 🔹 Maintain Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "🔹 Hello! I am a cybersecurity chatbot. Ask me about **cyber threats, attacks."}
    ]

# Display Chat History
for msg in st.session_state.messages:
    st.chat_message(msg['role']).write(msg['content'])

# User Query Input
user_query = st.chat_input(placeholder="Ask about the latest threats, cyberattacks")

if user_query:
    # Append user input to session
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    # Process Response
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        response = agent.run(user_query, callbacks=[st_cb])

        # Append assistant response to session
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.success(response.encode("utf-8", "ignore").decode())
