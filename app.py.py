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

df_base = st.session_state['dados'].copy()

if not df_base.empty:
    df_base['Data_Convertida'] = pd.to_datetime(df_base['Data'], format="%d/%m/%Y", errors='coerce')
    df_base['Mês'] = df_base['Data_Convertida'].dt.month
    df_base['Ano'] = df_base['Data_Convertida'].dt.year

with st.sidebar:
    st.header("Adicionar Registro")
    
    # Interruptor principal (fica fora do formulário para atualizar as categorias na hora)
    tipo_selecionado = st.radio("Selecione o Tipo:", ["Despesa", "Receita"], horizontal=True)

    with st.form("formulario_lancamento", clear_on_submit=True):
        data_input = st.date_input("Data do Lançamento", format="DD/MM/YYYY")
        
        # O sistema troca a lista de categorias dependendo do botão escolhido acima
        if tipo_selecionado == "Despesa":
            lista_categorias = ["Água", "Energia", "Manutenção do Carro", "Compras", "Lazer", "Alimentação", "Pets", "Casa", "Outros"]
        else:
            lista_categorias = ["Salário", "Renda Extra", "Investimentos", "Outros"]
            
        categoria = st.selectbox("Categoria", lista_categorias)
        desc = st.text_input("Descrição (Ex: Troca de óleo, Ração, Supermercado)")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")

        cadastrar = st.form_submit_button("Registrar Lançamento")

        if cadastrar:
            if desc and valor > 0:
                data_formatada = data_input.strftime("%d/%m/%Y")
                
                novo_dado = pd.DataFrame([[data_formatada, tipo_selecionado, categoria, desc, valor]], columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
                st.session_state['dados'] = pd.concat([st.session_state['dados'], novo_dado], ignore_index=True)
                st.session_state['dados'].to_csv(ARQUIVO_DADOS, index=False)
                
                st.success("Lançamento salvo com sucesso!")
                st.rerun() 
            else:
                st.error("Preencha a descrição e insira um valor.")

    st.divider()
    st.header("🔎 Filtros")
    
    if not df_base.empty:
        lista_anos = ["Todos"] + sorted(list(df_base['Ano'].dropna().unique()))
        ano_selecionado = st.selectbox("Filtrar por Ano", lista_anos)
        
        mapa_meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                      7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        
        lista_meses = ["Todos"] + [mapa_meses[m] for m in sorted(list(df_base['Mês'].dropna().unique()))]
        mes_selecionado = st.selectbox("Filtrar por Mês", lista_meses)
        
        df_filtrado = df_base.copy()
        if ano_selecionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Ano'] == ano_selecionado]
        if mes_selecionado != "Todos":
            numero_mes = [k for k, v in mapa_meses.items() if v == mes_selecionado][0]
            df_filtrado = df_filtrado[df_filtrado['Mês'] == numero_mes]
    else:
        df_filtrado = df_base.copy()
        st.info("Cadastre dados para liberar os filtros.")

    st.divider()
    st.header("⚙️ Manutenção do Sistema")
    
    if st.button("⏪ Desfazer Último", use_container_width=True):
        if not st.session_state['dados'].empty:
            st.session_state['dados'] = st.session_state['dados'].iloc[:-1] 
            st.session_state['dados'].to_csv(ARQUIVO_DADOS, index=False)
            st.rerun()
        else:
            st.warning("A planilha já está vazia.")
            
    if st.button("🗑️ Apagar Tudo", use_container_width=True):
        st.session_state['dados'] = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
        st.session_state['dados'].to_csv(ARQUIVO_DADOS, index=False)
        st.rerun()

if not df_filtrado.empty:
    receitas = df_filtrado[df_filtrado['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df_filtrado[df_filtrado['Tipo'] == 'Despesa']['Valor'].sum()
    saldo = receitas - despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Receitas", f"R$ {receitas:.2f}")
    col2.metric("Total de Despesas", f"R$ {despesas:.2f}")
    col3.metric("Saldo do Período", f"R$ {saldo:.2f}") 

    st.divider()

    aba_graficos, aba_dados = st.tabs(["📈 Visão Gráfica", "📋 Tabela de Dados"])

    with aba_graficos:
        col_grafico1, col_grafico2 = st.columns(2)
        
        with col_grafico1:
            st.subheader("Despesas por Categoria")
            df_despesas = df_filtrado[df_filtrado['Tipo'] == 'Despesa']
            if not df_despesas.empty:
                resumo_cat = df_despesas.groupby('Categoria')['Valor'].sum().reset_index()
                fig1 = px.pie(resumo_cat, values='Valor', names='Categoria', hole=0.4)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("Nenhuma despesa registrada para este período.")

        with col_grafico2:
            st.subheader("Entradas vs Saídas")
            resumo_tipo = df_filtrado.groupby('Tipo')['Valor'].sum().reset_index()
            fig2 = px.bar(resumo_tipo, x='Tipo', y='Valor', color='Tipo',
                          color_discrete_map={'Receita':'#2ecc71', 'Despesa':'#e74c3c'})
            st.plotly_chart(fig2, use_container_width=True)

    with aba_dados:
        st.subheader("Histórico do Período")
        df_mostrar = df_filtrado[['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor']]
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

else:
    st.info("Nenhum dado encontrado. Faça seu primeiro lançamento usando o formulário à esquerda.")
