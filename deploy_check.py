import subprocess
import sys
import time

# Configurações do Deployment
DEPLOYMENT_NAME = "deployment/api-deployment"  # 🔄 Nome do recurso corrigido com base no cluster
NAMESPACE = "default"
TIMEOUT_SECONDS = 120
CHECK_INTERVAL = 10

def run_command(command):
    """Executa um comando no terminal e retorna a saída e o código de status."""
    try:
        result = subprocess.run(command, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def check_deployment_health():
    print(f"🚀 [DevOps] Iniciando monitoramento do deployment '{DEPLOYMENT_NAME}'...")
    start_time = time.time()
    
    while time.time() - start_time < TIMEOUT_SECONDS:
        # Executa o rollout status do kubectl
        cmd = f"kubectl rollout status {DEPLOYMENT_NAME} --namespace={NAMESPACE} --timeout=5s"
        returncode, stdout, stderr = run_command(cmd)
        
        if returncode == 0:
            print("✅ [SUCESSO] Deployment concluído com sucesso e todos os Pods estão Ready!")
            return True
        
        print(f"⏳ Aguardando Pods estabilizarem... Status atual: {stdout if stdout else stderr}")
        time.sleep(CHECK_INTERVAL)
        
    return False

def trigger_rollback():
    print("⚠️ [ALERTA] Tempo limite atingido! O deployment falhou ou os Pods não passaram nas Probes.")
    print(f"🔄 [ROLLBACK] Iniciando Rollback automático para a versão estável anterior...")
    
    cmd = f"kubectl rollout undo {DEPLOYMENT_NAME} --namespace={NAMESPACE}"
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print("🛑 [ROLLBACK] Rollback executado com sucesso total! Ambiente preservado.")
    else:
        print(f"❌ [ERRO] Falha crítica ao tentar executar o rollback: {stderr}")

if __name__ == "__main__":
    success = check_deployment_health()
    
    if not success:
        trigger_rollback()
        sys.exit(1)
        
    sys.exit(0)