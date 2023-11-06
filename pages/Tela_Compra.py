# import banco
import pymysql
import ssl
# --------------
import numpy as np
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

ssl_config = {
    'ssl': {
        'ca': 'cert.pem',
        'ssl_version': ssl.PROTOCOL_TLSv1_2,  
    }
}
db_config.update(ssl_config)
st.session_state.travaDuploClick = 0

def Obtem_Preco_Banco():
    conn = pymysql.connect(**db_config)
    query = "SELECT * FROM dProdutos"
    df_precos = pd.read_sql(query, conn)
    conn.close()
    df_precos = df_precos.sort_values('Data', ascending=False).drop_duplicates('Item')
    return df_precos

def Tela_Compra():
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

    Verifica_Compras_No_Session_State()
    st.session_state.name = st.session_state.name
    if "nomeimutavel" in st.session_state: ##foda!!
        nome = st.session_state.nomeimutavel
    else:
        nome = st.session_state.name
    df_precos = Obtem_Preco_Banco()
    if 'travaDuploClick' not in st.session_state:
        st.session_state.travaDuploClick = 0

    st.title("Tela de Compra")
    st.subheader(f"Bem - Vindo, {nome.title()} faça sua compra abaixo.")
    col1,col2 = st.columns([2,1])
    col_but1,col_but2,col_but3= st.columns(3)
    with col1:
        product_input = st.selectbox(
    "Selecione o produto consumido",
    df_precos['Item'],
    key='product',
    index = None,
    placeholder='Selecione o produto'
    )
        
    with col2:
        quantity_input = st.number_input(
    "Selecione a quantidade comprada",
    min_value=1,
    max_value=10,
    step=1,
    key='quantity'
    ) 
    with col_but1:
        butao_comprar_mais = st.button("Salvar Compra",type='primary')
    with col_but2:
        butao_conclusao = st.button("Finalizar a Compra")
    with col_but3:
        butao_cancelar = st.button("Cancelar Compras")
    if butao_conclusao:
        if st.session_state.df_compras.empty:
            st.error("Você não cadastrou nenhuma compra!!!",icon="🚨")     
        else:
            switch_page("Tela_Conclusao")
    if butao_comprar_mais:
        st.success(f"Compra de {st.session_state.quantity} de {st.session_state.product} com sucesso")
        st.session_state.Flag_Clicou_aqui = True
        Salva_Compra()
    Escreve_Compras()
    if butao_cancelar:
        Cancela_Compras()
        st.session_state.df_compras()

def Salva_Compra():
    df_precos = Obtem_Preco_Banco()
    nome = st.session_state.name
    produto = st.session_state.product
    quantidade = st.session_state.quantity
    preco = df_precos.query("Item==@produto")['Valor'].iloc[0] * quantidade
    
    #Alteraçõo feita para corrigir o erro de append usando concat
    nova_compra = pd.DataFrame({"Nome": [nome], "Produto": [produto], "Quantidade": [quantidade], "Preco": [preco]})
    st.session_state.df_compras = pd.concat([st.session_state.df_compras, nova_compra], ignore_index=True)
    
    # Código estava dando erro pq não tem atributo append
    # AttributeError: 'DataFrame' object has no attribute 'append'
    #st.session_state.df_compras = st.session_state.df_compras.append({"Nome":nome,
     ##                                                               "Quantidade":quantidade,
       #                                                              "Preco":preco},ignore_index=True)
    
def Escreve_Compras():
    st.subheader("Compras Registradas:")
    if not st.session_state.df_compras.empty:
        st.write(st.session_state.df_compras)
        Valor_Gasto = np.sum(st.session_state.df_compras['Preco']*st.session_state.df_compras['Quantidade'])
        st.subheader(f"Gasto Total **{Valor_Gasto:.2f}**")
    else:
        st.text("Nenhuma compra registrada.")         


def Verifica_Compras_No_Session_State():
    if 'df_compras' not in st.session_state:
        st.session_state.df_compras = pd.DataFrame(columns=["Nome", "Produto", "Quantidade","Preco"])
        return st.session_state.df_compras


def Cancela_Compras():
    st.session_state.df_compras = pd.DataFrame(columns=["Nome", "Produto", "Quantidade","Preco"])
    switch_page("Tela_Nome")


if __name__ == "__main__":
    Tela_Compra()