# FinScore

## 📊 Visão Geral

O **FinScore** é um sistema para quantificação de riscos e classificação de clientes baseado em análise de dados contábeis. O projeto oferece uma interface web construída com Streamlit e processamento de dados financeiros.

## 🚀 Funcionalidades

- **Análise de Risco**: Cálculo do índice FinScore baseado em demonstrações contábeis
- **Interface Web**: Dashboard para visualização e análise de dados
- **Processamento de Dados**: Upload de arquivos Excel e integração com Google Sheets
- **Relatórios**: Geração de pareceres com análise financeira
- **Fluxo Guiado**: Processo passo a passo desde o cadastro até a análise

## 🏗️ Arquitetura do Projeto

```
FinScore/
├── app_front/              # Aplicação frontend (Streamlit)
│   ├── app.py             # Entry point do aplicativo
│   ├── assets/            # Recursos estáticos
│   ├── components/        # Componentes reutilizáveis
│   ├── services/          # Lógica de negócio e integrações
│   ├── styles/            # Customizações CSS
│   └── views/             # Views/páginas do app
└── requirements.txt       # Dependências do projeto
```

### Componentes Principais

- **`app_front/`**: Código principal do app Streamlit
  - **`views/`**: Cada arquivo representa uma seção do app (novo.py, resumo.py, parecer.py, etc.)
  - **`components/`**: Navegação, header, gerenciamento de estado
  - **`services/`**: Lógica de negócio (`finscore_service.py`) e validação (`io_validation.py`)
  - **`styles/`**: Customizações visuais para Streamlit

## 🛠️ Tecnologias Utilizadas

- **Frontend**: Streamlit, HTML/CSS, JavaScript
- **Backend**: Python, Pandas, NumPy
- **Dados**: Excel, Google Sheets
- **Análise**: Jupyter Notebooks
- **Versionamento**: Git

## 📋 Pré-requisitos

- Python 3.8+ (recomendado: 3.11)
- pip (gerenciador de pacotes Python)

## 🚢 Deploy em servidor Linux (produção)

