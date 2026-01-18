import streamlit as st
import json
import os
import glob
import time
import random
import gspread
from google.oauth2.service_account import Credentials

random.seed(12058563628920)


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)

gc = gspread.authorize(creds)



# anno_ids = {
#     '123': [(0, 25), (25, 50), (100, 125), (125, 150)],
#     '234': [(0, 25), (50, 75), (100, 125), (150, 175)],
#     '345': [(0, 25), (75, 100), (100, 125), (175, 200)],
# }

anno_ids = {
    '123': [(5, 25), (30, 50), (105, 125), (130, 150)],
    '234': [(0, 5), (50, 55), (100, 105), (150, 155)],
    '345': [(0, 5), (75, 80), (100, 105), (175, 180)],
}

def next_click():
    if st.session_state["pageNum"] == -1:
        worksheet = gc.open_by_url(st.secrets["sheet_url"]).worksheet(st.session_state['userID'])
        user_annos = worksheet.get_all_records()
        annotations = {}
        for rec in user_annos:
            annotations[rec['id']] = rec

        # If on the home page, skip ahead to the first incomplete annotation
        st.session_state['pageNum'] += 1
        while st.session_state["pageNum"] in annotations:
            st.session_state['pageNum'] += 1

        # Start the completion time clock
        st.session_state["starttime"] = time.time()
    else:
        # Write the completed annotation with completion time
        endtime = time.time() # this will be in seconds
        temp = [st.session_state['pageNum'], st.session_state['orig_id'], round(endtime - st.session_state["starttime"], 2)]
        for i in range(3):
            if "neither" in st.session_state[f"answer{str(i)}"]:
                temp.append('neither')
            else:
                answer = "1" in st.session_state[f"answer{str(i)}"]
                if answer:
                    temp.append('compose' if st.session_state[f"{st.session_state['pageNum']}_order"] else 'prose')
                else:
                    temp.append('prose' if st.session_state[f"{st.session_state['pageNum']}_order"] else 'compose')

        worksheet = gc.open_by_url(st.secrets["sheet_url"]).worksheet(st.session_state['userID'])
        worksheet.append_row(temp)

        # Reset values
        st.session_state['pageNum'] += 1
        st.session_state["starttime"] = time.time()


if __name__ == "__main__":
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stContainer"]) {
            overflow-y: scroll !important;
        }

        /* Optional: style the scrollbar (Chrome, Edge, Safari) */
        ::-webkit-scrollbar {
            width: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 6px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    # Initialize state
    expanded = False
    if "userID" not in st.session_state:
        st.session_state["userID"] = ""
        st.session_state["pageNum"] = -1
        st.session_state["answer"] = None
        expanded = True

    # Init the page
    with st.expander("Instructions", expanded=expanded):
        with open('personalization_study/instructions.md', "r") as f:
            instructions = f.read()
        st.markdown(instructions)

    # Load the data
    examples = []
    with open('personalization_study/human_eval_200_final.json', "r") as f:
        data = json.load(f)
    if st.session_state["userID"] in anno_ids:
        for (start, end) in anno_ids[st.session_state["userID"]]:
            for i in range(start, end):
                temp = data[str(i)]
                temp['orig_id'] = str(i)
                examples.append(temp)

    if st.session_state['pageNum'] < 0:
        # Collect UserID
        st.markdown(
            'Please enter your assigned user ID below to start the task. You can stop the task and revisit it later. Your progress will be saved connected to your user ID. Answer each question carefully as you will not be able to go back to a previous question once you have answered it.')

        valid_ids = ['123', '234', '345']
        if st.session_state["userID"] == "" or st.session_state["userID"] not in valid_ids:
            st.session_state["userID"] = st.text_input("Enter your assigned user ID:")
        if st.session_state["userID"] in valid_ids:
            st.success('Thank you!')
            # Next button moves on to next question
            st.button("Next", disabled=False, on_click=next_click)
    elif st.session_state["pageNum"] == len(examples):
        # End of the task.
        expanded = True
        st.success('You have finished the task. Please send us a message on Upwork and thank you for completing this milestone!')
    else:
        st.markdown(f'## Annotation {int(st.session_state["pageNum"]) + 1}/{len(examples)}')
        # Show a question.
        st.markdown('### Style Directions')
        style = examples[st.session_state['pageNum']]['style']
        task_type = examples[st.session_state['pageNum']]['task']
        task_type = task_type[0].upper() + task_type[1:]
        st.session_state['orig_id'] = examples[st.session_state['pageNum']]['orig_id']
        st.markdown(f"*{'*, *'.join(style[:-1])}*, and *{style[-1]}*")
        if f"{st.session_state['pageNum']}_order" in st.session_state:
            order = st.session_state[f"{st.session_state['pageNum']}_order"]
        else:
            order = random.randint(0, 1)
            st.session_state[f"{st.session_state['pageNum']}_order"] = order
        if order:
            example1 = examples[st.session_state['pageNum']]['ComPOSE']
            example2 = examples[st.session_state['pageNum']]['PROSE']
        else:
            example1 = examples[st.session_state['pageNum']]['PROSE']
            example2 = examples[st.session_state['pageNum']]['ComPOSE']
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'### {task_type} 1')
            with st.container(height=300):
                st.write(example1.replace('$', '\$'))
        with col2:
            st.markdown(f'### {task_type} 2')
            with st.container(height=300):
                st.write(example2.replace('$', '\$'))
        questions = []
        for i in range(3):
            questions.append(f"Which {task_type.lower()} better follows the style direction to *{style[i]}*?")
        answer_options = [f"{task_type} 1", f"{task_type} 2", f"Neither {task_type.lower()} follows the style direction"]

        next_disabled = False

        st.markdown('#### Questions:')
        for i, question in enumerate(questions):
            st.session_state[f"answer{str(i)}"] = st.radio(
                question,
                answer_options,
                key=f"q{st.session_state['pageNum']}_q{str(i)}_radio",
                index=None
            )

        # st.session_state[f"answer{str(i+1)}"] = st.radio(
        #     f"Overall, which {task_type.lower()} better follows all of the style directions to *{'*, *'.join(style[:-1])}*, and *{style[-1]}*?",
        #     answer_options,
        #     key=f"q{st.session_state['pageNum']}_q{str(i+1)}_radio",
        #     index=None
        # )
        #
        # st.session_state[f"answer{str(i + 2)}"] = st.radio(
        #     f"Overall, which {task_type.lower()} is more coherent?",
        #     answer_options,
        #     key=f"q{st.session_state['pageNum']}_q{str(i + 2)}_radio",
        #     index=None
        # )

        if st.session_state[f"q{st.session_state['pageNum']}_q{str(i)}_radio"] == None:
            next_disabled = True

        st.button("Next", disabled=next_disabled, on_click=next_click)
