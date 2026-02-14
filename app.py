# 🚚 Dashboard de Monitoramento de Viagens

Dashboard profissional para monitoramento de viagens em tempo real com integração ao Google Sheets.

## 🌟 Características

### Backend (API)
- ✅ **Cache Inteligente** com duas camadas (principal + filtros)
- ✅ **Auto-refresh** automático em background
- ✅ **Retry Logic** com até 3 tentativas
- ✅ **Métricas em tempo real** (hit rate, performance)
- ✅ **API RESTful** completa
- ✅ **Thread-safe** para múltiplas requisições

### Frontend (Dashboard)
- ✅ **Design Responsivo** 100% (desktop, tablet, mobile)
- ✅ **Interface Moderna** com gradientes e animações
- ✅ **Filtros Avançados** (ID, destino, status, datas)
- ✅ **Gráficos Interativos** com Plotly
- ✅ **Exportação para CSV**
- ✅ **Atualização automática** a cada 20 segundos

## 📋 Pré-requisitos

- Python 3.8+
- Conta Google Cloud com API Sheets habilitada
- Credenciais de service account do Google

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone <seu-repositorio>
cd dashboard-viagens
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as credenciais

**Opção A: Variável de ambiente (recomendado)**
```bash
export GOOGLE_CREDENTIALS='{"type": "service_account", ...}'
export PLANILHA_ID="sua_planilha_id"
```

**Opção B: Arquivo account.json**
- Coloque o arquivo `account.json` na raiz do projeto
- Crie arquivo `.env`:
```
PLANILHA_ID=sua_planilha_id
```

## 🎯 Como Usar

### Execução Completa (Recomendado)
```bash
python app_improved.py
```

Isso iniciará:
- Backend API na porta 8050
- Frontend Dashboard na porta 8051

Acesse: **http://localhost:8051**

### Execução Separada

**Backend apenas:**
```bash
python backend_improved.py
```

**Frontend apenas:**
```bash
python frontend_improved.py
```

## 🔌 API Endpoints

### Dados
- `GET /api/dados` - Obter dados filtrados
- `GET /api/filtros` - Opções de filtro disponíveis
- `GET /api/exportar` - Exportar dados em CSV

### Sistema
- `GET /api/health` - Status da API
- `GET /api/metrics` - Métricas de performance
- `POST /api/cache/clear` - Limpar cache
- `POST /api/cache/refresh` - Atualizar cache

### Exemplos de Uso

**Obter dados:**
```bash
curl http://localhost:8050/api/dados
```

**Filtrar por status:**
```bash
curl "http://localhost:8050/api/dados?status=[\"Em trânsito\"]"
```

**Ver métricas:**
```bash
curl http://localhost:8050/api/metrics
```

**Atualizar cache:**
```bash
curl -X POST http://localhost:8050/api/cache/refresh
```

## ⚙️ Configurações

### Backend (`backend_improved.py`)
```python
CACHE_DURATION = 30              # Duração do cache (segundos)
CACHE_AUTO_REFRESH = True        # Auto-refresh ativo
CACHE_AUTO_REFRESH_INTERVAL = 60 # Intervalo de refresh (segundos)
MAX_RETRIES = 3                  # Tentativas em caso de falha
RETRY_DELAY = 2                  # Delay entre tentativas (segundos)
```

### Frontend (`frontend_improved.py`)
```python
API_URL = "http://localhost:8050"  # URL da API
CORES_STATUS = {...}               # Cores dos status
```

## 📊 Estrutura do Projeto

```
dashboard-viagens/
├── app_improved.py          # Aplicação principal (integrada)
├── backend_improved.py      # Backend API
├── frontend_improved.py     # Frontend Dashboard
├── requirements.txt         # Dependências Python
├── .env                     # Variáveis de ambiente
├── account.json            # Credenciais Google (opcional)
└── README.md               # Este arquivo
```

## 🎨 Responsividade

O dashboard é totalmente responsivo:

| Dispositivo | Resolução | Layout |
|-------------|-----------|--------|
| Desktop 4K | 3840px | 4 colunas de filtros, sidebar 260px |
| Laptop | 1920px | 4 colunas de filtros |
| Tablet | 768-1200px | 2 colunas de filtros |
| Mobile | 480-768px | 1 coluna, sidebar compacta (70px) |
| Mobile Small | <480px | 1 coluna, sidebar mini (60px) |

## 📈 Performance

### Métricas Típicas
- **Cache Hit Rate**: ~85%
- **Tempo de Resposta** (com cache): ~0.1s
- **Tempo de Resposta** (sem cache): ~2s
- **Requisições ao Google Sheets**: Mínimas (graças ao cache)

### Otimizações
- Cache inteligente de dois níveis
- Auto-refresh em background (não bloqueia requisições)
- Retry automático em falhas
- Thread-safe para concorrência

## 🔒 Segurança

- ✅ CORS configurado adequadamente
- ✅ Credenciais em variáveis de ambiente
- ✅ Validação de parâmetros de entrada
- ✅ Tratamento de erros robusto
- ✅ Logging de todas as operações

## 🐛 Troubleshooting

### Backend não inicia
```bash
# Verificar credenciais
echo $GOOGLE_CREDENTIALS

# Verificar arquivo
ls -la account.json

# Ver logs detalhados
python backend_improved.py
```

### Cache não atualiza
```bash
# Limpar cache manualmente
curl -X POST http://localhost:8050/api/cache/clear

# Forçar refresh
curl -X POST http://localhost:8050/api/cache/refresh
```

### Frontend não conecta ao backend
```bash
# Verificar se backend está rodando
curl http://localhost:8050/api/health

# Verificar firewall/porta
netstat -an | grep 8050
```

## 📝 Logs

Os logs incluem:
- ✅ Timestamp de todas as operações
- ✅ Nível de severidade (INFO, WARNING, ERROR)
- ✅ Métricas de cache (hit/miss rate)
- ✅ Tempo de processamento
- ✅ Erros com stack trace

Exemplo:
```
2025-02-14 10:30:45 | INFO     | ✅ Cache HIT - Idade: 5.2s | Taxa: 85.3%
2025-02-14 10:30:46 | INFO     | 📨 GET /api/dados | IP: 127.0.0.1
2025-02-14 10:30:46 | INFO     | ✅ Dados enviados: 150 registros | Tempo: 0.123s
```

## 🚦 Variáveis de Ambiente

```bash
# Obrigatórias
GOOGLE_CREDENTIALS='...'     # Credenciais do Google
PLANILHA_ID='...'           # ID da planilha

# Opcionais
PORT=8051                   # Porta do frontend (padrão: 8051)
```

## 🆘 Suporte

Em caso de problemas:

1. Verifique os logs no console
2. Teste os endpoints da API diretamente
3. Verifique as métricas em `/api/metrics`
4. Limpe o cache se necessário

## 📄 Licença

[Sua licença aqui]

## 👥 Contribuidores

[Seus contribuidores aqui]

---

**Desenvolvido para monitoramento eficiente de viagens**