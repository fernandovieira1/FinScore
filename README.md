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
