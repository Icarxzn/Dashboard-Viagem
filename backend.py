import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import time
from datetime import datetime, timedelta
import logging
import json
import os
from dotenv import load_dotenv
from functools import wraps
import threading
from typing import Optional, Dict, Any
import hashlib

# Carregar variáveis de ambiente
load_dotenv()

print("="*70)
print("🚀 INICIANDO BACKEND DO DASHBOARD - VERSÃO PROFISSIONAL")
print("="*70)

# ============================================
# CONFIGURAÇÕES
# ============================================
PLANILHA_ID = os.getenv("PLANILHA_ID", "1BKB3rsrZFcHxRt0LkTABtSBlqv7VWU6TwmkbwX95TLI")
NOME_ABA = "Base Principal"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Cache e Performance
CACHE_DURATION = 30  # segundos
CACHE_AUTO_REFRESH = True  # Auto-refresh em background
CACHE_AUTO_REFRESH_INTERVAL = 60  # segundos

# Retry Logic
MAX_RETRIES = 3
RETRY_DELAY = 2  # segundos

# Colunas
COLUNAS_TABELA = [
    "trip_number", 
    "Status_da_Viagem", 
    "ETA Planejado", 
    "Ultima localização", 
    "Previsão de chegada", 
    "Ocorrencia"
]

CORES_STATUS = {
    "Parado": "#dc3545",
    "Em trânsito": "#28a745",
    "Em transito": "#28a745",
    "Finalizado": "#6c757d",
    "Cancelado": "#ffc107"
}