### 1) Preparar o servidor

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv unzip
# Opcional (reverse proxy)
sudo apt-get install -y nginx
# Firewall (opcional)
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8501  # acesso direto ao Streamlit, útil para testes
```

### 2) Criar usuário de execução

```bash
sudo adduser --system --group --home /opt/finscore --no-create-home finscore
```

### 3) Transferir e extrair o código

1. Copie o arquivo para o servidor:

   ```bash
   # Linux/macOS
   scp FinScore.zip usuario@SEU_SERVIDOR:/tmp/

   # Windows (PowerShell)
   scp .\FinScore.zip usuario@SEU_SERVIDOR:/tmp/
   ```
2. No servidor, extraia e configure permissões:

   ```bash
   sudo mkdir -p /opt/finscore
   sudo unzip /tmp/FinScore.zip -d /tmp/finscore_temp
   sudo cp -r /tmp/finscore_temp/FinScore*/* /opt/finscore/
   sudo chown -R finscore:finscore /opt/finscore
   sudo rm -rf /tmp/finscore_temp
   ```

### 4) Instalar dependências Python

**Cenário A: Servidor com internet**

```bash
cd /opt/finscore
sudo -u finscore python3.11 -m venv .venv
sudo -u finscore .venv/bin/pip install --upgrade pip
sudo -u finscore .venv/bin/pip install -r requirements.txt
```

**Cenário B: Servidor sem internet**

Prepare as dependências em uma máquina com internet:

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip download -r requirements.txt -d wheels
deactivate
# Inclua a pasta wheels/ no arquivo ZIP
```

No servidor, instale via cache local:

```bash
cd /opt/finscore
sudo -u finscore python3.11 -m venv .venv
sudo -u finscore .venv/bin/pip install --no-index --find-links wheels -r requirements.txt
```

### 5) Teste inicial

```bash
cd /opt/finscore
sudo -u finscore .venv/bin/streamlit run app_front/app.py \
   --server.headless=true \
   --server.address=0.0.0.0 \
   --server.port=8501
```

Acesse `http://SEU_IP:8501`. Pressione Ctrl+C para parar.

### 6) Configurar Streamlit (opcional)

```bash
sudo mkdir -p /opt/finscore/.streamlit
sudo tee /opt/finscore/.streamlit/config.toml <<'EOF'
[server]
headless = true
address = "0.0.0.0"
port = 8501
enableCORS = false
fileWatcherType = "none"

[browser]
gatherUsageStats = false
EOF
sudo chown -R finscore:finscore /opt/finscore/.streamlit
```

### 7) Configurar serviço systemd

```bash
sudo tee /etc/systemd/system/finscore.service <<'EOF'
[Unit]
Description=FinScore (Streamlit)
After=network.target

[Service]
User=finscore
Group=finscore
WorkingDirectory=/opt/finscore
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/finscore/.venv/bin/streamlit run app_front/app.py --server.headless=true --server.address=0.0.0.0 --server.port=8501 --server.fileWatcherType=none
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now finscore.service
sudo systemctl status finscore.service --no-pager
```

Logs:

```bash
sudo journalctl -u finscore.service -f
```

### 8) Configurar Nginx (opcional)

```bash
sudo tee /etc/nginx/sites-available/finscore <<'EOF'
server {
   listen 80;
   server_name seu-dominio.com;

   location / {
      proxy_pass http://127.0.0.1:8501/;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_read_timeout 600s;
   }
}
EOF

sudo ln -s /etc/nginx/sites-available/finscore /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Para HTTPS, use `certbot` ou instale certificado manualmente.

### 9) Atualizar versão

1. Envie o novo arquivo:

   ```bash
   scp FinScore.zip usuario@SEU_SERVIDOR:/tmp/
   ```
2. Pare o serviço:

   ```bash
   sudo systemctl stop finscore.service
   ```
3. Faça backup:

   ```bash
   sudo cp -r /opt/finscore /opt/finscore.bak_$(date +%Y%m%d_%H%M)
   ```
4. Extraia e atualize:

   ```bash
   sudo rm -rf /tmp/finscore_temp
   sudo unzip /tmp/FinScore.zip -d /tmp/finscore_temp
   sudo cp -r /tmp/finscore_temp/FinScore*/app_front /opt/finscore/
   sudo cp /tmp/finscore_temp/FinScore*/requirements.txt /opt/finscore/
   # Se incluiu wheels/ no ZIP
   sudo cp -r /tmp/finscore_temp/FinScore*/wheels /opt/finscore/ 2>/dev/null || true
   sudo chown -R finscore:finscore /opt/finscore
   sudo rm -rf /tmp/finscore_temp
   ```
5. Atualize dependências (se `requirements.txt` mudou):

   ```bash
   # Com internet
   sudo -u finscore /opt/finscore/.venv/bin/pip install -r /opt/finscore/requirements.txt --upgrade

   # Sem internet (usando wheels/)
   sudo -u finscore /opt/finscore/.venv/bin/pip install --no-index --find-links /opt/finscore/wheels -r /opt/finscore/requirements.txt --upgrade
   ```
6. Reinicie:

   ```bash
   sudo systemctl start finscore.service
   sudo systemctl status finscore.service --no-pager
   ```

### 10) Solução de problemas

- **Porta ocupada**: Altere `--server.port` em `/etc/systemd/system/finscore.service` e execute `sudo systemctl daemon-reload && sudo systemctl restart finscore`.
- **Erro venv/ensurepip**: Execute `sudo apt-get install -y python3.11-venv`.
- **Permissão negada**: Execute `sudo chown -R finscore:finscore /opt/finscore`.
- **Logs**: `sudo journalctl -u finscore.service -f`.
- **Serviço não inicia**: Execute `sudo systemctl status finscore.service` para ver erros.

## ⚡ Instalação Local

1. Extraia o arquivo:

   ```bash
   unzip FinScore.zip
   cd FinScore
   ```
2. Crie ambiente virtual e instale dependências:

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate   # Windows
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Execute:

   ```bash
   streamlit run app_front/app.py
   ```
4. Acesse:

   ```
   http://localhost:8501
   ```

## 🎯 Como Usar

### Fluxo de Trabalho

1. **Novo Cálculo**: Inicie o processo de análise
2. **Dados do Cliente**: Cadastre informações da empresa (CNPJ, período, Serasa Score)
3. **Dados Contábeis**: Faça upload das demonstrações financeiras
4. **Cálculo**: Execute o algoritmo FinScore
5. **Análise**: Visualize resultados, gráficos e indicadores
6. **Parecer**: Obtenha relatório com análise financeira

### Navegação

O sistema libera seções progressivamente:

- **Lançamentos** disponível após clicar em "Iniciar"
- **Análise** e **Parecer** disponíveis após o cálculo do FinScore

## 📊 Dados de Entrada

Formatos aceitos:

- **Arquivo Excel (.xlsx)**: Upload de planilhas
- **Google Sheets**: Integração via link
- **Entrada Manual**: Digitação direta

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

Fernando Vieira (FV)
fernandovieira1@outlook.com
+5565992550087

- **Desenvolvimento**: FV
- **Algoritmos**: FV
- **Design**: FV

---

*FinScore - Transformando dados contábeis em inteligência financeira*
Beta Version 1.0.00 (Brigadeiro) (04/11/2025)
