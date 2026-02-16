from dash import html, dcc, dash_table

def pagina_previsao():
    """Renderiza a página de Previsão com filtros e dashboard"""
    return html.Div([
        html.Div([html.Div([html.Label("ID (LT)"), dcc.Dropdown(id="filtro-id", multi=True, placeholder="Todos os LTs", options=[])], className="filter-item"),
        html.Div([html.Label("Destino"), dcc.Dropdown(id="filtro-destino", multi=True, placeholder="Todos os destinos", options=[])], className="filter-item"),
        html.Div([html.Label("Status"), dcc.Dropdown(id="filtro-status", multi=True, placeholder="Todos os status", options=[])], className="filter-item"),
        html.Div([html.Label("Limpar Filtros"), html.Button("🗑️ Limpar Tudo", id="btn-limpar", style={'width': '100%', 'height': '42px', 'background': 'linear-gradient(135deg, #6c757d, #adb5bd)', 'color': 'white', 'border': 'none', 'borderRadius': '8px', 'cursor': 'pointer', 'fontWeight': '600'})], className="filter-item"),
        html.Div([
            html.Div([html.Label("Data Inicial"), dcc.DatePickerSingle(id="filtro-data-inicial", display_format="DD/MM/YYYY", placeholder="DD/MM/AAAA", style={'width': '100%'})], className="filter-item"),
            html.Div([html.Label("Data Final"), dcc.DatePickerSingle(id="filtro-data-final", display_format="DD/MM/YYYY", placeholder="DD/MM/AAAA", style={'width': '100%'})], className="filter-item")
        ], className="dates-container")
    ], className="filters-container"),
    
    html.Div([
        html.Div([html.H3("Distribuição por Status", style={'marginBottom': '15px'}), dcc.Graph(id="grafico", style={'height': '400px'})], className="graph-card"),
        html.Div([html.H3("Resumo Estatístico", style={'marginBottom': '15px'}), html.Div([html.Div(id="stat-total", className="stat-item"), html.Div(id="stat-transito", className="stat-item"), html.Div(id="stat-parado", className="stat-item"), html.Div(id="stat-finalizado", className="stat-item")])], className="stats-card")
    ], className="dashboard-top"),
    
    html.Div([
        html.Div([
            html.H3("📋 Dados Detalhados"),
            html.Div([
                html.Button([html.Span("📥"), " Exportar Tabela"], id="btn-exportar-tabela", className="export-btn-secondary"),
                html.Div([html.Span("Mostrando ", style={'color': '#666', 'marginLeft': '15px'}), html.Span(id="contador-registros", style={'fontWeight': 'bold', 'color': '#FF6B35'}), html.Span(" registros", style={'color': '#666'})], style={'marginLeft': '15px', 'fontSize': '0.9rem'}),
                html.Div(id="ultima-atualizacao", style={'marginLeft': '15px', 'fontSize': '0.85rem', 'color': '#888', 'fontStyle': 'italic'})
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'})
        ], className="table-header"),
        
        dash_table.DataTable(
            id="tabela",
            page_size=20,
            page_current=0,
            sort_action="native",
            style_table={"borderRadius": "6px", "overflow": "hidden", "minHeight": "400px"},
            style_cell={"padding": "12px", "textAlign": "left", "fontFamily": "'Poppins', sans-serif", "fontSize": "13px", "whiteSpace": "normal", "height": "auto", "minWidth": "100px", "maxWidth": "200px", "overflow": "hidden", "textOverflow": "ellipsis"},
            style_header={"fontWeight": "700", "backgroundColor": "#FF6B35", "color": "white", "borderBottom": "2px solid #FF8C42", "fontSize": "14px", "padding": "15px", "textAlign": "left", "position": "sticky", "top": "0"},
            style_data={"border": "1px solid #ffe8dd"},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#FFF5F0"},
                {"if": {"state": "selected"}, "backgroundColor": "#FFE8DD !important", "border": "2px solid #FF6B35"},
                {"if": {"column_id": "Status_da_Viagem", "filter_query": "{Status_da_Viagem} = 'Parado'"}, "color": "#dc3545", "fontWeight": "bold"},
                {"if": {"column_id": "Status_da_Viagem", "filter_query": "{Status_da_Viagem} = 'Em trânsito'"}, "color": "#28a745", "fontWeight": "bold"}
            ],
            style_cell_conditional=[{"if": {"column_id": "trip_number"}, "fontWeight": "600", "color": "#FF6B35"}],
            tooltip_data=[],
            tooltip_duration=None
        )
    ], className="table-container")
    ])

def pagina_programado():
    """Renderiza a página de Viagens Programadas"""
    return html.Div([
        html.Div([
            html.H3("📅 Viagens Programadas", style={'color': '#FF6B35', 'marginBottom': '20px'}),
            html.Div([
                html.Div([
                    html.H4("Total Programado", style={'color': '#FF6B35', 'marginBottom': '10px'}),
                    html.Div("245", style={'fontSize': '2.5rem', 'fontWeight': 'bold', 'color': '#FF6B35'})
                ], className="stat-item", style={'padding': '20px'}),
                html.Div([
                    html.H4("Próximas 24h", style={'color': '#FF6B35', 'marginBottom': '10px'}),
                    html.Div("32", style={'fontSize': '2.5rem', 'fontWeight': 'bold', 'color': '#28a745'})
                ], className="stat-item", style={'padding': '20px'}),
                html.Div([
                    html.H4("Próximos 7 dias", style={'color': '#FF6B35', 'marginBottom': '10px'}),
                    html.Div("89", style={'fontSize': '2.5rem', 'fontWeight': 'bold', 'color': '#FF8C42'})
                ], className="stat-item", style={'padding': '20px'}),
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '20px', 'marginBottom': '30px'}),
            
            html.Div([
                html.H4("Próximas Viagens", style={'color': '#FF6B35', 'marginBottom': '15px'}),
                html.Div([
                    html.Div([
                        html.Div("LT-001", style={'fontWeight': 'bold', 'color': '#FF6B35', 'marginBottom': '5px'}),
                        html.Div("São Paulo → Rio de Janeiro", style={'color': '#666', 'fontSize': '0.9rem', 'marginBottom': '5px'}),
                        html.Div("Saída: 17/02/2026 08:00", style={'color': '#888', 'fontSize': '0.85rem'})
                    ], style={'padding': '15px', 'background': '#FFF5F0', 'borderRadius': '8px', 'borderLeft': '4px solid #FF6B35', 'marginBottom': '10px'}),
                    html.Div([
                        html.Div("LT-002", style={'fontWeight': 'bold', 'color': '#FF6B35', 'marginBottom': '5px'}),
                        html.Div("Belo Horizonte → Brasília", style={'color': '#666', 'fontSize': '0.9rem', 'marginBottom': '5px'}),
                        html.Div("Saída: 17/02/2026 10:30", style={'color': '#888', 'fontSize': '0.85rem'})
                    ], style={'padding': '15px', 'background': '#FFF5F0', 'borderRadius': '8px', 'borderLeft': '4px solid #FF6B35', 'marginBottom': '10px'}),
                    html.Div([
                        html.Div("LT-003", style={'fontWeight': 'bold', 'color': '#FF6B35', 'marginBottom': '5px'}),
                        html.Div("Curitiba → Salvador", style={'color': '#666', 'fontSize': '0.9rem', 'marginBottom': '5px'}),
                        html.Div("Saída: 17/02/2026 14:00", style={'color': '#888', 'fontSize': '0.85rem'})
                    ], style={'padding': '15px', 'background': '#FFF5F0', 'borderRadius': '8px', 'borderLeft': '4px solid #FF6B35'})
                ], style={'background': 'white', 'padding': '20px', 'borderRadius': '12px', 'border': '1px solid #ffe8dd'})
            ], style={'marginTop': '20px'})
        ], style={'margin': '20px', 'padding': '20px', 'background': 'white', 'borderRadius': '12px', 'border': '1px solid #ffe8dd'})
    ])

def pagina_viagens():
    """Renderiza a página de Viagens"""
    return html.Div([html.Div([html.H3("🚚 Viagens", style={'color': '#FF6B35'}), html.Div("Conteúdo em construção", style={'padding': '40px', 'textAlign': 'center', 'color': '#999'})], style={'margin': '20px', 'padding': '20px', 'background': 'white', 'borderRadius': '12px', 'border': '1px solid #ffe8dd'})])

def pagina_relatorios():
    """Renderiza a página de Relatórios"""
    return html.Div([html.Div([html.H3("📈 Relatórios", style={'color': '#FF6B35'}), html.Div("Conteúdo em construção", style={'padding': '40px', 'textAlign': 'center', 'color': '#999'})], style={'margin': '20px', 'padding': '20px', 'background': 'white', 'borderRadius': '12px', 'border': '1px solid #ffe8dd'})])

def pagina_config():
    """Renderiza a página de Configurações"""
    return html.Div([html.Div([html.H3("⚙️ Configurações", style={'color': '#FF6B35'}), html.Div("Conteúdo em construção", style={'padding': '40px', 'textAlign': 'center', 'color': '#999'})], style={'margin': '20px', 'padding': '20px', 'background': 'white', 'borderRadius': '12px', 'border': '1px solid #ffe8dd'})])

def get_pagina(nome_pagina):
    """Retorna a página baseado no nome"""
    paginas = {
        "previsao": pagina_previsao,
        "programado": pagina_programado,
        "viagens": pagina_viagens,
        "relatorios": pagina_relatorios,
        "config": pagina_config
    }
    return paginas.get(nome_pagina, pagina_previsao)()
