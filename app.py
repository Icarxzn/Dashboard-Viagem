# app.py - Aplicação integrada para rodar backend e frontend juntos
import subprocess
import sys
import time
import os
from threading import Thread

def run_backend():
    """Executa o backend em uma thread separada"""
    print("🔧 Iniciando Backend...")
    subprocess.run([sys.executable, "backend.py"])

def run_frontend():
    """Executa o frontend em uma thread separada"""
    print("🎨 Iniciando Frontend...")
    time.sleep(2)  # Aguarda backend iniciar
    subprocess.run([sys.executable, "frontend.py"])

if __name__ == "__main__":
    print("="*70)
    print("🚀 INICIANDO DASHBOARD COMPLETO")
    print("="*70)
    print("\n📦 Iniciando Backend e Frontend...\n")
    
    # Criar threads para backend e frontend
    backend_thread = Thread(target=run_backend, daemon=True)
    frontend_thread = Thread(target=run_frontend, daemon=True)
    
    # Iniciar threads
    backend_thread.start()
    frontend_thread.start()
    
    # Aguardar threads
    try:
        backend_thread.join()
        frontend_thread.join()
    except KeyboardInterrupt:
        print("\n\n⚠️  Encerrando aplicação...")
        print("="*70)
        sys.exit(0)
