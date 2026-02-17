# ============================================================================
# BACKEND DO DASHBOARD - API Flask com Google Sheets
# ============================================================================
# Responsável por:
# - Autenticar com Google Sheets
# - Carregar e cachear dados (10,500 registros)
# - Fornecer endpoints para filtros, dados e exportação
# - Gerenciar cache com duração de 15 segundos

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import time
from datetime import datetime
import logging
import json
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente (PLANILHA_ID, GOOGLE_CREDENTIALS)
load_dotenv()

print("="*70)
print("INICIANDO BACKEND DO DASHBOARD")
print("="*70)

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================
PLANILHA_ID = os.getenv("PLANILHA_ID", "1BKB3rsrZFcHxRt0LkTABtSBlqv7VWU6TwmkbwX95TLI")
NOME_ABA = "Base Principal"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CACHE_DURATION = 15  # Cache expira a cada 15 segundos
COLUNAS_TABELA = ["trip_number", "Status Veiculo", "Status_da_Viagem", "ETA Planejado", "Ultima localização", "Previsão de chegada", "Ocorrencia"] #--------
CORES_STATUS = {
    "Parado": "#dc3545",
    "Em trânsito": "#28a745",
    "Em transito": "#28a745",
    "Finalizado": "#6c757d",
    "Cancelado": "#ffc107"
}

# Configurar logging para rastrear operações
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache global para armazenar dados e timestamp
dados_cache = {"df": None, "timestamp": None}


