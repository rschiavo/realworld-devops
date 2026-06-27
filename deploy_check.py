import subprocess
import sys
import time

def run_command(command):
    """Executa um comando no terminal e retorna a saída."""
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    return result

def main():
    print("🚀 [CI/CD Automation] Iniciando atualização de imagem no Kubernetes...")
    
    # 1. Força o restart para simular/aplicar o novo deploy
    restart_cmd = "kubectl rollout restart deployment/api-deployment"
    print(f"🔄 Executando: {restart_cmd}")
    run_cmd = run_command(restart_cmd)
    
    if run_cmd.returncode != 0:
        print("❌ Erro ao iniciar o rollout!")
        sys.exit(1)
        
    print("⏳ Aguardando a estabilização do Deployment (Timeout: 120s)...")
    
    # 2. Monitora o status do rollout
    status_cmd = "kubectl rollout status deployment/api-deployment --timeout=120s"
    rollout_status = run_command(status_cmd)
    
    if rollout_status.returncode == 0:
        print("✅ [SUCESSO] O deploy foi concluído e todas as réplicas estão saudáveis!")
        sys.exit(0)
    else:
        print("⚠️ [FALHA] O rollout falhou ou estourou o timeout! Iniciando Rollback automático...")
        
        # 3. Executa o Rollback (Undo) caso o deploy falhe
        undo_cmd = "kubectl rollout undo deployment/api-deployment"
        rollback_exec = run_command(undo_cmd)
        
        if rollback_exec.returncode == 0:
            print("↩️ [ROLLBACK CONCLUÍDO] Infraestrutura restaurada com sucesso para a versão anterior estável.")
        else:
            print("🚨 [CRÍTICO] Falha ao tentar executar o rollback automático!")
        sys.exit(1)

if __name__ == "__main__":
    main()