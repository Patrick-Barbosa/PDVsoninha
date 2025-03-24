import pandas as pd
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from utils import get_postgres_conn, md_personalization
from sqlalchemy import text


def Nomes():
    conn = get_postgres_conn()
    schema = st.secrets["schema"]
    df = conn.query(f"SELECT nome, telefone FROM {schema}.dclientes", ttl = 10)
    df['nome'] = df['nome'].str.title()
    df = df.sort_values('nome')
    return df


def update_phone(nome, telefone):
    try:
        conn = get_postgres_conn()
        schema = st.secrets["schema"]
        # Use proper parameter binding with quotes for text comparison
        sql = text(f"UPDATE {schema}.dclientes SET telefone = :telefone WHERE nome ILIKE :nome")
        
        with conn.session as session:
            session.execute(
                sql,
                {"telefone": telefone, "nome": nome}
            )
            session.commit()
    except Exception as e:
        st.error(f"Erro ao atualizar telefone: {str(e)}")


def validate_phone(phone):
    # check if is between 8 and 11 digits:
    if len(str(phone)) >= 8 and len(str(phone)) <= 11:
        return True
    else:
        return False
    

@st.dialog("Precisamos do seu número de telefone")
def collect_phone():
    phone = st.number_input("Digite seu telefone:", placeholder='(XX) 9XXXX-XXXX', min_value=0, max_value=None, value=None)
    if st.button("Confirmar"):
        is_valid = validate_phone(phone)
        if is_valid:
            update_phone(st.session_state.name, phone)
            st.session_state.telefone = 1
            st.rerun()
        else:
            st.error("O telefone deve ter no máximo 11 dígitos", icon="🚨")


def tela_inicial():
    if 'telefone' not in st.session_state:
        st.session_state.telefone = 0
    else:
        if st.session_state.telefone == 1:
            switch_page("Tela_Compra")
            
    st.set_page_config(initial_sidebar_state="collapsed", page_title="Soninha Tech",  page_icon="🏪", menu_items={
        'About': """Soninha Tech
        Feito por Data Analytics, caso queira suporte ou tenha alguma sugestão, entre em contato conosco.
        Envie um e-mail para data_analytics@grupotrigo.com.br
        """
    })
    st.markdown(
        md_personalization(),
        unsafe_allow_html=True,
    )
    st.markdown("""
    <style>
        [data-testid="stNumberInputStepUp"] {display: none;}
        [data-testid="stNumberInputStepDown"] {display: none;}
        div[data-baseweb] {border-radius: 4px;}
    </style>""",
    unsafe_allow_html=True)

    nomes = Nomes()
    st.title("Delícias da Tia Sônia")
    st.subheader("Bem Vindo a lojinha da Sonia, o famoso Sônia Tech")
    name_input = st.selectbox(
        "Digite Seu Nome Abaixo:",
        nomes['nome'],  # Lista de nomes (dClientes)
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
            user_phone = nomes[nomes['nome'] == st.session_state.name]['telefone']
            
            if user_phone.isnull().sum() > 0:
                collect_phone()
            else:
                switch_page("Tela_Compra")
    with col2:
        botao_pagemento = st.button("Pagar Dívidas", type="secondary")
        if botao_pagemento and st.session_state.name != None:
            switch_page("Tela_Pagamento")

    if butao_compra and st.session_state.name == None:
            st.error("Você não digitou um nome", icon="🚨")
    if botao_pagemento and st.session_state.name == None:
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
