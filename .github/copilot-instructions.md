# Copilot Instructions for FinScore

## Visão Geral
O FinScore é um sistema para quantificação de riscos e classificação de clientes, com interface web (Streamlit) e backend de processamento de dados contábeis. O projeto é composto por notebooks de prototipação, scripts de processamento e um app frontend modular.

## Estrutura Principal
- `app_front/`: Código principal do app Streamlit, dividido em views, componentes, serviços e utilitários.
  - `app.py`: Entry point do app.
  - `views/`: Cada arquivo representa uma seção/aba do app (ex: `novo.py`, `resumo.py`, `parecer.py`).
  - `components/`: Componentes reutilizáveis (ex: navegação, header, tema, state manager).
  - `services/`: Lógica de negócio e integração (ex: `finscore_service.py`, `io_validation.py`).
  - `styles/`: Customizações CSS para Streamlit.
  - `assets/`: Imagens, logos e arquivos de apoio.
- `finscore/`: Notebooks, scripts e dados de prototipação e cálculo do índice.
- `requirements.txt`: Dependências do app frontend.

## Padrões e Convenções
- Cada view/aba do app é um arquivo em `views/` e deve ser registrada na navegação (`components/nav.py`).
- O fluxo do usuário é guiado por navegação lateral (sidebar) e controle de estado centralizado (`components/state_manager.py`).
- Dados de entrada são validados em `services/io_validation.py`.
- O cálculo do índice e regras de negócio ficam em `services/finscore_service.py`.
- Customizações visuais devem ser feitas em `styles/main.css`.
- Novos componentes devem ser adicionados em `components/` e importados conforme necessário.

## Workflows de Desenvolvimento
- Para rodar o app: `streamlit run app_front/app.py`
- Debug: Use o modo DEBUG ativando a flag em `app.py` para exibir informações de navegação e estado.
- Testes e prototipação de regras: Use os notebooks em `finscore/`.
- Atualizações de dependências: Edite `requirements.txt` e sincronize ambientes.

## Integrações e Pontos de Atenção
- O parecer IA usa OpenAI/LangChain (ver exemplos em notebooks v9+ e TO_DO_APP_FS.txt para tarefas pendentes).
- O app depende de arquivos Excel para dados contábeis, localizados em `app_front/projeto/` e `finscore/BDs/`.
- Mudanças na navegação ou novas views exigem atualização em múltiplos arquivos (`nav.py`, `state_manager.py`, views).
- Siga os exemplos de navegação e controle de estado já implementados.

## Exemplos de Padrões
- Para adicionar uma nova view:
  1. Crie o arquivo em `views/`.
  2. Registre na navegação em `components/nav.py`.
  3. Importe e gerencie o estado em `state_manager.py`.
- Para adicionar lógica de negócio, use `services/` e evite lógica pesada nas views.

## Referências
- Mockups e histórico de mudanças: `app_front/projeto/`, `TO_DO_APP_FS.txt`.
- Prototipação e experimentos: `finscore/` (notebooks e scripts).

---
Adapte instruções conforme mudanças no fluxo do app ou arquitetura. Consulte sempre os arquivos de navegação e state manager para manter a consistência.