# ============================================
# LOGGING PROFISSIONAL
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================
# CACHE INTELIGENTE
# ============================================
class SmartCache:
    """Sistema de cache inteligente com múltiplas camadas"""
    
    def __init__(self):
        self.main_cache = {
            "df": None,
            "timestamp": None,
            "hits": 0,
            "misses": 0
        }
        self.filter_cache = {}  # Cache de filtros
        self.max_filter_cache_size = 100
        self.lock = threading.Lock()
    
    def get_main_data(self) -> Optional[pd.DataFrame]:
        """Obtém dados principais do cache"""
        with self.lock:
            if self.main_cache["df"] is not None and self.main_cache["timestamp"] is not None:
                age = time.time() - self.main_cache["timestamp"]
                if age < CACHE_DURATION:
                    self.main_cache["hits"] += 1
                    logger.info(f"✅ Cache HIT - Idade: {age:.1f}s | Taxa: {self.get_hit_rate():.1%}")
                    return self.main_cache["df"]
            
            self.main_cache["misses"] += 1
            logger.info(f"❌ Cache MISS | Taxa: {self.get_hit_rate():.1%}")
            return None
    
    def set_main_data(self, df: pd.DataFrame):
        """Armazena dados principais no cache"""
        with self.lock:
            self.main_cache["df"] = df
            self.main_cache["timestamp"] = time.time()
            logger.info(f"💾 Cache atualizado - {len(df)} registros")
    
    def get_filtered_data(self, filter_key: str) -> Optional[pd.DataFrame]:
        """Obtém dados filtrados do cache"""
        with self.lock:
            if filter_key in self.filter_cache:
                cached = self.filter_cache[filter_key]
                age = time.time() - cached["timestamp"]
                if age < CACHE_DURATION:
                    return cached["df"]
                else:
                    del self.filter_cache[filter_key]
            return None
    
    def set_filtered_data(self, filter_key: str, df: pd.DataFrame):
        """Armazena dados filtrados no cache"""
        with self.lock:
            # Limitar tamanho do cache de filtros
            if len(self.filter_cache) >= self.max_filter_cache_size:
                # Remover o mais antigo
                oldest_key = min(self.filter_cache.keys(), 
                               key=lambda k: self.filter_cache[k]["timestamp"])
                del self.filter_cache[oldest_key]
            
            self.filter_cache[filter_key] = {
                "df": df,
                "timestamp": time.time()
            }
    
    def get_hit_rate(self) -> float:
        """Calcula taxa de acerto do cache"""
        total = self.main_cache["hits"] + self.main_cache["misses"]
        return self.main_cache["hits"] / total if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache"""
        with self.lock:
            age = time.time() - self.main_cache["timestamp"] if self.main_cache["timestamp"] else None
            return {
                "main_cache_age": age,
                "main_cache_size": len(self.main_cache["df"]) if self.main_cache["df"] is not None else 0,
                "filter_cache_count": len(self.filter_cache),
                "hit_rate": self.get_hit_rate(),
                "total_hits": self.main_cache["hits"],
                "total_misses": self.main_cache["misses"]
            }
    
    def clear(self):
        """Limpa todo o cache"""
        with self.lock:
            self.main_cache = {
                "df": None,
                "timestamp": None,
                "hits": self.main_cache["hits"],
                "misses": self.main_cache["misses"]
            }
            self.filter_cache.clear()
            logger.info("🗑️  Cache limpo")

# ============================================
# GERENCIADOR DE DADOS
# ============================================
class DataManager:
    """Gerencia o carregamento e processamento dos dados"""
    
    def __init__(self):
        self.creds = None
        self.gc = None
        self.cache = SmartCache()
        self.last_load_time = None
        self.auto_refresh_thread = None
        self.is_running = True
        
    def _autenticar(self):
        """Autentica com Google Sheets com retry"""
        for attempt in range(MAX_RETRIES):
            try:
                # Tentar usar variável de ambiente primeiro
                google_creds_json = os.getenv("GOOGLE_CREDENTIALS")
                
                if google_creds_json:
                    creds_dict = json.loads(google_creds_json)
                    self.creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
                    logger.info("🔐 Autenticação via variável de ambiente")
                else:
                    self.creds = Credentials.from_service_account_file("account.json", scopes=SCOPES)
                    logger.info("🔐 Autenticação via arquivo account.json")
                
                self.gc = gspread.authorize(self.creds)
                logger.info("✅ Autenticação Google Sheets realizada com sucesso")
                return
                
            except Exception as e:
                logger.warning(f"⚠️  Tentativa {attempt + 1}/{MAX_RETRIES} falhou: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("❌ Falha na autenticação após todas as tentativas")
                    raise
    
    def carregar_dados(self, force_reload: bool = False) -> pd.DataFrame:
        """Carrega dados com cache inteligente"""
        # Verificar cache primeiro
        if not force_reload:
            cached_df = self.cache.get_main_data()
            if cached_df is not None:
                return cached_df
        
        logger.info("📡 Carregando dados do Google Sheets...")
        start_time = time.time()
        
        # Carregar novos dados com retry
        for attempt in range(MAX_RETRIES):
            try:
                if not self.gc:
                    self._autenticar()
                
                sheet = self.gc.open_by_key(PLANILHA_ID).worksheet(NOME_ABA)
                all_values = sheet.get_all_values()
                
                if not all_values or len(all_values) < 2:
                    logger.warning("⚠️  Planilha vazia ou sem dados")
                    return pd.DataFrame()
                
                # Criar DataFrame
                df = pd.DataFrame(all_values[1:], columns=all_values[0])
                df = df.dropna(how='all')
                
                # Processamento de dados
                df = self._processar_dados(df)
                
                # Atualizar cache
                self.cache.set_main_data(df)
                self.last_load_time = time.time()
                
                elapsed = time.time() - start_time
                logger.info(f"✅ Dados carregados: {len(df)} registros em {elapsed:.2f}s")
                
                return df
                
            except Exception as e:
                logger.warning(f"⚠️  Tentativa {attempt + 1}/{MAX_RETRIES} falhou: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    # Reautenticar na próxima tentativa
                    self.gc = None
                else:
                    logger.error("❌ Falha ao carregar dados após todas as tentativas")
                    # Retornar cache antigo se disponível
                    cached_df = self.cache.main_cache["df"]
                    if cached_df is not None:
                        logger.warning("⚠️  Retornando dados do cache devido a erro")
                        return cached_df
                    return pd.DataFrame()
    
    def _processar_dados(self, df: pd.DataFrame) -> pd.DataFrame:
        """Processa e limpa os dados"""
        # Converter colunas de data
        for col in df.columns:
            if 'data' in col.lower() or 'Data' in col:
                try:
                    df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
                except Exception as e:
                    logger.debug(f"Não foi possível converter coluna {col} para data: {e}")
        
        # Limpar espaços em branco
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        
        return df
    
    def filtrar_dados(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Filtra dados com cache de filtros"""
        # Criar chave de cache baseada nos filtros
        filter_key = self._get_filter_key(filters)
        
        # Verificar cache de filtros
        cached_df = self.cache.get_filtered_data(filter_key)
        if cached_df is not None:
            logger.info(f"✅ Usando dados filtrados do cache")
            return cached_df
        
        # Carregar dados base
        df = self.carregar_dados()
        
        if df.empty:
            return df
        
        # Aplicar filtros
        if filters:
            logger.info(f"🔍 Aplicando filtros: {filters}")
            
            # Filtro por IDs
            if 'ids' in filters and filters['ids'] and "trip_number" in df.columns:
                df = df[df["trip_number"].isin(filters['ids'])]
            
            # Filtro por destinos
            if 'destinos' in filters and filters['destinos'] and "destination_station_code" in df.columns:
                df = df[df["destination_station_code"].isin(filters['destinos'])]
            
            # Filtro por status
            if 'status' in filters and filters['status'] and "Status_da_Viagem" in df.columns:
                df = df[df["Status_da_Viagem"].isin(filters['status'])]
            
            # Filtro por data inicial
            if 'data_inicial' in filters and filters['data_inicial'] and "Data" in df.columns:
                try:
                    data_inicial = pd.to_datetime(filters['data_inicial'])
                    df = df[df["Data"] >= data_inicial]
                except Exception as e:
                    logger.warning(f"Erro ao filtrar por data inicial: {e}")
            
            # Filtro por data final
            if 'data_final' in filters and filters['data_final'] and "Data" in df.columns:
                try:
                    data_final = pd.to_datetime(filters['data_final'])
                    df = df[df["Data"] <= data_final]
                except Exception as e:
                    logger.warning(f"Erro ao filtrar por data final: {e}")
        
        # Armazenar no cache de filtros
        self.cache.set_filtered_data(filter_key, df)
        
        return df
    
    def _get_filter_key(self, filters: Optional[Dict]) -> str:
        """Gera chave única para combinação de filtros"""
        if not filters:
            return "no_filters"
        
        # Criar string JSON ordenada dos filtros
        filter_str = json.dumps(filters, sort_keys=True)
        # Gerar hash
        return hashlib.md5(filter_str.encode()).hexdigest()
    
    def obter_estatisticas(self, df: Optional[pd.DataFrame] = None) -> Dict[str, int]:
        """Calcula estatísticas dos dados"""
        if df is None:
            df = self.carregar_dados()
        
        if df.empty:
            return {
                'total': 0,
                'transito': 0,
                'parado': 0,
                'finalizado': 0,
                'cancelado': 0
            }
        
        total = len(df)
        
        if "Status_da_Viagem" in df.columns:
            status_counts = df["Status_da_Viagem"].value_counts()
            transito = status_counts.get("Em trânsito", 0) + status_counts.get("Em transito", 0)
            parado = status_counts.get("Parado", 0)
            finalizado = status_counts.get("Finalizado", 0)
            cancelado = status_counts.get("Cancelado", 0)
        else:
            transito = parado = finalizado = cancelado = 0
        
        return {
            'total': int(total),
            'transito': int(transito),
            'parado': int(parado),
            'finalizado': int(finalizado),
            'cancelado': int(cancelado)
        }
    
    def obter_opcoes_filtro(self) -> Dict[str, list]:
        """Obtém opções para dropdowns de filtro"""
        df = self.carregar_dados()
        
        def get_options(col):
            if col in df.columns:
                valores = df[col].dropna().unique()
                return [{"label": str(v), "value": v} for v in sorted(valores, key=lambda x: str(x))]
            return []
        
        return {
            'ids': get_options("trip_number"),
            'destinos': get_options("destination_station_code"),
            'status': get_options("Status_da_Viagem")
        }
    
    def start_auto_refresh(self):
        """Inicia thread de auto-refresh em background"""
        if not CACHE_AUTO_REFRESH:
            return
        
        def refresh_worker():
            logger.info("🔄 Auto-refresh iniciado")
            while self.is_running:
                try:
                    time.sleep(CACHE_AUTO_REFRESH_INTERVAL)
                    if self.is_running:
                        logger.info("🔄 Executando auto-refresh do cache...")
                        self.carregar_dados(force_reload=True)
                except Exception as e:
                    logger.error(f"❌ Erro no auto-refresh: {e}")
        
        self.auto_refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        self.auto_refresh_thread.start()
        logger.info("✅ Thread de auto-refresh iniciada")
    
    def stop_auto_refresh(self):
        """Para thread de auto-refresh"""
        self.is_running = False
        if self.auto_refresh_thread:
            logger.info("🛑 Parando auto-refresh...")

