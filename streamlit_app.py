import streamlit as st
import subprocess
import sys
import os

st.title("Fake News Detection System")

st.write("Click button to start Flask App")

if st.button("Start App"):

    st.write("Starting server...")

    subprocess.Popen(
        [sys.executable, "app.py"]
    )

    st.success("App started")

    st.write("Open in browser:")
    st.code("http://127.0.0.1:5000")