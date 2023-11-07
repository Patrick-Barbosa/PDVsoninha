## import bd
import pymysql
import ssl

## import normal :D
import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime
import pandas as pd
import time


# Configurações do banco de dados
db_config = {
    'host': st.secrets["DATABASE_HOST"],
    'user': st.secrets["DATABASE_USERNAME"],
    'password': st.secrets["DATABASE_PASSWORD"],
    'database': st.secrets["DATABASE"],
    'autocommit': True,
}

# Configuração SSL
ssl_config = {
    'ssl': {
        'ca': 'cert.pem',
        'ssl_version': ssl.PROTOCOL_TLSv1_2,  
    }
}

# Combinar as configurações
db_config.update(ssl_config)

def des(key):
    if st.session_state.get(key) == None:
        return False
    else:
        return True
    
def selectboxpag():
    if Filtro != None:
        return False
    else:
        return True

def base():
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT * FROM fVendas"
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

        update_query = f"UPDATE fVendas SET `Data` = '{row['Data']}', Nome = '{row['Nome']}', Item = '{row['Item']}', Qtd = {row['Qtd']}, Valor = {row['Valor']}, Pago = {row['Pago']}, DataPagamento = {data_pagamento}, Registro = '{row['Registro']}' WHERE ID = {row['ID']}"

        # Executar a instrução SQL UPDATE
        cursor.execute(update_query)

    cursor.close()
    conn.close()

def resetcheck():
    return False

st.title('Consultor de Dívidas')
colunas_usadas = ['Pago', 'Valor', 'Qtd', 'Item', 'Nome']
df = base()
#st.dataframe(df)
df_nao_pago = df_nao_pago = df[df['Pago'] == 0]
df_nao_pago['Pago'] = df_nao_pago['Pago'].replace(0, False)
valores_distintos_nome = df_nao_pago['Nome'].unique().tolist()

Filtro = st.selectbox('Pessoa', valores_distintos_nome, placeholder='Filtre uma pessoa:', index=None, key = 'Filtro')

if Filtro != None:
    dfFiltrado = df_nao_pago.loc[df_nao_pago['Nome'] == Filtro]
    divida = dfFiltrado['Valor'].sum()
    st.write(f'O total de dívidas é :red[R$: {divida}]')
    df_editavel = st.data_editor(dfFiltrado[colunas_usadas], key='db', hide_index= True)
else:
    st.write('Filtre seu nome')
    
st.divider()
pagamento = st.selectbox('Opção de Pagamento:', ['Pagar linhas selecionadas', 'Pagar tudo'],placeholder="Selecione uma opção", index=None, disabled=selectboxpag(), key='pagamento')
botao = st.button('Confirmar alterações', disabled=not des('pagamento'), type='primary')
if pagamento == 'Pagar tudo':
    try:
        df_editavel['Pago'] = True
        soma_valores_pago = df_editavel.loc[df_editavel['Pago'] == True, 'Valor'].sum()
        st.write(f'Deseja aliviar a dívida de :red[R$:{soma_valores_pago}?]')
    except:
        st.error('Filtre outra pessoa')
if pagamento == 'Pagar linhas selecionadas':
    try:
        soma_valores_pago = df_editavel.loc[df_editavel['Pago'] == True, 'Valor'].sum()
        if soma_valores_pago == 0:
            st.write(':red[Selecione uma linha para dar baixa.]')
        else:
            st.write(f'Deseja pagar a dívida de :red[R$:{soma_valores_pago}?], faça o pix para o telefone **123456789-10**')
            st.write('Caso queira pagar outra linha, desmarque a linha atual e marque a linha desejada.')
    except:
        st.error('Filtre outra pessoa')

if botao:
    if soma_valores_pago == 0:
        st.error('Não é possível pagar uma dívida inexistente')
    else:
        df_nao_pago.update(df_editavel)
        hoje = datetime.now().strftime('%Y-%m-%d')
        df_nao_pago.loc[(df_nao_pago['Pago'] == True) & (df_nao_pago['DataPagamento'].isnull() | (df_nao_pago['DataPagamento'] == '')), 'DataPagamento'] = hoje
        atualizar(df_nao_pago)
        st.success('Dados atualizados!')
        st.success(f'O valor de :red[R$:{soma_valores_pago}] foi pago!')
        st.success('A página será atualizada em 5 segundos')
        st.spinner()
        time.sleep(5)
        st.rerun()
        