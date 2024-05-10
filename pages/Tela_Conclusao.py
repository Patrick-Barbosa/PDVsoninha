from datetime import datetime
import streamlit as st
import numpy as np
import pandas as pd
import time
from streamlit_extras.switch_page_button import switch_page
import pymysql
import threading

db_config = {
    'host': st.secrets["DATABASE_HOST"],
    'user': st.secrets["DATABASE_USERNAME"],
    'password': st.secrets["DATABASE_PASSWORD"],
    'database': st.secrets["DATABASE"],
    'autocommit': True,
}


def Tela_Conclusao():
    try:
        # Define a configuração de página para usar o layout wide por padrão
        st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

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
        
        if 'flagPagamento' not in st.session_state:
            st.session_state.flagPagamento = 'Não'
        
        dataframe = st.session_state.df_compras

        dataframe['FlagPagamento'] = st.session_state.flagPagamento == 'Sim'

        if 'FlagPagamento' not in dataframe.columns:
            dataframe['FlagPagamento'] = False

        st.title("Pagamento")    
        
        st.dataframe(dataframe, hide_index=True)
        valor_total = np.sum(dataframe['Preco'])

        st.markdown(
            f"<h1 style='font-size:30px;'>O Valor total da sua compra foi de <b>R$ {valor_total:.2f}</b></h1>", unsafe_allow_html=True)
        st.write('Scaneie o QR CODE e faça o pagamento para o telefone: **21 96475-0527**')
        st.image('img/pix.png', width=600)
        widgetPagamento = st.radio("**Você já pagou?**",
                                ["Sim", "Não"],
                                index=1, key='flagPagamento2')
        
        col1, col2, col3, col4,col5,col6 = st.columns(6)
        if widgetPagamento != st.session_state.flagPagamento:
            st.session_state.flagPagamento = widgetPagamento
            st.rerun()

        with col1:
            butao_finaliza_compra = st.button("Finalizar a Compra", type='primary')

        with col2:
            butao_cancela_compra = st.button("Cancelar a Compra")
        
        with col3: 
            butao_voltar = st.button("Voltar")

        if butao_finaliza_compra:
            Finaliza_Compra(dataframe, st.session_state.flagPagamento)

        if butao_cancela_compra:
            Cancela_Compras()

        if butao_voltar:
            Volta_Tela_Anterior()
    except Exception as e:
        st.title('Ops, erro no sistema')
        st.text('Voltando a página inicial')
        print(e)
        time.sleep(2)
        switch_page("Tela_Nome")

def Finaliza_Compra(df, FlagPagamento):
    if 'travaDuploClick' not in st.session_state:
        st.session_state.travaDuploClick = 0
    st.session_state.travaDuploClick += 1
    if st.session_state.travaDuploClick == 1:
        # Dedicando um thread exclusivo pra subir no banco e não haver falhas
        thread_envio = threading.Thread(
            target=Envia_Dados_BD, args=(df, FlagPagamento))
        thread_envio.start()

    time.sleep(1)
    time.sleep(1)

    st.success("Venda Enviada com Sucesso")

    st.balloons()
    time.sleep(2)
    Cancela_Compras()


def Volta_Tela_Anterior():
    st.session_state.name = st.session_state.df_compras['Nome'].unique()[0]
    switch_page("Tela_Compra")

def Cancela_Compras():
    st.session_state.df_compras = pd.DataFrame(
        columns=["Nome", "Produto", "Quantidade", "Preco"])
    switch_page("Tela_Nome")


def Envia_Dados_BD(df, FlagPagamento):
    datahora = datetime.now()
    data = datetime.now().date()
    datapagamento = data if FlagPagamento == 'Sim' else None
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    for index, row in df.iterrows():
        sql = "INSERT INTO fVendas (Data, Nome, Produto, Qtd, Valor, Pago, DataPagamento, Registro) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (data, row['Nome'], row['Produto'], row['Quantidade'],
                  row['Preco'], row['FlagPagamento'], datapagamento, datahora)
        cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    Tela_Conclusao()
