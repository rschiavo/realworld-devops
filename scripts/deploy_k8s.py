import subprocess
import sys
import time

# ==============================================================================
# CONFIGURAÇÕES DO AMBIENTE KUBERNETES
# ==============================================================================
DEPLOYMENT_NAME = "realworld-api"  # Nome do seu deployment no K8s
NAMESPACE = "default"              # Namespace onde está o deployment
TIMEOUT_SECONDS = 60               # Tempo máximo para aguardar o rollout

def executar_comando(comando):
    """Executa um comando no terminal e retorna a saída e o código de status."""
    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return resultado.returncode, resultado.stdout, resultado.stderr

def disparar_alerta(mensagem):
    """Gera um alerta visual chamativo exigido pelo Item 5 do desafio."""
    print("\n🚨 [ALERTA DE FALHA NO DEPLOY] 🚨")
    print(f"⚠️ Notificação: {mensagem}")
    print("=" * 60)

def atualizar_imagem(nova_imagem):
    print(f"🚀 Iniciando o deploy da nova imagem: {nova_imagem}...")
    
    # Executa o comando set image para disparar a atualização do pod
    comando_update = [
        "kubectl", "set", "image", f"deployment/{DEPLOYMENT_NAME}",
        f"api={nova_imagem}", f"--namespace={NAMESPACE}"
    ]
    
    codigo, stdout, stderr = executar_comando(comando_update)
    
    if codigo != 0:
        disparar_alerta(f"Falha ao aplicar a nova imagem via kubectl: {stderr.strip()}")
        sys.exit(1)
        
    print("✨ Imagem aplicada com sucesso no cluster. Monitorando o Rollout...")

def monitorar_e_validar():
    # Comando que aguarda e valida o status do rollout com um limite de tempo
    comando_status = [
        "kubectl", "rollout", "status", f"deployment/{DEPLOYMENT_NAME}",
        f"--namespace={NAMESPACE}", f"--timeout={TIMEOUT_SECONDS}s"
    ]
    
    print(f"⏳ Aguardando a conclusão do rollout (Timeout: {TIMEOUT_SECONDS}s)...")
    codigo, stdout, stderr = executar_comando(comando_status)
    
    if codigo == 0:
        print("\n============================================================")
        print("✅ SUCESSO: O deploy foi concluído e a aplicação está saudável!")
        print("============================================================")
    else:
        # Se o código for diferente de zero, houve falha ou estourou o timeout
        disparar_alerta(f"O Rollout falhou ou estourou o tempo limite de {TIMEOUT_SECONDS}s! Erro: {stderr.strip()}")
        executar_rollback()

def executar_rollback():
    print("↩️ Iniciando ROLLBACK automático para restaurar a versão estável anterior...")
    
    comando_undo = [
        "kubectl", "rollout", "undo", f"deployment/{DEPLOYMENT_NAME}",
        f"--namespace={NAMESPACE}"
    ]
    
    codigo, stdout, stderr = executar_comando(comando_undo)
    
    if codigo == 0:
        print("✅ Rollback executado com sucesso! Versão estável anterior reestabelecida.")
    else:
        print(f"❌ ERRO CRÍTICO: Falha grave ao tentar executar o rollback! {stderr.strip()}")

if __name__ == "__main__":
    # Permite passar a tag da imagem como argumento. Ex: python deploy_k8s.py realworld-api:v2
    if len(sys.argv) < 2:
        print("❌ Erro: Forneça o nome/tag da nova imagem. Exemplo:")
        print("python deploy_k8s.py realworld-devops-api:latest")
        sys.exit(1)
        
    nova_imagem = sys.argv[1]
    
    atualizar_imagem(nova_imagem)
    monitorar_e_validar()