import streamlit as st
import json
import os
import glob
import time
import random

random.seed(12058563628920)

def next_click():
    # Make sure the annotations file exists
    os.makedirs("rewrite_eval/annotations", exist_ok=True)
    if not os.path.exists(f"rewrite_eval/annotations/{st.session_state['userID']}.json"):
        with open(f"rewrite_eval/annotations/{st.session_state['userID']}.json", "w") as f:
            f.write(json.dumps({}))
            
    # Read the existing annotations
    with open(f"rewrite_eval/annotations/{st.session_state['userID']}.json", "r") as f:
        annotations = json.load(f)

    if st.session_state["pageNum"] == -1:
        # If on the home page, skip ahead to the first incomplete annotation
        st.session_state['pageNum'] += 1
        while str(st.session_state["pageNum"]) in annotations:
            st.session_state['pageNum'] += 1

        # Start the completion time clock
        st.session_state["starttime"] = time.time()
    elif st.session_state['qpart'] == 0:
        # Go to the next part of the question
        st.session_state['qpart'] += 1
    elif st.session_state['qpart'] == 1 and st.session_state["rewrite"].startswith("Yes"):
        # Go to the next part of the question
        st.session_state['qpart'] += 1
    else:
        # Write the completed annotation with completion time
        endtime = time.time() # this will be in seconds
        annotations[st.session_state["pageNum"]] = {
            "consistent": st.session_state["consistent"],
            "rewrite": st.session_state["rewrite"],
            "timing": round(endtime - st.session_state["starttime"], 2)
        }
        if st.session_state["rewrite"].startswith("Yes"):
            for i in range(len(claims[st.session_state['pageNum']]['explanation'])):
                annotations[st.session_state["pageNum"]][f"exp_{i}"] = st.session_state[f"q{st.session_state['pageNum']}_e_radio_{i}"]
        if st.session_state["consistent"] == "No":
            annotations[st.session_state["pageNum"]]["reason"] = st.session_state["reason"]
        with open(f"rewrite_eval/annotations/{st.session_state['userID']}.json", "w") as f:
            f.write(json.dumps(annotations))

        # Reset values
        st.session_state['pageNum'] += 1
        st.session_state['qpart'] = 0
        st.session_state["starttime"] = time.time()
    
def prep_download_file():
    # Download annotation files from Streamlit
    annotations = {}
    files = glob.glob(pathname="rewrite_eval/annotations/*")
    for output_name in files:
        with open(output_name, "r") as file:
            st.write(output_name)
            try:
                annotations[output_name.split('/')[-1].split('.json')[0]] = json.loads(file.readline())
            except:
                st.write("Failed")
                continue
    return annotations

def consistent_q():
    # Ask whether the line is consistent with the story
    choices = [
        "Yes",
        "No",
        "N/A, just commentary",
    ]
    st.session_state["consistent"] = st.radio(
        "Is the orange sentence in the summary consistent with the story?",
        choices,
        key=f"q{st.session_state['pageNum']}_c_radio",
        index=None
    )

def rewrite_q():
    # Ask whether the rewrite is preferred
    choices = [
        "Yes, the rewrite is more accurate and clear.",
        "No, the rewrite is worse than the orange sentence.",
        "Neutral, both sentences are similar quality.",
    ]
    st.radio(
        "Would you swap the orange sentence in the summary with this rewrite?",
        choices,
        key=f"q{st.session_state['pageNum']}_r_radio",
        index=None
    )
    if st.session_state[f"q{st.session_state['pageNum']}_r_radio"]:
        if st.session_state[f"{st.session_state['pageNum']}_order"] == 0:
            if st.session_state[f"q{st.session_state['pageNum']}_r_radio"].startswith('Yes'):
                st.session_state["rewrite"] = "No, the rewrite is worse than the orange sentence."
            elif st.session_state[f"q{st.session_state['pageNum']}_r_radio"].startswith('No'):
                st.session_state["rewrite"] = "Yes, the rewrite is more accurate and clear."
            else:
                st.session_state["rewrite"] = st.session_state[f"q{st.session_state['pageNum']}_r_radio"]
        else:
            st.session_state["rewrite"] = st.session_state[f"q{st.session_state['pageNum']}_r_radio"]
    
def explanation_q():
    # Ask about the different parts of the explanation
    choices = [
        "Yes, correcting this issue improves the sentence.",
        "Neutral, correcting this issue is okay but not necessary.",
        "No, the issue described is not a reasonable interpretation of the text or is overly nitpicky.",
    ]
    if st.session_state[f"{st.session_state['pageNum']}_order"]:
        st.markdown("Consider the following reasons why the **rewrite** may be better than the **:orange[orange sentence]**.")
    else:
        st.markdown("Consider the following reasons why the **:orange[orange sentence]** may be better than the **rewrite**.")
    for i, exp in enumerate(claims[st.session_state['pageNum']]['explanation']):
        st.markdown(f"**Reason {i}:** {exp}")
        st.radio(
            "Is the issue described by this reasoning important to correct?",
            choices,
            key=f"q{st.session_state['pageNum']}_e_radio_{i}",
            index=None
        )

