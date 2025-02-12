import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import base64
import locale
import os
import json


# Carregar credenciais da variável de ambiente
firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS")
if firebase_credentials_json:
    cred_dict = json.loads(firebase_credentials_json)  # Converte a string JSON em um dicionário
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    raise ValueError("Variável de ambiente FIREBASE_CREDENTIALS não encontrada!")


# Função para hash da senha
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Função para cadastrar usuário
def register_user(username, password):
    users_ref = db.collection("users").document(username)
    if users_ref.get().exists:
        st.error("Usuário já existe!")
    else:
        users_ref.set({
            "password": hash_password(password),
            "balance": 100.0
        })
        st.success("Conta criada com sucesso! Faça login.")

# Função para autenticar usuário
def login_user(username, password):
    user = db.collection("users").document(username).get()
    if user.exists and user.to_dict()["password"] == hash_password(password):
        return user.to_dict()
    return None

# Função para obter saldo
def get_balance(username):
    user = db.collection("users").document(username).get()
    return user.to_dict().get("balance", 0) if user.exists else 0

# Função para realizar transferência
def transfer_money(sender, receiver, amount):
    sender_ref = db.collection("users").document(sender)
    receiver_ref = db.collection("users").document(receiver)

    sender_data = sender_ref.get().to_dict()
    receiver_data = receiver_ref.get().to_dict()

    if sender_data and receiver_data and sender_data["balance"] >= amount:
        sender_ref.update({"balance": sender_data["balance"] - amount})
        receiver_ref.update({"balance": receiver_data["balance"] + amount})
        db.collection("transactions").add({
            "sender": sender,
            "receiver": receiver,
            "amount": amount
        })
        st.success("Transferência realizada com sucesso!")
    else:
        st.error("Saldo insuficiente!")

# Interface Streamlit
st.set_page_config(page_title="Legacy Bank", page_icon="🏛️")

if "logged_in" not in st.session_state:
    st.title("Legacy Bank 🏛️")

    menu = ["Login", "Registrar"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Registrar":
        st.subheader("Criar Conta")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.button("Registrar"):
            register_user(username, password)

    elif choice == "Login":
        st.subheader("Login")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            user = login_user(username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Bem-vindo, {username}!")
            else:
                st.error("Usuário ou senha incorretos")

if "logged_in" in st.session_state:
    username = st.session_state["username"]
    st.subheader("Painel de Controle")
    balance = get_balance(username)
    st.write(f"**Saldo:** R$ {balance:.2f}")