class DataManager:
    """
    Gerenciador de dados do Dashboard
    Responsável por:
    - Autenticar com Google Sheets
    - Carregar dados com cache
    - Filtrar dados por critérios
    - Calcular estatísticas
    - Fornecer opções para dropdowns
    """
    
    def __init__(self):
        """Inicializa o gerenciador com credenciais vazias"""
        self.creds = None
        self.gc = None
        
    def _autenticar(self):
        """
        Autentica com Google Sheets
        Tenta usar variável de ambiente primeiro, depois arquivo local
        """
        try:
            # Tentar usar variável de ambiente primeiro (para deploy)
            google_creds_json = os.getenv("GOOGLE_CREDENTIALS")
            
            if google_creds_json:
                # Usar credenciais da variável de ambiente
                creds_dict = json.loads(google_creds_json)
                self.creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
                logger.info("Autenticação via variável de ambiente")
            else:
                # Fallback para arquivo local - procurar no diretório correto
                account_path = os.path.join(os.path.dirname(__file__), "account.json")
                self.creds = Credentials.from_service_account_file(account_path, scopes=SCOPES)
                logger.info("Autenticação via arquivo account.json")
            
            self.gc = gspread.authorize(self.creds)
            logger.info("Autenticação Google Sheets realizada com sucesso")
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            raise
    
    def carregar_dados(self, force_reload=False):
        """
        Carrega dados da Google Sheets com cache
        
        Args:
            force_reload (bool): Se True, ignora cache e recarrega dados
            
        Returns:
            pd.DataFrame: DataFrame com os dados carregados
        """
        global dados_cache
        
        # Verificar se cache ainda é válido
        if not force_reload and dados_cache["df"] is not None and dados_cache["timestamp"] is not None:
            tempo_decorrido = time.time() - dados_cache["timestamp"]
            if tempo_decorrido < CACHE_DURATION:
                logger.info(f"Retornando dados do cache (idade: {int(tempo_decorrido)}s)")
                return dados_cache["df"]
        
        logger.info("Cache expirado ou forçando reload - carregando novos dados...")
        
        # Carregar novos dados
        try:
            if not self.gc:
                self._autenticar()
            
            # Buscar dados da planilha
            sheet = self.gc.open_by_key(PLANILHA_ID).worksheet(NOME_ABA)
            all_values = sheet.get_all_values()
            
            if not all_values or len(all_values) < 2:
                logger.warning("Planilha vazia ou sem dados")
                return pd.DataFrame()
            
            # Criar DataFrame a partir dos dados
            df = pd.DataFrame(all_values[1:], columns=all_values[0]).dropna(how='all')
            
            # Converter colunas de data para formato datetime
            for col in df.columns:
                if 'data' in col.lower() or 'Data' in col:
                    try:
                        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
                    except:
                        pass
            
            # Atualizar cache
            dados_cache["df"] = df
            dados_cache["timestamp"] = time.time()
            
            logger.info(f"Dados carregados: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            # Retornar cache antigo se disponível
            if dados_cache["df"] is not None:
                logger.warning("Retornando dados do cache devido a erro")
                return dados_cache["df"]
            return pd.DataFrame()
    
    def filtrar_dados(self, filters=None):
        """
        Filtra dados com base nos critérios fornecidos
        
        Args:
            filters (dict): Dicionário com filtros (ids, destinos, status, datas)
            
        Returns:
            pd.DataFrame: DataFrame filtrado
        """
        df = self.carregar_dados()
        
        if df.empty:
            return df
        
        if filters:
            # Filtro por IDs (LT numbers)
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
                df = df[df["Data"] >= pd.to_datetime(filters['data_inicial'])]
            
            # Filtro por data final
            if 'data_final' in filters and filters['data_final'] and "Data" in df.columns:
                df = df[df["Data"] <= pd.to_datetime(filters['data_final'])]
        
        return df
    
    def obter_estatisticas(self, df=None):
        """
        Calcula estatísticas dos dados (total, em trânsito, parado, etc)
        
        Args:
            df (pd.DataFrame): DataFrame para calcular estatísticas. Se None, carrega dados
            
        Returns:
            dict: Dicionário com estatísticas
        """
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
        
        # Contar por status
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
    
    def obter_opcoes_filtro(self):
        """
        Obtém opções únicas para cada filtro (para dropdowns)
        
        Returns:
            dict: Dicionário com opções para ids, destinos e status
        """
        df = self.carregar_dados()
        
        def get_options(col):
            """Helper para extrair opções de uma coluna"""
            if col in df.columns:
                valores = df[col].dropna().unique()
                return [{"label": str(v), "value": v} for v in sorted(valores, key=lambda x: str(x))]
            return []
        
        return {
            'ids': get_options("trip_number"),
            'destinos': get_options("destination_station_code"),
            'status': get_options("Status_da_Viagem")
        }

# ============================================================================
# INICIALIZAR GERENCIADOR DE DADOS
# ============================================================================
data_manager = DataManager()

# ============================================================================
# CRIAR APP FLASK E CONFIGURAR CORS
# ============================================================================
app = Flask(__name__)
CORS(app)  # Permitir CORS para frontend fazer requisições


# ============================================================================
# ENDPOINTS DA API
# ============================================================================

@app.route('/api/dados', methods=['GET'])
def get_dados():
    """
    Endpoint para obter dados filtrados
    
    Query Parameters:
        - ids: JSON array de IDs (LT numbers)
        - destinos: JSON array de destinos
        - status: JSON array de status
        - data_inicial: Data inicial (YYYY-MM-DD)
        - data_final: Data final (YYYY-MM-DD)
    
    Returns:
        JSON com dados, colunas, estatísticas e informações de cache
    """
    try:
        logger.info("=== Requisição recebida em /api/dados ===")
        
        # Obter parâmetros de filtro
        filters = {}
        
        # IDs
        ids = request.args.get('ids')
        if ids:
            filters['ids'] = json.loads(ids)
        
        # Destinos
        destinos = request.args.get('destinos')
        if destinos:
            filters['destinos'] = json.loads(destinos)
        
        # Status
        status = request.args.get('status')
        if status:
            filters['status'] = json.loads(status)
        
        # Datas
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        if data_inicial:
            filters['data_inicial'] = data_inicial
        if data_final:
            filters['data_final'] = data_final
        
        logger.info(f"Filtros aplicados: {filters}")
        
        # Filtrar dados
        df = data_manager.filtrar_dados(filters)
        logger.info(f"Dados filtrados: {len(df)} registros")
        
        # Selecionar colunas para tabela
        colunas_existentes = [c for c in COLUNAS_TABELA if c in df.columns]
        df_tabela = df[colunas_existentes] if colunas_existentes else df
        
        # Obter estatísticas
        stats = data_manager.obter_estatisticas(df)
        logger.info(f"Estatísticas calculadas: {stats}")
        
        # Preparar resposta
        response = {
            'success': True,
            'dados': df_tabela.to_dict('records'),
            'colunas': list(df_tabela.columns),
            'estatisticas': stats,
            'total_registros': len(df_tabela),
            'timestamp': datetime.now().isoformat(),
            'cache_age': int(time.time() - dados_cache["timestamp"]) if dados_cache["timestamp"] else 0
        }
        
        logger.info(f"Resposta enviada: {len(response['dados'])} registros, cache age: {response['cache_age']}s")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Erro no endpoint /api/dados: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/filtros', methods=['GET'])
def get_filtros():
    """
    Endpoint para obter opções de filtro
    
    Returns:
        JSON com opções para ids, destinos e status
    """
    try:
        opcoes = data_manager.obter_opcoes_filtro()
        return jsonify({
            'success': True,
            'opcoes': opcoes
        })
    except Exception as e:
        logger.error(f"Erro no endpoint /api/filtros: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/exportar', methods=['GET'])
def exportar_dados():
    """
    Endpoint para exportar dados em CSV
    
    Query Parameters: (mesmos de /api/dados)
        - ids, destinos, status, data_inicial, data_final
    
    Returns:
        Arquivo CSV com os dados filtrados
    """
    try:
        # Obter parâmetros de filtro (mesmo que /api/dados)
        filters = {}
        
        # IDs
        ids = request.args.get('ids')
        if ids:
            filters['ids'] = json.loads(ids)
        
        # Destinos
        destinos = request.args.get('destinos')
        if destinos:
            filters['destinos'] = json.loads(destinos)
        
        # Status
        status = request.args.get('status')
        if status:
            filters['status'] = json.loads(status)
        
        # Datas
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        if data_inicial:
            filters['data_inicial'] = data_inicial
        if data_final:
            filters['data_final'] = data_final
        
        # Filtrar dados
        df = data_manager.filtrar_dados(filters)
        
        # Converter para CSV
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        
        # Criar nome do arquivo
        filename = f"dados_viagens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Retornar como arquivo
        response = Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erro no endpoint /api/exportar: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Endpoint de verificação de saúde da API
    
    Returns:
        JSON com status, timestamp e idade do cache
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cache_age': time.time() - dados_cache["timestamp"] if dados_cache["timestamp"] else None
    })

# ============================================================================
# INICIALIZAÇÃO DO SERVIDOR
# ============================================================================

if __name__ == '__main__':
    # Carregar dados inicialmente
    logger.info("Carregando dados iniciais...")
    data_manager.carregar_dados()
    
    print("\n" + "="*70)
    print("✅ BACKEND API INICIADO COM SUCESSO!")
    print("="*70)
    print("\n🔌 API rodando em: http://localhost:8050")
    print("🔌 Também disponível em: http://127.0.0.1:8050")
    print("\n📡 Endpoints disponíveis:")
    print("   • GET /api/dados - Obter dados filtrados")
    print("   • GET /api/filtros - Obter opções de filtro")
    print("   • GET /api/exportar - Exportar dados em CSV")
    print("   • GET /api/health - Verificar saúde da API")
    print("\n💡 Pressione CTRL+C para parar o servidor")
    print("="*70 + "\n")
    
    app.run(debug=False, port=8050, host='127.0.0.1', use_reloader=False)