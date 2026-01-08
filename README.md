# Dashboard Streamlit

Dashboard interativo desenvolvido com Streamlit para visualização de dados e métricas.

## Estrutura do Projeto

```
streamlit-dashboard/
├── app.py                      # Arquivo principal da aplicação
├── pages/                      # Páginas do dashboard
│   ├── __init__.py
│   ├── home.py                # Página inicial
│   ├── analytics.py           # Página de analytics
│   ├── reports.py             # Página de relatórios
│   └── settings.py            # Página de configurações
├── utils/                      # Utilitários
│   ├── __init__.py
│   ├── data_loader.py         # Funções para carregar dados
│   └── charts.py              # Funções para criar gráficos
├── .streamlit/
│   └── config.toml            # Configurações do Streamlit
├── requirements.txt           # Dependências do projeto
└── README.md                  # Este arquivo
```

## Funcionalidades

- 🏠 **Home**: Visão geral com métricas principais e gráficos resumidos
- 📈 **Analytics**: Análises detalhadas com filtros e visualizações avançadas
- 📄 **Relatórios**: Geração e exportação de relatórios em CSV/Excel
- ⚙️ **Configurações**: Personalização de aparência, notificações e perfil

## Instalação

1. Clone o repositório ou navegue até a pasta do projeto

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Como Executar

Execute o dashboard com o comando:

```bash
streamlit run app.py
```

O dashboard será aberto automaticamente no navegador em `http://localhost:8501`

## Personalização

### Adicionar Nova Página

1. Crie um novo arquivo em `pages/`, exemplo: `pages/nova_pagina.py`
2. Implemente a função `show()`:
```python
import streamlit as st

def show():
    st.title("Nova Página")
    st.write("Conteúdo da página")
```
3. Importe e adicione no `app.py`

### Modificar Tema

Edite o arquivo `.streamlit/config.toml` para alterar cores e aparência

### Conectar Dados Reais

Modifique as funções em `utils/data_loader.py` para carregar dados de:
- Bancos de dados (PostgreSQL, MySQL, MongoDB)
- APIs
- Arquivos (CSV, Excel, JSON)
- Data warehouses

## Tecnologias

- **Streamlit**: Framework principal
- **Pandas**: Manipulação de dados
- **Plotly**: Gráficos interativos
- **NumPy**: Operações numéricas

## Próximos Passos

- [ ] Conectar a fonte de dados real
- [ ] Adicionar autenticação de usuários
- [ ] Implementar cache para melhor performance
- [ ] Adicionar mais tipos de visualizações
- [ ] Criar testes automatizados
