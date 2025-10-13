# app_front/views/guia_rapido.py
import streamlit as st

def render():
    st.markdown("<h3 style='text-align: left;'>🔦 Conheça o FinScore</h3>", unsafe_allow_html=True)
    st.markdown(
        """
O FinScore é um índice que quantifica a saúde financeira de uma empresa, integrando dados contábeis para avaliar 
riscos e classificar clientes. 

Seus principais objetivos incluem fornecer uma visão objetiva da situação financeira, identificar pontos de 
atenção e apoiar decisões estratégicas.

O método permite uma análise rápida e padronizada, facilitando a avaliação patrimonial, financeira e econômica
dos clientes, o que auxilia na mitigação de riscos e contribui para a geração de pareceres técnicos fundamentados,
equilibrando otimização de oportunidades e segurança nas decisões de crédito.

### Seções disponíveis

O aplicativo é dividido em várias seções principais, acessíveis pelo menu superior (topbar **↑**) ou 
pela barra lateral (sidebar **←**).

No menu superior, que serve como navegação principal, você encontra:
* **"Página Inicial"**: retorna à página inicial do aplicativo.
* **"Estoque"**: informações sobre a base de dados contendo os processos e propostas cadastradas.
* **"Cadastros"**: registros dos cadastros de clientes, usuários e outros dados relevantes.
* **"Guia Rápido"**: este guia introdutório. 

De natureza operacional, a barra lateral permite o lançamento das informações dos clientes, a análise e a emissão de
pareceres técnicos, além de informações metodológicas e de suporte. 

Tudo isso é acessível através das seguintes opções:
* **"Processo"**: Menu suspenso (dropdown) com as subseções que perfazem o fluxo de trabalho:
    - **"Lançamentos"**: onde você insere os dados do cliente e as demonstrações contábeis.
    - **"Análise"**: resultados preliminares da análise financeira.
    - **"Parecer"**: geração/edição de um parecer em PDF.
* **"Sobre"**: informações mais aprofundadas sobre a metodologia, com glossário de termos e perguntas mais frequentes (FAQ).
* **"Contato"**: formulário para dúvidas/sugestões.

A seção **"Lançamentos"** fica disponível após clicar no botão **[Iniciar]**, na seção **"Novo"**. Igualmente, as 
seções **"Análise"** e **"Parecer"** ficam disponíveis após o cálculo do FinScore na seção **"Lançamentos"**.

Para maiores detalhes sobre a metodologia e a interpretação dos resultados, consulte o guia completo na seção **"Sobre"**.

Dúvidas ou sugestões? Utilize o formulário na seção **"Contato"**.
 """,
        unsafe_allow_html=True,
    )