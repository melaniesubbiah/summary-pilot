import streamlit as st
import json
import os
import glob
import time


DEFINITIONS = {
    "old timey radio": "mimicking the style or radio broadcasts from the mid-1900s",
    "tweet": "imiting the style of a post on Twitter/X",
    "inquisitive": "uses questions and/or a tone of curiosity"
}

def next_click():
    # Make sure the annotations file exists
    os.makedirs("personalization_pilot/annotations", exist_ok=True)
    if not os.path.exists(f"personalization_pilot/annotations/{st.session_state['userID']}.json"):
        with open(f"personalization_pilot/annotations/{st.session_state['userID']}.json", "w") as f:
            f.write(json.dumps({}))

    # Read the existing annotations
    with open(f"personalization_pilot/annotations/{st.session_state['userID']}.json", "r") as f:
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
        annotations[st.session_state["pageNum"]] = {
            "answers": [st.session_state[f"answer_{x}"] for x in range(5)],
            "timing": round(endtime - st.session_state["starttime"], 2)
        }

        with open(f"personalization_pilot/annotations/{st.session_state['userID']}.json", "w") as f:
            f.write(json.dumps(annotations))

        # Reset values
        st.session_state['pageNum'] += 1
        st.session_state["starttime"] = time.time()

def prep_download_file():
    # Download annotation files from Streamlit
    annotations = {}
    files = glob.glob(pathname="personalization_pilot/annotations/*")
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
    # Initialize state
    expanded = False
    if "userID" not in st.session_state:
        st.session_state["userID"] = ""
        st.session_state["pageNum"] = -1
        st.session_state["answer_0"] = None
        st.session_state["answer_1"] = None
        st.session_state["answer_2"] = None
        st.session_state["answer_3"] = None
        st.session_state["answer_4"] = None
        st.session_state["questionID"] = ""
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
    for key, val in data.items():
        val['id'] = key
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
        if st.session_state["userID"] == 'download':
            # If the user enters 'download' as the user ID, then we can download all files.
            btn = st.download_button(
                label="Download all annotations",
                data=json.dumps(prep_download_file(), indent=2),
                file_name="personalization_pilot_annotations.json",
            )
    elif st.session_state["pageNum"] == len(examples):
        # End of the task.
        expanded = True
        st.success('You have finished the task. Please send us a message on Upwork and thank you for completing the pilot!')
    else:
        st.markdown(f'## Annotation {int(st.session_state["pageNum"]) + 1}/{len(examples)}')
        st.session_state['questionID'] = examples[st.session_state['pageNum']]['id']
        # Show a question.
        st.markdown('### Style Preferences')
        styles = examples[st.session_state['pageNum']]['style']
        for style in styles:
            st.markdown(f'**{style}**: {DEFINITIONS[style]}')
        if 'examples' in examples[st.session_state['pageNum']]:
            st.markdown('### Example 1')
            st.write(examples[st.session_state['pageNum']]['examples'][0])
            st.markdown('### Example 2')
            st.write(examples[st.session_state['pageNum']]['examples'][1])
            question = "Which example better exhibits %s style?"
            answer_options = ["Example 1", "Example 2"]
        else:
            st.markdown('### Example:')
            st.markdown(examples[st.session_state['pageNum']]['example'].replace('#', '\#'))
            question = "Does the example contradict or exhibit %s style?"
            answer_options = ["1 - clearly contradicts", "2 - somewhat contradicts", "3 - I'm not sure", "4 - somewhat exhibits", "5 - clearly exhibits"]

        next_disabled = False

        st.markdown('#### Questions:')
        for idx, style in enumerate(examples[st.session_state['pageNum']]['style']):
            st.session_state[f"answer_{idx}"] = st.radio(
                question.format(style),
                answer_options,
                key=f"q{st.session_state['pageNum']}_q_radio_{idx}",
                index=None
            )

            if st.session_state[f"q{st.session_state['pageNum']}_q_radio_{idx}"] == None:
                next_disabled = True

        st.button("Next", disabled=next_disabled, on_click=next_click)
