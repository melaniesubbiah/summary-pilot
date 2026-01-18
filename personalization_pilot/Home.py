import streamlit as st
import json
import os
import glob
import time
import gspread
from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)

gc = gspread.authorize(creds)

DEFINITIONS = {
    "old timey radio": "mimicking the style or radio broadcasts from the mid-1900s",
    "tweet": "imiting the style of a post on Twitter/X",
    "inquisitive": "uses questions and/or a tone of curiosity"
}

def next_click():
    if st.session_state["pageNum"] == -1:
        worksheet = gc.open_by_url(st.secrets["sheet_url"]).worksheet("pilot")
        user_annos = worksheet.get_all_records()
        annotations = {}
        for rec in user_annos:
            if rec["user"] == st.session_state['userID']:
                annotations[rec['id']] = rec

        # If on the home page, skip ahead to the first incomplete annotation
        st.session_state['pageNum'] += 1
        while str(st.session_state["pageNum"]) in annotations:
            st.session_state['pageNum'] += 1

        # Start the completion time clock
        st.session_state["starttime"] = time.time()
    else:
        # Write the completed annotation with completion time
        endtime = time.time() # this will be in seconds
        temp = [
            st.session_state['userID'],
            st.session_state["pageNum"],
            st.session_state["answer"],
            round(endtime - st.session_state["starttime"], 2)
        ]

        worksheet = gc.open_by_url(st.secrets["sheet_url"]).worksheet("pilot")
        worksheet.append_row(temp)

        # Reset values
        st.session_state['pageNum'] += 1
        st.session_state["starttime"] = time.time()



if __name__ == "__main__":
    # Initialize state
    expanded = False
    if "userID" not in st.session_state:
        st.session_state["userID"] = ""
        st.session_state["pageNum"] = -1
        st.session_state["answer"] = None
        expanded = True

    # Init the page
    with st.expander("Instructions", expanded=expanded):
        with open('personalization_pilot/instructions.md', "r") as f:
            instructions = f.read()
        st.markdown(instructions)

    # Load the data
    examples = []
    with open('personalization_pilot/pilot_examples.json', "r") as f:
        data = json.load(f)
    for val in data.values():
        examples.append(val)

    if st.session_state['pageNum'] < 0:
        # Collect UserID
        st.markdown(
            'Please enter your assigned user ID below to start the task. You can stop the task and revisit it later. Your progress will be saved connected to your user ID. Answer each question carefully as you will not be able to go back to a previous question once you have answered it.')

        valid_ids = ['test', '123', '234', '345']
        if st.session_state["userID"] == "" or st.session_state["userID"] not in valid_ids:
            st.session_state["userID"] = st.text_input("Enter your assigned user ID:")
        if st.session_state["userID"] in valid_ids:
            st.success('Thank you!')
            # Next button moves on to next question
            st.button("Next", disabled=False, on_click=next_click)
    elif st.session_state["pageNum"] == len(examples):
        # End of the task.
        expanded = True
        st.success('You have finished the task. Please send us a message on Upwork and thank you for completing the pilot!')
    else:
        st.markdown(f'## Annotation {int(st.session_state["pageNum"]) + 1}/{len(examples)}')
        # Show a question.
        st.markdown('### Style Preference')
        style = examples[st.session_state['pageNum']]['style']
        st.markdown(f'**{style}**: {DEFINITIONS[style]}')
        if 'examples' in examples[st.session_state['pageNum']]:
            st.markdown('### Example 1')
            st.write(examples[st.session_state['pageNum']]['examples'][0])
            st.markdown('### Example 2')
            st.write(examples[st.session_state['pageNum']]['examples'][1])
            question = "Which example better exhibits the style attribute?"
            answer_options = ["Example 1", "Example 2"]
        else:
            st.markdown('### Example:')
            st.markdown(examples[st.session_state['pageNum']]['example'].replace('#', '\#'))
            question = "Does the example contradict or exhibit the style preference?"
            answer_options = ["1 - clearly contradicts", "2 - somewhat contradicts", "3 - I'm not sure", "4 - somewhat exhibits", "5 - clearly exhibits"]

        next_disabled = False

        st.markdown('#### Question:')
        st.session_state["answer"] = st.radio(
            f'#### {question}',
            answer_options,
            key=f"q{st.session_state['pageNum']}_q_radio",
            index=None
        )

        if st.session_state[f"q{st.session_state['pageNum']}_q_radio"] == None:
            next_disabled = True

        st.button("Next", disabled=next_disabled, on_click=next_click)
