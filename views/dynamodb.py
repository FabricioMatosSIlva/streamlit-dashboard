import streamlit as st
import pandas as pd
from datetime import datetime
import time
from utils.dynamodb_monitor import get_dynamodb_monitor_instance
from utils.config import AWSConfig


def format_time_diff(seconds):
    """Format time difference in human readable format"""
    if seconds >= 0:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        seconds = abs(seconds)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"-{hours:02d}:{minutes:02d}:{secs:02d}"


def show():
    st.title("🗄️ Monitoramento DynamoDB - Work Pool")

    monitor = get_dynamodb_monitor_instance()

    # Sidebar para configurações
    with st.sidebar:
        st.markdown("### ⚙️ Configurações AWS")

        # Verificar se há credenciais no .env
        has_env_credentials = AWSConfig.has_credentials()

        if has_env_credentials:
            st.success("✅ Credenciais carregadas do arquivo .env")
            use_env = st.checkbox("Usar credenciais do .env", value=True, help="Desmarque para inserir credenciais manualmente", key="dynamodb_use_env")
        else:
            st.info("💡 Crie um arquivo .env para salvar suas credenciais")
            use_env = False

        if use_env and has_env_credentials:
            # Usar credenciais do .env
            if AWSConfig.get_profile():
                profile_name = AWSConfig.get_profile()
                aws_access_key = None
                aws_secret_key = None
                aws_session_token = None
            else:
                aws_access_key = AWSConfig.get_access_key_id()
                aws_secret_key = AWSConfig.get_secret_access_key()
                aws_session_token = AWSConfig.get_session_token() or None
                profile_name = None
        else:
            # Método de autenticação manual
            auth_method = st.radio(
                "Método de Autenticação",
                ["Credenciais", "Profile", "IAM Role/Env Vars"],
                key="dynamodb_auth_method"
            )

            if auth_method == "Credenciais":
                aws_access_key = st.text_input("AWS Access Key ID", type="password", key="dynamodb_access_key")
                aws_secret_key = st.text_input("AWS Secret Access Key", type="password", key="dynamodb_secret_key")
                aws_session_token = st.text_input("AWS Session Token (opcional)", type="password", help="Necessário para credenciais temporárias", key="dynamodb_session_token")
                profile_name = None
            elif auth_method == "Profile":
                profile_name = st.text_input("Profile Name", value="default", key="dynamodb_profile")
                aws_access_key = None
                aws_secret_key = None
                aws_session_token = None
            else:
                aws_access_key = None
                aws_secret_key = None
                aws_session_token = None
                profile_name = None

        region = st.text_input("Região AWS", value=AWSConfig.get_region(), key="dynamodb_region")
        table_name = st.text_input("Nome da Tabela", value=AWSConfig.get_dynamodb_table_name(), key="dynamodb_table")

        update_interval = st.slider(
            "Intervalo de atualização (segundos)",
            min_value=5,
            max_value=60,
            value=5,
            step=5,
            key="dynamodb_interval"
        )

        st.markdown("---")

        # Botão para iniciar/parar monitoramento
        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ Iniciar", use_container_width=True, key="dynamodb_start"):
                monitor.region_name = region
                monitor.table_name = table_name
                monitor.set_update_interval(update_interval)

                if monitor.initialize_client(aws_access_key, aws_secret_key, profile_name, aws_session_token):
                    monitor.start_monitoring()
                    st.success("Monitoramento iniciado!")
                    st.rerun()
                else:
                    st.error(f"Erro: {monitor.get_error_message()}")

        with col2:
            if st.button("⏹️ Parar", use_container_width=True, key="dynamodb_stop"):
                monitor.stop_monitoring()
                st.info("Monitoramento parado")
                st.rerun()

    # Área principal
    if not monitor.monitoring:
        st.info("👈 Configure as credenciais AWS na barra lateral e clique em 'Iniciar' para começar o monitoramento")

        # Instruções
        st.markdown("""
        ### Como usar:

        1. **Escolha o método de autenticação:**
           - **Credenciais**: Insira suas credenciais AWS diretamente
           - **Profile**: Use um profile configurado no ~/.aws/credentials
           - **IAM Role/Env Vars**: Use credenciais de variáveis de ambiente ou IAM role (em EC2/ECS)

        2. **Configure a região AWS** onde sua tabela está localizada

        3. **Informe o nome da tabela DynamoDB** a ser monitorada

        4. **Ajuste o intervalo de atualização** (recomendado: 5 segundos para monitorar expirações)

        5. **Clique em 'Iniciar'** para começar o monitoramento em tempo real

        ### Regras de Status:

        - 🟢 **Verde**: Item ainda não expirou (expires > tempo atual)
        - 🟡 **Amarelo**: Item expirado há menos de 10 segundos
        - 🔴 **Vermelho**: Item expirado há mais de 10 segundos
        """)

        return

    # Exibir erros se houver
    error = monitor.get_error_message()
    if error:
        st.error(f"⚠️ {error}")
        if st.button("Limpar erro", key="dynamodb_clear_error"):
            monitor.clear_error()
            st.rerun()

    # Informações do status
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Status", "🟢 Ativo" if monitor.monitoring else "🔴 Inativo")

    with col2:
        last_update = monitor.get_last_update()
        if last_update:
            st.metric("Última atualização", last_update.strftime("%H:%M:%S"))
        else:
            st.metric("Última atualização", "Aguardando...")

    with col3:
        st.metric("Intervalo", f"{monitor.update_interval}s")

    st.markdown("---")

    # Obter dados da tabela
    table_data = monitor.get_table_data()

    if not table_data:
        st.warning("Nenhum dado encontrado ou aguardando primeira atualização...")

        # Auto-refresh para atualizar quando os dados chegarem
        if monitor.monitoring:
            st.button("🔄 Atualizar", key="dynamodb_refresh_waiting")
            if st.session_state.get('dynamodb_refresh_waiting'):
                st.rerun()

        return

    # Calcular estatísticas
    total_items = len(table_data)
    active_items = len([item for item in table_data if item['status'] == 'active'])
    warning_items = len([item for item in table_data if item['status'] == 'warning'])
    expired_items = len([item for item in table_data if item['status'] == 'expired'])

    # Métricas gerais
    st.markdown("### 📊 Visão Geral")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Items", f"{total_items:,}")

    with col2:
        st.metric("🟢 Ativos", f"{active_items:,}")

    with col3:
        st.metric("🟡 Avisos", f"{warning_items:,}")

    with col4:
        st.metric("🔴 Expirados", f"{expired_items:,}")

    st.markdown("---")

    # Tabela com dados
    st.markdown("### 📋 Items da Tabela")

    # Preparar DataFrame
    df_data = []
    for item in table_data:
        status_icon = {
            'active': '🟢',
            'warning': '🟡',
            'expired': '🔴'
        }.get(item['status'], '⚪')

        df_data.append({
            'Status': status_icon,
            'Entidade': item['entity_name'],
            'UID': item['uid'][:20] + '...' if len(item['uid']) > 20 else item['uid'],
            'Expira em': format_time_diff(item['time_diff']),
            'Data/Hora Expiração': item['expires_formatted']
        })

    df = pd.DataFrame(df_data)

    # Estilizar tabela baseado no status
    def highlight_rows(row):
        if row['Status'] == '🔴':
            return ['background-color: #ffebee'] * len(row)
        elif row['Status'] == '🟡':
            return ['background-color: #fff3e0'] * len(row)
        elif row['Status'] == '🟢':
            return ['background-color: #e8f5e9'] * len(row)
        else:
            return [''] * len(row)

    st.dataframe(
        df.style.apply(highlight_rows, axis=1),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # Informações detalhadas expandíveis
    with st.expander("🔍 Informações Detalhadas"):
        for item in table_data:
            status_icon = {
                'active': '🟢 Ativo',
                'warning': '🟡 Aviso',
                'expired': '🔴 Expirado'
            }.get(item['status'], '⚪ Desconhecido')

            st.markdown(f"#### {item['entity_name']} - {status_icon}")
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**UID:** `{item['uid']}`")
                st.write(f"**Tempo até expirar:** {format_time_diff(item['time_diff'])}")

            with col2:
                st.write(f"**Data/Hora Expiração:** {item['expires_formatted']}")
                st.write(f"**Timestamp:** {item['expires']}")

            st.markdown("---")

    # Botão de refresh manual
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"*Atualização automática a cada {monitor.update_interval} segundos*")
    with col2:
        if st.button("🔄 Atualizar Agora", key="dynamodb_refresh_main", use_container_width=True):
            st.rerun()

    # Auto-refresh automático
    time.sleep(monitor.update_interval)
    st.rerun()
