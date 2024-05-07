# import banco
import pymysql
# --------------
import pandas as pd
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

db_config = {
    'host': st.secrets["DATABASE_HOST"],
    'user': st.secrets["DATABASE_USERNAME"],
    'password': st.secrets["DATABASE_PASSWORD"],
    'database': st.secrets["DATABASE"],
    'autocommit': True,
}

def Nomes():
    conn = pymysql.connect(**db_config)
    query = "SELECT Nome FROM dClientes"
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def tela_inicial():
    st.set_page_config(initial_sidebar_state="collapsed", page_title="Soninha Tech",  page_icon="🏪", menu_items={
        'About': """Soninha Tech
        Feito por Data Analytics, caso queira suporte ou tenha alguma sugestão, entre em contato conosco.
        Envie um e-mail para data_analytics@grupotrigo.com.br
        """
    })
    st.markdown(
        """
    <style>
    [data-testid="collapsedControl"] {
        display: none
    }
    footer {
        visibility: hidden;
    }
    footer:before{
        content: '🧠 Feito por João, Hugo & Patrick';
        visibility: visible;
        display: block;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    nomes = Nomes()
    st.title("Delícias da Tia Sônia")
    st.subheader("Bem Vindo a lojinha da Sonia, o famoso Sônia Tech")
    name_input = st.selectbox(
        "Digite Seu Nome Abaixo:",
        nomes,  # Lista de nomes (dClientes)
        key='name',
        index=None,
        placeholder='Selecione seu nome'
    )

    col1, col2, col3, col4 = st.columns(4)
    nome = st.session_state.name
    with col1:
        butao_compra = st.button("Fazer Compra", type="primary")
        if butao_compra and nome != None:
            switch_page("Tela_Compra")
        elif butao_compra and nome == None:
            st.error("Você não digitou um nome", icon="🚨")
    with col2:
        botao_pagemento = st.button("Pagar Dívidas", type="secondary")
        if botao_pagemento and nome != None:
            switch_page("Tela_Pagamento")
        elif botao_pagemento and nome == None:
            st.error("Você não digitou um nome", icon="🚨")
    st.divider()


if __name__ == "__main__":
    tela_inicial()
