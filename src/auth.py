# src/auth.py
import streamlit as st

def render_login_screen():
    st.title("Login to Stock Street")
    st.markdown("""
    Welcome to Stock Street. Please authenticate with your 
    Google Account to initialize your account and access your stocks journal.
    """)
    if st.button("Authenticate with Google", type="primary", width='content'):
        st.login()
    st.stop()

def render_sidebar_profile():
    st.sidebar.markdown("### **User Authentication Identity**")
    st.sidebar.text(f"Identity: {st.user.name}")
    st.sidebar.text(f"Account: {st.user.email}")
    
    if st.sidebar.button("Disconnect Session", type="secondary", width='stretch'):
        st.logout()
        st.rerun()