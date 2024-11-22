import streamlit as st
import pandas as pd
import numpy as np

from utils.aws import read_file_from_s3

st.set_page_config(layout="wide")

st.sidebar.title('Bot Dashboard')
option = st.sidebar.selectbox(
    'Select a project',
    ('galway-daily-bot-prod', 'life-compare-bot-prod', 'backlink-outreach-bot-prod')
)
primary_choice = st.sidebar.radio("Select a section:", ["Home", "Features"])
st.title(option)
tabs = st.tabs(["Configure", "Monitor", "Outreach"])

if 'messages' not in st.session_state:
    st.session_state.messages = []

with tabs[0]:
    col1, empty_col, col2 = st.columns([1, 0.1, 1])  # Adjust the width ratio as needed

    with col1:
        st.header('Role Prompt')

        role_prompt = read_file_from_s3(option, 'role_prompt.md')
        edit_mode = st.button('Edit', key='edit_role_prompt')
        
        if edit_mode:
            role_prompt = st.text_area('', role_prompt, height=600)
            if st.button('Save', key='save_role_prompt'):
                pass
        else:
            st.markdown(role_prompt)
            
        st.markdown('---')
        st.header('Chat')

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        user_input = st.chat_input('Type your message here...')
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": "Hi! How can I help you today?"})

    with col2:
        st.header('Communication')
        st.subheader('Email (Zapier)')
        st.markdown('**Account:** darragh@galwaydaily.com')
        email_zapier_api_key = st.text_input('API Key', 'fake-email-zapier-api-key-123')
        st.button('Save', key='save_email_zapier_api_key')

        st.markdown('---')
        st.header('Tools')
        
        with st.container():
            do_not_reply_checked = st.checkbox('**do_not_reply**')
            if do_not_reply_checked:
                do_not_reply_desc = st.text_area('When to use', 'Use this tool to send automated emails that do not require a reply. This is useful for sending notifications and alerts.', height=100)

        with st.container():
            send_slack_message_checked = st.checkbox('**send_slack_message**', value=True)
            if send_slack_message_checked:
                st.json({'channel': '#general', 'text': 'Hello, world!'}, expanded=False)
                send_slack_message_api_key = st.text_input('API Key', 'fake-slack-api-key-123')
                send_slack_message_desc = st.text_area('When to use', 'Use this tool to send a message to a specified Slack channel. This is useful for team notifications and updates.', height=100)

        with st.container():
            send_invoice_checked = st.checkbox('**send_invoice**', value=True)
            if send_invoice_checked:
                st.json({'client_id': '12345', 'amount': 100.0, 'currency': 'USD'}, expanded=False)
                send_invoice_api_key = st.text_input('API Key', 'fake-invoice-api-key-456')
                send_invoice_desc = st.text_area('When to use', 'Use this tool to generate and send invoices to clients. This is useful for billing and payment processing.', height=100)

        if st.button('Save', key='save_tools'):
            pass

with tabs[1]:
    import matplotlib.pyplot as plt

    st.header('Overview')

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric('Total Messages', 123, delta=15)
    with col2:
        st.metric('Total Users', 10, delta=-1)
    with col3:
        st.metric('Total Conversations', 5, delta=0)
    with col4:
        st.metric('New Users', 2, delta=1)
    with col5:
        st.metric('Active Users', 8, delta=2)
    with col6:
        st.metric('Inactive Users', 2, delta=-1)

    data = pd.DataFrame(
        np.random.randn(10, 3),
        columns=['Metric 1', 'Metric 2', 'Metric 3']
    )

    st.line_chart(data)

    col1, col2 = st.columns([1, 3])
    with col1:
        for i in range(1, 6):
            with st.container():
                st.subheader(f'Thread ID: {i}')
                st.link_button('View', f'/threads/{i}')
                st.text(f'Email: user{i}@example.com')
                st.text(f'Last message time: {pd.Timestamp.now()}')
                if i == 3:
                    st.success('Successful sale')
                if i == 4:
                    st.error('Do not contact')
                st.markdown('---')

    with col2:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        user_input = st.chat_input('Type your message here...', key='chat_input')
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": "Hi! How can I help you today?"})

with tabs[2]:
    st.write("Outreach content goes here")
