# websearch/app.py
import streamlit as st
from manager import ManagerAgent
import asyncio

# Fix for "no current event loop" in Streamlit
import nest_asyncio
nest_asyncio.apply()

if not asyncio.get_event_loop_policy().get_event_loop():
    asyncio.set_event_loop(asyncio.new_event_loop())

class App:
    def __init__(self):
        st.set_page_config(
            page_title="AI Agent",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        self._render_sidebar()

        if "messages" not in st.session_state:
            st.session_state.messages = []

    def _render_sidebar(self):
        with st.sidebar:
            st.title("Web search")
            st.write("This tool ...")

            st.subheader("How it works")
            st.write(
                """
                1. Enter a query  
                2. Click send  
                3. The AI agent will:  
                    - Search  
                    - Extract  
                    - Generate answer  
                """
            )

            st.subheader("Settings")

            self.model_choice = st.selectbox(
                label="Choose language model",
                options=["GigaChat"],
                index=0
            )

            self.temperature = st.slider(
                "Temperature (Creativity)",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1
            )

            self.max_iterations = st.slider(
                "Max search iterations",
                min_value=1,
                max_value=10,
                value=5
            )

    def run(self):
        st.title("Web Search AI Agent")
        st.write("Ask me anything ..")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_question = st.chat_input("What would you like to know?")
        agent = None

        try:
            agent = ManagerAgent(
                # model_name=self.model_choice,
                temperature=self.temperature,
                # max_iterations=self.max_iterations,
            )
        except Exception as e:
            st.error(f"Error initializing agent: {e}")

        if user_question and agent:
            st.session_state.messages.append({"role": "user", "content": user_question})

            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                with st.status("Working on it...", expanded=True) as status:
                    st.write("Searching the web...")

                    try:
                        response = agent.run(user_question)
                        status.update(label="Search complete", state="complete")
                        message_placeholder.markdown(response)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )
                    except Exception as e:
                        status.update(label="Error", state="error")
                        error_message = f"An error occured: {str(e)}"
                        message_placeholder.error(error_message)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": error_message}
                        )
