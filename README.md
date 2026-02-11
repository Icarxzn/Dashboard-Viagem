# Dashboard-Viagem

# 📊 Dashboard de Monitoramento de Viagens

Dashboard interativo para visualização e análise de dados de viagens em tempo real.

### Variáveis de Ambiente Necessárias:

- `PLANILHA_ID` - ID da planilha do Google Sheets
- `GOOGLE_CREDENTIALS` - JSON completo do account.json (em uma linha)

### Exemplo de GOOGLE_CREDENTIALS:

```json
{"type":"service_account","project_id":"seu-projeto",...}
```

## 📁 Estrutura do Projeto
```
dashboard-viagens/
├── backend.py          # API Flask
├── frontend.py         # Dashboard Dash
├── requirements.txt    # Dependências Python
├── .gitignore         # Arquivos ignorados pelo Git
└── README.md          # Este arquivo
```

## 🛠️ Tecnologias

- **Backend:** Flask + Google Sheets API
- **Frontend:** Dash + Plotly
- **Dados:** Google Sheets
