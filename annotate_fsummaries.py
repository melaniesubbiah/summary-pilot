import os

import streamlit as st
import streamlit_nested_layout
from text_highlighter import text_highlighter
import glob
import json
import nltk
import csv
import random

query = st.query_params
format_1 = [1, 28, 18, 12, 22]
format_2 = [4, 7, 3, 6, 15, 23]
format_3 = [14, 21, 10, 30, 24]

to_download = ""
if "download" in query:
    # We can download all files.
    annotations = []
    files = glob.glob(pathname="data/annotations/*/*")
    for output_name in files:
        with open(output_name, "r") as file:
            st.write(output_name)
            try:
                annotations.append(json.loads(file.readline()))
            except:
                st.write("Failed")
                continue

    btn = st.download_button(
            label="Download all annotations",
            data=json.dumps(annotations, indent=2),
            file_name="annotations.json",
        )
elif any(["username" not in query, "summaryid" not in query]):
    # display summarization guidelines
    # load summarization guideline from guideline.md
    guideline_name = "fsummary_guideline.md"
    with open(guideline_name, "r") as f:
        guideline = f.read()
    st.markdown(guideline)
else:
    st.set_page_config(layout="wide")
    nltk.download('punkt')
    username = query["username"]
    summary_id = query["summaryid"]
    peek = 0
    if "peek" in query:
        peek = query["peek"]

    if 'clicked' not in st.session_state:
        st.session_state.clicked = False
    def clicked():
        st.session_state.clicked = True

    col1, col2 = st.columns(2)
    # open the jsonl containing all source articles into a dictionary
    # each line is a json contains two entries: "id" and "text"
    with open(f"fsummaries.json", "r") as f:
        source_articles = json.load(f)
    # get the text of the article
    story_id = source_articles[summary_id]['story-id']
    if story_id not in format_1 + format_2 + format_3:
        st.markdown("Wrong URL.")
    else:
        random.seed(story_id)
        article_text = source_articles[summary_id]['story'].replace('\n', '\n\n')
        if story_id in format_1 or story_id in format_3:
            summary_text = source_articles[summary_id]['fsummary']
        else:
            summary_text = source_articles[summary_id]['summary']
        actual_subj = source_articles[summary_id]['subj']
        is_subj = source_articles[summary_id]['fsummary_subj']
        themes = source_articles[summary_id]['fsummary_themes']

        with col1.container(height=700):
            with st.container():
                st.markdown("### Story")
                st.markdown(article_text)
                st.markdown("---")
        with col2.container(height=700):
            with st.container():
                outfolder = f"data/annotations/{username}"
                os.makedirs(outfolder, exist_ok=True)
                output_name = os.path.join(outfolder, f"{summary_id}.jsonl")
                selected = dict()
                selected = dict()
                if peek == '1':
                    for i, line in enumerate(summary_text):
                        if is_subj[i] == 1:
                            if actual_subj[i][0] == is_subj[i]:
                                st.markdown(f":red[Theme {themes[i]}: {line}]")
                            else:
                                st.markdown(f":red[Objective swapped to Theme {themes[i]} Subjective, {line}]")
                        else:
                            if actual_subj[i][0] == is_subj[i]:
                                st.markdown(f":green[{line}]")
                            else:
                                st.markdown(f":green[Subjective Theme {actual_subj[i][1]} swapped to Objective: {line}]")
                else:
                    if story_id in format_1:
                        st.markdown("### Summary")
                        st.markdown(" ".join(summary_text))
                        st.markdown(f"### Summary Evaluation")
                        st.markdown("For each line in the summary, evaluate if it is consistent with the story.")
                        st.markdown("Along with the selected input, you can provide an explanation as to why you selected a particular answer, *if you mark the line as inconsistent to the story*. When evaluating, remember that the events and details described in a consistent summary should not misrepresent details from the story or include details that are unsupported by the story.")
                        st.markdown("#### Answers")
                        for i, line in enumerate(summary_text):
                            st.markdown(f"Line {i+1}: {line}")
                            binary_choice_list = ["Yes", "No", "N/A, just commentary"]
                            selected[f"consistent_{i}"] = st.radio(
                                "Is this line in the summary consistent with the story?",
                                key=hash("consistent")+i,
                                options=binary_choice_list,
                                index=None,
                            )
                            if selected[f"consistent_{i}"] == "No":
                                selected[f"explanation_{i}"] = st.text_area("Provide an explanation for your selection.", key=hash("explanation")+i)
                    if story_id in format_2:
                        with open(f"storysumm_claim_level.json", "r") as f:
                            claims = json.load(f)
                        st.markdown("### Summary")
                        st.markdown(" ".join(summary_text))
                        st.markdown(f"### Summary Evaluation")
                        st.markdown("For some lines in the summary, choose between two potential candidates.")
                        for i, (line, is_subj) in enumerate(zip(summary_text, actual_subj)):
                            if is_subj[0] == 1 and is_subj[1] != 4:
                                obj_line = claims[f"{summary_id}_{i}"]["sentences"]["objective"]
                                if random.randint(0, 1) == 0:
                                    st.markdown(f"Line {i+1}: {line}")
                                    st.markdown(f"Alternate Line {i+1}: {obj_line}")
                                    selected[f"alternate_{i}"] = "objective"
                                else:
                                    st.markdown(f"Line {i+1}: {obj_line}")
                                    st.markdown(f"Alternate Line {i+1}: {line}")
                                    selected[f"alternate_{i}"] = "subjective"
                                binary_choice_list = ["Yes", "No"]
                                selected[f"consistent_{i}"] = st.radio(
                                    "Would you swap the line with its alternate?",
                                    key=hash("consistent")+i,
                                    options=binary_choice_list,
                                    index=None,
                                )
                                selected[f"explanation_{i}"] = st.text_area("Provide an explanation for your selection.", key=hash("explanation")+i)
                    if story_id in format_3:
                        st.markdown("### Summary")
                        st.markdown(" ".join(summary_text))
                        st.markdown(f"### Summary Evaluation")
                        st.markdown("For each line in the summary, highlight any portion that makes the line ambiguous with respect to the story. You can do so by clicking and dragging the cursor on the text.")
                        st.markdown("Along with the selected input, you can provide an explanation as to why you highlighted this portion as ambiguous.")
                        st.markdown("#### Answers")
                        for i, line in enumerate(summary_text):
                            selected[f"annotation_{i}"] = text_highlighter(
                                text=line,
                                labels=[("ambiguous", "red")],
                                annotations=[]
                            )
                            if selected[f"annotation_{i}"]:
                                selected[f"explanation_{i}"] = st.text_area("Provide an explanation for your selection.", key=hash("explanation")+i)
                    annotation = {
                        "id": summary_id,
                        "username": username,
                        "story": article_text,
                        "summary": summary_text,
                        "annotation": selected,
                    }
                    # create a submit button and refresh the page when the button is clicked
                    if st.button("Submit", on_click=clicked):
                        os.makedirs("data/annotations", exist_ok=True)
                        with open(output_name, "w") as f:
                            f.write(json.dumps(annotation) + "\n")
                        # display a success message
                        st.success("Annotation submitted successfully!")
