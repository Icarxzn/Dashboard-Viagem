# frontend.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta
import json

print("="*70)
print("INICIANDO FRONTEND DO DASHBOARD")
print("="*70)

# URL da API backend
API_URL = "http://localhost:8050"

# Configurações
CORES_STATUS = {
    "Parado": "#dc3545",
    "Em trânsito": "#28a745",
    "Em transito": "#28a745",
    "Finalizado": "#6c757d",
    "Cancelado": "#ffc107"
}

# Funções auxiliares
def buscar_dados(filters=None):
    """Busca dados da API backend"""
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
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Buscando dados da API com filtros: {params}")
        response = requests.get(f"{API_URL}/api/dados", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Dados recebidos: {data.get('total_registros')} registros, cache age: {data.get('cache_age', 'N/A')}s")
        return data
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Erro ao buscar dados: {e}")
        return {
            'success': False,
            'dados': [],
            'colunas': [],
            'estatisticas': {'total': 0, 'transito': 0, 'parado': 0, 'finalizado': 0},
            'total_registros': 0
        }

def buscar_filtros():
    """Busca opções de filtro da API"""
    try:
        response = requests.get(f"{API_URL}/api/filtros", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao buscar filtros: {e}")
        return {'success': False, 'opcoes': {}}

# App Dash
app = dash.Dash(__name__)
app.title = "Dashboard de Monitoramento de Viagens"

# CSS melhorado (mesmo do código original)
app.index_string = '''<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}<style>
/* CSS mantido do original */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#fff5f0 0%,#ffe8dd 50%,#ffd4c4 100%);min-height:100vh;padding:20px}
#react-entry-point{max-width:1600px;margin:0 auto}

/* Header com gradiente laranja */
.title-container{
    background:linear-gradient(135deg,#FF6B35 0%,#FF8C42 50%,#FFB085 100%);
    padding:25px 30px;
    border-radius:0;
    margin-bottom:0;
    box-shadow:0 2px 10px rgba(255,107,53,.15);
    display:flex;
    justify-content:space-between;
    align-items:center;
    flex-wrap:wrap;
    gap:15px;
    width:100%;
    box-sizing:border-box;
}
.title-left{flex:1;}
.title-gradient{
    color:white;
    font-weight:700;
    font-size:2rem;
    margin:0 0 5px 0;
    text-shadow:2px 2px 4px rgba(0,0,0,.1);
}
.header-subtitle{color:rgba(255,255,255,.95);font-size:1rem;font-weight:400}

/* Botão secundário */
.export-btn-secondary{
    background:linear-gradient(135deg, #6c757d 0%, #495057 100%);
    color:white;
    border:none;
    padding:10px 20px;
    border-radius:8px;
    cursor:pointer;
    font-weight:600;
    font-size:0.9rem;
    transition:all 0.3s ease;
    display:flex;
    align-items:center;
    gap:6px;
}
.export-btn-secondary:hover{
    background:linear-gradient(135deg, #495057 0%, #343a40 100%);
    transform:translateY(-2px);
}

/* Filtros em linha compacta */
.filters-container{
    display:grid;
    grid-template-columns:repeat(4, 1fr);
    gap:15px;
    margin:20px;
    padding:20px;
    background:white;
    border-radius:12px;
    box-shadow:0 2px 10px rgba(0,0,0,.08);
    border:1px solid #ffe8dd;
    width:calc(100% - 40px);
    box-sizing:border-box;
}
.filter-item{display:flex;flex-direction:column}
.filter-item label{
    font-weight:600;
    color:#FF6B35;
    margin-bottom:8px;
    font-size:.9rem;
}
.dates-container{
    grid-column:1 / -1;
    display:grid;
    grid-template-columns:repeat(2, 1fr);
    gap:15px;
    margin-top:10px;
    padding-top:15px;
    border-top:2px solid #ffe8dd;
}

/* Container para gráfico e estatísticas */
.dashboard-top{
    display:grid;
    grid-template-columns:2fr 1fr;
    gap:20px;
    margin:0 20px 20px 20px;
    width:calc(100% - 40px);
    box-sizing:border-box;
}
.graph-card{
    background:white;
    border-radius:16px;
    padding:20px;
    box-shadow:0 4px 16px rgba(255,107,53,.1);
    border:2px solid #ffe8dd;
    transition:all .3s ease;
    position:relative;
    overflow:hidden;
}
.graph-card::before{
    content:'';
    position:absolute;
    top:0;
    left:0;
    right:0;
    height:4px;
    background:linear-gradient(90deg,#FF6B35 0%,#FF8C42 50%,#FFB085 100%);
}
.stats-card{
    background:white;
    border-radius:16px;
    padding:20px;
    box-shadow:0 4px 16px rgba(255,107,53,.1);
    border:2px solid #ffe8dd;
    display:flex;
    flex-direction:column;
    gap:15px;
}
.stat-item{
    background:linear-gradient(135deg, #fff5f0 0%, #ffe8dd 100%);
    padding:15px;
    border-radius:12px;
    border-left:4px solid #FF6B35;
}
.stat-value{
    font-size:2rem;
    font-weight:700;
    color:#FF6B35;
    margin:5px 0;
}
.stat-label{
    font-size:0.9rem;
    color:#666;
    font-weight:500;
}

/* Tabela */
.table-header{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:15px;
    flex-wrap:wrap;
    gap:10px;
}
h3{
    color:#FF6B35;
    font-size:1.5rem;
    margin:0;
    font-weight:700;
    position:relative;
    display:inline-block;
}
h3::after{
    content:'';
    position:absolute;
    bottom:-5px;
    left:0;
    width:60px;
    height:3px;
    background:linear-gradient(90deg,#FF6B35,#FF8C42);
    border-radius:2px;
}
.table-container{
    background:white;
    border-radius:12px;
    padding:20px;
    box-shadow:0 2px 10px rgba(0,0,0,.08);
    border:1px solid #ffe8dd;
    margin:0 20px 20px 20px;
    width:calc(100% - 40px);
    box-sizing:border-box;
}
.dash-table-container{
    border-radius:12px;
    overflow:hidden;
    border:2px solid #ffe8dd;
    max-height:600px;
    overflow-y:auto;
}
.dash-spreadsheet{font-size:.9rem}
.dash-table-header{
    background:linear-gradient(135deg,#FF6B35 0%,#FF8C42 100%)!important;
    color:white!important;
    font-weight:600!important;
    position:sticky;
    top:0;
    z-index:100;
}
.dash-table-header th{
    background:inherit!important;
    color:white!important;
    border-right:1px solid rgba(255,255,255,.15)!important;
    padding:16px!important;
    white-space:nowrap;
}
.dash-table-row{
    border-bottom:1px solid #ffe8dd;
    transition:background .2s ease;
}
.dash-table-row:hover{
    background:linear-gradient(135deg,#fff5f0 0%,#ffe8dd 100%)!important;
}
.dash-table-cell{padding:12px!important; white-space:nowrap;}

/* Dropdown styling */
.Select-control{
    border:2px solid #ffe8dd!important;
    border-radius:8px!important;
    transition:all .2s ease!important;
    background:white!important;
    min-height:42px!important;
}
.Select-control:hover{
    border-color:#FF8C42!important;
    box-shadow:0 0 0 3px rgba(255,107,53,.1)!important;
}
.Select-control.is-focused{
    border-color:#FF6B35!important;
    box-shadow:0 0 0 3px rgba(255,107,53,.15)!important;
}

/* Responsive */
@media (max-width:1200px){
    .filters-container{grid-template-columns:repeat(2, 1fr)}
    .dashboard-top{grid-template-columns:1fr}
}
@media (max-width:768px){
    .filters-container{grid-template-columns:1fr}
    .title-container{flex-direction:column;text-align:center}
    .title-left{text-align:center}
    .table-header{flex-direction:column;align-items:stretch}
}

/* Scrollbar laranja */
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-track{background:#ffe8dd;border-radius:4px}
::-webkit-scrollbar-thumb{background:linear-gradient(135deg,#FF6B35,#FF8C42);border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:linear-gradient(135deg,#FF8C42,#FFB085)}

/* SIDEBAR FIXA */
.sidebar{position:fixed;left:0;top:0;width:250px;height:100vh;background:linear-gradient(180deg,#FF6B35 0%,#F7931E 50%,#FF8C42 100%);box-shadow:4px 0 20px rgba(255,107,53,0.2);z-index:1000;display:flex;flex-direction:column;overflow-y:auto}
.sidebar-logo{color:white;font-size:1.5rem;font-weight:800;text-align:center;padding:25px 20px;background:rgba(0,0,0,0.1);border-bottom:1px solid rgba(255,255,255,0.15)}
.sidebar-item{padding:15px 20px;color:rgba(255,255,255,0.9);font-weight:500;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:12px;border-left:3px solid transparent}
.sidebar-item:hover{background:rgba(255,255,255,0.12);color:white;border-left-color:white;padding-left:25px}
.sidebar-item.active{background:rgba(255,255,255,0.2);color:white;border-left-color:white;font-weight:600}
.main-with-sidebar{margin-left:250px;width:calc(100% - 250px);padding:0;box-sizing:border-box}

body{margin:0;padding:0;overflow-x:hidden}
#react-entry-point{width:100%;max-width:100vw;overflow-x:hidden}

@media(max-width:768px){
.sidebar{width:70px}
.sidebar-logo{font-size:1.2rem;padding:20px 10px}
.sidebar-item{padding:14px;justify-content:center;font-size:1.2rem}
.sidebar-item span:last-child{display:none}
.main-with-sidebar{margin-left:70px;width:calc(100% - 70px)}
}
</style></head><body>{%app_entry%}{%config%}{%scripts%}{%renderer%}</body></html>'''

app.layout = html.Div([
    # Sidebar Fixa
    html.Div([
        html.Div("📊 Dashboard", className="sidebar-logo"),
        html.Div([html.Span("📈"), html.Span(" Previsão")], className="sidebar-item active"),
        html.Div([html.Span("📅"), html.Span(" Programado")], className="sidebar-item"),
        html.Div([html.Span("🚚"), html.Span(" Viagens")], className="sidebar-item"),
        html.Div([html.Span("📊"), html.Span(" Relatórios")], className="sidebar-item"),
        html.Div([html.Span("⚙️"), html.Span(" Configurações")], className="sidebar-item"),
    ], className="sidebar"),
    
    # Conteúdo Principal
    html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1("📊 Dashboard de Monitoramento de Viagens", className="title-gradient"),
            html.Div("Visualize e exporte dados de viagens em tempo real", className="header-subtitle"),
            html.Div(id="api-status", style={'color': 'rgba(255,255,255,.9)', 'fontSize': '0.85rem', 'marginTop': '5px'})
        ], className="title-left"),
    ], className="title-container"),
    
    dcc.Interval(id="interval", interval=20000, n_intervals=0),
    dcc.Download(id="download-csv"),
    
    # Filtros
    html.Div([
        html.Div([
            html.Label("ID (LT)"),
            dcc.Dropdown(id="filtro-id", multi=True, placeholder="Todos os LTs", options=[])
        ], className="filter-item"),
        
        html.Div([
            html.Label("Destino"),
            dcc.Dropdown(id="filtro-destino", multi=True, placeholder="Todos os destinos", options=[])
        ], className="filter-item"),
        
        html.Div([
            html.Label("Status"),
            dcc.Dropdown(id="filtro-status", multi=True, placeholder="Todos os status", options=[])
        ], className="filter-item"),
        
        html.Div([
            html.Label("Limpar Filtros"),
            html.Button(
                "🗑️ Limpar Tudo",
                id="btn-limpar",
                style={
                    'width': '100%',
                    'height': '42px',
                    'background': 'linear-gradient(135deg, #6c757d, #adb5bd)',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'fontWeight': '600'
                }
            )
        ], className="filter-item"),
        
        # Datas
        html.Div([
            html.Div([
                html.Label("Data Inicial"),
                dcc.DatePickerSingle(
                    id="filtro-data-inicial",
                    display_format="DD/MM/YYYY",
                    placeholder="DD/MM/AAAA",
                    style={'width': '100%'}
                )
            ], className="filter-item"),
            
            html.Div([
                html.Label("Data Final"),
                dcc.DatePickerSingle(
                    id="filtro-data-final",
                    display_format="DD/MM/YYYY",
                    placeholder="DD/MM/AAAA",
                    style={'width': '100%'}
                )
            ], className="filter-item")
        ], className="dates-container")
    ], className="filters-container"),
    
    # Gráfico e Estatísticas
    html.Div([
        html.Div([
            html.H3("Distribuição por Status", style={'marginBottom': '15px'}),
            dcc.Graph(id="grafico", style={'height': '400px'})
        ], className="graph-card"),
        
        html.Div([
            html.H3("Resumo Estatístico", style={'marginBottom': '15px'}),
            html.Div([
                html.Div(id="stat-total", className="stat-item"),
                html.Div(id="stat-transito", className="stat-item"),
                html.Div(id="stat-parado", className="stat-item"),
                html.Div(id="stat-finalizado", className="stat-item"),
            ])
        ], className="stats-card")
    ], className="dashboard-top"),
    
    # Tabela
    html.Div([
        html.Div([
            html.H3("📋 Dados Detalhados"),
            html.Div([
                html.Button(
                    [html.Span("📥"), " Exportar Tabela"],
                    id="btn-exportar-tabela",
                    className="export-btn-secondary"
                ),
                html.Div([
                    html.Span("Mostrando ", style={'color': '#666', 'marginLeft': '15px'}),
                    html.Span(id="contador-registros", style={'fontWeight': 'bold', 'color': '#FF6B35'}),
                    html.Span(" registros", style={'color': '#666'})
                ], style={'marginLeft': '15px', 'fontSize': '0.9rem'}),
                html.Div(id="ultima-atualizacao", style={
                    'marginLeft': '15px',
                    'fontSize': '0.85rem',
                    'color': '#888',
                    'fontStyle': 'italic'
                })
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'})
        ], className="table-header"),
        
        dash_table.DataTable(
            id="tabela",
            page_size=20,
            page_current=0,
            sort_action="native",
            filter_action="native",
            style_table={
                "borderRadius": "6px",
                "overflow": "hidden",
                "minHeight": "400px"
            },
            style_cell={
                "padding": "12px",
                "textAlign": "left",
                "fontFamily": "'Poppins', sans-serif",
                "fontSize": "13px",
                "whiteSpace": "normal",
                "height": "auto",
                "minWidth": "100px",
                "maxWidth": "200px",
                "overflow": "hidden",
                "textOverflow": "ellipsis"
            },
            style_header={
                "fontWeight": "700",
                "backgroundColor": "#FF6B35",
                "color": "white",
                "borderBottom": "2px solid #FF8C42",
                "fontSize": "14px",
                "padding": "15px",
                "textAlign": "left",
                "position": "sticky",
                "top": "0"
            },
            style_data={
                "border": "1px solid #ffe8dd"
            },
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "#FFF5F0"
                },
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "#FFE8DD !important",
                    "border": "2px solid #FF6B35"
                },
                {
                    "if": {"column_id": "Status_da_Viagem", "filter_query": "{Status_da_Viagem} = 'Parado'"},
                    "color": "#dc3545",
                    "fontWeight": "bold"
                },
                {
                    "if": {"column_id": "Status_da_Viagem", "filter_query": "{Status_da_Viagem} = 'Em trânsito'"},
                    "color": "#28a745",
                    "fontWeight": "bold"
                }
            ],
            style_filter={
                "backgroundColor": "#FFE8DD",
                "fontWeight": "600",
                "padding": "10px"
            },
            style_cell_conditional=[
                {
                    "if": {"column_id": "trip_number"},
                    "fontWeight": "600",
                    "color": "#FF6B35"
                }
            ],
            tooltip_data=[],
            tooltip_duration=None
        )
    ], className="table-container")
    ], className="main-with-sidebar")
])

