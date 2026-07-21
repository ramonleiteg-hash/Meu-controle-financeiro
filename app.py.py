import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

ARQUIVO_DADOS = 'dados_financeiros.csv'

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        df_salvo = pd.read_csv(ARQUIVO_DADOS)
        
        if 'Data' not in df_salvo.columns:
            df_salvo['Data'] = date.today().strftime("%d/%m/%Y")
            
        if 'Categoria' not in df_salvo.columns:
            df_salvo['Categoria'] = 'Outros'
            
        return df_salvo
    else:
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])

st.set_page_config(page_title="Controle Financeiro", layout="wide")

if 'dados' not in st.session_state:
    st.session_state['dados'] = carregar_dados()

st.title("📊 Dashboard de Controle Financeiro")

with st.sidebar:
    with st.form("formulario_lancamento", clear_on_submit=True):
        st.header("Adicionar Registro")
        
        data_input = st.date_input("Data do Lançamento", format="DD/MM/YYYY")
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
        categoria = st.selectbox("Categoria", ["Manutenção Automotiva", "Ferramentas & Eletrônica", "Pets", "Casa", "Alimentação", "Salário", "Outros"])
        desc = st.text_input("Descrição (Ex: Pneus aro 13, Ração, Conta de luz)")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")

        cadastrar = st.form_submit_button("Registrar Lançamento")

        if cadastrar:
            if desc and valor > 0:
                data_formatada = data_input.strftime("%d/%m/%Y")
                
                novo_dado = pd.DataFrame([[data_formatada, tipo, categoria, desc, valor]], columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
                st.session_state['dados'] = pd.concat([st.session_state['dados'], novo_dado], ignore_index=True)
                
                st.session_state['dados'].to_csv(ARQUIVO_DADOS, index=False)
                
                st.success("Lançamento salvo! Pode inserir o próximo.")
            else:
                st.error("Preencha a descrição e insira um valor.")

df = st.session_state['dados']

if not df.empty:
    receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    saldo = receitas - despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Receitas", f"R$ {receitas:.2f}")
    col2.metric("Total de Despesas", f"R$ {despesas:.2f}")
    col3.metric("Saldo Atual", f"R$ {saldo:.2f}")

    st.divider()

    aba_graficos, aba_dados = st.tabs(["📈 Visão Gráfica", "📋 Tabela de Dados"])

    with aba_graficos:
        col_grafico1, col_grafico2 = st.columns(2)
        
        with col_grafico1:
            st.subheader("Despesas por Categoria")
            df_despesas = df[df['Tipo'] == 'Despesa']
            if not df_despesas.empty:
                resumo_cat = df_despesas.groupby('Categoria')['Valor'].sum().reset_index()
                fig1 = px.pie(resumo_cat, values='Valor', names='Categoria', hole=0.4)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("Nenhuma despesa para gerar o gráfico.")

        with col_grafico2:
            st.subheader("Entradas vs Saídas")
            resumo_tipo = df.groupby('Tipo')['Valor'].sum().reset_index()
            fig2 = px.bar(resumo_tipo, x='Tipo', y='Valor', color='Tipo',
                          color_discrete_map={'Receita':'#2ecc71', 'Despesa':'#e74c3c'})
            st.plotly_chart(fig2, use_container_width=True)

    with aba_dados:
        st.subheader("Histórico Completo")
        st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.info("Nenhum dado registrado ainda. Use a barra lateral para adicionar receitas e despesas.")
