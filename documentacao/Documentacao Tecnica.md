📑 Manual de Engenharia e Operação — Stack RealWorld DevOps
Classificação: Técnico / Interno (N1, N2 e SRE)

Objetivo: Fornecer autonomia completa para mitigação de incidentes, recuperação de desastres e análise de causa raiz.

🏗️ 1. Arquitetura de Baixo Nível & Fluxo de Dados
Abaixo está o mapa de interatividade física dos containers e barramentos locais. Toda a comunicação de microsserviços e coleta é realizada de forma isolada dentro da malha de rede virtual realworld-net.

                        [ REQUISIÇÃO CLIENTE ]
                                  │ (Porta 3000)
                                  ▼
                        ┌───────────────────┐
                        │   realworld-api   │ ◄───┐
                        └─────────┬─────────┘     │
                                  │ (Porta 27017) │ (Volume Unix Socket)
                                  ▼               │
                        ┌───────────────────┐     │
                        │   realworld-db    │     │
                        │    (MongoDB)      │     │
                        └───────────────────┘     │
                                                  │
 ┌────────────────────────────────────────────────┼────────────────────────────────┐
 │ MONITORAMENTO & INFRAESTRUTURA (Rede: realworld-net / monitoring)               │
 │                                                ▼                                │
 │ ┌──────────────┐   File Reads   ┌─────────────────────┐  Push (3100)  ┌──────┐  │
 │ │   cAdvisor   │ ─────────────► │      Promtail       │ ────────────► │ Loki │  │
 │ └──────┬───────┘                │ (Socket /var/run..) │               └───┬──┘  │
 │        │                        └─────────────────────┘                   │     │
 │        │ Scraping (8080)                                                  │     │
 │        ▼                                                                  │     │
 │ ┌──────────────┐                                                          │     │
 │ │  Prometheus  │ ◄────────────────────────────────────────────────────────┘     │
 │ └──────┬───────┘                        Queries (3100 / 9090)                   │
 │        │                                                                        │
 │        └──────────────────────────────► ┌─────────┐                             │
 │                                         │ Grafana │ (Acesso: Porta 3050)        │
 │                                         └─────────┘                             │
 └─────────────────────────────────────────────────────────────────────────────────┘
🐋 1. Docker & Persistência (Deep Dive)
📂 Estrutura de Diretórios e Mapeamentos
Os dados do banco não são salvos dentro do container. Eles utilizam persistência via Named Volumes e Bind Mounts gerenciados pelo Docker Engine:

Banco de Dados (MongoDB): Mapeia o volume mongo_data para a pasta interna /data/db. Se o container do banco cair ou for deletado, os dados estão salvos no disco da máquina hospedeira.

Coleta de Logs (Promtail): Realiza um Bind Mount do diretório /var/lib/docker/containers do hospedeiro para dentro do container do Promtail em modo Read-Only (:ro).

⚙️ Variáveis de Ambiente Críticas
Se a API perder comunicação ou crashar no boot, valide estas variáveis no docker-compose.yml:

DATABASE_URL e MONGODB_URI: Devem apontar obrigatoriamente para mongodb://realworld-db:27017/conduit?authSource=admin. O Prisma ORM utiliza essa string exata para mapear o banco. Se o nome do container do banco mudar, a API não inicializa.

🚨 Playbook de Mitigação: Erro de Validação do Prisma ORM
Sintoma: API fora do ar e logs exibindo: Error validating datasource db: the URL must start with the protocol....

Causa: O arquivo schema.prisma foi alterado ou o container foi alimentado com a imagem de banco errada (ex: Postgres em vez de Mongo).

Resolução:

Certifique-se de que o serviço mongodb no docker-compose.yml está utilizando a imagem oficial mongo:6.0-jammy.

Force a limpeza absoluta de caches de build antigos e reinicie a stack limpa:

Bash
docker-compose down -v
docker-compose up -d --build
☸️ 2. Kubernetes Local (Topologia de Resiliência)
A aplicação em produção local é gerenciada via manifesto declarativo no Kubernetes.

🛡️ Engenharia de Confiabilidade (Probes & HPA)
Anti-Autodestruição (livenessProbe): Executa uma checagem HTTP na rota /api/health a cada 10 segundos. Se falhar 3 vezes seguidas, o Kubernetes mata o Pod instável e cria um novo automaticamente.

Proteção de Tráfego (readinessProbe): Garante que um Pod recém-criado só receba requisições dos usuários após validar que a conexão com o MongoDB está estabelecida.

Auto-Escalonamento (HPA): Configurado para monitorar as réplicas. Se a média de consumo de CPU ultrapassar 70%, o cluster gera novas réplicas dinamicamente até o limite configurado (mínimo 2, máximo 5).