# Callbacks
@app.callback(
    Output("filtro-id", "options"),
    Output("filtro-destino", "options"),
    Output("filtro-status", "options"),
    Output("api-status", "children"),
    Input("interval", "n_intervals")
)
def atualizar_filtros(_):
    """Atualiza opções de filtro da API"""
    try:
        response = buscar_filtros()
        
        if response.get('success'):
            opcoes = response.get('opcoes', {})
            
            # Verificar saúde da API
            health_response = requests.get(f"{API_URL}/api/health", timeout=5)
            if health_response.ok:
                status_text = "✅ Conectado ao servidor"
            else:
                status_text = "⚠️ Servidor lento"
            
            return (
                opcoes.get('ids', []),
                opcoes.get('destinos', []),
                opcoes.get('status', []),
                status_text
            )
        else:
            return [], [], [], "❌ Erro ao carregar filtros"
            
    except Exception as e:
        print(f"Erro ao atualizar filtros: {e}")
        return [], [], [], "❌ Servidor offline"

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
    """Limpa todos os filtros"""
    if n_clicks:
        return None, None, None, None, None
    return dash.no_update

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
    """Atualiza todo o dashboard com dados da API"""
    # Preparar filtros
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
    
    # Buscar dados da API
    response = buscar_dados(filters)
    
    if not response.get('success'):
        # Retornar dados vazios em caso de erro
        fig = criar_grafico_fallback()
        empty_columns = [{"name": "Erro", "id": "erro"}]
        empty_data = [{"erro": "Não foi possível carregar os dados. Verifique a conexão com o servidor."}]
        
        return (
            fig,
            empty_columns,
            empty_data,
            "0",
            f"Erro na atualização",
            [html.Div("Total de Viagens", className="stat-label"), html.Div("0", className="stat-value")],
            [html.Div("Em Trânsito", className="stat-label"), html.Div("0", className="stat-value", style={'color': '#28a745'})],
            [html.Div("Parado", className="stat-label"), html.Div("0", className="stat-value", style={'color': '#dc3545'})],
            [html.Div("Finalizado", className="stat-label"), html.Div("0", className="stat-value", style={'color': '#6c757d'})]
        )
    
    # Extrair dados da resposta
    dados = response.get('dados', [])
    colunas = response.get('colunas', [])
    estatisticas = response.get('estatisticas', {})
    total_registros = response.get('total_registros', 0)
    timestamp = response.get('timestamp', datetime.now().isoformat())
    
    # Converter timestamp para formato legível
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        ultima_atualizacao = f"Última atualização: {dt.strftime('%H:%M:%S')}"
    except:
        ultima_atualizacao = f"Atualizado há {n_intervals * 30} segundos"
    
    # Criar DataFrame para gráfico
    if dados and len(dados) > 0:
        df = pd.DataFrame(dados)
        fig = criar_grafico(df)
    else:
        fig = criar_grafico_fallback()
    
    # Preparar colunas para tabela
    columns = [{"name": col, "id": col} for col in colunas] if colunas else []
    
    # Componentes de estatísticas
    stat_total = [
        html.Div("Total de Viagens", className="stat-label"),
        html.Div(f"{estatisticas.get('total', 0)}", className="stat-value")
    ]
    
    stat_transito = [
        html.Div("Em Trânsito", className="stat-label"),
        html.Div(f"{estatisticas.get('transito', 0)}", className="stat-value", style={'color': '#28a745'})
    ]
    
    stat_parado = [
        html.Div("Parado", className="stat-label"),
        html.Div(f"{estatisticas.get('parado', 0)}", className="stat-value", style={'color': '#dc3545'})
    ]
    
    stat_finalizado = [
        html.Div("Finalizado", className="stat-label"),
        html.Div(f"{estatisticas.get('finalizado', 0)}", className="stat-value", style={'color': '#6c757d'})
    ]
    
    return (
        fig,
        columns,
        dados,
        str(total_registros),
        ultima_atualizacao,
        stat_total,
        stat_transito,
        stat_parado,
        stat_finalizado
    )

