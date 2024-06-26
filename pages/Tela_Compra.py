# import banco
import pymysql
# --------------
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import time
import threading
from datetime import datetime
db_config = {
    'host': st.secrets["DATABASE_HOST"],
    'user': st.secrets["DATABASE_USERNAME"],
    'password': st.secrets["DATABASE_PASSWORD"],
    'database': st.secrets["DATABASE"],
    'autocommit': True,
}

st.session_state.travaDuploClick = 0


def Obtem_Preco_Banco():
    conn = pymysql.connect(**db_config)
    query = "SELECT * FROM dProdutos"
    df_precos = pd.read_sql(query, conn)
    conn.close()
    df_precos = df_precos.sort_values(
        'Data', ascending=False).drop_duplicates('Produto')
    df_precos['Filtro'] = df_precos['Produto'] + \
        ' - R$: ' + df_precos['Valor'].astype(str)
    return df_precos


def Tela_Compra():
    try:
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

        Verifica_Compras_No_Session_State()
        st.session_state.name = st.session_state.name
        if "nomeimutavel" in st.session_state:  # foda!!
            nome = st.session_state.nomeimutavel
        else:
            nome = st.session_state.name
        df_precos = Obtem_Preco_Banco()
        if 'travaDuploClick' not in st.session_state:
            st.session_state.travaDuploClick = 0

        st.title("Cardápio")
        col1, col2 = st.columns([2, 1])
        use_category_filter = st.checkbox("Deseja procurar por categoria?")

        if use_category_filter:
            category_input = st.selectbox(
                "Selecione a categoria",
                df_precos['Categoria'].unique(),
                key='category',
                index=None,
                placeholder='Selecione a categoria'
            )

        with col1:
            product_input = st.selectbox(
                "Selecione o produto consumido",
                df_precos['Filtro'] if not use_category_filter else df_precos.query(
                    "Categoria==@category_input")['Filtro'],
                key='product',
                index=None,
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

        butao_comprar_mais = st.button("Adicionar ao carrinho", type='primary')

        if butao_comprar_mais:
            if product_input is not None and quantity_input != 0:
                st.session_state.Flag_Clicou_aqui = True
                Salva_Compra()
                st.success(
                    f"{st.session_state.quantity} {df_precos.loc[df_precos['Filtro'] == st.session_state.product, 'Produto'].iloc[0]} adicionado ao carrinho!")
            else:
                st.error("Você não selecionou nenhum produto!!!", icon="🚨")
        Escreve_Compras()
        col_but2, col_but3,col_but4 = st.columns(3)
        with col_but2:
            butao_conclusao_fiado = st.button("Finalizar a Compra e Pagar Depois")
        with col_but3:
            butao_conclusao_pagamento= st.button("Ir para a Tela de Pagamento")
        with col_but4:
            butao_cancelar = st.button("Cancelar Compras")

        if st.session_state.df_compras.shape[0] == 0 or "Cancelando" not in st.session_state or st.session_state.Cancelando == True :
            col_but2 = st.write(" ")
            col_but3 = st.write(" ")
            col_but4 = st.write(" ")
        else:
            if butao_conclusao_pagamento:
                switch_page("Tela_Conclusao")
            if butao_cancelar:
                Cancela_Compras()
            if butao_conclusao_fiado:
                Finaliza_Compra(st.session_state.df_compras, False)
                st.session_state.clear()
                switch_page("Tela_Nome")
    except Exception as e:
        st.title('Ops, erro no sistema')
        st.text('Voltando a página inicial')
        print(e)
        time.sleep(2)
        switch_page("Tela_Nome")
    


def Salva_Compra():
    st.session_state.Cancelando = False
    df_precos = Obtem_Preco_Banco()
    nome = st.session_state.name
    produto = df_precos.loc[df_precos['Filtro'] ==
                            st.session_state.product, 'Produto'].iloc[0]
    quantidade = st.session_state.quantity
    preco = df_precos.query("Produto==@produto")['Valor'].iloc[0] * quantidade

    # Alteraçõo feita para corrigir o erro de append usando concat
    nova_compra = pd.DataFrame({"Nome": [nome], "Produto": [
                               produto], "Quantidade": [quantidade], "Preco": [preco]})
    st.session_state.df_compras = pd.concat(
        [st.session_state.df_compras, nova_compra], ignore_index=True)

def Escreve_Compras():
    st.subheader("Compras Registradas:")
    if not st.session_state.df_compras.empty:
        st.dataframe(st.session_state.df_compras,hide_index=True)
        Valor_Gasto = np.sum(st.session_state.df_compras['Preco'])
        st.subheader(f"Gasto Total **{Valor_Gasto:.2f}**")
    else:
        st.text("Nenhuma compra registrada.")

def Verifica_Compras_No_Session_State():
    if 'df_compras' not in st.session_state:
        st.session_state.df_compras = pd.DataFrame(
            columns=["Nome", "Produto", "Quantidade", "Preco"])
        return st.session_state.df_compras

def Cancela_Compras():
    st.session_state.Cancelando = True
    st.session_state.clear()
    switch_page("Tela_Nome")
def Finaliza_Compra(df, FlagPagamento):
    st.session_state.Cancelando = True
    if 'travaDuploClick' not in st.session_state:
        st.session_state.travaDuploClick = 0
    st.session_state.travaDuploClick += 1
    if st.session_state.travaDuploClick == 1:
        # Dedicando um thread exclusivo pra subir no banco e não haver falhas
        thread_envio = threading.Thread(
            target=Envia_Dados_BD, args=(df, FlagPagamento))
        thread_envio.start()

    time.sleep(0.5)
    time.sleep(0.5)

    st.balloons()
    
    time.sleep(2)
    
def Envia_Dados_BD(df, FlagPagamento):
    datahora = datetime.now()
    data = datetime.now().date()
    datapagamento = data if FlagPagamento == 'Sim' else None
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    for index, row in df.iterrows():
        sql = "INSERT INTO fVendas (Data, Nome, Produto, Qtd, Valor, Pago, DataPagamento, Registro) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (data, row['Nome'], row['Produto'], row['Quantidade'],
                  row['Preco'], FlagPagamento, datapagamento, datahora)
        cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()
    Cancela_Compras()

if __name__ == "__main__":
    Tela_Compra()
