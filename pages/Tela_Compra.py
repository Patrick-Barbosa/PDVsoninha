# import banco
import pymysql
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
    col_but2, col_but3 = st.columns(2)
    if product_input is None:
        col_but2 = st.write(" ")
        col_but3 = st.write(" ")
    else:
        with col_but2:
            butao_conclusao = st.button("Finalizar a Compra")
        with col_but3:
            butao_cancelar = st.button("Cancelar Compras")
        if butao_conclusao:
            switch_page("Tela_Conclusao")
        if butao_cancelar:
            Cancela_Compras()


def Salva_Compra():
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

    # Código estava dando erro pq não tem atributo append
    # AttributeError: 'DataFrame' object has no attribute 'append'
    # st.session_state.df_compras = st.session_state.df_compras.append({"Nome":nome,
    # "Quantidade":quantidade,
    #                                                              "Preco":preco},ignore_index=True)


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
    st.session_state.df_compras = pd.DataFrame(
        columns=["Nome", "Produto", "Quantidade", "Preco"])
    switch_page("Tela_Nome")


if __name__ == "__main__":
    Tela_Compra()
