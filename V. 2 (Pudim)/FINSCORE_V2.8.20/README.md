# FinScore — V. 2.8.20 (Pudim)

Aplicação Streamlit para análise econômico-patrimonial, cálculo do FinScore e elaboração de pareceres de crédito com trilha de evidências e governança.

## Conteúdo da entrega

```
FINSCORE_V2.8.20/
├── app.py                 # ponto de entrada: streamlit run app.py
├── app_front/             # aplicação, ativos, motor FinScore e serviços
│   └── config/openai.env.example # modelo local de configuração OpenAI
├── requirements.txt       # dependências fixadas para Python 3.12
├── notas_versao.md        # diferenças em relação à V.1 (Brigadeiro)
└── .streamlit/config.toml # tema da aplicação
```

A entrega contém um `app_front/finscore_auth.db` vazio, criado pela validação técnica, apenas com o esquema das tabelas e sem usuários, dossiês, sessões ou telemetria. Ele pode ser excluído antes do primeiro uso, caso se deseje que o aplicativo o recrie automaticamente. A chave OpenAI não acompanha a entrega.

## INSTALAÇÃO LOCAL (Desenvolvimento)

Use este método para desenvolvimento, testes ou execução em computador local. O projeto requer **Python 3.12** e conexão com a internet na primeira instalação das dependências.

### Windows (PowerShell)

```powershell
cd "C:\caminho\para\FINSCORE_V2.8.20"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Se o PowerShell impedir a ativação, execute uma única vez no perfil do usuário e abra um novo terminal:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Inicie o aplicativo pelo ponto de entrada da raiz:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\app.py
```

### macOS e Linux

Em distribuições Debian/Ubuntu, instale antes o Python, o módulo de ambientes virtuais e dependências usuais do Chromium:

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip
```

No macOS, instale o Python 3.12 pelo instalador oficial ou Homebrew (`brew install python@3.12`). Em seguida, nos dois sistemas:

```bash
cd /caminho/para/FINSCORE_V2.8.20
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m streamlit run app.py
```

Abra o endereço exibido no terminal, normalmente `http://localhost:8501`, e pressione `Ctrl+C` para encerrar. Para atualizar as dependências posteriormente, ative o mesmo ambiente e execute `python -m pip install -r requirements.txt --upgrade`.

## Configuração da OpenAI

Crie o arquivo local a partir do modelo e depois cole a chave **após** o sinal de igual:

```powershell
Copy-Item .\app_front\config\openai.env.example .\app_front\.env
```

Em macOS/Linux:

```bash
cp app_front/config/openai.env.example app_front/.env
```

Edite `app_front/.env`:

```env
OPENAI_API_KEY=cole_a_chave_aqui
```

Não envie esse arquivo por e-mail, Git ou ZIP destinado a terceiros. O recurso de parecer com IA só funciona após essa configuração; as demais partes do aplicativo podem ser iniciadas sem ela.

Opcionalmente, ajuste em `app_front/.env` os e-mails autorizados a deliberar:

```env
FINSCORE_AUTHORITY_EMAILS=gestor.credito@instituicao.com
FINSCORE_ADMIN_EMAILS=administrador@instituicao.com
```

## INSTALAÇÃO (Deploy em servidor Linux)

Estas instruções usam Ubuntu/Debian, diretório `/opt/finscore` e o usuário de serviço `finscore`. Ajuste domínio, firewall e política de backup à instituição.

### 1. Preparar o servidor

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip unzip nginx
sudo adduser --system --group --home /opt/finscore --no-create-home finscore
sudo mkdir -p /opt/finscore
```

Se utilizar UFW, libere SSH e HTTPS; a porta 8501 só precisa ser pública para acesso direto de teste:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
# Opcional para testes sem Nginx: sudo ufw allow 8501
```

### 2. Transferir e instalar a aplicação

Empacote o conteúdo da pasta `FINSCORE_V2.8.20` sem incluir `.venv`, bancos de dados reais ou a chave OpenAI. Transfira o ZIP ao servidor e execute:

```bash
sudo unzip /tmp/FINSCORE_V2.8.20.zip -d /tmp/finscore_temp
sudo cp -a /tmp/finscore_temp/FINSCORE_V2.8.20/. /opt/finscore/
sudo chown -R finscore:finscore /opt/finscore
sudo -u finscore python3.12 -m venv /opt/finscore/.venv
sudo -u finscore /opt/finscore/.venv/bin/python -m pip install --upgrade pip
sudo -u finscore /opt/finscore/.venv/bin/python -m pip install -r /opt/finscore/requirements.txt
sudo -u finscore /opt/finscore/.venv/bin/python -m playwright install chromium
```

