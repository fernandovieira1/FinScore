"""Contexto e diagnósticos auxiliares; não participa das notas do FinScore."""
from datetime import date, datetime
import re
import unicodedata

COMPANY_TYPES = (
    'Não informado', 'Indústria', 'Comércio', 'Serviços não financeiros',
    'Seguradora', 'Banco', 'Instituição financeira', 'Cooperativa de crédito',
    'Holding patrimonial', 'Outra entidade incompatível',
)
DEBT_SCOPE = ('Perímetro da dívida FinScore: empréstimos e financiamentos de curto prazo + '
              'empréstimos e financiamentos de longo prazo - caixa e equivalentes. '
              'Arrendamentos, mútuos e outras obrigações financeiras somente integram esta '
              'medida quando classificados nas rubricas de dívida previstas na entrada.')
DEBT_EXTENSION = {'habilitada': False, 'contas': ['divida_financeira_adicional', 'arrendamentos', 'mutuos_onerosos']}
STANDARD_RECOMMENDATION = ('A recomendação padrão FinScore é uma leitura quantitativa padronizada e permanece '
                           'sujeita à política de crédito e à decisão da alçada competente.')

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(value or '').casefold()) if not unicodedata.combining(c)).strip()

def springate_applicability(context=None):
    """Usa classificação estruturada; nunca deduz atividade pelo nome."""
    context=context or {}
    kind=normalize(context.get('tipo_empresa') or context.get('setor') or context.get('segmento'))
    cnae=re.sub(r'\D','',str(context.get('cnae') or ''))
    excluded={'seguradora','banco','instituicao financeira','cooperativa de credito','holding patrimonial','outra entidade incompativel'}
    if kind in excluded or (len(cnae)>=2 and cnae[:2] in {'64','65','66'}):
        return False, 'Não aplicável à classificação financeira, seguradora ou patrimonial informada; sua estrutura não é compatível com a calibração do índice.'
    if kind in {'industria','comercio','servicos','servicos comuns','servicos nao financeiros'}:
        return True, 'Aplicabilidade baseada no tipo de empresa declarado; diagnóstico complementar, sem efeito no score.'
    return False, 'Aplicabilidade não confirmada: informe o tipo de empresa. O setor não é inferido pelo nome ou por notas livres.'

def is_springate_applicable(company_context=None):
    return springate_applicability(company_context)[0]

def parse_date(value):
    if isinstance(value,datetime):return value.date()
    if isinstance(value,date):return value
    text=str(value or '').strip()
    for fmt in ('%d/%m/%Y','%Y-%m-%d'):
        try:return datetime.strptime(text,fmt).date()
        except ValueError:pass
    raise ValueError('Informe uma data de consulta válida em DD/MM/AAAA.')

def validate_serasa_date(value, analysis_date=None):
    parsed=parse_date(value)
    reference=parse_date(analysis_date) if analysis_date is not None else date.today()
    if parsed>reference:raise ValueError('A data da consulta ao Serasa não pode ser posterior à data da análise.')
    return parsed
