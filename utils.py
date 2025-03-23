import streamlit as st

# PostgreSQL connection
def get_postgres_conn():
    return st.connection("postgresql", type="sql")

def md_personalization():
    return"""
    <style>
    [data-testid="stSidebarCollapsedControl"] {
        display: none
    }
    footer:before{
        content: '🧠 Feito por João, Hugo & Patrick';
        visibility: visible;
        display: block;
    }
    </style>
    """