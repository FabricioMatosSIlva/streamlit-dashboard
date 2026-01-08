# 🚀 Setup do Monitor AWS

## Configuração das Credenciais AWS

Para não precisar inserir suas credenciais manualmente toda vez, siga estes passos:

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Criar arquivo `.env`

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

### 3. Editar o arquivo `.env`

Abra o arquivo `.env` e preencha com suas credenciais AWS:

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_SESSION_TOKEN=seu_session_token_aqui_se_necessario

# AWS Region
AWS_REGION=eu-west-1

# DynamoDB Table Name
DYNAMODB_TABLE_NAME=dcxstg-dev-converter-work-pool
```

**Importante:** O arquivo `.env` está no `.gitignore` e não será commitado no Git, mantendo suas credenciais seguras.

### 4. Executar a aplicação

```bash
streamlit run app.py
```

## Como funciona

- **Com arquivo `.env`**: As credenciais são carregadas automaticamente e você verá a mensagem "✅ Credenciais carregadas do arquivo .env"
- **Sem arquivo `.env`**: Você pode inserir as credenciais manualmente através da interface

## Opções de Autenticação

### Opção 1: Credenciais diretas (arquivo `.env`)
```env
AWS_ACCESS_KEY_ID=sua_key
AWS_SECRET_ACCESS_KEY=sua_secret
AWS_SESSION_TOKEN=seu_token (opcional)
AWS_REGION=eu-west-1
```

### Opção 2: AWS Profile (arquivo `.env`)
```env
AWS_PROFILE=default
AWS_REGION=eu-west-1
```

### Opção 3: Manual
Deixe o `.env` vazio ou desmarque "Usar credenciais do .env" e insira manualmente na interface.

## Estrutura do Projeto

```
streamlit-dashboard/
├── .env                    # Suas credenciais (NÃO commitar!)
├── .env.example            # Exemplo de configuração
├── app.py                  # Aplicação principal
├── utils/
│   ├── config.py          # Carregamento das configurações
│   ├── aws_queue_monitor.py
│   └── dynamodb_monitor.py
├── views/
│   ├── queues.py          # Monitor de Filas SQS
│   └── dynamodb.py        # Monitor DynamoDB
└── requirements.txt
```

## Funcionalidades

### 📬 Filas SQS
- Monitoramento em tempo real de filas AWS SQS
- Auto-refresh configurável
- Filtro por prefixo de fila
- Métricas e gráficos

### 🗄️ DynamoDB Work Pool
- Monitoramento de tabela DynamoDB
- Status de expiração com cores:
  - 🟢 Verde: Item não expirou
  - 🟡 Amarelo: Expirado há menos de 10s
  - 🔴 Vermelho: Expirado há mais de 10s
- Formato de tempo legível (HH:MM:SS)

## Suporte

Para problemas ou dúvidas, verifique:
- Se o arquivo `.env` está na raiz do projeto
- Se as credenciais AWS estão corretas
- Se você instalou todas as dependências do `requirements.txt`