Para um servidor sem internet, baixe previamente as rodas em uma máquina compatível: `python -m pip download -r requirements.txt -d wheels`. Inclua `wheels/` no ZIP e substitua a instalação por:

```bash
sudo -u finscore /opt/finscore/.venv/bin/python -m pip install --no-index --find-links /opt/finscore/wheels -r /opt/finscore/requirements.txt
```

### 3. Configurar segredos e alçadas

Crie o arquivo que não deve ir ao repositório nem ao ZIP de distribuição:

```bash
sudo -u finscore nano /opt/finscore/app_front/.env
```

Conteúdo mínimo:

```env
OPENAI_API_KEY=cole_a_chave_de_producao_aqui
FINSCORE_AUTHORITY_EMAILS=gestor.credito@instituicao.com
FINSCORE_ADMIN_EMAILS=administrador@instituicao.com
```

Restrinja a leitura do arquivo e faça uma inicialização manual antes de criar o serviço:

```bash
sudo chown finscore:finscore /opt/finscore/app_front/.env
sudo chmod 600 /opt/finscore/app_front/.env
sudo -u finscore /opt/finscore/.venv/bin/python -m streamlit run /opt/finscore/app.py --server.headless=true --server.address=127.0.0.1 --server.port=8501
```

Confirme a abertura e encerre com `Ctrl+C`.

### 4. Criar o serviço systemd

```bash
sudo tee /etc/systemd/system/finscore.service <<'EOF'
[Unit]
Description=FinScore Streamlit
After=network.target

[Service]
User=finscore
Group=finscore
WorkingDirectory=/opt/finscore
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/finscore/.venv/bin/python -m streamlit run /opt/finscore/app.py --server.headless=true --server.address=127.0.0.1 --server.port=8501 --server.fileWatcherType=none
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now finscore.service
sudo systemctl status finscore.service --no-pager
```

Logs do aplicativo:

```bash
sudo journalctl -u finscore.service -f
```

### 5. Publicar com Nginx e HTTPS

Crie `/etc/nginx/sites-available/finscore` e troque `seu-dominio.com` pelo domínio real:

```nginx
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
```

```bash
sudo ln -s /etc/nginx/sites-available/finscore /etc/nginx/sites-enabled/finscore
sudo nginx -t
sudo systemctl reload nginx
```

Para HTTPS, instale e execute o Certbot conforme a política de certificados da instituição. Não exponha a porta 8501 publicamente quando Nginx estiver em uso.

### 6. Atualizar uma instalação existente

Faça backup do banco e da configuração antes da atualização. Não sobrescreva `app_front/.env` nem `app_front/finscore_auth.db`.

```bash
sudo systemctl stop finscore.service
sudo cp -a /opt/finscore/app_front/finscore_auth.db /opt/finscore/finscore_auth.db.bak_$(date +%Y%m%d_%H%M%S)
sudo cp -a /opt/finscore/app_front/.env /opt/finscore/.env.bak_$(date +%Y%m%d_%H%M%S)
# Extraia a nova versão e copie somente código, ativos, requirements.txt e documentação.
sudo -u finscore /opt/finscore/.venv/bin/python -m pip install -r /opt/finscore/requirements.txt --upgrade
sudo systemctl start finscore.service
sudo systemctl status finscore.service --no-pager
```

## PDF

A exportação usa Playwright/Chromium, instalado nos procedimentos acima. Caso o navegador não possa ser instalado em ambiente restrito, o aplicativo mantém o mecanismo alternativo incluído nas dependências.

## Operação e segurança

- Faça backup periódico de `app_front/finscore_auth.db`; ele contém usuários, dossiês, manifestações, deliberações e telemetria local.
- Defina os e-mails de alçada antes de colocar o sistema em uso operacional.
- Antes da entrega final, revogue/rotacione toda chave que tenha sido usada durante desenvolvimento ou exposta em arquivos locais.
- Para produção, use um usuário de serviço sem privilégios, HTTPS/reverse proxy e backups fora do diretório da aplicação.

## Licença e contato

Software proprietário.

FinScore — Versão 2.8.20 (Pudim), outubro de 2026.
----------------------------------------------------

Modelo matemático e Aplicativo desenvolvido por FSV (fernandodvieira@usp.br)

Assertif - Todos os direitos reservados
