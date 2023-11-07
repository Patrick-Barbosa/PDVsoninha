# import banco
import pymysql
import ssl
# --------------
import pandas as pd
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import os

db_config = {
    'host': st.secrets["DATABASE_HOST"],
    'user': st.secrets["DATABASE_USERNAME"],
    'password': st.secrets["DATABASE_PASSWORD"],
    'database': st.secrets["DATABASE"],
    'autocommit': True,
}

ssl_config = {
    'ssl': {
        'ca': 'cert.pem',
        'ssl_version': ssl.PROTOCOL_TLSv1_2,  
    }
}
db_config.update(ssl_config)

def Nomes():
    conn = pymysql.connect(**db_config)
    query = "SELECT Nome FROM dClientes"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def tela_inicial():
    st.set_page_config(initial_sidebar_state="collapsed")
    st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] {
        display: none
    }
    </style>
    """,
    unsafe_allow_html=True,
    )
    nomes = Nomes()
    st.title("Ponto de Venda : Sonia Tech")
    st.subheader("Bem Vindo ao PDV da Sonia, o Famoso Sonia Tech")
    name_input = st.selectbox(
    "Digite Seu Nome Abaixo:",
    nomes, ## Lista de nomes (dClientes)
    key='name',
    index = None,
    placeholder='Selecione seu nome'
    )
    butao_compra = st.button("Fazer Compra")
    nome = st.session_state.name
    if butao_compra:
        switch_page("Tela_Compra")
        
    st.markdown("""
            <style>
            footer {
                visibility: hidden;
            }
            footer:after{
                content: 'Feito por Data Analytics';
                visibility: visible;
                display: block;
                position: relative;
                #background-color: red;
                padding: 5px;
                top: 2px;
                text-align: left;
            }
            </style>
            """ , unsafe_allow_html=True)

if __name__ == "__main__":
    tela_inicial()