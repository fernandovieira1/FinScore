# FinScore

## 📊 Visão Geral

O **FinScore** é um sistema completo para quantificação de riscos e classificação de clientes baseado em análise de dados contábeis. O projeto oferece uma interface web intuitiva construída com Streamlit e um robusto backend de processamento de dados financeiros.

## 🚀 Funcionalidades Principais

- **Análise de Risco Personalizada**: Cálculo automatizado do índice FinScore baseado em demonstrações contábeis
- **Interface Web Responsiva**: Dashboard interativo para visualização e análise de dados
- **Processamento de Dados**: Suporte para upload de arquivos Excel e integração com Google Sheets
- **Relatórios Automatizados**: Geração de pareceres detalhados com insights financeiros
- **Fluxo Guiado**: Processo step-by-step desde o cadastro até a análise final

## 🏗️ Arquitetura do Projeto

```
FinScore/
├── app_front/              # Aplicação frontend (Streamlit)
│   ├── app.py             # Entry point do aplicativo
│   ├── views/             # Views/páginas do app
│   ├── components/        # Componentes reutilizáveis
│   ├── services/          # Lógica de negócio e integrações
│   ├── styles/            # Customizações CSS
│   └── assets/            # Recursos estáticos
├── finscore/              # Notebooks e scripts de prototipação
└── requirements.txt       # Dependências do projeto
```

### Componentes Principais

- **`app_front/`**: Código principal do app Streamlit
  - **`views/`**: Cada arquivo representa uma seção do app (novo.py, resumo.py, parecer.py, etc.)
  - **`components/`**: Navegação, header, gerenciamento de estado
  - **`services/`**: Lógica de negócio (`finscore_service.py`) e validação (`io_validation.py`)
  - **`styles/`**: Customizações visuais para Streamlit

- **`finscore/`**: Notebooks Jupyter para prototipação e desenvolvimento de algoritmos

## 🛠️ Tecnologias Utilizadas

- **Frontend**: Streamlit, HTML/CSS, JavaScript
- **Backend**: Python, Pandas, NumPy
- **Dados**: Excel, Google Sheets
- **Análise**: Jupyter Notebooks
- **Versionamento**: Git

## 📋 Pré-requisitos

- Python 3.8+
- Pip (gerenciador de pacotes Python)
- Navegador web moderno

## ⚡ Instalação e Execução

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/fernandovieira1/FinScore.git
   cd FinScore
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o aplicativo**:
   ```bash
   streamlit run app_front/app.py
   ```

4. **Acesse no navegador**:
   ```
   http://localhost:8501
   ```

## 🎯 Como Usar

### Fluxo Principal

1. **Novo Cálculo**: Inicie um novo processo de análise
2. **Dados do Cliente**: Cadastre informações da empresa (CNPJ, período, Serasa Score)
3. **Dados Contábeis**: Faça upload das demonstrações financeiras
4. **Cálculo**: Execute o algoritmo FinScore
5. **Análise**: Visualize resultados, gráficos e indicadores
6. **Parecer**: Obtenha relatório detalhado com recomendações

### Navegação Inteligente

- O sistema possui navegação progressiva que libera seções conforme o usuário avança
- **Lançamentos** fica disponível após clicar em "Iniciar"
- **Análise** e **Parecer** ficam disponíveis após o cálculo do FinScore

## 📊 Dados de Entrada

O sistema aceita demonstrações contábeis nos formatos:
- **Arquivo Excel (.xlsx)**: Upload direto de planilhas
- **Google Sheets**: Integração via link compartilhado
- **Entrada Manual**: Interface para dados diretos

### Campos Obrigatórios

- Nome da empresa
- CNPJ
- Período das demonstrações (ano inicial/final)
- Pontuação Serasa
- Data de consulta Serasa
- Balanço Patrimonial (BP)
- Demonstração do Resultado (DRE)

## 🔧 Desenvolvimento

### Estrutura de Desenvolvimento

- **Prototipação**: Use notebooks em `finscore/` para experimentos
- **Views**: Adicione novas páginas em `app_front/views/`
- **Componentes**: Crie componentes reutilizáveis em `app_front/components/`
- **Estilos**: Customize visual em `app_front/styles/main.css`

### Padrões de Código

- Cada view é um arquivo em `views/` registrado na navegação
- Estado centralizado via `components/state_manager.py`
- Validações em `services/io_validation.py`
- Lógica de negócio em `services/finscore_service.py`

## 📄 Licença

Este projeto está sob licença proprietária. Consulte o arquivo LICENSE para mais detalhes.

## 👥 Equipe

- **Desenvolvimento**: Fernando Vieira
- **Algoritmos**: Fernando Vieira
- **Design**: Fernando Vieira e equipe Assertif

---

*FinScore - Transformando dados contábeis em inteligência financeira*

## 🖥️ Especificações de Servidor para Deploy

> Esta seção descreve recomendações e passos para hospedar o FinScore em produção. A escolha do provedor (VM, container ou serviço PaaS) depende do tráfego esperado e políticas internas — trate as recomendações abaixo como ponto de partida.

