"""
Aplicação unificada para deploy no Render
Roda backend e frontend juntos
"""
import os
from threading import Thread
import time
import requests

def run_backend():
    """Inicia o backend Flask em thread separada"""
    from backend import app as backend_app, data_manager
    print("Carregando dados iniciais do backend...")
    data_manager.carregar_dados()
    backend_app.run(host='0.0.0.0', port=8050, debug=False, use_reloader=False, threaded=True)

def wait_for_backend():
    """Aguarda o backend estar pronto"""
    for i in range(30):
        try:
            response = requests.get('http://localhost:8050/api/health', timeout=2)
            if response.status_code == 200:
                print("✅ Backend pronto!")
                return True
        except:
            pass
        time.sleep(1)
    return False

if __name__ == '__main__':
    # Iniciar backend em thread separada
    backend_thread = Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Aguardar backend inicializar
    if not wait_for_backend():
        print("❌ Erro: Backend não iniciou")
        exit(1)
    
    # Iniciar frontend
    from frontend import app as frontend_app
    port = int(os.environ.get('PORT', 8051))
    frontend_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