# ============================================
# INICIALIZAR GERENCIADOR
# ============================================
data_manager = DataManager()

# ============================================
# FLASK APP
# ============================================
app = Flask(__name__)
CORS(app)

# Middleware para logging de requisições
@app.before_request
def log_request():
    logger.info(f"📨 {request.method} {request.path} | IP: {request.remote_addr}")

@app.after_request
def log_response(response):
    logger.info(f"📤 {request.method} {request.path} | Status: {response.status_code}")
    return response

# ============================================
# ENDPOINTS
# ============================================

@app.route('/api/dados', methods=['GET'])
def get_dados():
    """Endpoint para obter dados filtrados"""
    start_time = time.time()
    
    try:
        # Obter parâmetros de filtro
        filters = {}
        
        if request.args.get('ids'):
            filters['ids'] = json.loads(request.args.get('ids'))
        
        if request.args.get('destinos'):
            filters['destinos'] = json.loads(request.args.get('destinos'))
        
        if request.args.get('status'):
            filters['status'] = json.loads(request.args.get('status'))
        
        if request.args.get('data_inicial'):
            filters['data_inicial'] = request.args.get('data_inicial')
        
        if request.args.get('data_final'):
            filters['data_final'] = request.args.get('data_final')
        
        # Filtrar dados
        df = data_manager.filtrar_dados(filters if filters else None)
        
        # Selecionar colunas para tabela
        colunas_existentes = [c for c in COLUNAS_TABELA if c in df.columns]
        df_tabela = df[colunas_existentes] if colunas_existentes else df
        
        # Obter estatísticas
        stats = data_manager.obter_estatisticas(df)
        
        # Tempo de processamento
        elapsed = time.time() - start_time
        
        # Preparar resposta
        response = {
            'success': True,
            'dados': df_tabela.to_dict('records'),
            'colunas': list(df_tabela.columns),
            'estatisticas': stats,
            'total_registros': len(df_tabela),
            'timestamp': datetime.now().isoformat(),
            'cache_age': int(time.time() - data_manager.cache.main_cache["timestamp"]) if data_manager.cache.main_cache["timestamp"] else 0,
            'processing_time': round(elapsed, 3)
        }
        
        logger.info(f"✅ Dados enviados: {len(response['dados'])} registros | Tempo: {elapsed:.3f}s")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Erro no endpoint /api/dados: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/filtros', methods=['GET'])
