# Dashboard-Viagem

# 📊 Dashboard de Monitoramento de Viagens

Dashboard interativo para visualização e análise de dados de viagens em tempo real.

## 🚀 Como Rodar Localmente

### 1. Instale as dependências:
```bash
pip install -r requirements.txt
```

### 2. Configure as variáveis de ambiente:
Copie o arquivo `.env.example` para `.env` e preencha com suas credenciais:
```bash
cp .env.example .env
```

### 3. Rode o backend (Terminal 1):
```bash
python backend.py
```

### 4. Rode o frontend (Terminal 2):
```bash
python frontend.py
```

### 5. Acesse no navegador:
```
http://127.0.0.1:8051
```

## 📦 Deploy (Render, Railway, etc.)

### Variáveis de Ambiente Necessárias:
- `PLANILHA_ID` - ID da planilha do Google Sheets
- `GOOGLE_CREDENTIALS` - JSON completo do account.json (em uma linha)

### Exemplo de GOOGLE_CREDENTIALS:
```json
{"type":"service_account","project_id":"seu-projeto",...}
```

## 🔒 Segurança

- ❌ Nunca commite o arquivo `account.json`
- ❌ Nunca commite o arquivo `.env`
- ✅ Use variáveis de ambiente em produção
- ✅ O `.gitignore` já está configurado

## 📁 Estrutura do Projeto

```
dashboard-viagens/
├── backend.py          # API Flask
├── frontend.py         # Dashboard Dash
├── requirements.txt    # Dependências Python
├── .env               # Variáveis de ambiente (local)
├── .env.example       # Exemplo de configuração
├── .gitignore         # Arquivos ignorados pelo Git
└── README.md          # Este arquivo
```

## 🛠️ Tecnologias

- **Backend:** Flask + Google Sheets API
- **Frontend:** Dash + Plotly
- **Dados:** Google Sheets
