## import normal :D
import streamlit as st
from datetime import datetime
import pandas as pd
import time
from streamlit_extras.switch_page_button import switch_page
from db_config import get_postgres_conn
from sqlalchemy import text

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

def des(key):
    if st.session_state.get(key) == None:
        return False
    else:
        return True
    
def base(nomeCliente):
    try:
        conn = get_postgres_conn()
        df = conn.query(f"SELECT * FROM dev.fvendas WHERE nome = '{nomeCliente}'", ttl = 0)
        return df
    except Exception as e:
        print("Database Error:", e)

def atualizar(base):
    conn = get_postgres_conn()
    with conn.session as session:
        for index, row in base.iterrows():
            query = text("""
                UPDATE dev.fvendas 
                SET data = :data, 
                    nome = :nome, 
                    produto = :produto, 
                    qtd = :qtd, 
                    valor = :valor, 
                    pago = :pago, 
                    data_pagamento = :data_pagamento, 
                    registro = :registro 
                WHERE id = :id
            """)
            session.execute(query, {
                "data": row['data'],
                "nome": row['nome'],
                "produto": row['produto'],
                "qtd": row['qtd'],
                "valor": row['valor'],
                "pago": row['pago'],
                "data_pagamento": row['data_pagamento'] if pd.notna(row['data_pagamento']) else None,
                "registro": row['registro'],
                "id": row['id']
            })
        session.commit()

def resetcheck():
    return False

try:
    if 'name' not in st.session_state:
        st.session_state.name = None
    nome = st.session_state.name

    st.title('Tela de Pagamento')

    colunas_usadas = ['pago', 'valor', 'qtd', 'produto', 'nome', 'data']
    df = base(nome)

    df_nao_pago = df[df['pago'] == False]
    #df_nao_pago['pago'] = df_nao_pago['pago'].replace(0, False)

    if len(df_nao_pago) != 0:
        st.caption('💡 Para pagar uma dívida, selecione as linhas na tabela ou selecione a opção abaixo para pagar tudo.')
        pagamento = st.selectbox('Deseja pagar tudo?:', ['Pagar linhas selecionadas', 'Pagar tudo'],placeholder="Selecione uma opção", index=None, key='pagamento')
        divida = df_nao_pago['valor'].sum()
        st.write(f'O total de dívidas é :red[R$: {divida}]')
        
        df_nao_pago['valor'] = df_nao_pago['valor'].astype(float)
        
        df_editavel = st.data_editor(
            df_nao_pago[colunas_usadas],
            key='db',
            hide_index=True,
            column_config={
                "valor": st.column_config.NumberColumn(
                    "Valor",
                    help="Valor devido",
                    format="R$: %.2f",
                    disabled=True,
                    step=0.01,
                ),
                "qtd": st.column_config.TextColumn(
                    "Qtd",
                    help="Quantidade",
                    disabled=True,
                ),
                "produto": st.column_config.TextColumn(
                    "Produto",
                    help="Nome do Produto",
                    disabled=True,
                ),
                "nome": st.column_config.TextColumn(
                    "Nome",
                    help="Nome do pagador",
                    disabled=True,
                ),
                "data":st.column_config.DateColumn(
                    "Data de Compra",
                    help="Data de Compra",
                    format="DD/MM/YYYY",
                    disabled=True,
                )
            }
        )
        st.divider()
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col1:
            botao = st.button('Confirmar', disabled=not des('pagamento'), type='primary')
        if pagamento == 'Pagar tudo':
            try:
                df_editavel['pago'] = True
                soma_valores_pago = df_editavel.loc[df_editavel['pago'] == True, 'valor'].sum()
                st.write(f'Deseja aliviar a dívida de :red[R$:{soma_valores_pago}?]')
                st.image('img/pix.png', width=600)

            except:
                st.error('Filtre outra pessoa')
        if pagamento == 'Pagar linhas selecionadas':
            try:
                soma_valores_pago = df_editavel.loc[df_editavel['pago'] == True, 'valor'].sum()
                if soma_valores_pago == 0:
                    st.write(':red[Selecione uma linha para dar baixa.]')
                else:
                    st.write(f'Deseja pagar a dívida de :red[R$:{soma_valores_pago}?], faça o pix para o telefone **21 96475-0527**')
                    st.image('img/pix.png', width=600)
            except:
                st.error('Filtre outra pessoa')
                
        with col2:
            Voltar = st.button('Voltar')
        if Voltar:
            switch_page("Tela_Nome")
            
        if botao:
            if soma_valores_pago == 0:
                st.error('❌ Nenhuma linha foi selecionada.')
            else:
                df_nao_pago.update(df_editavel)
                hoje = datetime.now().strftime('%Y-%m-%d')
                df_nao_pago.loc[(df_nao_pago['pago'] == True) & (df_nao_pago['data_pagamento'].isnull() | (df_nao_pago['data_pagamento'] == '')), 'data_pagamento'] = hoje
                atualizar(df_nao_pago)
                st.success('Dados atualizados!')
                st.balloons()
                st.success(f'O valor de :red[R$:{soma_valores_pago}] foi pago!')
                st.success('Você será redirecionado em 5 segundos')
                st.spinner()
                time.sleep(5)
                switch_page("Tela_Nome")
    else:
        ## nenhuma divida encontrada
        st.balloons()
        st.success('Nenhuma dívida encontrada')
        time.sleep(3)
        switch_page("Tela_Nome")
except Exception as e:
    st.title('Ops, erro no sistema')
    st.text('Voltando a página inicial')
    time.sleep(2)
    switch_page("Tela_Nome")