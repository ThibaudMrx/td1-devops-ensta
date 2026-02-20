import streamlit as st
import pandas as pd

st.set_page_config(page_title="Enstartup", page_icon="🚀")
st.title("🚀 Enstartup Analytics")

def load_data():
    return pd.read_csv("data/sales.csv")

def display_metrics(data):
    total = data["amount"].sum()
    count = len(data)
    avg = total // count if count > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total ventes", f"{total} €")
    col2.metric("Panier moyen", f"{avg} €")
    col3.metric("Transactions", count)

def main():
    data = load_data()
    display_metrics(data)
    st.dataframe(data)

if __name__ == "__main__":
    main()