def get_filtros():
    """Endpoint para obter opções de filtro"""
    try:
        opcoes = data_manager.obter_opcoes_filtro()
        return jsonify({
            'success': True,
            'opcoes': opcoes,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Erro no endpoint /api/filtros: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/exportar', methods=['GET'])
def exportar_dados():
    """Endpoint para exportar dados"""
    try:
        # Obter parâmetros de filtro
        filters = {}
        
        if request.args.get('ids'):
            filters['ids'] = json.loads(request.args.get('ids'))
        
        if request.args.get('destinos'):
            filters['destinos'] = json.loads(request.args.get('destinos'))
        
        if request.args.get('status'):
            filters['status'] = json.loads(request.args.get('status'))
        
        if request.args.get('data_inicial'):
            filters['data_inicial'] = request.args.get('data_inicial')
        
        if request.args.get('data_final'):
            filters['data_final'] = request.args.get('data_final')
        
        # Filtrar dados
        df = data_manager.filtrar_dados(filters if filters else None)
        
        # Converter para CSV com encoding UTF-8
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        
        # Criar nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"dados_viagens_{timestamp}.csv"
        
        logger.info(f"📥 Exportando {len(df)} registros para {filename}")
        
        # Retornar como arquivo
        response = Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Erro no endpoint /api/exportar: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde"""
    cache_stats = data_manager.cache.get_stats()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - app_start_time if 'app_start_time' in globals() else 0,
        'cache': cache_stats,
        'last_load': data_manager.last_load_time
    })

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Endpoint de métricas do sistema"""
    cache_stats = data_manager.cache.get_stats()
    
    df = data_manager.carregar_dados()
    
    return jsonify({
        'success': True,
        'metrics': {
            'total_records': len(df) if df is not None else 0,
            'cache_stats': cache_stats,
            'last_load_time': data_manager.last_load_time,
            'uptime_seconds': time.time() - app_start_time if 'app_start_time' in globals() else 0,
            'auto_refresh_enabled': CACHE_AUTO_REFRESH,
            'cache_duration': CACHE_DURATION
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Endpoint para limpar o cache manualmente"""
    try:
        data_manager.cache.clear()
        return jsonify({
            'success': True,
            'message': 'Cache limpo com sucesso',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Erro ao limpar cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/cache/refresh', methods=['POST'])
def refresh_cache():
    """Endpoint para forçar refresh do cache"""
    try:
        logger.info("🔄 Refresh manual do cache solicitado")
        df = data_manager.carregar_dados(force_reload=True)
        return jsonify({
            'success': True,
            'message': f'Cache atualizado com {len(df)} registros',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == '__main__':
    app_start_time = time.time()
    
    try:
        # Carregar dados inicialmente
        logger.info("📡 Carregando dados iniciais...")
        data_manager.carregar_dados()
        
        # Iniciar auto-refresh
        if CACHE_AUTO_REFRESH:
            data_manager.start_auto_refresh()
        
        print("\n" + "="*70)
        print("✅ BACKEND API INICIADO COM SUCESSO!")
        print("="*70)
        print(f"\n🔌 API rodando em: http://localhost:8050")
        print(f"🔌 Também disponível em: http://127.0.0.1:8050")
        print(f"\n📡 Endpoints disponíveis:")
        print(f"   • GET  /api/dados           - Obter dados filtrados")
        print(f"   • GET  /api/filtros         - Obter opções de filtro")
        print(f"   • GET  /api/exportar        - Exportar dados em CSV")
        print(f"   • GET  /api/health          - Verificar saúde da API")
        print(f"   • GET  /api/metrics         - Métricas do sistema")
        print(f"   • POST /api/cache/clear     - Limpar cache")
        print(f"   • POST /api/cache/refresh   - Atualizar cache")
        print(f"\n⚙️  Configurações:")
        print(f"   • Cache Duration: {CACHE_DURATION}s")
        print(f"   • Auto-refresh: {'Ativado' if CACHE_AUTO_REFRESH else 'Desativado'}")
        if CACHE_AUTO_REFRESH:
            print(f"   • Refresh Interval: {CACHE_AUTO_REFRESH_INTERVAL}s")
        print(f"   • Max Retries: {MAX_RETRIES}")
        print(f"\n💡 Pressione CTRL+C para parar o servidor")
        print("="*70 + "\n")
        
        # Iniciar servidor
        app.run(debug=False, port=8050, host='127.0.0.1', use_reloader=False)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Servidor interrompido pelo usuário")
        data_manager.stop_auto_refresh()
    except Exception as e:
        logger.error(f"❌ Erro fatal ao iniciar servidor: {e}", exc_info=True)
    finally:
        data_manager.stop_auto_refresh()
        logger.info("👋 Servidor encerrado")