### Requisitos mínimos (desenvolvimento / PoC)
- Sistema Operacional: Ubuntu 20.04+ (recomendado: 22.04 LTS) ou Debian 11+.
- CPU: 2 vCPUs.
- Memória RAM: 2 GB.
- Disco: 10 GB SSD (mais espaço para uploads/relatórios).
- Rede: Saída para Internet (para uso de APIs de LLM e integração com Google Sheets).

### Recomendado (produção leve / equipes pequenas)
- Sistema Operacional: Ubuntu 22.04 LTS.
- CPU: 4 vCPUs.
- Memória RAM: 8 GB.
- Disco: 40–80 GB SSD (dependendo do volume de arquivos e backups).
- Rede: Conexão com baixa latência e largura de banda suficiente (LLM calls podem gerar tráfego considerável).

### Componentes e serviços adicionais
- Banco de dados: O projeto usa SQLite por padrão (arquivo `finscore_auth.db`) — adequado para PoC e uso com poucos usuários. Para produção recomenda-se migrar para PostgreSQL/MySQL quando houver concorrência ou necessidade de backups gerenciados.
- Armazenamento de arquivos: Use volume persistente (NFS, disco gerenciado ou S3) para uploads e `assets/` se desejar manter em armazenamento central.
- Reverse proxy: Nginx (recomendado) para TLS, redirecionamento e balanceamento reverse-proxy.
- Certificados TLS: Let's Encrypt (/certbot) ou gerenciador de certificados do provedor.

### Variáveis de ambiente importantes
- `OPENAI_API_KEY` - chave para LLM (requerida se funcionalidade de IA estiver ativa).
- `FINSCORE_LLM_MODEL` - modelo padrão (ex.: `gpt-4o-mini`).
- `FINSCORE_LLM_TEMPERATURE` - temperatura do modelo (ex.: `0.1`).
- `FINSCORE_LLM_FALLBACK1/2/3` - modelos de fallback.
- Outras: use `.env` ou secrets do provedor; nunca comite chaves em repositório.

### Portas padrão
- Streamlit: 8501 (padrão). Em deploy com Nginx use: Streamlit escutando `127.0.0.1:8501` e Nginx como proxy reverso para `:443`.

### Exemplo rápido — implantação sem Docker (Ubuntu + systemd + Nginx)
1. Criar um user dedicado:
   ```bash
   sudo adduser --system --group --no-create-home finscore
   sudo mkdir -p /opt/finscore
   sudo chown finscore:finscore /opt/finscore
   ```
2. Copiar código para `/opt/finscore` e criar um venv:
   ```bash
   python3 -m venv /opt/finscore/venv
   source /opt/finscore/venv/bin/activate
   pip install -r /opt/finscore/requirements.txt
   ```
3. Configurar variáveis de ambiente (ex: `/etc/default/finscore`) com `OPENAI_API_KEY` e outras chaves.
4. Criar arquivo systemd `/etc/systemd/system/finscore.service`:
   ```ini
   [Unit]
   Description=FinScore Streamlit service
   After=network.target

   [Service]
   User=finscore
   Group=finscore
   WorkingDirectory=/opt/finscore
   EnvironmentFile=/etc/default/finscore
   ExecStart=/opt/finscore/venv/bin/streamlit run app_front/app.py --server.port 8501 --server.address 127.0.0.1
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```
5. Definir um bloco básico de Nginx (proxy reverso e TLS):
   ```nginx
   server {
       listen 80;
       server_name finscore.example.com;
       location /.well-known/acme-challenge/ { root /var/www/certbot; }
       location / { return 301 https://$host$request_uri; }
   }

   server {
       listen 443 ssl;
       server_name finscore.example.com;

       ssl_certificate /etc/letsencrypt/live/finscore.example.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/finscore.example.com/privkey.pem;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
6. Iniciar e habilitar o serviço:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now finscore.service
   ```

### Exemplo rápido — Docker + Docker Compose
Um deploy via Docker garante isolamento e facilita CI/CD em PaaS. Exemplo (resumido):

docker-compose.yml (essencial):
```yaml
version: '3.8'
services:
  finscore:
    build: .
    image: finscore:latest
    ports:
      - "8501:8501"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./app_front:/app/app_front
      - ./finscore_auth:/app/finscore_auth
``` 

Observação: a imagem deve rodar `streamlit run app_front/app.py --server.port 8501 --server.address 0.0.0.0`.

### Segurança e manutenção 🔒
- Não comite chaves e segredos — use o gerenciador de secrets do provedor (AWS Secrets Manager, GCP Secret Manager), ou o `.streamlit/secrets.toml`.
- Faça backups regulares do arquivo `finscore_auth.db` (ou do DB em produção).
- Configure logs rotativos (ex: `logrotate` no diretório do Streamlit logs) e monitoramento (Prometheus, Grafana, Sentry para erros).
- Teste a integração LLM (chaves API) em ambiente seguro — chamadas ao OpenAI têm custo.

### Observações finais
- Streamlit é ótimo para MVPs e dashboards internos; para alta concorrência considere re-architecting (microservices, multi-instance com state externo).
- Se pretende usar PostgreSQL para a camada de autenticação/usuários, atualize `app_front/services/db.py` para usar a URL de conexão do PostgreSQL e provisionar usuários e permissões.

