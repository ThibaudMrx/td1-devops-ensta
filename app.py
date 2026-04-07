import streamlit as st
import pandas as pd
import os
import hashlib

# --- Configuration ---
app_title = os.getenv("APP_TITLE", "ENStartup Analytics")

# --- Connexion Redis (optionnelle) ---
try:
    import redis
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
        socket_connect_timeout=2,
    )
    r.ping()
    visit_count = r.incr("visits")
    redis_available = True
except Exception:
    visit_count = None
    redis_available = False

# --- Infos replica Azure (pour l'exercice de scaling) ---
replica_name = os.getenv("CONTAINER_APP_REPLICA_NAME", "local")
color_hash = hashlib.md5(replica_name.encode()).hexdigest()[:6]
replica_color = f"#{color_hash}"

# --- Interface ---
st.set_page_config(page_title=app_title, page_icon="📊")
st.title(f"📊 {app_title}")

# Sidebar : indicateur de replica (couleur unique par instance)
st.sidebar.markdown(
    f'<div style="background-color: {replica_color}; padding: 15px; '
    f'border-radius: 10px; margin-bottom: 10px;">'
    f'<strong>🖥️ Replica</strong><br/>'
    f'<code style="font-size: 12px;">{replica_name[:20]}</code></div>',
    unsafe_allow_html=True,
)

if redis_available:
    st.sidebar.metric("Visites (Redis)", visit_count)
else:
    st.sidebar.caption("Redis non connecté — mode dégradé")

# Données
try:
    data = pd.read_csv("data/sales.csv")
    st.subheader("Données de ventes")
    st.dataframe(data)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total ventes", f"{data['amount'].sum():,.0f} €")
    with col2:
        st.metric("Transactions", len(data))

    st.bar_chart(data.set_index("date")["amount"])

except FileNotFoundError:
    st.warning("Fichier `data/sales.csv` non trouvé.")
    st.info("Ajoutez un fichier `data/sales.csv` avec des colonnes `date` et `amount`.")
