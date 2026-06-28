import subprocess
import re
import sys
import os

# ==============================================================================
# DECISÕES ARQUITETURAIS:
# 1. Escolha do Python: Flexibilidade para parsing de texto e expressões regulares.
# 2. Coleta via Subprocess: Interação direta com a API do Docker (stdout/stderr).
# 3. Mecanismo de Alerta: Se anomalias forem detectadas, o script dispara um
#    alerta visual no console e gera um artefato físico ('ALERTA_FALHA.log') na raiz,
#    simulando a trigger de incidentes que seria enviada para um Webhook.
# ==============================================================================

CONTAINER_PADRAO = "realworld-api"
ARQUIVO_ALERTA = "ALERTA_FALHA.log"

def coletar_logs_docker(container):
    """Executa o comando docker logs para obter a saída padrão da aplicação."""
    try:
        resultado = subprocess.run(
            ["docker", "logs", container],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return resultado.stdout + resultado.stderr
    except subprocess.CalledProcessError:
        disparar_alerta(f"CRITICAL: Não foi possível conectar ao container '{container}'.")
        print(f"❌ Erro: Falha ao ler os logs do container '{container}'.")
        sys.exit(1)

def analisar_logs(logs):
    """Filtra erros baseados em padrões 5xx ou termos como ERROR/CRITICAL."""
    linhas = logs.splitlines()
    erros_encontrados = []
    
    padrao_erro = re.compile(r"ERROR|CRITICAL|\b5[0-9]{2}\b", re.IGNORECASE)

    for num_linha, linha in enumerate(linhas, 1):
        if padrao_erro.search(linha):
            erros_encontrados.append((num_linha, linha.strip()))
            
    return erros_encontrados

def disparar_alerta(mensagem_erro):
    """Cria um alerta visual chamativo e gera um arquivo de log de incidente."""
    print("\n🚨 [ALERTA DISPARADO] 🚨")
    print(f"⚠️ Notificação de Incidente: Padrão de falha detectado!")
    print(f"Descrição: {mensagem_erro}")
    
    # Simulação de persistência/notificação de alerta
    with open(ARQUIVO_ALERTA, "w", encoding="utf-8") as f:
        f.write(f"=== INCIDENTE DETECTADO ===\n")
        f.write(f"Status: CRITICAL\n")
        f.write(f"Detalhe: {mensagem_erro}\n")

def gerar_resumo(erros, total_linhas, container):
    """Formata e exibe o resumo executivo dos problemas encontrados nos logs."""
    print("=" * 60)
    print(f"📋 RELATÓRIO DE SAÚDE - CONTAINER: {container}")
    print("=" * 60)
    print(f"Total de linhas analisadas: {total_linhas}")
    print(f"Total de anomalias/erros detectados: {len(erros)}")
    print("-" * 60)
    
    if not erros:
        print("✅ Sucesso! Nenhum erro 5xx ou padrão 'ERROR' foi encontrado nos logs.")
        # Remove o arquivo de alerta antigo se o ambiente voltou a ficar saudável
        if os.path.exists(ARQUIVO_ALERTA):
            os.remove(ARQUIVO_ALERTA)
    else:
        print("🚨 Detalhes das ocorrências encontradas:")
        for linha_num, conteudo in erros:
            print(f" [Linha {linha_num}]: {conteudo}")
        
        # Dispara o alerta técnico exigido pelo item 5
        disparar_alerta(f"Detectados {len(erros)} erros críticos no container {container}.")
            
    print("=" * 60)

if __name__ == "__main__":
    container_alvo = sys.argv[1] if len(sys.argv) > 1 else CONTAINER_PADRAO
    
    print(f"🔍 Coletando logs do container '{container_alvo}'...")
    conteudo_logs = coletar_logs_docker(container_alvo)
    
    total_linhas = len(conteudo_logs.splitlines())
    lista_erros = analisar_logs(conteudo_logs)
    
    gerar_resumo(lista_erros, total_linhas, container_alvo)