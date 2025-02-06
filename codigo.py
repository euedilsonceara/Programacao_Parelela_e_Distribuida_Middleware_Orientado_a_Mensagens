import paho.mqtt.client as mqtt
import random
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

# Configuração do Broker MQTT
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_PREFIX = "sensor_network/"

equipamentos = []


def generate_sensor_value(equipamento):

    while equipamento["ligado"]:
        valor = int(random.uniform(equipamento["min"] * 0.9, equipamento["max"] * 1.1))
        equipamento["valor"] = valor

        if valor < equipamento["min"] or valor > equipamento["max"]:
            timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            mensagem = f"[{timestamp}] ALERTA! {equipamento['nome']} atingiu o valor crítico: {valor}"
                
            equipamento["client"].publish(equipamento["topic"], mensagem)  # Envia via MQTT
            equipamento["alarmes"].append(mensagem)  # Armazena localmente
                
        atualizar_interface()
        time.sleep(1)


def on_message(client, userdata, msg):
    for equipamento in equipamentos:
        if msg.topic == equipamento["topic"]:
            equipamento["alarmes"].append(msg.payload.decode())
            atualizar_interface()

def criar_equipamento(nome, parametro, minimo, maximo):
    topic = TOPIC_PREFIX + nome
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)
    client.subscribe(topic)
    client.on_message = on_message
    client.loop_start()
    
    equipamento = {
        "nome": nome,
        "parametro": parametro,
        "min": minimo,
        "max": maximo,
        "ligado": False,
        "valor": None,
        "topic": topic,
        "client": client,
        "alarmes": []
    }
    equipamentos.append(equipamento)
    atualizar_interface()

def ligar_equipamento(nome):
    for equipamento in equipamentos:
        if equipamento["nome"] == nome and not equipamento["ligado"]:
            equipamento["ligado"] = True
            thread = threading.Thread(target=generate_sensor_value, args=(equipamento,))
            thread.start()
            atualizar_interface()

def desligar_equipamento(nome):
    for equipamento in equipamentos:
        if equipamento["nome"] == nome:
            equipamento["ligado"] = False
            atualizar_interface()

def remover_equipamento(nome):
    for equipamento in equipamentos:
        if equipamento["nome"] == nome:
            equipamento["client"].disconnect()
            equipamentos.remove(equipamento)
            atualizar_interface()
            break


def atualizar_interface():
    listbox.delete(*listbox.get_children())
    for equipamento in equipamentos:
        status = "Ligado" if equipamento["ligado"] else "Desligado"
        valor = f"{equipamento['valor']}" if equipamento["valor"] else "-"
        listbox.insert("", "end", values=(equipamento["nome"], equipamento["parametro"], valor, status))
    
    listbox_alarmes.delete(*listbox_alarmes.get_children())
    for equipamento in equipamentos:
        for alarme in equipamento["alarmes"]:
            listbox_alarmes.insert("", "end", values=(equipamento["nome"], alarme))

def adicionar_equipamento():
    nome = entry_nome.get()
    parametro = combo_parametro.get()
    minimo = float(entry_min.get())
    maximo = float(entry_max.get())
    criar_equipamento(nome, parametro, minimo, maximo)

def toggle_equipamento():
    nome = entry_nome.get()
    for equipamento in equipamentos:
        if equipamento["nome"] == nome:
            if equipamento["ligado"]:
                desligar_equipamento(nome)
            else:
                ligar_equipamento(nome)

def remover_equipamento_interface():
    nome = entry_nome.get()
    remover_equipamento(nome)


# Interface gráfica
root = tk.Tk()
root.title("Gerenciador de Equipamentos")
root.geometry("1200x700")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Nome do Equipamento:").grid(row=0, column=0)
entry_nome = tk.Entry(frame)
entry_nome.grid(row=0, column=1)

tk.Label(frame, text="Parâmetro:").grid(row=1, column=0)
combo_parametro = ttk.Combobox(frame, values=["Temperatura", "Pressão", "Umidade", "Velocidade"])
combo_parametro.grid(row=1, column=1)
combo_parametro.current(0)

tk.Label(frame, text="Valor Mínimo:").grid(row=2, column=0)
entry_min = tk.Entry(frame)
entry_min.grid(row=2, column=1)

tk.Label(frame, text="Valor Máximo:").grid(row=3, column=0)
entry_max = tk.Entry(frame)
entry_max.grid(row=3, column=1)

btn_add = tk.Button(frame, text="Adicionar Equipamento", command=adicionar_equipamento)
btn_add.grid(row=4, column=0, columnspan=2, pady=5)

btn_toggle = tk.Button(frame, text="Ligar/Desligar", command=toggle_equipamento)
btn_toggle.grid(row=5, column=0, columnspan=2, pady=5)

btn_remove = tk.Button(frame, text="Remover Equipamento", command=remover_equipamento_interface)
btn_remove.grid(row=6, column=0, columnspan=2, pady=5)

listbox = ttk.Treeview(root, columns=("Nome", "Parâmetro", "Valor", "Status"), show="headings")

# Definir os títulos das colunas
listbox.heading("Nome", text="Nome", anchor="center")
listbox.heading("Parâmetro", text="Parâmetro", anchor="center")
listbox.heading("Valor", text="Valor", anchor="center")
listbox.heading("Status", text="Status", anchor="center")
# Centralizar o conteúdo das colunas
listbox.column("Nome", anchor="center")
listbox.column("Parâmetro", anchor="center")
listbox.column("Valor", anchor="center")
listbox.column("Status", anchor="center")
listbox.pack(fill="both", expand=True)


listbox_alarmes = ttk.Treeview(root, columns=("Nome", "Alarme"), show="headings")
listbox_alarmes.heading("Nome", text="Nome", anchor="center")
listbox_alarmes.heading("Alarme", text="Alarme", anchor="center")
listbox_alarmes.pack(fill="both", expand=True)

root.mainloop()