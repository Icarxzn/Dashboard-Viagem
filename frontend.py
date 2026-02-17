# ============================================================================
# FRONTEND DO DASHBOARD - Interface Dash com navegação e callbacks
# ============================================================================
# Responsável por:
# - Renderizar a UI com sidebar e conteúdo dinâmico
# - Gerenciar navegação entre páginas
# - Executar callbacks para atualizar dados e gráficos
# - Exportar dados em CSV

import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime
import json
from Routes import get_pagina

print("="*70)
print("INICIANDO FRONTEND DO DASHBOARD")
print("="*70)

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================
# URL da API backend para requisições
API_URL = "http://localhost:8050"

# Mapeamento de cores para cada status de viagem
CORES_STATUS = {
    "Parado": "#dc3545",
    "Em trânsito": "#28a745",
    "Em transito": "#28a745",
    "Finalizado": "#6c757d",
    "Cancelado": "#ffc107"
}

# ============================================================================
# FUNÇÕES AUXILIARES - Requisições à API
# ============================================================================

def buscar_dados(filters=None):
    """
    Busca dados da API backend com filtros opcionais
    
    Args:
        filters (dict): Dicionário com filtros (ids, destinos, status, datas)
    
    Returns:
        dict: Resposta JSON da API com dados, colunas, estatísticas
    """
    try:
        params = {}
        if filters:
            if filters.get('ids'):
                params['ids'] = json.dumps(filters['ids'])
            if filters.get('destinos'):
                params['destinos'] = json.dumps(filters['destinos'])
            if filters.get('status'):
                params['status'] = json.dumps(filters['status'])
            if filters.get('data_inicial'):
                params['data_inicial'] = filters['data_inicial']
            if filters.get('data_final'):
                params['data_final'] = filters['data_final']
        
        response = requests.get(f"{API_URL}/api/dados", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return {'success': False, 'dados': [], 'colunas': [], 'estatisticas': {'total': 0, 'transito': 0, 'parado': 0, 'finalizado': 0}, 'total_registros': 0}

def buscar_filtros():
    """
    Busca opções de filtro da API backend
    
    Returns:
        dict: Resposta JSON com opções para ids, destinos e status
    """
    try:
        response = requests.get(f"{API_URL}/api/filtros", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao buscar filtros: {e}")
        return {'success': False, 'opcoes': {}}

def buscar_programado():
    """
    Busca dados de viagens programadas da API backend
    
    Returns:
        dict: Resposta JSON com estatísticas e próximas viagens
    """
    try:
        response = requests.get(f"{API_URL}/api/programado", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao buscar programado: {e}")
        return {'success': False, 'estatisticas': {'total_programado': 0, 'proximas_24h': 0, 'proximos_7dias': 0}, 'proximas_viagens': []}

def buscar_programado_filtrado(data=None, turno=None, status=None):
    """
    Busca dados de viagens programadas com filtros
    
    Args:
        data (str): Data (YYYY-MM-DD)
        turno (str): Turno (Manhã, Tarde, Noite)
        status (str): Status
    
    Returns:
        dict: Resposta JSON com dados, colunas e estatísticas (sacas, scuttle, palete, total)
    """
    try:
        params = {}
        if data:
            params['data'] = data
        if turno:
            params['turno'] = turno
        if status:
            params['status'] = status
        
        response = requests.get(f"{API_URL}/api/programado", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao buscar programado filtrado: {e}")
        return {'success': False, 'dados': [], 'colunas': [], 'estatisticas': {'total_sacas': 0, 'total_scuttle': 0, 'total_palete': 0, 'total_geral': 0}, 'total_registros': 0}

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Dashboard de Monitoramento de Viagens"

# ============================================================================
# SEÇÃO DE ESTILOS CSS - Define toda a aparência visual do dashboard
# ============================================================================
# Inclui: cores, fontes, layout responsivo, animações, temas
app.index_string = '''<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#fff5f0 0%,#ffe8dd 50%,#ffd4c4 100%);min-height:100vh;padding:20px;margin:0;overflow-x:hidden}
#react-entry-point{width:100%;max-width:100vw;overflow-x:hidden}

.title-container{background:linear-gradient(135deg,#FF6B35 0%,#FF8C42 50%,#FFB085 100%);padding:25px 30px;border-radius:16px;box-shadow:0 2px 10px rgba(255,107,53,.15);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px;width:100%;box-sizing:border-box}
.title-left{flex:1}
.title-gradient{color:white;font-weight:700;font-size:2rem;margin:0 0 5px 0;text-shadow:2px 2px 4px rgba(0,0,0,.1)}
.header-subtitle{color:rgba(255,255,255,.95);font-size:1rem;font-weight:400}

.export-btn-secondary{background:linear-gradient(135deg, #6c757d 0%, #495057 100%);color:white;border:none;padding:10px 20px;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9rem;transition:all 0.3s ease;display:flex;align-items:center;gap:6px}
.export-btn-secondary:hover{background:linear-gradient(135deg, #495057 0%, #343a40 100%);transform:translateY(-2px)}

.filters-container{display:grid;grid-template-columns:repeat(4, 1fr);gap:15px;margin:20px;padding:20px;background:white;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.08);border:1px solid #ffe8dd;width:calc(100% - 40px);box-sizing:border-box}
.filter-item{display:flex;flex-direction:column}
.filter-item label{font-weight:600;color:#FF6B35;margin-bottom:8px;font-size:.9rem}
.dates-container{grid-column:1 / -1;display:grid;grid-template-columns:repeat(2, 1fr);gap:15px;margin-top:10px;padding-top:15px;border-top:2px solid #ffe8dd}

.dashboard-top{display:grid;grid-template-columns:2fr 1fr;gap:20px;margin:0 20px 20px 20px;width:calc(100% - 40px);box-sizing:border-box}
.graph-card{background:white;border-radius:16px;padding:20px;box-shadow:0 4px 16px rgba(255,107,53,.1);border:2px solid #ffe8dd;position:relative;overflow:hidden}
.graph-card::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#FF6B35 0%,#FF8C42 50%,#FFB085 100%)}
.stats-card{background:white;border-radius:16px;padding:20px;box-shadow:0 4px 16px rgba(255,107,53,.1);border:2px solid #ffe8dd;display:flex;flex-direction:column;gap:15px}
.stat-item{background:linear-gradient(135deg, #fff5f0 0%, #ffe8dd 100%);padding:15px;border-radius:12px;border-left:4px solid #FF6B35;margin-bottom:10px}
.stat-value{font-size:2rem;font-weight:700;color:#FF6B35;margin:5px 0}
.stat-label{font-size:0.9rem;color:#666;font-weight:500}

.table-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;flex-wrap:wrap;gap:10px}
h3{color:#FF6B35;font-size:1.5rem;margin:0;font-weight:700;position:relative;display:inline-block}
h3::after{content:'';position:absolute;bottom:-5px;left:0;width:60px;height:3px;background:linear-gradient(90deg,#FF6B35,#FF8C42);border-radius:2px}
.table-container{background:white;border-radius:12px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,.08);border:1px solid #ffe8dd;margin:0 20px 20px 20px;width:calc(100% - 40px);box-sizing:border-box}
.dash-table-container{border-radius:12px;overflow:hidden;border:2px solid #ffe8dd;max-height:600px;overflow-y:auto}
.dash-spreadsheet{font-size:.9rem}
.dash-table-header{background:linear-gradient(135deg,#FF6B35 0%,#FF8C42 100%)!important;color:white!important;font-weight:600!important;position:sticky;top:0;z-index:100}
.dash-table-header th{background:inherit!important;color:white!important;border-right:1px solid rgba(255,255,255,.15)!important;padding:16px!important;white-space:nowrap}
.dash-table-row{border-bottom:1px solid #ffe8dd;transition:background .2s ease}
.dash-table-row:hover{background:linear-gradient(135deg,#fff5f0 0%,#ffe8dd 100%)!important}
.dash-table-cell{padding:12px!important;white-space:nowrap}

.Select-control{border:2px solid #ffe8dd!important;border-radius:8px!important;transition:all .2s ease!important;background:white!important;min-height:42px!important}
.Select-control:hover{border-color:#FF8C42!important;box-shadow:0 0 0 3px rgba(255,107,53,.1)!important}
.Select-control.is-focused{border-color:#FF6B35!important;box-shadow:0 0 0 3px rgba(255,107,53,.15)!important}

.sidebar{position:fixed;left:0;top:0;width:250px;height:100vh;background:linear-gradient(180deg,#FF6B35 0%,#F7931E 50%,#FF8C42 100%);box-shadow:4px 0 20px rgba(255,107,53,0.2);z-index:1000;display:flex;flex-direction:column;overflow-y:auto}
.sidebar-logo{color:white;font-size:1.5rem;font-weight:800;text-align:center;padding:25px 20px;background:rgba(0,0,0,0.1);border-bottom:1px solid rgba(255,255,255,0.15)}
.sidebar-item{padding:15px 20px;color:rgba(255,255,255,0.9);font-weight:500;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:12px;border-left:3px solid transparent}
.sidebar-item:hover{background:rgba(255,255,255,0.12);color:white;border-left-color:white;padding-left:25px}
.sidebar-item.active{background:rgba(255,255,255,0.2);color:white;border-left-color:white;font-weight:600}
.main-with-sidebar{margin-left:250px;width:calc(100% - 250px);padding:0;box-sizing:border-box}

::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-track{background:#ffe8dd;border-radius:4px}
::-webkit-scrollbar-thumb{background:linear-gradient(135deg,#FF6B35,#FF8C42);border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:linear-gradient(135deg,#FF8C42,#FFB085)}

@media (max-width:1200px){.filters-container{grid-template-columns:repeat(2, 1fr)}.dashboard-top{grid-template-columns:1fr}}
@media (max-width:768px){.filters-container{grid-template-columns:1fr}.title-container{flex-direction:column;text-align:center}.title-left{text-align:center}.table-header{flex-direction:column;align-items:stretch}.sidebar{width:70px}.sidebar-logo{font-size:1.2rem;padding:20px 10px}.sidebar-item{padding:14px;justify-content:center;font-size:1.2rem}.sidebar-item span:last-child{display:none}.main-with-sidebar{margin-left:70px;width:calc(100% - 70px)}}
</style></head><body>{%app_entry%}{%config%}{%scripts%}{%renderer%}</body></html>'''

# ============================================================================
# SEÇÃO DE LAYOUT - Estrutura HTML do dashboard
# ============================================================================
# Componentes principais:
# - Sidebar: Menu lateral fixo com navegação
# - Header: Título e status da API
# - Conteúdo dinâmico: Renderizado pelos callbacks
# - Componentes auxiliares: Interval, Download, Store
app.layout = html.Div([
    # ========================================================================
    # SIDEBAR - Menu lateral fixo com navegação entre páginas
    # ========================================================================
    html.Div([
        html.Div("Dashboard", className="sidebar-logo"),
        html.Div([html.Span("📊"), html.Span(" Previsão")], id="menu-previsao", className="sidebar-item active"),
        html.Div([html.Span("📅"), html.Span(" Programado")], id="menu-programado", className="sidebar-item"),
        html.Div([html.Span("🚚"), html.Span(" Viagens")], id="menu-viagens", className="sidebar-item"),
        html.Div([html.Span("📈"), html.Span(" Relatórios")], id="menu-relatorios", className="sidebar-item"),
        html.Div([html.Span("⚙️"), html.Span(" Configurações")], id="menu-config", className="sidebar-item"),
    ], className="sidebar"),
    
    # ========================================================================
    # CONTEÚDO PRINCIPAL - Área com header e conteúdo dinâmico
    # ========================================================================
    html.Div([
        # ====================================================================
        # HEADER - Título, subtítulo e status da API
        # ====================================================================
        html.Div([
            html.Div([
                html.H1("📊 Dashboard de Monitoramento de Viagens", className="title-gradient"),
                html.Div("Visualize e exporte dados de viagens em tempo real", className="header-subtitle"),
                html.Div(id="api-status", style={'color': 'rgba(255,255,255,.9)', 'fontSize': '0.85rem', 'marginTop': '5px'})
            ], className="title-left"),
        ], className="title-container"),
        
        # ====================================================================
        # COMPONENTES AUXILIARES - Interval, Download, Store
        # ====================================================================
        dcc.Interval(id="interval", interval=20000, n_intervals=0),  # Auto-refresh a cada 20s
        dcc.Download(id="download-csv"),  # Para exportar dados
        dcc.Store(id="pagina-ativa", data="previsao"),  # Armazena página ativa
        
        # ====================================================================
        # CONTEÚDO DINÂMICO - Renderizado pelos callbacks
        # ====================================================================
        html.Div(id="conteudo-pagina")
    ], className="main-with-sidebar")
])

# ============================================================================
# SEÇÃO DE CALLBACKS - Lógica interativa do dashboard
# ============================================================================
# Callbacks executam quando inputs mudam e atualizam outputs
# Ordem de execução: mudar_pagina → renderizar_pagina → atualizar_filtros → atualizar_dashboard

# CALLBACK 1: Mudar página ao clicar no menu
@app.callback(
    Output("pagina-ativa", "data"),
    Input("menu-previsao", "n_clicks"),
    Input("menu-programado", "n_clicks"),
    Input("menu-viagens", "n_clicks"),
    Input("menu-relatorios", "n_clicks"),
    Input("menu-config", "n_clicks"),
    prevent_initial_call=True
)
def mudar_pagina(previsao, programado, viagens, relatorios, config):
    """
    Detecta qual menu foi clicado e atualiza a página ativa
    
    Args:
        previsao, programado, viagens, relatorios, config: Número de cliques em cada menu
    
    Returns:
        str: Nome da página ativa ('previsao', 'programado', 'viagens', 'relatorios', 'config')
    """
    if not callback_context.triggered:
        return "previsao"
    trigger_id = callback_context.triggered[0]["prop_id"].split(".")[0]
    paginas = {"menu-previsao": "previsao", "menu-programado": "programado", "menu-viagens": "viagens", "menu-relatorios": "relatorios", "menu-config": "config"}
    return paginas.get(trigger_id, "previsao")

# CALLBACK 2: Renderizar página e atualizar menu ativo
@app.callback(
    Output("conteudo-pagina", "children"),
    Output("menu-previsao", "className"),
    Output("menu-programado", "className"),
    Output("menu-viagens", "className"),
    Output("menu-relatorios", "className"),
    Output("menu-config", "className"),
    Input("pagina-ativa", "data")
)
def renderizar_pagina(pagina):
    """
    Renderiza o conteúdo da página selecionada e marca menu como ativo
    
    Args:
        pagina (str): Nome da página ativa
    
    Returns:
        tuple: Conteúdo da página + classes CSS para cada menu item
    """
    classes = {"previsao": "sidebar-item", "programado": "sidebar-item", "viagens": "sidebar-item", "relatorios": "sidebar-item", "config": "sidebar-item"}
    classes[pagina] = "sidebar-item active"
    conteudo = get_pagina(pagina)
    return conteudo, classes["previsao"], classes["programado"], classes["viagens"], classes["relatorios"], classes["config"]

# CALLBACK 3: Atualizar opções de filtro da API
@app.callback(
    Output("filtro-id", "options"),
    Output("filtro-destino", "options"),
    Output("filtro-status", "options"),
    Output("filtro-prog-turno", "options"),
    Output("api-status", "children"),
    Input("interval", "n_intervals")
)
def atualizar_filtros(_):
    """
    Busca opções de filtro da API e verifica saúde do servidor
    
    Args:
        _ (int): Número de intervalos (não usado)
    
    Returns:
        tuple: Opções para cada filtro + status da API
    """
    try:
        response = buscar_filtros()
        if response.get('success'):
            opcoes = response.get('opcoes', {})
            try:
                health_response = requests.get(f"{API_URL}/api/health", timeout=5)
                status_text = "✅ Conectado ao servidor" if health_response.ok else "⚠️ Servidor lento"
            except:
                status_text = "⚠️ Verificando conexão..."
            # garantir opção 'Todos' no topo e preencher turno com valores normalizados (T1/T2/T3)
            turno_opts = opcoes.get('turno', []) or []
            # prefix Todos
            turno_opts = [{"label": "Todos", "value": ""}] + turno_opts
            return opcoes.get('ids', []), opcoes.get('destinos', []), opcoes.get('status', []), turno_opts, status_text
        else:
            return [], [], [], [], "❌ Erro ao carregar filtros"
    except Exception as e:
        print(f"Erro ao atualizar filtros: {e}")
        return [], [], [], [], "❌ Servidor offline"

# CALLBACK 4: Limpar todos os filtros
@app.callback(
    Output("filtro-id", "value"),
    Output("filtro-destino", "value"),
    Output("filtro-status", "value"),
    Output("filtro-data-inicial", "date"),
    Output("filtro-data-final", "date"),
    Input("btn-limpar", "n_clicks"),
    prevent_initial_call=True
)
def limpar_filtros(n_clicks):
    """
    Reseta todos os filtros para valores vazios
    
    Args:
        n_clicks (int): Número de cliques no botão
    
    Returns:
        tuple: Valores vazios para todos os filtros
    """
    return None, None, None, None, None

# CALLBACK 5: Atualizar dashboard com dados filtrados
@app.callback(
    Output("grafico", "figure"),
    Output("tabela", "columns"),
    Output("tabela", "data"),
    Output("contador-registros", "children"),
    Output("ultima-atualizacao", "children"),
    Output("stat-total", "children"),
    Output("stat-transito", "children"),
    Output("stat-parado", "children"),
    Output("stat-finalizado", "children"),
    Input("filtro-id", "value"),
    Input("filtro-destino", "value"),
    Input("filtro-status", "value"),
    Input("filtro-data-inicial", "date"),
    Input("filtro-data-final", "date"),
    Input("interval", "n_intervals")
)
def atualizar_dashboard(ids, destinos, status, data_inicial, data_final, n_intervals):
    """
    Busca dados da API com filtros e atualiza gráfico, tabela e estatísticas
    
    Args:
        ids, destinos, status, data_inicial, data_final: Filtros aplicados
        n_intervals (int): Número de intervalos (para auto-refresh)
    
    Returns:
        tuple: Gráfico, colunas da tabela, dados, contador, timestamp, estatísticas
    """
    filters = {}
    if ids:
        filters['ids'] = ids
    if destinos:
        filters['destinos'] = destinos
    if status:
        filters['status'] = status
    if data_inicial:
        filters['data_inicial'] = data_inicial
    if data_final:
        filters['data_final'] = data_final
    
    response = buscar_dados(filters)
    
    if not response.get('success'):
        fig = criar_grafico_fallback()
        return fig, [{"name": "Erro", "id": "erro"}], [{"erro": "Não foi possível carregar os dados."}], "0", "Erro", [html.Div("Total de Viagens", className="stat-label"), html.Div("0", className="stat-value")], [html.Div("Em Trânsito", className="stat-label"), html.Div("0", className="stat-value", style={'color': '#28a745'})], [html.Div("Parado", className="stat-label"), html.Div("0", className="stat-value", style={'color': '#dc3545'})], [html.Div("Finalizado", className="stat-label"), html.Div("0", className="stat-value", style={'color': '#6c757d'})]
    
    dados = response.get('dados', [])
    colunas = response.get('colunas', [])
    estatisticas = response.get('estatisticas', {})
    total_registros = response.get('total_registros', 0)
    timestamp = response.get('timestamp', datetime.now().isoformat())
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        ultima_atualizacao = f"Última atualização: {dt.strftime('%H:%M:%S')}"
    except:
        ultima_atualizacao = f"Atualizado há {n_intervals * 20} segundos"
    
    fig = criar_grafico(pd.DataFrame(dados)) if dados else criar_grafico_fallback()
    columns = [{"name": col, "id": col} for col in colunas] if colunas else []
    
    return (
        fig,
        columns,
        dados,
        str(total_registros),
        ultima_atualizacao,
        [html.Div("Total de Viagens", className="stat-label"), html.Div(f"{estatisticas.get('total', 0)}", className="stat-value")],
        [html.Div("Em Trânsito", className="stat-label"), html.Div(f"{estatisticas.get('transito', 0)}", className="stat-value", style={'color': '#28a745'})],
        [html.Div("Parado", className="stat-label"), html.Div(f"{estatisticas.get('parado', 0)}", className="stat-value", style={'color': '#dc3545'})],
        [html.Div("Finalizado", className="stat-label"), html.Div(f"{estatisticas.get('finalizado', 0)}", className="stat-value", style={'color': '#6c757d'})]
    )

def criar_grafico(df):
    """
    Cria gráfico de barras com distribuição por status
    
    Args:
        df (pd.DataFrame): DataFrame com dados
    
    Returns:
        plotly.graph_objects.Figure: Gráfico de barras
    """
    if df.empty or 'Status_da_Viagem' not in df.columns:
        return criar_grafico_fallback()
    
    status_counts = df['Status_da_Viagem'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Quantidade']
    
    fig = px.bar(status_counts, x='Status', y='Quantidade', title='', color='Status', color_discrete_map=CORES_STATUS, text='Quantidade')
    fig.update_traces(textposition='outside', textfont=dict(size=12, color="#333"), marker=dict(line=dict(width=1, color='white')))
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis=dict(title="Status", showgrid=False, tickangle=0), yaxis=dict(title="Quantidade", showgrid=True, gridcolor='#ffe8dd'), legend=dict(title="Status da Viagem", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=20, r=20, t=40, b=40), hovermode="x unified")
    return fig

def criar_grafico_fallback():
    """
    Cria gráfico vazio com mensagem de carregamento
    
    Returns:
        plotly.graph_objects.Figure: Gráfico vazio
    """
    fig = go.Figure()
    fig.add_annotation(text="Aguardando dados...", showarrow=False, font=dict(size=16, color="#666"))
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis=dict(showgrid=False, zeroline=False, visible=False), yaxis=dict(showgrid=False, zeroline=False, visible=False))
    return fig

@app.callback(
    Output("download-csv", "data"),
    Input("btn-exportar-tabela", "n_clicks"),
    State("filtro-id", "value"),
    State("filtro-destino", "value"),
    State("filtro-status", "value"),
    State("filtro-data-inicial", "date"),
    State("filtro-data-final", "date"),
    prevent_initial_call=True
)
def exportar_csv(n_clicks, ids, destinos, status, data_inicial, data_final):
    """
    Exporta dados filtrados em CSV
    
    Args:
        n_clicks (int): Número de cliques no botão
        ids, destinos, status, data_inicial, data_final: Filtros aplicados
    
    Returns:
        dcc.send_bytes: Arquivo CSV para download
    """
    if not n_clicks:
        return dash.no_update
    
    try:
        params = {}
        if ids:
            params['ids'] = json.dumps(ids)
        if destinos:
            params['destinos'] = json.dumps(destinos)
        if status:
            params['status'] = json.dumps(status)
        if data_inicial:
            params['data_inicial'] = data_inicial
        if data_final:
            params['data_final'] = data_final
        
        response = requests.get(f"{API_URL}/api/exportar", params=params, timeout=30)
        response.raise_for_status()
        
        content_disposition = response.headers.get('Content-Disposition', '')
        filename = 'dados_exportados.csv'
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        
        return dcc.send_bytes(response.content, filename)
    except Exception as e:
        print(f"Erro ao exportar: {e}")
        return dcc.send_string("Erro ao exportar dados", "erro_exportacao.txt")

# CALLBACK 6: Limpar filtros da página programado
@app.callback(
    Output("filtro-prog-data", "date"),
    Output("filtro-prog-turno", "value"),
    Output("filtro-prog-status", "value"),
    Input("btn-limpar-programado", "n_clicks"),
    prevent_initial_call=True
)
def limpar_filtros_programado(n_clicks):
    """
    Reseta todos os filtros da página programado
    
    Args:
        n_clicks (int): Número de cliques no botão
    
    Returns:
        tuple: Valores vazios para todos os filtros
    """
    return None, "", ""

# CALLBACK 7: Atualizar dados da página de programado
@app.callback(
    Output("stat-total-sacas", "children"),
    Output("stat-total-scuttle", "children"),
    Output("stat-total-palete", "children"),
    Output("stat-total-geral", "children"),
    Output("tabela-programado", "columns"),
    Output("tabela-programado", "data"),
    Output("contador-registros-programado", "children"),
    Output("ultima-atualizacao-programado", "children"),
    Input("filtro-prog-data", "date"),
    Input("filtro-prog-turno", "value"),
    Input("filtro-prog-status", "value"),
    Input("interval-programado", "n_intervals")
)
def atualizar_programado(data, turno, status, n_intervals):
    """
    Atualiza dados da página de viagens programadas com filtros
    
    Args:
        data (str): Data
        turno (str): Turno selecionado
        status (str): Status selecionado
        n_intervals (int): Número de intervalos (para auto-refresh)
    
    Returns:
        tuple: Estatísticas (sacas, scuttle, palete, total), colunas, dados, contador e timestamp
    """
    try:
        # Buscar dados com filtros
        response = buscar_programado_filtrado(data, turno if turno else None, status if status else None)
        
        if not response.get('success'):
            error_msg = response.get('error') if isinstance(response, dict) else None
            display_msg = error_msg or "Não foi possível carregar os dados."
            return (
                "0", "0", "0", "0",
                [{"name": "Erro", "id": "erro"}],
                [{"erro": display_msg}],
                "0",
                display_msg
            )
        
        stats = response.get('estatisticas', {})
        dados = response.get('dados', [])
        colunas = response.get('colunas', [])
        total_registros = response.get('total_registros', 0)
        timestamp = response.get('timestamp', datetime.now().isoformat())
        
        # Formatar timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            ultima_atualizacao = f"Atualizado às {dt.strftime('%H:%M:%S')}"
        except:
            ultima_atualizacao = "Atualizado agora"
        
        # Preparar colunas da tabela
        columns = [{"name": col, "id": col} for col in colunas] if colunas else []
        
        # Formatar números com separador de milhares
        total_sacas = f"{stats.get('total_sacas', 0):,}".replace(',', '.')
        total_scuttle = f"{stats.get('total_scuttle', 0):,}".replace(',', '.')
        total_palete = f"{stats.get('total_palete', 0):,}".replace(',', '.')
        total_geral = f"{stats.get('total_geral', 0):,}".replace(',', '.')
        
        return (
            total_sacas,
            total_scuttle,
            total_palete,
            total_geral,
            columns,
            dados,
            str(total_registros),
            ultima_atualizacao
        )
        
    except Exception as e:
        print(f"Erro ao atualizar programado: {e}")
        return (
            "0", "0", "0", "0",
            [{"name": "Erro", "id": "erro"}],
            [{"erro": "Erro ao carregar dados"}],
            "0",
            "Erro ao atualizar"
        )


# ============================================================================
# INICIALIZAÇÃO DO SERVIDOR
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 DASHBOARD INICIADO COM SUCESSO!")
    print("="*70)
    print("\n📊 Acesse em: http://127.0.0.1:8051")
    print("⚙️  API em: http://localhost:8050")
    print("="*70 + "\n")
    app.run(debug=False, port=8051, host='127.0.0.1', use_reloader=False)
