import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from utils.aws_queue_monitor import get_monitor_instance
from utils.config import AWSConfig


def show():
    st.title("📬 Monitoramento de Filas AWS SQS")

    monitor = get_monitor_instance()

    # Sidebar para configurações
    with st.sidebar:
        st.markdown("### ⚙️ Configurações AWS")

        # Verificar se há credenciais no .env
        has_env_credentials = AWSConfig.has_credentials()

        if has_env_credentials:
            st.success("✅ Credenciais carregadas do arquivo .env")
            use_env = st.checkbox("Usar credenciais do .env", value=True, help="Desmarque para inserir credenciais manualmente")
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
                ["Credenciais", "Profile", "IAM Role/Env Vars"]
            )

            if auth_method == "Credenciais":
                aws_access_key = st.text_input("AWS Access Key ID", type="password")
                aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
                aws_session_token = st.text_input("AWS Session Token (opcional)", type="password", help="Necessário para credenciais temporárias")
                profile_name = None
            elif auth_method == "Profile":
                profile_name = st.text_input("Profile Name", value="default")
                aws_access_key = None
                aws_secret_key = None
                aws_session_token = None
            else:
                aws_access_key = None
                aws_secret_key = None
                aws_session_token = None
                profile_name = None

        region = st.text_input("Região AWS", value=AWSConfig.get_region())

        # Opção para especificar filas
        monitor_all = st.checkbox("Monitorar todas as filas", value=True)

        queue_names = []
        if not monitor_all:
            queue_names_input = st.text_area(
                "Nomes das filas (uma por linha)",
                help="Digite os nomes das filas, uma por linha"
            )
            if queue_names_input:
                queue_names = [q.strip() for q in queue_names_input.split('\n') if q.strip()]

        update_interval = st.slider(
            "Intervalo de atualização (segundos)",
            min_value=10,
            max_value=300,
            value=30,
            step=10
        )

        st.markdown("---")

        # Botão para iniciar/parar monitoramento
        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ Iniciar", use_container_width=True):
                monitor.region_name = region
                monitor.queue_names = queue_names
                monitor.set_update_interval(update_interval)

                if monitor.initialize_client(aws_access_key, aws_secret_key, profile_name, aws_session_token):
                    monitor.start_monitoring()
                    st.success("Monitoramento iniciado!")
                    st.rerun()
                else:
                    st.error(f"Erro: {monitor.get_error_message()}")

        with col2:
            if st.button("⏹️ Parar", use_container_width=True):
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

        2. **Configure a região AWS** onde suas filas estão localizadas

        3. **Escolha quais filas monitorar:**
           - Marque "Monitorar todas as filas" para ver todas as filas da região
           - Desmarque para especificar filas específicas

        4. **Ajuste o intervalo de atualização** (recomendado: 30 segundos)

        5. **Clique em 'Iniciar'** para começar o monitoramento em tempo real
        """)

        return

    # Exibir erros se houver
    error = monitor.get_error_message()
    if error:
        st.error(f"⚠️ {error}")
        if st.button("Limpar erro"):
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

    # Filtro por prefixo
    st.markdown("### 🔍 Filtros")
    filter_prefix = st.text_input(
        "Filtrar filas por prefixo",
        value="",
        placeholder="Digite o prefixo da fila (ex: prod-, dev-)",
        help="Filtra as filas que começam com o prefixo especificado. Deixe vazio para ver todas."
    )

    st.markdown("---")

    # Obter dados das filas
    queue_data = monitor.get_queue_data()

    # Aplicar filtro por prefixo se especificado
    if filter_prefix:
        queue_data = {
            name: data
            for name, data in queue_data.items()
            if name.startswith(filter_prefix)
        }

    if not queue_data:
        st.warning("Nenhuma fila encontrada ou aguardando primeira atualização...")

        # Auto-refresh para atualizar quando os dados chegarem
        if monitor.monitoring:
            st.button("🔄 Atualizar", key="refresh_waiting")
            if st.session_state.get('refresh_waiting'):
                st.rerun()

        return

    # Calcular totais
    total_available = sum(q['messages_available'] for q in queue_data.values())
    total_in_flight = sum(q['messages_in_flight'] for q in queue_data.values())
    total_delayed = sum(q['messages_delayed'] for q in queue_data.values())
    total_messages = sum(q['total_messages'] for q in queue_data.values())

    # Métricas gerais
    st.markdown("### 📊 Visão Geral")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Mensagens", f"{total_messages:,}")

    with col2:
        st.metric("Mensagens Disponíveis", f"{total_available:,}")

    with col3:
        st.metric("Em Processamento", f"{total_in_flight:,}")

    with col4:
        st.metric("Atrasadas", f"{total_delayed:,}")

    st.markdown("---")

    # Tabela detalhada de filas
    st.markdown("### 📋 Detalhes das Filas")

    df_queues = pd.DataFrame([
        {
            'Fila': name,
            'Disponíveis': data['messages_available'],
            'Em Processamento': data['messages_in_flight'],
            'Atrasadas': data['messages_delayed'],
            'Total': data['total_messages']
        }
        for name, data in sorted(queue_data.items())
    ])

    # Estilizar tabela
    def highlight_rows(row):
        if row['Total'] > 1000:
            return ['background-color: #ffebee'] * len(row)
        elif row['Total'] > 500:
            return ['background-color: #fff3e0'] * len(row)
        else:
            return [''] * len(row)

    st.dataframe(
        df_queues.style.apply(highlight_rows, axis=1),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # Gráfico de barras - Status das mensagens (largura total)
    st.markdown("### 📊 Status das Mensagens")
    status_data = pd.DataFrame({
        'Status': ['Disponíveis', 'Em Processamento', 'Atrasadas'],
        'Quantidade': [total_available, total_in_flight, total_delayed]
    })

    fig_bar = px.bar(
        status_data,
        x='Status',
        y='Quantidade',
        title='',
        color='Status',
        color_discrete_map={
            'Disponíveis': '#2ecc71',
            'Em Processamento': '#f39c12',
            'Atrasadas': '#e74c3c'
        }
    )
    fig_bar.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Informações detalhadas expandíveis
    with st.expander("🔍 Informações Detalhadas"):
        for name, data in sorted(queue_data.items()):
            st.markdown(f"#### {name}")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Mensagens Disponíveis:** {data['messages_available']:,}")
                st.write(f"**Em Processamento:** {data['messages_in_flight']:,}")

            with col2:
                st.write(f"**Atrasadas:** {data['messages_delayed']:,}")
                st.write(f"**Total:** {data['total_messages']:,}")

            with col3:
                st.write(f"**URL:** `{data['url']}`")

            st.markdown("---")

    # Botão de refresh manual
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"*Atualização automática a cada {monitor.update_interval} segundos*")
    with col2:
        if st.button("🔄 Atualizar Agora", key="refresh_main", use_container_width=True):
            st.rerun()

    # Auto-refresh automático
    time.sleep(monitor.update_interval)
    st.rerun()
