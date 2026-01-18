import streamlit as st
import json
import os
import glob
import time
import random

random.seed(12058563628920)



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
    # Make sure the annotations file exists
    os.makedirs("personalization_study/annotations", exist_ok=True)
    if not os.path.exists(f"personalization_study/annotations/{st.session_state['userID']}.json"):
        with open(f"personalization_study/annotations/{st.session_state['userID']}.json", "w") as f:
            f.write(json.dumps({}))

    # Read the existing annotations
    with open(f"personalization_study/annotations/{st.session_state['userID']}.json", "r") as f:
        annotations = json.load(f)

    if st.session_state["pageNum"] == -1:
        # If on the home page, skip ahead to the first incomplete annotation
        st.session_state['pageNum'] += 1
        while str(st.session_state["pageNum"]) in annotations:
            st.session_state['pageNum'] += 1

        # Start the completion time clock
        st.session_state["starttime"] = time.time()
    else:
        # Write the completed annotation with completion time
        endtime = time.time() # this will be in seconds
        temp = {
            "timing": round(endtime - st.session_state["starttime"], 2),
            'id': st.session_state['orig_id'],
        }
        for i in range(3):
            if "neither" in st.session_state[f"answer{str(i)}"]:
                temp[f"style{str(i)}"] = 'neither'
            else:
                answer = "1" in st.session_state[f"answer{str(i)}"]
                if answer:
                    temp[f"style{str(i)}"] = 'compose' if st.session_state[f"{st.session_state['pageNum']}_order"] else 'prose'
                else:
                    temp[f"style{str(i)}"] = 'prose' if st.session_state[f"{st.session_state['pageNum']}_order"] else 'compose'
        annotations[st.session_state["pageNum"]] = temp

        with open(f"personalization_study/annotations/{st.session_state['userID']}.json", "w") as f:
            f.write(json.dumps(annotations))

        # Reset values
        st.session_state['pageNum'] += 1
        st.session_state["starttime"] = time.time()

def prep_download_file():
    # Download annotation files from Streamlit
    annotations = {}
    files = glob.glob(pathname="personalization_study/annotations/*")
    for output_name in files:
        with open(output_name, "r") as file:
            st.write(output_name)
            try:
                annotations[output_name.split('/')[-1].split('.json')[0]] = json.loads(file.readline())
            except:
                st.write("Failed")
                continue
    return annotations


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
        if st.session_state["userID"] == 'download':
            # If the user enters 'download' as the user ID, then we can download all files.
            btn = st.download_button(
                label="Download all annotations",
                data=json.dumps(prep_download_file(), indent=2),
                file_name="personalization_study_annotations.json",
            )
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
