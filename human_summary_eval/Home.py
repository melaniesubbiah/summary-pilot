import streamlit as st
import json
import os
import glob
import time

def next_click():
    os.makedirs("annotations", exist_ok=True)
    if not os.path.exists(f"annotations/{st.session_state['userID']}.json"):
        with open(f"annotations/{st.session_state['userID']}.json", "w") as f:
            f.write(json.dumps({}))
    with open(f"annotations/{st.session_state['userID']}.json", "r") as f:
        annotations = json.load(f)

    if st.session_state["pageNum"] == -1:
        st.session_state['pageNum'] += 1
        while str(st.session_state["pageNum"]) in annotations:
            st.session_state['pageNum'] += 1
    else:
        # This is in seconds
        endtime = time.time()
        annotations[st.session_state["pageNum"]] = {
            "answer": st.session_state[f"q{st.session_state['pageNum']}_radio"],
            "timing": round(endtime - st.session_state[f'q{st.session_state["pageNum"]}_starttime'], 2)
        }
        if f"q{st.session_state['pageNum']}_explanation" in st.session_state:
            annotations[st.session_state["pageNum"]].update({"explanation": st.session_state[f"q{st.session_state['pageNum']}_explanation"]})
        with open(f"annotations/{st.session_state['userID']}.json", "w") as f:
            f.write(json.dumps(annotations))
        st.session_state['pageNum'] += 1

    st.session_state[f'q{st.session_state["pageNum"]}_starttime'] = time.time()

if __name__ == "__main__":
    # Initialize User ID
    expanded = False
    if "userID" not in st.session_state:
        st.session_state["userID"] = ""
        st.session_state["pageNum"] = -1
        expanded = True

    # Init the page
    with st.expander("Instructions", expanded=expanded):
        with open('instructions.md', "r") as f:
            instructions = f.read()
        st.markdown(instructions)

    # Load stories
    with open('../../storysumm.json', 'r') as f:
        storysumm = json.load(f)

    # Load the data
    claims = []
    with open('../../human_summaries.json', "r") as f:
        human_summaries = json.load(f)
        for storyid, summary in human_summaries.items():
            for i in range(len(summary)):
                claims.append({
                    'story': storysumm[storyid]['story'],
                    'summary': ' '.join(summary[:i]) + f" **:orange[{summary[i]}]** " + ' '.join(summary[i+1:]),
                    'claim': summary[i]
                })

    # Collect UserID
    if st.session_state['pageNum'] < 0:
        st.markdown(
            'Please enter your assigned user ID below to start the task. You can stop the task and revisit it later. Your progress will be saved connected to your user ID.')

        valid_ids = ['test1', 'test2', 'test3']
        if st.session_state["userID"] == "" or st.session_state["userID"] not in valid_ids:
            st.session_state["userID"] = st.text_input("Enter your assigned user ID:")
        if st.session_state["userID"] in valid_ids:
            st.success('Thank you!')
            # Next button moves on to next question
            st.button("Next", disabled=False, on_click=next_click)
        if st.session_state["userID"] == 'download':
            # We can download all files.
            annotations = {}
            files = glob.glob(pathname="annotations/*")
            for output_name in files:
                with open(output_name, "r") as file:
                    st.write(output_name)
                    try:
                        annotations[output_name.split('/')[-1].split('.json')[0]] = json.loads(file.readline())
                    except:
                        st.write("Failed")
                        continue

            btn = st.download_button(
                label="Download all annotations",
                data=json.dumps(annotations, indent=2),
                file_name="human_summary_annotations.json",
            )
    elif st.session_state["pageNum"] == len(claims):
        expanded = True
        st.success('You have finished the task. Please send us a message on Upwork and thank you for your work!')
    else:
        # Show a question
        st.markdown('## Story')
        st.write(claims[st.session_state['pageNum']]['story'])
        st.markdown('## Summary')
        st.markdown(claims[st.session_state['pageNum']]['summary'])

        st.markdown(f'### Annotation {int(st.session_state["pageNum"]) + 1}/{len(claims)}')

        disabled = False

        choices = [
            "Yes",
            "No",
            "N/A, just commentary",
        ]
        st.radio(
            "Is the orange sentence in the summary consistent with the story?",
            choices,
            key=f"q{st.session_state['pageNum']}_radio",
            index=None
        )

        if st.session_state[f"q{st.session_state['pageNum']}_radio"] == None:
            disabled = True

        if st.session_state[f"q{st.session_state['pageNum']}_radio"] == 'No':
            st.text_area(
                "Explain why this sentence is inconsistent with the story",
                key = f"q{st.session_state['pageNum']}_explanation",
            )#.replace('"', "'")
            if st.session_state[f"q{st.session_state['pageNum']}_explanation"] == "":
                disabled = True

        st.button("Next", disabled=disabled, on_click=next_click)
