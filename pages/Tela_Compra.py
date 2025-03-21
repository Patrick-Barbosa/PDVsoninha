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

st.session_state.travaDuploClick = 0

schema = st.secrets["schema"]

def Obtem_Preco_Banco():
    conn = get_postgres_conn()
    df_precos = conn.query(f"SELECT * FROM {schema}.dprodutos", ttl=10)
    df_precos = df_precos.sort_values(
        'data', ascending=False).drop_duplicates('produto')
    df_precos['Filtro'] = df_precos['produto'] + \
        ' - R$: ' + df_precos['valor'].astype(str)
    df_precos = df_precos.sort_values(
        'produto', ascending=True)
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

        # Get first name by splitting the full name
        first_name = st.session_state.name.split()[0] if st.session_state.name else ""
        st.title(f"Olá, {first_name}.")
        st.subheader("O que deseja pedir hoje?")
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
                    "categoria==@category_input")['Filtro'],
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
        st.write(e)
        time.sleep(2)
        #switch_page("Tela_Nome")
    


def Salva_Compra():
    st.session_state.Cancelando = False
    df_precos = Obtem_Preco_Banco()
    nome = st.session_state.name
    produto = df_precos.loc[df_precos['Filtro'] ==
                            st.session_state.product, 'produto'].iloc[0]
    quantidade = st.session_state.quantity
    preco_unitario = df_precos.query("produto==@produto")['valor'].iloc[0]
    preco = preco_unitario * quantidade

    nova_compra = pd.DataFrame({
        "Nome": [nome], 
        "Produto": [produto], 
        "Quantidade": [quantidade], 
        "Preco_Unitario": [preco_unitario],
        "Preco": [preco]
    }).astype({
        "Nome": str,
        "Produto": str,
        "Quantidade": int,
        "Preco_Unitario": float,
        "Preco": float
    })

    if st.session_state.df_compras.empty:
        st.session_state.df_compras = nova_compra
    else:
        # Check if product already exists
        if produto in st.session_state.df_compras['Produto'].values:
            # Update quantity and price for existing product
            idx = st.session_state.df_compras['Produto'] == produto
            st.session_state.df_compras.loc[idx, 'Quantidade'] += quantidade
            st.session_state.df_compras.loc[idx, 'Preco'] = (
                st.session_state.df_compras.loc[idx, 'Quantidade'] * 
                st.session_state.df_compras.loc[idx, 'Preco_Unitario']
            )
        else:
            # Add new product
            st.session_state.df_compras = pd.concat(
                [st.session_state.df_compras, nova_compra], 
                ignore_index=True,
                verify_integrity=True
            )

def Remove_Item_Carrinho(index):
    st.session_state.df_compras = st.session_state.df_compras.drop(index).reset_index(drop=True)

def Update_Item_Quantity(index, change):
    current_qty = st.session_state.df_compras.loc[index, 'Quantidade']
    new_qty = current_qty + change
    
    if new_qty <= 0:
        # Remove item if quantity becomes 0 or negative
        st.session_state.df_compras = st.session_state.df_compras.drop(index).reset_index(drop=True)
    else:
        # Update quantity and recalculate total price
        st.session_state.df_compras.loc[index, 'Quantidade'] = new_qty
        st.session_state.df_compras.loc[index, 'Preco'] = (
            new_qty * st.session_state.df_compras.loc[index, 'Preco_Unitario']
        )

def Escreve_Compras():
    st.subheader("Carrinho de Compras:")
    if not st.session_state.df_compras.empty:
        # Ensure all required columns exist
        required_columns = ["Nome", "Produto", "Quantidade", "Preco_Unitario", "Preco"]
        missing_columns = [col for col in required_columns if col not in st.session_state.df_compras.columns]
        
        if missing_columns:
            # If Preco_Unitario is missing, calculate it from Preco and Quantidade
            if "Preco_Unitario" in missing_columns:
                st.session_state.df_compras["Preco_Unitario"] = st.session_state.df_compras["Preco"] / st.session_state.df_compras["Quantidade"]
        
        # Sort by product name for better organization
        df_sorted = st.session_state.df_compras.sort_values('Produto')
        
        for idx, row in df_sorted.iterrows():
            col1, col2, col3, col4 = st.columns([3, 0.5, 0.5, 0.5])
            with col1:
                st.text(f"{row['Quantidade']}x {row['Produto']} (R$ {row['Preco_Unitario']:.2f} cada) - Total: R$ {row['Preco']:.2f}")
            with col2:
                # Only show minus button if quantity > 1
                if row['Quantidade'] > 1:
                    if st.button("➖", key=f"minus_{idx}"):
                        Update_Item_Quantity(idx, -1)
                        st.rerun()
            with col3:
                if st.button("➕", key=f"plus_{idx}"):
                    Update_Item_Quantity(idx, 1)
                    st.rerun()
            with col4:
                if st.button("🗑️", key=f"delete_{idx}"):
                    Remove_Item_Carrinho(idx)
                    st.rerun()
        
        Valor_Gasto = np.sum(st.session_state.df_compras['Preco'])
        st.subheader(f"Gasto Total **{Valor_Gasto:.2f}**")
    else:
        st.text("Nenhuma compra registrada.")

def Verifica_Compras_No_Session_State():
    if 'df_compras' not in st.session_state:
        st.session_state.df_compras = pd.DataFrame(
            columns=["Nome", "Produto", "Quantidade", "Preco_Unitario", "Preco"])
        return st.session_state.df_compras

def Cancela_Compras():
    st.session_state.Cancelando = True
    st.session_state.df_compras = pd.DataFrame(
        columns=["Nome", "Produto", "Quantidade", "Preco_Unitario", "Preco"])
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
    datapagamento = datahora if FlagPagamento == 'Sim' else None
    conn = get_postgres_conn()
    
    with conn.session as session:
        for index, row in df.iterrows():
            query = text(f"""
                INSERT INTO {schema}.fvendas 
                (data, nome, produto, qtd, valor, pago, data_pagamento, registro)
                VALUES (:data, :nome, :produto, :qtd, :valor, :pago, :data_pagamento, :registro)
            """)
            session.execute(query, {
                "data": datahora,
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
