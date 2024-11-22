import os

import streamlit as st
import json
from openai import OpenAI

from utils.aws import read_file_from_s3, write_file_to_s3, list_objects_in_s3
from thread import Thread


client = OpenAI(api_key=os.environ.get('OPENAI_KEY'))

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    [role=radiogroup]{
        gap: 1rem;
    }
    </style>
    """,unsafe_allow_html=True)


st.sidebar.title('Bot Dashboard')
project = st.sidebar.selectbox('Select a project',
    [
        'galway-daily-bot-prod', 
        'life-compare-bot-prod', 
        'backlink-outreach-bot-prod'
    ]
)
view = st.sidebar.radio("Select a view", 
    [
        "Monitor",
        "Configure",
        "Outreach"
    ]
)

st.title(project)


match view:
    case "Monitor":
        col1, col2 = st.columns([1, 4])

        with col1:
            threads = list_objects_in_s3(project, prefix='threads/')
            if 'page' not in st.session_state:
                st.session_state.page = 0

            threads_per_page = 12
            total_pages = (len(threads) - 1) // threads_per_page + 1

            start_idx = st.session_state.page * threads_per_page
            end_idx = start_idx + threads_per_page
            paginated_threads = threads[start_idx:end_idx]

            thread_titles = [f"**{t['Key'].removeprefix('threads/').removesuffix('.json')}**\n\r{t['LastModified'].strftime('%d/%m/%Y, %H:%M:%S')}" for t in paginated_threads]

            selected_thread_title = st.radio("Threads", thread_titles)

            if start_idx > 0:
                if st.button("Previous"):
                    if st.session_state.page > 0:
                        st.session_state.page -= 1
                        st.rerun()

            if st.button("Next"):
                if st.session_state.page < total_pages - 1:
                    st.session_state.page += 1
                    st.rerun()
            
        with col2:
            thread_id = selected_thread_title.split('\n')[0].removeprefix('**').removesuffix('**')
            thread = read_file_from_s3(project, f'threads/{thread_id}.json')
            thread = Thread.from_json(client, '', thread)
#
            for message in reversed(thread.messages):
                if message['content'] is None:
                    continue

                with st.chat_message(message['role']):
                    st.markdown(f"**{message.get('email_address', message.get('role').title()).replace('Assistant','Bot')}**")
                    if message['role'] == 'tool':
                        tool_call = thread.get_tool_call(message)
                        st.success(f"**Name:** {tool_call['name']}\n\n**Arguments:** {tool_call['arguments']}")
                    else:
                        st.write(message['content'])
                    st.markdown(f"*{message.get('timestamp','')}*")
                    st.json(message, expanded=False)
                    st.markdown('---')


    case "Configure":
        col1, col2 = st.columns([3, 2])

        with col1:
            st.header("Role Prompt")
            role_prompt = read_file_from_s3(project, 'role_prompt.md')
            if 'edit_mode' not in st.session_state:
                st.session_state.edit_mode = False

            if st.session_state.edit_mode:
                role_prompt = st.text_area('', role_prompt, height=1000)
                if st.button('Save', key='save_role_prompt'):
                    write_file_to_s3(project, 'role_prompt.md', role_prompt)
                    st.session_state.edit_mode = False
                    st.rerun()

                if st.button('Cancel', key='cancel_role_prompt'):
                    st.session_state.edit_mode = False
                    st.rerun()

            else:
                st.markdown(role_prompt)
                if st.button('Edit', key='edit_role_prompt'):
                    st.session_state.edit_mode = True
                    st.rerun()


    case "Outreach":
        st.write("Outreach view")