if __name__ == "__main__":
    # Initialize state
    expanded = False
    if "userID" not in st.session_state:
        st.session_state["userID"] = ""
        st.session_state["pageNum"] = -1
        st.session_state["qpart"] = 0
        st.session_state["answer"] = None
        st.session_state["explanation"] = ""
        st.session_state["reason"] = None
        expanded = True

    # Init the page
    with st.expander("Instructions", expanded=expanded):
        with open('rewrite_eval/instructions.md', "r") as f:
            instructions = f.read()
        st.markdown(instructions)

    # Load stories
    with open('rewrite_eval/storysumm_w_subj.json', 'r') as f:
        storysumm = json.load(f)

    # Load the data
    claims = []
    with open('rewrite_eval/human_summaries.json', "r") as f:
        human_summaries = json.load(f)
        for storyid, val in human_summaries.items():
            summary = val['summary']
            for i in range(len(summary)):
                # Skip this claim if there is no rewrite for it
                if val['rewrites'][i] == "":
                    continue

                if f"{len(claims)}_order" in st.session_state:
                    order = st.session_state[f"{len(claims)}_order"]
                else:
                    order = random.randint(0, 1)
                    st.session_state[f"{len(claims)}_order"] = order
                if order:
                    claims.append({
                        'story': storysumm[storyid]['story'],
                        'summary': ' '.join(summary[:i]) + f" **:orange[{summary[i]}]** " + ' '.join(summary[i+1:]),
                        'claim': summary[i],
                        'explanation': val['explanation'][i],
                        'rewrite': val['rewrites'][i],
                    })
                else:
                    claims.append({
                        'story': storysumm[storyid]['story'],
                        'summary': ' '.join(summary[:i]) + f" **:orange[{val['rewrites'][i]}]** " + ' '.join(summary[i+1:]),
                        'claim': val['rewrites'][i],
                        'explanation': val['explanation'][i],
                        'rewrite': summary[i],
                    })


    if st.session_state['pageNum'] < 0:
        # Collect UserID
        st.markdown(
            'Please enter your assigned user ID below to start the task. You can stop the task and revisit it later. Your progress will be saved connected to your user ID. Answer each question carefully as you will not be able to go back to a previous question once you have answered it. **Read each comparison question carefully as the ordering of options changes.**')

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
                file_name="human_summary_annotations.json",
            )
    elif st.session_state["pageNum"] == len(claims):
        # End of the task.
        expanded = True
        st.success('You have finished the task. Please send us a message on Upwork and thank you for your work!')
    else:
        # Show a question.
        st.markdown('## Story')
        st.write(claims[st.session_state['pageNum']]['story'])
        st.markdown('## Summary')
        st.markdown(claims[st.session_state['pageNum']]['summary'])

        st.markdown(f'### Annotation {int(st.session_state["pageNum"]) + 1}/{len(claims)}')

        next_disabled = False

        print(st.session_state['pageNum'], st.session_state['qpart'])
        if st.session_state["qpart"] == 0:
            # First ask the consistency question
            consistent_q()
            
            if st.session_state[f"q{st.session_state['pageNum']}_c_radio"] == None:
                next_disabled = True

            if st.session_state[f"q{st.session_state['pageNum']}_c_radio"] == 'No':
                st.session_state["reason"] = st.text_area(
                    "Explain why this sentence is inconsistent with the story",
                    key=f"q{st.session_state['pageNum']}_explanation",
                )
                if st.session_state[f"q{st.session_state['pageNum']}_explanation"] == "":
                    next_disabled = True
        else:
            # Show the rewrite (but actually this is the original)
            st.markdown(f"**Rewrite:** {claims[st.session_state['pageNum']]['rewrite']}")

            if st.session_state["qpart"] == 1:
                # Ask about the rewrite
                rewrite_q()

                if st.session_state[f"q{st.session_state['pageNum']}_r_radio"] == None:
                    next_disabled = True
            else:
                # Ask about the explanation if they preferred the rewrite
                explanation_q()

                for i, exp in enumerate(claims[st.session_state['pageNum']]['explanation']):
                    if st.session_state[f"q{st.session_state['pageNum']}_e_radio_{i}"] == None:
                        next_disabled = True


        st.button("Next", disabled=next_disabled, on_click=next_click)
