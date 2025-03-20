import streamlit as st

# PostgreSQL connection
def get_postgres_conn():
    return st.connection("postgresql", type="sql")
