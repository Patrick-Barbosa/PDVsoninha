import pandas as pd
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from db_config import get_postgres_conn

db_config = {
    'host': st.secrets["DATABASE_HOST"],
    'user': st.secrets["DATABASE_USERNAME"],
    'password': st.secrets["DATABASE_PASSWORD"],
    'database': st.secrets["DATABASE"],
    'autocommit': True,
}

def Nomes():
    conn = get_postgres_conn()
    df = conn.query("SELECT nome FROM dev.dclientes", ttl = 10)
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
        key='nome',
        index=None,
        placeholder='Selecione seu nome'
    )

    col1, col2, col3, col4 = st.columns(4)
    
    if 'name' not in st.session_state:
        st.session_state.name = None
    if 'nome' not in st.session_state:
        st.session_state.nome = None

    st.session_state.name = st.session_state.nome

    with col1:
        butao_compra = st.button("Fazer Compra", type="primary")
        if butao_compra and st.session_state.name != None:
            switch_page("Tela_Compra")
        elif butao_compra and st.session_state.name == None:
            st.error("Você não digitou um nome", icon="🚨")
    with col2:
        botao_pagemento = st.button("Pagar Dívidas", type="secondary")
        if botao_pagemento and st.session_state.name != None:
            switch_page("Tela_Pagamento")
        elif botao_pagemento and st.session_state.name == None:
            st.error("Você não digitou um nome", icon="🚨")
    st.write(' ')
    st.markdown(
        """
        Seu nome não está aqui? [Clique Aqui](https://forms.office.com/Pages/ResponsePage.aspx?id=3GyatybLvU2MnuuPjHR9r4pFuuHnKhJGn0b9oLFKKfhUMUZNR0JERVFTRExPWEhBSFlERU1YREFNNi4u)
        """,
        unsafe_allow_html=True
    )
    st.divider()


if __name__ == "__main__":
    tela_inicial()
