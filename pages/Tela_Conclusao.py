from datetime import datetime
import streamlit as st
import numpy as np
import pandas as pd
import time
from streamlit_extras.switch_page_button import switch_page
import pymysql
import ssl
import threading

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

global travaDuploClick
travaDuploClick = 0

# Combinar as configurações
db_config.update(ssl_config)
    
def Tela_Conclusao():
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

    st.title("Tela de Finalização de Compra")
    col1= st.columns([1,1])
   
    
    dataframe = st.session_state.df_compras
    valor_total = np.sum(dataframe['Quantidade'] * dataframe['Preco'])


    if 'FlagPagamento' in dataframe.columns:
        pass
    else:
        dataframe['FlagPagamento'] = False
    

        
    st.write(f"O Valor total da sua compra foi de **R$ {valor_total:.2f}**")
    st.write('Faça o pagamento para o **pix telefone número: 12345678910**')
    FlagPagamento= st.radio("**Você já pagou?**",
                        ["Sim","Não"],
                        index=1)
        
    if FlagPagamento == 'Sim':
            FlagPagamentoBool = True
    elif FlagPagamento == 'Não':
            FlagPagamentoBool = False
    dataframe['FlagPagamento'] = FlagPagamentoBool


    st.dataframe(dataframe, hide_index=True)
    col_but1,col_but2,col_but3= st.columns(3)
    
    st.session_state.travaBotoes = 0

    with col_but1:
        butao_finaliza_compra = st.button("Finalizar a Compra", type='primary')

    with col_but2:
        butao_volta_tela = st.button("Voltar para a Tela Anterior")

    with col_but3:
        butao_cancela_compra = st.button("Cancelar a Compra")
             
    if butao_finaliza_compra:
        Finaliza_Compra(dataframe, FlagPagamento)
        
    if butao_volta_tela:
        Volta_Tela_Anterior()
        
    if butao_cancela_compra:
            Cancela_Compras()   
    
    
def Finaliza_Compra(df, FlagPagamento):
    if 'travaDuploClick' not in st.session_state:
        st.session_state.travaDuploClick = 0
    st.session_state.travaDuploClick += 1
    if st.session_state.travaDuploClick == 1:
        # Dedicando um thread exclusivo pra subir no banco e não haver falhas
        thread_envio = threading.Thread(target=Envia_Dados_BD, args=(df, FlagPagamento))
        thread_envio.start()

    time.sleep(1)
    time.sleep(1)

    st.success("Venda Enviada com Sucesso")
    time.sleep(2)
    Cancela_Compras()
        
def Volta_Tela_Anterior():
      st.session_state.name = st.session_state.df_compras['Nome'].unique()[0]
      switch_page("Tela_Compra")

def Cancela_Compras():
    st.session_state.df_compras = pd.DataFrame(columns=["Nome", "Produto", "Quantidade","Preco"])
    switch_page("Tela_Nome")
      
def Envia_Dados_BD(df, FlagPagamento):
    datahora = datetime.now()
    data = datetime.now().date()
    datapagamento = data if FlagPagamento == 'Sim' else None
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    for index, row in df.iterrows(): 
        sql = "INSERT INTO fVendas (Data, Nome, Item, Qtd, Valor, Pago, DataPagamento, Registro) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (data, row['Nome'], row['Produto'], row['Quantidade'], row['Preco'], row['FlagPagamento'], datapagamento, datahora)
        cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    Tela_Conclusao()