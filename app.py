"""
BattleBot controlado pelo celular - Raspberry Pi + L298N + servo (arma)
Versão para Raspberry Pi do projeto:
https://roboticapratica.com.br/projeto/battlebot-arduino.html

Modos de conexão:
  sudo python3 app.py           Wi-Fi: o celular abre http://<ip do Pi> no navegador
  sudo python3 app.py --uart    módulo HC-06 ligado no UART do Pi (app roboBT do projeto)
  sudo python3 app.py --serial  Bluetooth do próprio Pi, sem HC-06 (app roboBT do projeto)

Comandos (1 caractere cada):
  App roboBT:  w frente | s ré | a esquerda | d direita | p parar | x ataque | b recolhe arma
  controle.html: F B L R S + diagonais G/I (frente-esq/dir) e H/J (ré-esq/dir), x / b
A velocidade é fixa (VELOCIDADE).
"""
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from gpiozero import AngularServo, Motor, Robot

# ---- Pinos (BCM) do L298N ----
# Motor esquerdo (A): IN1, IN2, ENA | Motor direito (B): IN3, IN4, ENB
ESQ = dict(forward=17, backward=18, enable=12)
DIR = dict(forward=22, backward=23, enable=13)

# ---- Servo da arma ----
PINO_ARMA = 24
ARMA_REPOUSO = 130   # graus (igual ao projeto Arduino)
ARMA_ATAQUE = 180

# Velocidade fixa dos motores (0.0 a 1.0). O projeto Arduino usa 120 de 255.
VELOCIDADE = 120 / 255

# Wi-Fi: o Pi serve o controle.html e recebe os comandos em POST /cmd
PORTA_WIFI = 80
PAGINA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "controle.html")

CANAL_RFCOMM = 1
PORTA_UART = "/dev/serial0"
BAUD_UART = 9600     # padrão do HC-06

# Para o carrinho se ficar esse tempo sem receber comando (None = desativado).
# O controle.html repete o comando a cada 150 ms, então no modo Wi-Fi fica ativado.
# O app roboBT manda o comando só uma vez, então nos outros modos fica desativado.
TIMEOUT_S = None

robo = Robot(left=Motor(**ESQ), right=Motor(**DIR))
arma = AngularServo(PINO_ARMA, initial_angle=ARMA_REPOUSO, min_angle=0, max_angle=180,
                    min_pulse_width=0.0005, max_pulse_width=0.0025)

estado = {"cmd": "S", "arma": ARMA_REPOUSO, "ultimo": time.time()}
trava = threading.Lock()

# (esquerdo, direito) para cada comando, multiplicado pela velocidade
MOVIMENTOS = {
    "F": (1, 1),
    "B": (-1, -1),
    "L": (-1, 1),
    "R": (1, -1),
    "G": (0.4, 1),
    "I": (1, 0.4),
    "H": (-0.4, -1),
    "J": (-1, -0.4),
    "S": (0, 0),
}
# Letras do app roboBT (projeto Arduino) -> comandos acima
ROBOBT = {"w": "F", "s": "B", "a": "L", "d": "R", "p": "S"}
ARMA = {"x": ARMA_ATAQUE, "b": ARMA_REPOUSO}


def aplicar():
    esq, dir_ = MOVIMENTOS[estado["cmd"]]
    robo.value = (esq * VELOCIDADE, dir_ * VELOCIDADE)


def mover_arma(angulo):
    estado["arma"] = angulo
    arma.angle = angulo


def processar(c):
    """Trata um caractere recebido do celular."""
    c = ROBOBT.get(c, c)
    with trava:
        if c in ARMA:
            mover_arma(ARMA[c])
            estado["ultimo"] = time.time()
        elif c in MOVIMENTOS:
            estado["cmd"] = c
            estado["ultimo"] = time.time()
            aplicar()
        # outros caracteres (\r, \n, números...) são ignorados


def receber(dados):
    """Trata um bloco de bytes recebido do celular."""
    for c in bytes(dados).decode("ascii", "ignore"):
        processar(c)


def parar(*_):
    """Para os motores e recolhe a arma (usado ao desconectar)."""
    with trava:
        estado["cmd"] = "S"
        robo.stop()
        mover_arma(ARMA_REPOUSO)


def atender(conn):
    """Lê comandos de uma conexão serial até ela fechar."""
    try:
        while True:
            dados = conn.recv(64)
            if not dados:
                break
            receber(dados)
    except OSError:
        pass
    finally:
        parar()
        conn.close()


def watchdog():
    """Sem comando há TIMEOUT_S (Wi-Fi caiu, controle fechado): para e recolhe a arma."""
    while True:
        if (TIMEOUT_S is not None and time.time() - estado["ultimo"] > TIMEOUT_S
                and (estado["cmd"] != "S" or estado["arma"] != ARMA_REPOUSO)):
            parar()
        time.sleep(0.1)


class Controle(BaseHTTPRequestHandler):
    """Entrega o controle.html e recebe os comandos do celular pela rede Wi-Fi."""
    protocol_version = "HTTP/1.1"  # mantém a conexão aberta entre um comando e outro

    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/index.html", "/controle.html"):
            self.responder(404)
            return
        with open(PAGINA, "rb") as f:
            self.responder(200, f.read(), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/cmd":
            self.responder(404)
            return
        receber(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        self.responder(204)

    def responder(self, codigo, corpo=b"", tipo="text/plain"):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *_):
        pass  # não imprime cada comando


def rodar_wifi():
    srv = ThreadingHTTPServer(("", PORTA_WIFI), Controle)
    try:
        ips = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.split()
    except OSError:
        ips = []
    porta = "" if PORTA_WIFI == 80 else f":{PORTA_WIFI}"
    print("Controle no Wi-Fi. No celular, abra:")
    for ip in ips or ["<ip do Pi>"]:
        print(f"  http://{ip}{porta}")
    try:
        srv.serve_forever()
    finally:
        srv.server_close()


def rodar_serial():
    srv = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    srv.bind((socket.BDADDR_ANY, CANAL_RFCOMM))
    srv.listen(1)
    print(f"Aguardando conexão Bluetooth no canal {CANAL_RFCOMM}...")
    try:
        while True:
            conn, endereco = srv.accept()
            print("Conectado:", endereco[0])
            atender(conn)
            print("Desconectado")
    finally:
        srv.close()


def rodar_uart():
    import serial

    with serial.Serial(PORTA_UART, BAUD_UART, timeout=0.1) as porta:
        print(f"Lendo o HC-06 em {PORTA_UART} ({BAUD_UART} bps)...")
        while True:
            dados = porta.read(64)
            if dados:
                receber(dados)


def main():
    global TIMEOUT_S
    if "--uart" in sys.argv:
        rodar = rodar_uart
    elif "--serial" in sys.argv:
        rodar = rodar_serial
    else:
        rodar = rodar_wifi
        if TIMEOUT_S is None:
            TIMEOUT_S = 0.6
    threading.Thread(target=watchdog, daemon=True).start()
    try:
        rodar()
    except KeyboardInterrupt:
        pass
    finally:
        robo.stop()
        arma.angle = ARMA_REPOUSO
        time.sleep(0.3)


if __name__ == "__main__":
    main()
