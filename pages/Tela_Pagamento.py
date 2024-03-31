## import bd
import pymysql

## import normal :D
import streamlit as st
from datetime import datetime
import pandas as pd
import time
from streamlit_extras.switch_page_button import switch_page

# Configurações do banco de dados
db_config = {
    'host': st.secrets["DATABASE_HOST"],
    'user': st.secrets["DATABASE_USERNAME"],
    'password': st.secrets["DATABASE_PASSWORD"],
    'database': st.secrets["DATABASE"],
    'autocommit': True,
}

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
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        query = f"SELECT * FROM fVendas WHERE Nome = '{nomeCliente}'"
        cursor.execute(query)

        # Obter os resultados
        results = cursor.fetchall()

        # Obter os nomes das colunas
        columns = [desc[0] for desc in cursor.description]
        # Criar um DataFrame com os resultados
        df = pd.DataFrame(results, columns=columns)
        cursor.close()
        conn.close()
        return df

    except pymysql.Error as e:
        print("MySQL Error:", e)

def atualizar(base):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    for index, row in base.iterrows():
        # Construir a parte da instrução SQL para a coluna DataPagamento
        if pd.isna(row['DataPagamento']):
            data_pagamento = "NULL"
        else:
            data_pagamento = f"'{row['DataPagamento']}'"

        update_query = f"UPDATE fVendas SET `Data` = '{row['Data']}', Nome = '{row['Nome']}', Produto = '{row['Produto']}', Qtd = {row['Qtd']}, Valor = {row['Valor']}, Pago = {row['Pago']}, DataPagamento = {data_pagamento}, Registro = '{row['Registro']}' WHERE ID = {row['ID']}"

        # Executar a instrução SQL UPDATE
        cursor.execute(update_query)

    cursor.close()
    conn.close()

def resetcheck():
    return False

st.session_state.name = st.session_state.name
if "nomeimutavel" in st.session_state: ##foda!!
    nome = st.session_state.nomeimutavel
else:
    nome = st.session_state.name

st.title('Tela de Pagamento')

colunas_usadas = ['Pago', 'Valor', 'Qtd', 'Produto', 'Nome','Data']
df = base(nome)

df_nao_pago = df_nao_pago = df[df['Pago'] == 0]
df_nao_pago['Pago'] = df_nao_pago['Pago'].replace(0, False)

if len(df_nao_pago) != 0:
    st.caption('💡 Para pagar uma dívida, selecione as linhas na tabela ou selecione a opção abaixo para pagar tudo.')
    pagamento = st.selectbox('Deseja pagar tudo?:', ['Pagar linhas selecionadas', 'Pagar tudo'],placeholder="Selecione uma opção", index=None, key='pagamento')
    divida = df_nao_pago['Valor'].sum()
    st.write(f'O total de dívidas é :red[R$: {divida}]')
    
    df_nao_pago['Valor'] = df_nao_pago['Valor'].astype(float)
    
    df_editavel = st.data_editor(
        df_nao_pago[colunas_usadas],
        key='db',
        hide_index=True,
        column_config={
            "Valor": st.column_config.NumberColumn(
                "Valor",
                help="Valor devido",
                format="R$: %.2f",
                disabled=True,
                step=0.01,
            ),
            "Qtd": st.column_config.TextColumn(
                "Qtd",
                help="Quantidade",
                disabled=True,
            ),
            "Produto": st.column_config.TextColumn(
                "Produto",
                help="Nome do Produto",
                disabled=True,
            ),
            "Nome": st.column_config.TextColumn(
                "Nome",
                help="Nome do pagador",
                disabled=True,
            ),
            "Data":st.column_config.DateColumn(
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
            df_editavel['Pago'] = True
            soma_valores_pago = df_editavel.loc[df_editavel['Pago'] == True, 'Valor'].sum()
            st.write(f'Deseja aliviar a dívida de :red[R$:{soma_valores_pago}?]')
            st.image('img/pix.png', width=600)

        except:
            st.error('Filtre outra pessoa')
    if pagamento == 'Pagar linhas selecionadas':
        try:
            soma_valores_pago = df_editavel.loc[df_editavel['Pago'] == True, 'Valor'].sum()
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
            df_nao_pago.loc[(df_nao_pago['Pago'] == True) & (df_nao_pago['DataPagamento'].isnull() | (df_nao_pago['DataPagamento'] == '')), 'DataPagamento'] = hoje
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