def criar_grafico(df):
    """Cria gráfico de barras a partir do DataFrame"""
    if df.empty or 'Status_da_Viagem' not in df.columns:
        return criar_grafico_fallback()
    
    # Contar status
    status_counts = df['Status_da_Viagem'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Quantidade']
    
    # Criar gráfico
    fig = px.bar(
        status_counts,
        x='Status',
        y='Quantidade',
        title='',
        color='Status',
        color_discrete_map=CORES_STATUS,
        text='Quantidade'
    )
    
    fig.update_traces(
        textposition='outside',
        textfont=dict(size=12, color="#333"),
        marker=dict(line=dict(width=1, color='white'))
    )
    
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            title="Status",
            showgrid=False,
            tickangle=0
        ),
        yaxis=dict(
            title="Quantidade",
            showgrid=True,
            gridcolor='#ffe8dd'
        ),
        legend=dict(
            title="Status da Viagem",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=40, b=40),
        hovermode="x unified"
    )
    
    return fig

def criar_grafico_fallback():
    """Cria gráfico fallback quando não há dados"""
    fig = go.Figure()
    fig.add_annotation(
        text="Aguardando dados...",
        showarrow=False,
        font=dict(size=16, color="#666")
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False)
    )
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
    """Exporta dados via API"""
    if not n_clicks:
        return dash.no_update
    
    try:
        # Preparar filtros
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
        
        # Fazer requisição para API de exportação
        response = requests.get(f"{API_URL}/api/exportar", params=params, timeout=30)
        response.raise_for_status()
        
        # Obter nome do arquivo do header
        content_disposition = response.headers.get('Content-Disposition', '')
        filename = 'dados_exportados.csv'
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        
        # Retornar conteúdo para download
        return dcc.send_bytes(response.content, filename)
        
    except Exception as e:
        print(f"Erro ao exportar: {e}")
        # Fallback: criar arquivo vazio
        return dcc.send_string("Erro ao exportar dados", "erro_exportacao.txt")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 DASHBOARD INICIADO COM SUCESSO!")
    print("="*70)
    print("\n📊 Acesse o dashboard em: http://127.0.0.1:8051")
    print("🔗 Ou use: http://localhost:8051")
    print("\n⚙️  API backend rodando em: http://localhost:8050")
    print("\n💡 Pressione CTRL+C para parar o servidor")
    print("="*70 + "\n")
    app.run(debug=False, port=8051, host='127.0.0.1', use_reloader=False)