🩺 Playbook de Mitigação: Pods em CrashLoopBackOff
Se o comando kubectl get pods retornar Pods que não sobem, execute a triagem abaixo:

Verifique os eventos do cluster relacionados ao Pod:

Bash
kubectl describe pod <nome-do-pod-problematico>
Procure na seção "Events" por falhas de falta de memória (OOMKilled) ou falhas de Probes.

Inspecione as Secrets e ConfigMaps:
Se as credenciais do banco estiverem erradas na Secret, o Pod crasha no boot. Verifique se o mapeamento está correto:

Bash
kubectl get configmap api-config -o yaml
🚀 3. Ciclo de Vida CI/CD (Pipeline Failures)
O fluxo automatizado roda via GitHub Actions. Se a pipeline quebrar ou o deploy falhar, o time deve agir nas seguintes frentes:

🛠️ Correção de Quebras na Pipeline
Falha no Estágio de Lint/Build (Pull Request): Geralmente causada por erros de sintaxe de código ou tipagem do TypeScript. O desenvolvedor deve corrigir localmente e commitar novamente na branch de origem do PR.

Falha de Autenticação no GHCR (Push na Main): Se a imagem não for publicada no GitHub Container Registry, valide os tokens de acesso (GITHUB_TOKEN) nas configurações de Secrets do repositório no GitHub. O workflow precisa de permissões de escrita (write-all) no pacote do registry.

📊 4. Observabilidade Baseada em Sintomas (Métricas & Logs)
🔍 Arquitetura de Coleta do Promtail (Resolução de Telas Vazias)
O Promtail lê os logs diretamente do socket do Docker usando a configuração de job global containerlogs. Se o painel do Grafana exibir "No Data", o barramento de socket ou a malha de rede interna foi desconectada.

🛠️ Playbook: Painel do Grafana Parou de Exibir Dados
Verifique se o Socket está acessível no container:

Bash
docker logs promtail
Se houver erros de "Cannot connect to the Docker daemon", certifique-se de que o Docker Desktop está com a opção "Allow the default Docker socket to be used" ativada nas configurações gerais.

Queries de Emergência no Painel Explore:
Para isolar problemas na API diretamente na console do Loki, ignore filtros refinados de tags e utilize o filtro de linha por expressão regular:

Snippet de código
{job="containerlogs"} |= "realworld-api"
Métricas do Prometheus Sumiram:
Se o gráfico de CPU/Memória falhar, utilize a tag interna do Docker Compose injetada pelo cAdvisor, que é imune a variações do Windows:

Snippet de código
sum(rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_service="api"}[5m])) * 100
🤖 5. Automação Avançada com o Script de Diagnóstico
Para evitar intervenção manual demorada, o time N2 possui um script automatizado (check_cluster_health.py) escrito em Python.

📋 Fluxograma de Ação do Script
O script utiliza a biblioteca oficial do Kubernetes ou chamadas de sistema embrulhadas para rodar o seguinte fluxo lógico:

[ Início do Script ] ──► Faz a checagem do contexto ativo do kubectl
                                │
                                ▼
                   [ O Cluster está respondendo? ]
                     │                      │
                     ├───► NÃO ──► Alerta N2: "Cluster Inacessível" ──► Encerra
                     │
                     └───► SIM
                            │
                            ▼
              Varre todos os Namespaces procurando Pods
                            │
                            ▼
           [ Status do Pod == "Running" ou "Completed"? ]
                     │                          │
                     ├───► SIM ──► Ignora (Saudável)
                     │
                     └───► NÃO ──► Captura o ID do Pod e o Erro (Ex: Evicted)
                                        │
                                        ▼
                   Gera o arquivo texto bruto "cluster_report.txt"
🚨 Procedimento Operacional Padrão (POP) em Casos de Alerta
Se o script retornar erros no arquivo cluster_report.txt, a equipe N2 deve seguir esta árvore de decisão:

Status ImagePullBackOff / ErrImagePull: A imagem publicada no GHCR foi deletada ou a tag informada no manifesto de Deployment não existe. Ação: Verificar o repositório do GitHub e reexecutar o último workflow de sucesso.

Status OOMKilled: O Pod estourou o limite físico de memória RAM configurado nos manifestos. Ação: Editar o arquivo de deployment e incrementar os limites na seção resources.limits.memory.

Status Evicted: O nó do cluster ficou sem espaço em disco ou memória disponível no hospedeiro. Ação: Executar o comando docker system prune -a --volumes para liberar espaço em disco no Docker Desktop local.

Com este nível de detalhamento técnico, as equipes N1 e N2 possuem total rastreabilidade das dependências e isolamento da stack, garantindo a continuidade do ambiente e mitigação imediata de desastres sem gargalos.