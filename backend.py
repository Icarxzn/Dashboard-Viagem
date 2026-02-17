# ============================================================================
# BACKEND DO DASHBOARD - API Flask com Google Sheets
# ============================================================================
# Sistema de monitoramento de viagens com dados em tempo real
# Funcionalidades:
# - Autenticação com Google Sheets
# - Cache de dados (15 segundos)
# - Endpoints REST para dados, filtros e exportação
# - Página de Previsão: dados gerais com filtros
# - Página de Programado: viagens programadas com totais de carga

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
# CONFIGURAÇÕES
# ============================================================================
PLANILHA_ID = os.getenv("PLANILHA_ID", "1BKB3rsrZFcHxRt0LkTABtSBlqv7VWU6TwmkbwX95TLI")
NOME_ABA = "Base Principal"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CACHE_DURATION = 15  # segundos
COLUNAS_TABELA = ["trip_number", "Status Veiculo", "Status_da_Viagem", "ETA Planejado", 
                  "Ultima localização", "Previsão de chegada", "Ocorrencia"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dados_cache = {"df": None, "timestamp": None}


def _normalize_turno(val):
    """Normaliza valores de turno para T1/T2/T3.

    Regras simples: procura por '1'/'man' -> T1, '2'/'tar' -> T2, '3'/'noi' -> T3.
    Mantém T1/T2/T3 se já estiverem nesse formato.
    """
    if val is None:
        return None
    s = str(val).strip().lower()
    if s == 't1' or s == 't01' or s == '1' or 't 1' in s:
        return 'T1'
    if s == 't2' or s == 't02' or s == '2' or 't 2' in s:
        return 'T2'
    if s == 't3' or s == 't03' or s == '3' or 't 3' in s:
        return 'T3'
    if 'man' in s or 'manha' in s or 'manhã' in s:
        return 'T1'
    if 'tar' in s or 'tarde' in s:
        return 'T2'
    if 'noi' in s or 'noite' in s:
        return 'T3'
    # fallback: try to extract digit
    import re
    m = re.search(r"([123])", s)
    if m:
        return f'T{m.group(1)}'
    return None


class DataManager:
    """Gerenciador de dados do Google Sheets com cache"""
    
    def __init__(self):
        self.creds = None
        self.gc = None
        
    def _autenticar(self):
        """Autentica com Google Sheets (variável de ambiente ou arquivo local)"""
        try:
            google_creds_json = os.getenv("GOOGLE_CREDENTIALS")
            
            if google_creds_json:
                creds_dict = json.loads(google_creds_json)
                self.creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
                logger.info("Autenticação via variável de ambiente")
            else:
                account_path = os.path.join(os.path.dirname(__file__), "account.json")
                self.creds = Credentials.from_service_account_file(account_path, scopes=SCOPES)
                logger.info("Autenticação via arquivo account.json")
            
            self.gc = gspread.authorize(self.creds)
            logger.info("Autenticação realizada com sucesso")
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            raise
    
    def carregar_dados(self, force_reload=False):
        """Carrega dados da planilha com sistema de cache"""
        global dados_cache
        
        # Verificar cache
        if not force_reload and dados_cache["df"] is not None and dados_cache["timestamp"] is not None:
            tempo_decorrido = time.time() - dados_cache["timestamp"]
            if tempo_decorrido < CACHE_DURATION:
                logger.info(f"Retornando dados do cache ({int(tempo_decorrido)}s)")
                return dados_cache["df"]
        
        logger.info("Carregando novos dados da planilha...")
        
        try:
            if not self.gc:
                self._autenticar()
            
            sheet = self.gc.open_by_key(PLANILHA_ID).worksheet(NOME_ABA)
            all_values = sheet.get_all_values()
            
            if not all_values or len(all_values) < 2:
                logger.warning("Planilha vazia")
                return pd.DataFrame()
            
            df = pd.DataFrame(all_values[1:], columns=all_values[0]).dropna(how='all')
            
            # Converter colunas de data
            for col in df.columns:
                if 'data' in col.lower() or 'data' in col:
                    try:
                        # tentar inferir o formato (aceita 'DD/MM/YYYY' e 'YYYY-MM-DD' etc.)
                        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                    except Exception:
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        except Exception:
                            pass
            
            dados_cache["df"] = df
            dados_cache["timestamp"] = time.time()
            
            logger.info(f"Dados carregados: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            if dados_cache["df"] is not None:
                logger.warning("Retornando cache antigo")
                return dados_cache["df"]
            return pd.DataFrame()
    
    def filtrar_dados(self, filters=None):
        """Aplica filtros aos dados"""
        df = self.carregar_dados()
        
        if df.empty or not filters:
            return df
        
        # Filtros da página Previsão
        if 'ids' in filters and filters['ids'] and "trip_number" in df.columns:
            df = df[df["trip_number"].isin(filters['ids'])]
        
        if 'destinos' in filters and filters['destinos'] and "destination_station_code" in df.columns:
            df = df[df["destination_station_code"].isin(filters['destinos'])]
        
        if 'status' in filters and filters['status'] and "Status_da_Viagem" in df.columns:
            df = df[df["Status_da_Viagem"].isin(filters['status'])]
        
        if 'data_inicial' in filters and filters['data_inicial'] and "Data" in df.columns:
            df = df[df["Data"] >= pd.to_datetime(filters['data_inicial'])]
        
        if 'data_final' in filters and filters['data_final'] and "Data" in df.columns:
            df = df[df["Data"] <= pd.to_datetime(filters['data_final'])]
        
        return df
    
    def obter_estatisticas(self, df=None):
        """Calcula estatísticas de status das viagens"""
        if df is None:
            df = self.carregar_dados()
        
        if df.empty:
            return {'total': 0, 'transito': 0, 'parado': 0, 'finalizado': 0, 'cancelado': 0}
        
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
    
    def obter_opcoes_filtro(self):
        """Retorna opções únicas para dropdowns de filtro"""
        df = self.carregar_dados()
        
        def get_options(col):
            if col in df.columns:
                valores = df[col].dropna().unique()
                return [{"label": str(v), "value": v} for v in sorted(valores, key=lambda x: str(x))]
            return []

        # detectar coluna de turno (variações: 'Turno', 'turno_programado', etc.)
        turno_col = None
        for c in df.columns:
            if 'turn' in c.lower():
                turno_col = c
                break

        # Normalizar opções de turno para T1/T2/T3
        turno_options = []
        if turno_col and turno_col in df.columns:
            raw_vals = df[turno_col].dropna().unique()
            normalized = sorted({v for v in (_normalize_turno(v) for v in raw_vals) if v})
            turno_options = [{"label": v, "value": v} for v in normalized]

        return {
            'ids': get_options("trip_number"),
            'destinos': get_options("destination_station_code"),
            'status': get_options("Status_da_Viagem"),
            'turno': turno_options
        }


# ============================================================================
# INICIALIZAR APP
# ============================================================================
data_manager = DataManager()
app = Flask(__name__)
CORS(app)


# ============================================================================
# ENDPOINTS - PÁGINA PREVISÃO
# ============================================================================

@app.route('/api/dados', methods=['GET'])
def get_dados():
    """
    Endpoint principal da página Previsão
    Retorna dados filtrados com estatísticas e colunas para tabela
    """
    try:
        logger.info("=== /api/dados ===")
        
        # Obter filtros
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
        df = data_manager.filtrar_dados(filters)
        logger.info(f"Dados filtrados: {len(df)} registros")
        
        # Selecionar colunas para tabela
        colunas_existentes = [c for c in COLUNAS_TABELA if c in df.columns]
        df_tabela = df[colunas_existentes] if colunas_existentes else df
        
        # Calcular estatísticas
        stats = data_manager.obter_estatisticas(df)
        
        return jsonify({
            'success': True,
            'dados': df_tabela.to_dict('records'),
            'colunas': list(df_tabela.columns),
            'estatisticas': stats,
            'total_registros': len(df_tabela),
            'timestamp': datetime.now().isoformat(),
            'cache_age': int(time.time() - dados_cache["timestamp"]) if dados_cache["timestamp"] else 0
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/dados: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/filtros', methods=['GET'])
def get_filtros():
    """Retorna opções para os dropdowns de filtro"""
    try:
        opcoes = data_manager.obter_opcoes_filtro()
        return jsonify({'success': True, 'opcoes': opcoes})
    except Exception as e:
        logger.error(f"Erro em /api/filtros: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/exportar', methods=['GET'])
def exportar_dados():
    """Exporta dados filtrados em formato CSV"""
    try:
        # Obter filtros (mesmos de /api/dados)
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
        
        df = data_manager.filtrar_dados(filters)
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        filename = f"dados_viagens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erro em /api/exportar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ENDPOINTS - PÁGINA PROGRAMADO
# ============================================================================

@app.route('/api/programado', methods=['GET'])
def get_programado():
    """
    Endpoint da página Programado
    Retorna viagens programadas com totais de carga (Sacas, Scuttle, Palete, Total)
    Filtros: data, turno, status
    """
    try:
        logger.info("=== /api/programado ===")
        
        # Obter filtros
        data = request.args.get('data')
        turno = request.args.get('turno')
        status = request.args.get('status')
        
        df = data_manager.carregar_dados()
        
        if df.empty:
            return jsonify({
                'success': True,
                'dados': [],
                'colunas': [],
                'estatisticas': {'total_sacas': 0, 'total_scuttle': 0, 'total_palete': 0, 'total_geral': 0},
                'total_registros': 0
            })
        
        # Filtrar apenas programadas (excluir finalizadas/canceladas)
        if "Status_da_Viagem" in df.columns:
            df_programado = df[~df["Status_da_Viagem"].isin(["Finalizado", "Cancelado"])].copy()
        else:
            df_programado = df.copy()
        
        # Converter Data Planejada para datetime
        if "Data Planejada" in df_programado.columns:
            try:
                # Use parsing without fixed format to accept both 'DD/MM/YYYY' and 'YYYY-MM-DD'
                df_programado['Data_dt'] = pd.to_datetime(df_programado["Data Planejada"], dayfirst=True, errors='coerce')
            except Exception as e:
                logger.warning(f"Erro ao processar Data Planejada: {e}")
        
        # Aplicar filtros
        if data and "Data_dt" in df_programado.columns:
            try:
                data_dt = pd.to_datetime(data)
                data_final_dt = data_dt + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                df_programado = df_programado[(df_programado['Data_dt'] >= data_dt) & 
                                             (df_programado['Data_dt'] <= data_final_dt)]
            except Exception as e:
                logger.error(f"Erro ao aplicar filtro data: {e}")
        
        # Filtrar por turno — aceitar variações no nome da coluna (ex: 'Turno', 'turno_programado')
        turno_col = None
        for c in df_programado.columns:
            if 'turn' in c.lower():
                turno_col = c
                break

        # Criar coluna padronizada 'Turno_std' com valores T1/T2/T3
        if turno_col and turno_col in df_programado.columns:
            df_programado['Turno_std'] = df_programado[turno_col].apply(_normalize_turno)
        else:
            df_programado['Turno_std'] = df_programado.get('Turno').apply(_normalize_turno) if 'Turno' in df_programado.columns else None

        if turno and turno != "" and 'Turno_std' in df_programado.columns:
            df_programado = df_programado[df_programado['Turno_std'].astype(str).str.strip().str.lower() == turno.lower()]
        
        if status and status != "" and "Status" in df_programado.columns:
            df_programado = df_programado[df_programado['Status'].astype(str).str.strip().str.lower() == status.lower()]
        
        logger.info(f"Registros após filtros: {len(df_programado)}")
        
        # Calcular totais de carga
        def calcular_total(coluna_nome):
            """Helper para calcular total de uma coluna"""
            for col in df_programado.columns:
                if col.lower().strip() == coluna_nome.lower():
                    try:
                        # Substituir "-" por 0, remover pontos (separador de milhares)
                        valores = df_programado[col].replace(['-', '', ' ', 'nan', 'NaN'], '0')
                        valores = valores.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        valores_numericos = pd.to_numeric(valores, errors='coerce').fillna(0)
                        return int(valores_numericos.sum())
                    except:
                        return 0
            return 0
        
        total_sacas = calcular_total('saca')
        total_scuttle = calcular_total('scuttle')
        total_palete = calcular_total('palete')
        total_geral = calcular_total('total')
        
        # Selecionar colunas para exibição
        # Ajustar colunas a exibir: usar o nome real de coluna de turno quando detectado
        # Garantir que a coluna de exibição chamada 'Turno' exista (vinda do original ou do padrão)
        if turno_col and turno_col in df_programado.columns:
            df_programado['Turno'] = df_programado[turno_col]
        elif 'Turno_std' in df_programado.columns:
            df_programado['Turno'] = df_programado['Turno_std']

        colunas_exibir = ["trip_number", "Data Planejada", "Turno", "Status Veiculo", 
                         "ETA Planejado", "origin_station_code", "destination_station_code", 
                         "Ultima localização", "Previsão de chegada", "Ocorrencia", 
                         "Saca", "Scuttle", "Palete", "Total"]
        
        colunas_existentes = [c for c in colunas_exibir if c in df_programado.columns]
        df_resultado = df_programado[colunas_existentes] if colunas_existentes else df_programado
        
        # Ordenar por Data Planejada e remover colunas auxiliares (somente se estiver presente em df_resultado)
        if 'Data_dt' in df_resultado.columns:
            df_resultado = df_resultado.sort_values('Data_dt', na_position='last')
            df_resultado = df_resultado.drop(columns=['Data_dt'])
        
        # Converter registros para tipos JSON-serializáveis (tratando NaT/Timestamp)
        records = df_resultado.to_dict('records')

        def _convert_value(v):
            try:
                if pd.isna(v):
                    return None
            except Exception:
                pass
            if isinstance(v, (pd.Timestamp, datetime)):
                try:
                    return v.isoformat()
                except Exception:
                    return str(v)
            return v

        records = [ {k: _convert_value(v) for k, v in row.items()} for row in records ]

        return jsonify({
            'success': True,
            'dados': records,
            'colunas': list(df_resultado.columns),
            'estatisticas': {
                'total_sacas': total_sacas,
                'total_scuttle': total_scuttle,
                'total_palete': total_palete,
                'total_geral': total_geral
            },
            'total_registros': len(df_resultado),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/programado: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ENDPOINTS - UTILITÁRIOS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica saúde da API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cache_age': time.time() - dados_cache["timestamp"] if dados_cache["timestamp"] else None
    })


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

if __name__ == '__main__':
    logger.info("Carregando dados iniciais...")
    data_manager.carregar_dados()
    
    print("\n" + "="*70)
    print("✅ BACKEND API INICIADO COM SUCESSO!")
    print("="*70)
    print("\n🔌 API: http://localhost:8050")
    print("\n📡 Endpoints:")
    print("   • GET /api/dados - Dados filtrados (Página Previsão)")
    print("   • GET /api/filtros - Opções de filtro")
    print("   • GET /api/programado - Viagens programadas (Página Programado)")
    print("   • GET /api/exportar - Exportar CSV")
    print("   • GET /api/health - Status da API")
    print("\n💡 CTRL+C para parar")
    print("="*70 + "\n")
    
    app.run(debug=False, port=8050, host='127.0.0.1', use_reloader=False)