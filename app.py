import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import json
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Painel Socioeconômico do Brasil")
st.title("Painel Socioeconômico do Brasil")
st.markdown("Análise de indicadores socioeconômicos por Unidade da Federação (UF) e Ano.")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(
            "dados_consolidados_corrigido.csv", # Certifique-se que o nome do arquivo está correto
            sep=',', # SEU NOVO ARQUIVO USA VÍRGULA, NÃO PONTO E VÍRGULA
            decimal='.' # Assumindo que os decimais agora usam ponto
        )

        # --- CORREÇÃO AQUI ---
        # Usar o nome correto da coluna 'Populacao_total' com P maiúsculo
        df['Populacao_total'] = pd.to_numeric(df['Populacao_total'], errors='coerce')
        df = df.dropna(subset=['Populacao_total']) 

        # --- CORREÇÃO AQUI ---
        pop_100k = df['Populacao_total'] / 100000
        
        cols_to_convert = [
            'num_homicidios', 'num_obitos_suicidio', 'num_internacoes_cardio',
            'num_mortes_cardio', 'num_obitos_transporte'
        ]
        
        for col in cols_to_convert:
             # Verificar se a coluna existe antes de tentar converter
             if col in df.columns:
                 rate_col_name = f"{col.replace('num_', '')}_por_100k"
                 # Usar replace para tratar possíveis infinitos antes de dividir
                 numeric_col = pd.to_numeric(df[col], errors='coerce').replace([np.inf, -np.inf], np.nan)
                 df[rate_col_name] = (numeric_col / pop_100k).round(2)
             else:
                 st.warning(f"Coluna '{col}' não encontrada no CSV para cálculo de taxa.")


        return df
    except FileNotFoundError:
        st.error("Erro: Arquivo 'dados_consolidados_corrigido.csv' não encontrado. Certifique-se de que ele está no mesmo diretório.")
        return pd.DataFrame() 
    except Exception as e: # Captura outros erros de leitura/processamento
        st.error(f"Erro ao carregar ou processar dados: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

st.sidebar.header("Filtros")
anos_disponiveis = sorted(df['Ano'].unique(), reverse=True)
ano_selecionado = st.sidebar.selectbox("Selecione o Ano:", anos_disponiveis)

ufs_disponiveis = sorted(df['UF'].unique())
uf_selecionada = st.sidebar.selectbox("Selecione a UF (para detalhes):", ["Brasil"] + ufs_disponiveis)

metricas = {
    'Taxa de Desemprego (%)': 'taxa_desemprego_media',
    'Renda Média Anual': 'renda_media_anual',
    'População Total': 'Populacao_total',
    'Taxa de Escolarização (Fundamental %)': 'perc_esc_fundamental',
    'Taxa de Escolarização (Médio %)': 'perc_esc_medio',
    'Homicídios (por 100k hab.)': 'homicidios_por_100k',
    'Suicídios (por 100k hab.)': 'obitos_suicidio_por_100k',
    'Internações Cardio (por 100k hab.)': 'internacoes_cardio_por_100k',
    'Mortes Cardio (por 100k hab.)': 'mortes_cardio_por_100k',
    'Óbitos Transporte (por 100k hab.)': 'obitos_transporte_por_100k',
    'Homicídios (Absoluto)': 'num_homicidios',
    'Homicídios Arma de Fogo (Absoluto)': 'num_homicidios_arma'
}
lista_nomes_metricas = list(metricas.keys())
lista_cols_metricas_numericas = list(metricas.values())


df_filtrado_ano = df[df['Ano'] == ano_selecionado]

st.header(f"Indicadores Nacionais - {ano_selecionado}")

media_desemprego_br = df_filtrado_ano['taxa_desemprego_media'].mean()
media_renda_br = df_filtrado_ano['renda_media_anual'].mean()
total_pop_br = df_filtrado_ano['Populacao_total'].sum()
media_homicidios_100k_br = df_filtrado_ano['homicidios_por_100k'].mean()

pop_formatado = f"{total_pop_br:,.0f}".replace(",", ".") if pd.notna(total_pop_br) else "N/D"
desemprego_formatado = f"{media_desemprego_br:.1f}%" if pd.notna(media_desemprego_br) else "N/D"
renda_formatado = f"R$ {media_renda_br:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(media_renda_br) else "N/D"
homicidios_formatado = f"{media_homicidios_100k_br:.1f}" if pd.notna(media_homicidios_100k_br) else "N/D"

st.markdown(f"""
<style>
.kpi-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
.kpi-card {{ background-color: #FFFFFF; border-radius: 8px; padding: 1.5rem; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border-left: 5px solid #007bff; transition: transform 0.2s ease-in-out; }}
.kpi-card:hover {{ transform: translateY(-5px); }}
.kpi-title {{ font-size: 0.9rem; color: #555; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; }}
.kpi-value {{ font-size: 2rem; font-weight: 700; color: #333; }}
.kpi-card.pop {{ border-left-color: #17a2b8; }} 
.kpi-card.econ {{ border-left-color: #28a745; }} 
.kpi-card.social {{ border-left-color: #dc3545; }} 
</style>
<div class="kpi-container">
    <div class="kpi-card pop"><div class="kpi-title">População Total</div><div class="kpi-value">{pop_formatado}</div></div>
    <div class="kpi-card econ"><div class="kpi-title">Desemprego Médio</div><div class="kpi-value">{desemprego_formatado}</div></div>
    <div class="kpi-card econ"><div class="kpi-title">Renda Média Anual</div><div class="kpi-value">{renda_formatado}</div></div>
    <div class="kpi-card social"><div class="kpi-title">Homicídios (por 100k)</div><div class="kpi-value">{homicidios_formatado}</div></div>
</div>
""", unsafe_allow_html=True)

st.divider()

st.header(f"Mapa do Brasil - {ano_selecionado}")
metrica_mapa_nome = st.selectbox("Selecione a Métrica para o Mapa:", lista_nomes_metricas, index=0) 
metrica_mapa_col = metricas[metrica_mapa_nome]

try:
    geojson_path = 'brasil_estados.json' 
    with open(geojson_path, 'r', encoding='utf-8') as f: 
        geojson_br = json.load(f)
except FileNotFoundError:
    st.error(f"Arquivo '{geojson_path}' não encontrado.")
    geojson_br = None
except json.JSONDecodeError:
    st.error(f"Erro ao decodificar o arquivo '{geojson_path}'.")
    geojson_br = None
except Exception as e:
    st.error(f"Erro inesperado ao carregar GeoJSON: {e}")
    geojson_br = None


if geojson_br and metrica_mapa_col in df_filtrado_ano.columns:
    
    uf_to_sigla_map = {
        'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM',
        'Bahia': 'BA', 'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES',
        'Goiás': 'GO', 'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS',
        'Minas Gerais': 'MG', 'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR',
        'Pernambuco': 'PE', 'Piauí': 'PI', 'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN',
        'Rio Grande do Sul': 'RS', 'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC',
        'São Paulo': 'SP', 'Sergipe': 'SE', 'Tocantins': 'TO'
    }
    
    df_mapa = df_filtrado_ano.copy()
    df_mapa['UF_Sigla'] = df_mapa['UF'].map(uf_to_sigla_map)
    
    ufs_nao_mapeadas = df_mapa[df_mapa['UF_Sigla'].isna()]['UF'].unique()
    if len(ufs_nao_mapeadas) > 0:
        st.warning(f"UFs não mapeadas: {', '.join(ufs_nao_mapeadas)}.")
        df_mapa = df_mapa.dropna(subset=['UF_Sigla'])

    df_mapa[metrica_mapa_col] = pd.to_numeric(df_mapa[metrica_mapa_col], errors='coerce')
    df_mapa = df_mapa.dropna(subset=[metrica_mapa_col])

    if not df_mapa.empty:
        try:
            fig_map = px.choropleth_mapbox(df_mapa,
                                       geojson=geojson_br,
                                       locations='UF_Sigla', 
                                       featureidkey="id", 
                                       color=metrica_mapa_col,
                                       color_continuous_scale="Blues", 
                                       mapbox_style="carto-darkmatter", 
                                       zoom=3, center = {"lat": -14.2350, "lon": -51.9253},
                                       opacity=0.7,
                                       hover_name='UF', 
                                       hover_data={'UF_Sigla': False, metrica_mapa_col: ':.2f'}, 
                                       title=f"{metrica_mapa_nome} por UF em {ano_selecionado}",
                                       labels={metrica_mapa_col: metrica_mapa_nome.split('(')[0].strip()}
                                      )
            fig_map.update_layout(
                margin={"r":0,"t":40,"l":0,"b":0},
                coloraxis_colorbar=dict(
                    title=dict(
                        text=metrica_mapa_nome.split('(')[0].strip(), 
                        font=dict(color='white') 
                    ),
                    tickfont=dict(color='white') 
                )
             )
            st.plotly_chart(fig_map, use_container_width=True)
            
        except Exception as map_error:
            st.error(f"Erro ao gerar o mapa: {map_error}")

    else:
        st.warning(f"Não há dados válidos para '{metrica_mapa_nome}' em {ano_selecionado} para o mapa.")

elif not geojson_br:
    st.warning("Não é possível exibir o mapa sem o arquivo GeoJSON.")
else:
    st.warning(f"Métrica '{metrica_mapa_nome}' não encontrada para o mapa.")

st.divider()

st.header(f"Ranking dos Estados - {ano_selecionado}")
metrica_ranking_nome = st.selectbox("Selecione a Métrica para o Ranking:", lista_nomes_metricas, index=0)
metrica_ranking_col = metricas[metrica_ranking_nome]

if metrica_ranking_col in df_filtrado_ano.columns:
    df_ranking = df_filtrado_ano[['UF', metrica_ranking_col]].copy()
    df_ranking[metrica_ranking_col] = pd.to_numeric(df_ranking[metrica_ranking_col], errors='coerce')
    df_ranking = df_ranking.dropna(subset=[metrica_ranking_col])

    if not df_ranking.empty:
        col_rank1, col_rank2 = st.columns(2)
        
        with col_rank1:
            st.subheader("Maiores Valores")
            top_chart = alt.Chart(df_ranking.nlargest(10, metrica_ranking_col)).mark_bar().encode(
                y=alt.Y('UF:N', sort='-x', title="UF"),
                x=alt.X(f'{metrica_ranking_col}:Q', title=metrica_ranking_nome),
                tooltip=['UF', alt.Tooltip(f'{metrica_ranking_col}:Q', format=".2f")]
            ).properties(height=300)
            st.altair_chart(top_chart, use_container_width=True)
            
        with col_rank2:
            st.subheader("Menores Valores")
            bottom_chart = alt.Chart(df_ranking.nsmallest(10, metrica_ranking_col)).mark_bar(color='#5276A7').encode(
                y=alt.Y('UF:N', sort='x', title="UF"),
                x=alt.X(f'{metrica_ranking_col}:Q', title=metrica_ranking_nome),
                tooltip=['UF', alt.Tooltip(f'{metrica_ranking_col}:Q', format=".2f")]
            ).properties(height=300)
            st.altair_chart(bottom_chart, use_container_width=True)
    else:
        st.warning(f"Não há dados válidos para '{metrica_ranking_nome}' em {ano_selecionado} para o ranking.")
else:
     st.warning(f"Métrica '{metrica_ranking_nome}' não encontrada para o ranking.")

st.divider()

st.header(f"Evolução do Estado: {uf_selecionada}")

if uf_selecionada != "Brasil":
    df_estado = df[df['UF'] == uf_selecionada].sort_values('Ano')
    
    metricas_evolucao_nomes = st.multiselect(
        "Selecione as Métricas para Evolução:",
        lista_nomes_metricas,
        default=lista_nomes_metricas[:2] 
    )
    
    if metricas_evolucao_nomes:
        metricas_evolucao_cols = [metricas[nome] for nome in metricas_evolucao_nomes]
        
        df_estado_melted = df_estado.melt(
            id_vars=['Ano'], 
            value_vars=metricas_evolucao_cols, 
            var_name='Métrica', 
            value_name='Valor'
        )
        mapa_nomes_metricas_rev = {v: k for k, v in metricas.items()}
        df_estado_melted['Métrica'] = df_estado_melted['Métrica'].map(mapa_nomes_metricas_rev)
        df_estado_melted['Valor'] = pd.to_numeric(df_estado_melted['Valor'], errors='coerce')
        
        line_chart = alt.Chart(df_estado_melted).mark_line(point=True).encode(
            x=alt.X('Ano:O', title='Ano'), 
            y=alt.Y('Valor:Q', title='Valor', scale=alt.Scale(zero=False)), 
            color='Métrica:N',
            tooltip=['Ano', 'Métrica', alt.Tooltip('Valor:Q', format=".2f")]
        ).properties(
            title=f"Evolução de Indicadores para {uf_selecionada}"
        ).interactive()
        
        st.altair_chart(line_chart, use_container_width=True)
    else:
        st.warning("Selecione pelo menos uma métrica para visualizar a evolução.")
else:
    df_brasil_evol = df.groupby('Ano').agg(
        taxa_desemprego_media=('taxa_desemprego_media', 'mean'),
        renda_media_anual=('renda_media_anual', 'mean'),
        homicidios_por_100k=('homicidios_por_100k', 'mean'),
        populacao_total=('Populacao_total', 'sum')
    ).reset_index()

    metricas_br_evol_nomes = st.multiselect(
        "Selecione as Métricas Nacionais para Evolução:",
        ['Taxa de Desemprego (%)', 'Renda Média Anual', 'Homicídios (por 100k hab.)', 'População Total'],
        default=['Taxa de Desemprego (%)', 'Renda Média Anual']
    )

    if metricas_br_evol_nomes:
        mapa_br = {
            'Taxa de Desemprego (%)': 'taxa_desemprego_media',
            'Renda Média Anual': 'renda_media_anual',
            'Homicídios (por 100k hab.)': 'homicidios_por_100k',
            'População Total': 'populacao_total'
        }
        metricas_br_evol_cols = [mapa_br[nome] for nome in metricas_br_evol_nomes]

        df_br_melted = df_brasil_evol.melt(
            id_vars=['Ano'],
            value_vars=metricas_br_evol_cols,
            var_name='Métrica',
            value_name='Valor'
        )
        mapa_nomes_metricas_rev_br = {v: k for k, v in mapa_br.items()}
        df_br_melted['Métrica'] = df_br_melted['Métrica'].map(mapa_nomes_metricas_rev_br)
        df_br_melted['Valor'] = pd.to_numeric(df_br_melted['Valor'], errors='coerce')

        line_chart_br = alt.Chart(df_br_melted).mark_line(point=True).encode(
            x=alt.X('Ano:O', title='Ano'),
            y=alt.Y('Valor:Q', title='Valor', scale=alt.Scale(zero=False)),
            color='Métrica:N',
            tooltip=['Ano', 'Métrica', alt.Tooltip('Valor:Q', format=".2f")]
        ).properties(
            title="Evolução de Indicadores Nacionais (Médias/Somas)"
        ).interactive()
        st.altair_chart(line_chart_br, use_container_width=True)
    else:
        st.warning("Selecione pelo menos uma métrica para visualizar a evolução.")

st.divider()

st.header("Comparativo de Indicadores por UF")
st.markdown(f"Compare diferentes métricas lado a lado para os estados no ano de **{ano_selecionado}**.")


metricas_comp_nomes = st.multiselect(
    "Selecione 2 ou 3 Métricas para Comparação:",
    lista_nomes_metricas,
    default=lista_nomes_metricas[:3], 
    max_selections=3 
)

if len(metricas_comp_nomes) >= 2:
    metricas_comp_cols = [metricas[nome] for nome in metricas_comp_nomes]
    

    col_ordem1, col_ordem2 = st.columns(2)
    with col_ordem1:
        metrica_ordem_nome = st.selectbox(
            "Ordenar UFs por qual métrica?",
            metricas_comp_nomes,
            index=0
        )
    with col_ordem2:
        tipo_ranking = st.radio(
            "Mostrar Ranking:",
            ("Top 10 (Maiores)", "Bottom 10 (Menores)"),
            horizontal=True
        )
        
    metrica_ordem_col = metricas[metrica_ordem_nome]


    df_comp = df_filtrado_ano[['UF'] + metricas_comp_cols].copy()
    

    for col in metricas_comp_cols:
        df_comp[col] = pd.to_numeric(df_comp[col], errors='coerce')
    df_comp = df_comp.dropna(subset=[metrica_ordem_col])

    if not df_comp.empty:

        if "Top 10" in tipo_ranking:
            df_plot = df_comp.nlargest(10, metrica_ordem_col)

            sort_order = alt.SortField(field=metrica_ordem_col, order='descending') 
        else:
            df_plot = df_comp.nsmallest(10, metrica_ordem_col)

            sort_order = alt.SortField(field=metrica_ordem_col, order='ascending')


        df_plot_melted = df_plot.melt(
            id_vars='UF', 
            value_vars=metricas_comp_cols, 
            var_name='Métrica Código', 
            value_name='Valor'
        )
        

        mapa_nomes_metricas_rev = {v: k for k, v in metricas.items()}
        df_plot_melted['Métrica'] = df_plot_melted['Métrica Código'].map(mapa_nomes_metricas_rev)


        st.subheader(f"{tipo_ranking} UFs por '{metrica_ordem_nome}'")
        

        df_plot_melted_px = df_plot_melted.copy()
        

        uf_order = df_plot['UF'].tolist()

        fig_comp = px.bar(
            df_plot_melted_px,
            x='UF', 
            y='Valor',
            color='Métrica', 
            barmode='group', 
            title=f"Comparativo: {', '.join(metricas_comp_nomes)}",
            labels={'Valor': 'Valor do Indicador', 'Métrica': 'Indicador'},
            category_orders={'UF': uf_order} 
        )
        
        fig_comp.update_layout(
            xaxis_title="Unidade da Federação",
            yaxis_title="Valor",
            legend_title="Métricas",
            title_font_size=20,
            xaxis_tickangle=-45 
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        
    else:
        st.warning(f"Não há dados suficientes ou válidos para a métrica '{metrica_ordem_nome}' em {ano_selecionado} para gerar o gráfico.")

else:
    st.warning("Selecione pelo menos duas métricas para comparação.")


st.divider()

if st.checkbox("Mostrar Tabela de Dados Completa"):
    st.header("Tabela de Dados Anual Consolidada")
    colunas_display = ['UF', 'Ano', 'populacao_total', 'taxa_desemprego_media', 'renda_media_anual', 'perc_esc_fundamental', 'perc_esc_medio', 'homicidios_por_100k', 'obitos_suicidio_por_100k'] 
    st.dataframe(df[colunas_display + [col for col in df.columns if '_por_100k' in col and col not in colunas_display]].sort_values(by=['UF', 'Ano']))

st.divider()

st.header("Comparativo Bivariado por UF")
st.markdown(f"""
Compare dois indicadores selecionados entre as UFs para o ano de **{ano_selecionado}**. 
O primeiro indicador é mostrado como colunas (eixo esquerdo), e o segundo como uma linha (eixo direito). 
As UFs são ordenadas pelo valor do primeiro indicador (colunas).
""")

# (O dicionário 'tabelas' continua igual)
try:
    tabelas = {
        'Renda Média vs Mortes Cardio (100k)': df[['UF', 'Ano', 'renda_media_anual', 'mortes_cardio_por_100k']].dropna(),
        'Renda Média vs Internações Cardio (100k)': df[['UF', 'Ano', 'renda_media_anual', 'internacoes_cardio_por_100k']].dropna(),
        'Escolaridade Média (%) vs Mortes Cardio (100k)': df[['UF', 'Ano', 'perc_esc_medio', 'mortes_cardio_por_100k']].dropna(),
        'Escolaridade Média (%) vs Internações Cardio (100k)': df[['UF', 'Ano', 'perc_esc_medio', 'internacoes_cardio_por_100k']].dropna(),
        'Escolaridade Fundamental (%) vs Mortes Cardio (100k)': df[['UF', 'Ano', 'perc_esc_fundamental', 'mortes_cardio_por_100k']].dropna(),
        'Escolaridade Fundamental (%) vs Internações Cardio (100k)': df[['UF', 'Ano', 'perc_esc_fundamental', 'internacoes_cardio_por_100k']].dropna(),
        'Suicídios (100k) vs Mortes Cardio (100k)': df[['UF', 'Ano', 'obitos_suicidio_por_100k', 'mortes_cardio_por_100k']].dropna(),
        'Suicídios (100k) vs Internações Cardio (100k)': df[['UF', 'Ano', 'obitos_suicidio_por_100k', 'internacoes_cardio_por_100k']].dropna(),
        'Renda Média vs Homicídios (100k)': df[['UF', 'Ano', 'renda_media_anual', 'homicidios_por_100k']].dropna(),
        'Renda Média vs Desemprego (%)': df[['UF', 'Ano', 'renda_media_anual', 'taxa_desemprego_media']].dropna(),
    }

    par_selecionado_nome = st.selectbox(
        "Selecione o Par de Indicadores para Comparar:",
        list(tabelas.keys())
    )

    df_par_original = tabelas[par_selecionado_nome]

    # Filtrar pelo ano selecionado na sidebar
    df_par_ano = df_par_original[df_par_original['Ano'] == ano_selecionado].copy()

    if not df_par_ano.empty:
        metric_cols = [col for col in df_par_ano.columns if col not in ['UF', 'Ano']]
        
        if len(metric_cols) == 2:
            # A primeira métrica do par será as colunas, a segunda a linha
            coluna_metrica_col = metric_cols[0] 
            linha_metrica_col = metric_cols[1]
            
            mapa_nomes_metricas_rev = {v: k for k, v in metricas.items()}
            coluna_metrica_nome = mapa_nomes_metricas_rev.get(coluna_metrica_col, coluna_metrica_col)
            linha_metrica_nome = mapa_nomes_metricas_rev.get(linha_metrica_col, linha_metrica_col)

            # Ordenar o DataFrame pela métrica das colunas (decrescente) para definir a ordem no eixo X
            df_par_ano_sorted = df_par_ano.sort_values(by=coluna_metrica_col, ascending=False)
            uf_order = df_par_ano_sorted['UF'].tolist()

            # Base chart (define o eixo X e a fonte de dados)
            base = alt.Chart(df_par_ano_sorted).encode(
                alt.X('UF:N', sort=uf_order, title='UF') # Ordena o eixo X
            )

            # Camada das Colunas (eixo Y esquerdo)
            bars = base.mark_bar().encode(
                alt.Y(f'{coluna_metrica_col}:Q', title=coluna_metrica_nome, axis=alt.Axis(grid=True)),
                tooltip=[
                    alt.Tooltip('UF:N', title='UF'),
                    alt.Tooltip(f'{coluna_metrica_col}:Q', format=".2f", title=coluna_metrica_nome)
                ]
            )

            line = base.mark_line(color='orange').encode( # Define a cor da LINHA aqui
                alt.Y(f'{linha_metrica_col}:Q', title=linha_metrica_nome, axis=alt.Axis(grid=False)), 
                tooltip=[
                    alt.Tooltip('UF:N', title='UF'),
                    alt.Tooltip(f'{linha_metrica_col}:Q', format=".2f", title=linha_metrica_nome)
                ]
            )
            
            # Camada separada para os PONTOS (com cor diferente)
            points = base.mark_point(color='red', size=50, filled=True).encode( # Define a cor e tamanho dos PONTOS aqui
                 alt.Y(f'{linha_metrica_col}:Q'), # Mapeia para o mesmo eixo Y da linha
                 tooltip=[ # Repete o tooltip para os pontos
                    alt.Tooltip('UF:N', title='UF'),
                    alt.Tooltip(f'{linha_metrica_col}:Q', format=".2f", title=linha_metrica_nome)
                ]
            )

            # Combinar as camadas: barras, linha e pontos
            dual_axis_chart = alt.layer(bars, line, points).resolve_scale( # Adiciona 'points' à camada
                y='independent' 
            ).properties(
                 title=f"{coluna_metrica_nome} (Colunas) vs. {linha_metrica_nome} (Linha/Pontos) por UF - {ano_selecionado}" # Atualiza título
            ).interactive()

            st.altair_chart(dual_axis_chart, use_container_width=True)
            
            # Calcular e mostrar correlação (ainda útil como referência)
            correlacao_par = df_par_ano[coluna_metrica_col].corr(df_par_ano[linha_metrica_col])
            st.caption(f"Correlação de Pearson para {ano_selecionado}: **{correlacao_par:.3f}**")


        else:
            st.warning("A tabela selecionada não contém exatamente duas colunas de métricas.")
    else:
        st.warning(f"Não há dados completos (sem valores ausentes) para o par selecionado no ano {ano_selecionado}.")

except KeyError as e:
    st.error(f"Erro ao acessar coluna: {e}. Verifique se os nomes das colunas no dicionário 'tabelas' correspondem exatamente aos nomes no DataFrame 'df'.")
except Exception as e_bivar:
     st.error(f"Ocorreu um erro inesperado na análise bivariada: {e_bivar}")


# --- Seção da Tabela Opcional (continua igual) ---
st.divider()