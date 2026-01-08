import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Monitor AWS - SQS & DynamoDB",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
        .main {
            padding: 0rem 1rem;
        }
        .stMetric {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# Importar páginas
from views import queues, dynamodb

# Sidebar para navegação
with st.sidebar:
    st.title("📊 Monitor AWS")
    st.markdown("---")

    page = st.radio(
        "Navegação",
        ["📬 Filas SQS", "🗄️ DynamoDB Work Pool"]
    )

    st.markdown("---")

# Roteamento
if page == "📬 Filas SQS":
    queues.show()
elif page == "🗄️ DynamoDB Work Pool":
    dynamodb.show()
