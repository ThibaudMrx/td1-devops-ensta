import streamlit as st
import pandas as pd

st.set_page_config(page_title="Enstartup", page_icon="🚀")
st.title("🚀 Enstartup Analytics")

def load_data():
    return pd.read_csv("data/sales.csv")

def main():
    data = load_data()
    st.dataframe(data)

if __name__ == "__main__":
    main()
