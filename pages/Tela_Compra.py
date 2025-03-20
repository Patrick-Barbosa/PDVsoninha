# --------------
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import time
import threading
from datetime import datetime
from db_config import get_postgres_conn
from sqlalchemy import text

db_config = {
    'host': st.secrets["DATABASE_HOST"],
    'user': st.secrets["DATABASE_USERNAME"],
    'password': st.secrets["DATABASE_PASSWORD"],
    'database': st.secrets["DATABASE"],
    'autocommit': True,
}

st.session_state.travaDuploClick = 0


def Obtem_Preco_Banco():
    conn = get_postgres_conn()
    df_precos = conn.query("SELECT * FROM dev.dprodutos", ttl=10)
    df_precos = df_precos.sort_values(
        'data', ascending=False).drop_duplicates('produto')
    df_precos['Filtro'] = df_precos['produto'] + \
        ' - R$: ' + df_precos['valor'].astype(str)
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
        if 'name' not in st.session_state:
            st.session_state.name = None
        st.session_state.name = st.session_state.name
        
        df_precos = Obtem_Preco_Banco()
        if 'travaDuploClick' not in st.session_state:
            st.session_state.travaDuploClick = 0

        st.title("Cardápio")
        col1, col2 = st.columns([2, 1])
        use_category_filter = st.checkbox("Deseja procurar por categoria?")

        if use_category_filter:
            category_input = st.selectbox(
                "Selecione a categoria",
                df_precos['categoria'].unique(),
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
                Salva_Compra()
                st.success(
                    f"{st.session_state.quantity} {df_precos.loc[df_precos['Filtro'] == st.session_state.product, 'produto'].iloc[0]} adicionado ao carrinho!")
            else:
                st.error("Você não selecionou nenhum produto!!!", icon="🚨")
        Escreve_Compras()
        col_but2, col_but3,col_but4 = st.columns(3)
        tamanhoDfCompras = len(st.session_state.df_compras)
        with col_but2:
            butao_conclusao_fiado = st.button("Finalizar Compra no Fiado")
        with col_but3:
            butao_conclusao_pagamento= st.button("Ir para a Tela de Pagamento")
        with col_but4:
            butao_cancelar = st.button("Cancelar Compras")
        if butao_conclusao_pagamento:
            if tamanhoDfCompras > 0:
                switch_page("Tela_Conclusao")
            else:
                st.error("Você não adicionou nenhum produto ao carrinho!!!", icon="🚨")
        if butao_cancelar:
                st.session_state.clear()
                switch_page("Tela_Nome")
        if butao_conclusao_fiado:
            if tamanhoDfCompras > 0:
                Finaliza_Compra(st.session_state.df_compras, False)
                st.session_state.clear()
                switch_page("Tela_Nome")
            else:
                st.error("Você não adicionou nenhum produto ao carrinho!!!", icon="🚨")
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
                            st.session_state.product, 'produto'].iloc[0]
    quantidade = st.session_state.quantity
    preco = df_precos.query("produto==@produto")['valor'].iloc[0] * quantidade

    # Fix concatenation warning by ensuring consistent dtypes
    nova_compra = pd.DataFrame({
        "Nome": [nome], 
        "Produto": [produto], 
        "Quantidade": [quantidade], 
        "Preco": [preco]
    }).astype({
        "Nome": str,
        "Produto": str,
        "Quantidade": int,
        "Preco": float
    })

    if st.session_state.df_compras.empty:
        st.session_state.df_compras = nova_compra
    else:
        st.session_state.df_compras = pd.concat(
            [st.session_state.df_compras, nova_compra], 
            ignore_index=True,
            verify_integrity=True
        )

def Escreve_Compras():
    st.subheader("Carrinho de Compras:")
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
    st.session_state.df_compras = pd.DataFrame(
        columns=["Nome", "Produto", "Quantidade", "Preco"])
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
    conn = get_postgres_conn()
    
    with conn.session as session:
        for index, row in df.iterrows():
            query = text("""
                INSERT INTO dev.fvendas 
                (data, nome, produto, qtd, valor, pago, data_pagamento, registro)
                VALUES (:data, :nome, :produto, :qtd, :valor, :pago, :data_pagamento, :registro)
            """)
            session.execute(query, {
                "data": data,
                "nome": row['Nome'],
                "produto": row['Produto'],
                "qtd": row['Quantidade'],
                "valor": row['Preco'],
                "pago": FlagPagamento == 'Sim',
                "data_pagamento": datapagamento,
                "registro": datahora
            })
        session.commit()

if __name__ == "__main__":
    Tela_Compra()
