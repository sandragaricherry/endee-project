import streamlit as st
import pandas as pd
from resume_matcher import ResumeMatcher
import os

# Set page config
st.set_page_config(page_title="Endee Resume Matcher", page_icon="📄", layout="wide")

# Initialize matcher (cached to avoid reloading model)
@st.cache_resource
def get_matcher():
    matcher = ResumeMatcher()
    # Check if index is empty (if possible) or just assume persistence
    # We can try a lightweight query or just let user ingest if needed.
    # But for UX, let's try to ingest if it feels empty (optional)
    # For now, we rely on persistence.
    return matcher

try:
    matcher = get_matcher()
    if matcher.index is None:
        st.error(f"Endee index could not be initialized at {matcher.base_url}")
        st.info("If your Endee server is on a different port, set the `ENDEE_URL` environment variable.")
except Exception as e:
    st.error(f"Failed to initialize matcher: {e}")
    st.stop()

st.title("Endee Resume Matcher 🚀")
st.markdown("Semantic search for resumes using **Endee** vector database.")

# Sidebar for controls
with st.sidebar:
    st.header("Search Filters")
    min_years = st.slider("Min Years of Experience", 0, 20, 0)
    
    role_filter = st.selectbox(
        "Filter by Role", 
        ["Any", "Senior Frontend Engineer", "SDE-II", "Backend Developer", "Data Scientist", "DevOps Engineer"]
    )
    
    selected_skills = st.multiselect(
        "Required Skills (Any of)",
        ["React", "Python", "AWS", "Docker", "Java", "Go", "Rust", "Kubernetes"]
    )
    
    min_score = st.slider("Minimum Match Score", 0.0, 1.0, 0.35, step=0.05)
    
    if st.button("Re-ingest Data"):
        matcher.ingest("data/resumes.json")
        st.success("Data re-ingested!")

# Main search area
query = st.text_input("Enter Job Description or Keywords", placeholder="e.g. Senior React developer with AWS experience")

if st.button("Search") or query:
    filters = {}
    if min_years > 0:
        filters["years"] = {"$gte": min_years}
    if role_filter != "Any":
        filters["role"] = {"$eq": role_filter}
    if selected_skills:
        filters["skills"] = {"$in": selected_skills}
        
    with st.spinner("Searching..."):
        results = matcher.query(query, filters)
        
    # Filter by score threshold
    results = [r for r in results if r['score'] >= min_score]
        
    if results:
        st.success(f"Found {len(results)} matches")
        
        # Display as cards
        for res in results:
            with st.expander(f"{res['role']} - Score: {res['score']}", expanded=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Summary:** {res['summary']}")
                    st.markdown(f"**Skills:** {', '.join(res['skills'])}")
                with col2:
                    st.metric("Years Exp", res['years'])
                    st.metric("Match Score", f"{res['score']:.4f}")
    else:
        st.warning(f"No matches found with score >= {min_score}. Try relaxing the filters or threshold.")

# Dataset Preview
with st.expander("View Raw Dataset"):
    import json
    with open("data/resumes.json") as f:
        data = json.load(f)
    st.dataframe(pd.DataFrame(data))
