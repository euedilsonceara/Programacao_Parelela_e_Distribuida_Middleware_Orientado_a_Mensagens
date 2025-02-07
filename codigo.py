# CÓDIGO DESENVOLVIDO DURANTE A DISCIPLINA DE PROGRAMAÇÃO PARALELA E DISTRIBUÍDA (PPD)
# UNIVERSIDADE: INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DO CEARÁ (IFCE) - CAMPUS FORTALEZA
# CURSO: ENGENHARIA DA COMPUTAÇÃO
# DATA: 06/02/2025
# DENSENVOLVEDOR: JOSÉ EDILSON CEARÁ GOMES FILHO

# INSTRUÇÕES
# 1. EXECUTE O ARQUIVO codigo.py
# 2. INTERAJA COM OS CAMPOS DA INTERFACE DO GERENCIADOR DE EQUIPAMENTOS, INSERINDO/REMOVENDO OS SENSORES E DEFININDO SEUS PARÂMETROS DA FORMA QUE PREFERIR
# 3. NA PARTE CENTRAL DA TELA SERÁ MOSTRADO O SENSOR E O VALOR E SUA MEDIÇÃO
# 4. NA PARTE INFERIOR DA TELA SERÁ MOSTRADO O LOG COM REGISTRO DOS MOMENTOS EM QUE O SENSOR ULTRAPASSOU OS LIMITES MÁXIMO OU MÁNIMO DEFINIDOS COMO PARÂMETRO

##################################################################################################################

import paho.mqtt.client as mqtt
import random
import threading
import time
import tkinter as tk
from tkinter import ttk
import datetime

# Configuração do Broker MQTT
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_PREFIX = "sensor_network/"

equipamentos = []

# Dicionário para armazenar cores únicas por equipamento
cores_equipamentos = {}

# Lista de cores para os alertas
cores_disponiveis = ["#FFDDC1", "#C1FFD7", "#D1C1FF", "#FFC1E3", "#C1E3FF"]

def obter_cor_equipamento(nome):
    """Retorna uma cor para o equipamento, garantindo que cada um tenha uma cor única."""
    if nome not in cores_equipamentos:
        cor = cores_disponiveis[len(cores_equipamentos) % len(cores_disponiveis)]
        cores_equipamentos[nome] = cor
    return cores_equipamentos[nome]

def generate_sensor_value(equipamento):
    while equipamento["ligado"]:
        valor = int(random.uniform(equipamento["min"] * 0.9, equipamento["max"] * 1.1))
        equipamento["valor"] = valor

        if valor < equipamento["min"] or valor > equipamento["max"]:
            timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            mensagem = f"[{timestamp}] ALERTA! {equipamento['nome']} atingiu um valor crítico: {valor}"
            
            if mensagem not in equipamento["alarmes"]:
                equipamento["client"].publish(equipamento["topic"], mensagem)
                equipamento["alarmes"].append(mensagem)
                
        atualizar_interface()
        time.sleep(1)

def on_message(client, userdata, msg):
    for equipamento in equipamentos:
        if msg.topic == equipamento["topic"]:
            mensagem = msg.payload.decode()
            if mensagem not in equipamento["alarmes"]:
                equipamento["alarmes"].append(mensagem)
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
            equipamento["valor"] = None  # Reseta o valor ao desligar
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
        valor = f"{equipamento['valor']}" if equipamento["ligado"] else "-"
        listbox.insert("", "end", values=(equipamento["nome"], equipamento["parametro"], valor, status))

    listbox_alarmes.delete(*listbox_alarmes.get_children())
    for equipamento in equipamentos:
        cor_fundo = obter_cor_equipamento(equipamento["nome"])
        for alarme in reversed(equipamento["alarmes"]):  # Agora os mais recentes vêm primeiro
            listbox_alarmes.insert("", "end", values=(equipamento["nome"], alarme), tags=(equipamento["nome"],))
            listbox_alarmes.tag_configure(equipamento["nome"], background=cor_fundo)


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
listbox.heading("Nome", text="Nome", anchor="center")
listbox.heading("Parâmetro", text="Parâmetro", anchor="center")
listbox.heading("Valor", text="Valor", anchor="center")
listbox.heading("Status", text="Status", anchor="center")
listbox.column("Nome", anchor="center")
listbox.column("Parâmetro", anchor="center")
listbox.column("Valor", anchor="center")
listbox.column("Status", anchor="center")
listbox.pack(fill="both", expand=True)

# Criando a listbox de alarmes com tags
listbox_alarmes = ttk.Treeview(root, columns=("Nome", "Alarme"), show="headings")
listbox_alarmes.heading("Nome", text="Nome", anchor="center")
listbox_alarmes.heading("Alarme", text="Alarme", anchor="center")
listbox_alarmes.column("Nome", anchor="center")
listbox_alarmes.column("Alarme", anchor="center")
listbox_alarmes.pack(fill="both", expand=True)

root.mainloop()