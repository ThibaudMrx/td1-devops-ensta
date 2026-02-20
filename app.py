import streamlit as st
import pandas as pd

st.set_page_config(page_title="Enstartup", page_icon="🚀")
st.title("🚀 Enstartup Analytics")

def load_data():
    return pd.read_csv("data/sales.csv")

def display_metrics(data):
    total = data["amount"].sum()
    count = len(data)
    avg = total // int(count)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total ventes", f"{total} €")
    col2.metric("Panier moyen", f"{avg} €")
    col3.metric("Transactions", count)

def main():
    data = load_data()
    
    products = data["product"].unique().tolist()
    selected = st.multiselect("Filtrer par produit", products, default=products)
    filtered = data[data["product"].isin(selected)]
    
    display_metrics(filtered)
    
    st.subheader("Données")
    st.dataframe(filtered)
    
    st.sidebar.title("Détail transaction")
    row_index = st.sidebar.number_input("Numéro de ligne", min_value=1, max_value=100, value=1)
    if st.sidebar.button("Voir détail"):
        row = filtered.iloc[row_index]
        st.sidebar.write(f"Produit: {row['product']}")
        st.sidebar.write(f"Montant: {row['amount']} €")

if __name__ == "__main__":
    main()
