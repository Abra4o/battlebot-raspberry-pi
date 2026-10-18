"""Teste do app.py com pinos simulados, uma conexão falsa no lugar do Bluetooth e o servidor Wi-Fi local."""
import os
import socket
import sys
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer

from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPWMPin

Device.pin_factory = MockFactory(pin_class=MockPWMPin)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app  # noqa: E402

pin = Device.pin_factory.pin
falhas = 0
V = round(app.VELOCIDADE, 2)         # 120/255 = 0.47
C = round(app.VELOCIDADE * 0.4, 2)   # roda de dentro na curva


def motores():
    esq = round(app.robo.left_motor.value, 2)
    dir_ = round(app.robo.right_motor.value, 2)
    return esq, dir_


def resultado(nome, ok, esperado, obtido):
    global falhas
    falhas += not ok
    print(f"{'OK  ' if ok else 'FALHA'} {nome:36} esperado={esperado} obtido={obtido}")


def checar(nome, esperado):
    obtido = motores()
    resultado(nome, obtido == esperado, esperado, obtido)


def checar_arma(nome, esperado):
    obtido = round(app.arma.angle)
    resultado(nome, obtido == esperado, esperado, obtido)


# Conexão falsa: o "celular" escreve num lado, o app lê no outro
celular, carro = socket.socketpair()
t = threading.Thread(target=app.atender, args=(carro,), daemon=True)
t.start()


def enviar(txt):
    celular.sendall(txt.encode())
    time.sleep(0.1)


print("-- app roboBT (letras do projeto Arduino) --")
checar_arma("arma começa em repouso (130°)", 130)
enviar("w")
checar("w = frente", (V, V))
enviar("s")
checar("s = ré", (-V, -V))
enviar("a")
checar("a = esquerda (gira no eixo)", (-V, V))
enviar("d")
checar("d = direita (gira no eixo)", (V, -V))
enviar("p")
checar("p = parar", (0.0, 0.0))
enviar("x")
checar_arma("x = ataque (180°)", 180)
enviar("w")
checar("andar não mexe na arma", (V, V))
checar_arma("arma continua em 180°", 180)
enviar("b")
checar_arma("b = recolhe (130°)", 130)
checar("arma não mexe no motor", (V, V))
enviar("p")

print("-- controle.html --")
enviar("F")
checar("F = frente", (V, V))
enviar("B")
checar("B = ré", (-V, -V))
enviar("L")
checar("L = esquerda", (-V, V))
enviar("R")
checar("R = direita", (V, -V))
enviar("G")
checar("G = curva frente-esquerda", (C, V))
enviar("I")
checar("I = curva frente-direita", (V, C))
enviar("H")
checar("H = ré-esquerda", (-C, -V))
enviar("J")
checar("J = ré-direita", (-V, -C))
enviar("F9q4\r\n")
checar("números e lixo ignorados", (V, V))
enviar("S")
checar("S = parar", (0.0, 0.0))

print("-- pinos --")
enviar("F")
ok = (round(pin(17).state, 2) == V and not pin(18).state and round(pin(22).state, 2) == V
      and not pin(23).state and pin(12).state == 1 and pin(13).state == 1)
resultado("L298N frente: IN1/IN3 PWM, IN2/IN4 0", ok, f"IN1=IN3={V}",
          f"IN1={pin(17).state:.2f} IN2={pin(18).state} IN3={pin(22).state:.2f} IN4={pin(23).state}")
enviar("x")
pulso = round(pin(app.PINO_ARMA).state * 20, 2)  # duty * período de 20 ms
resultado("servo 180° = pulso 2,5 ms", pulso == 2.5, 2.5, pulso)
enviar("b")
pulso = round(pin(app.PINO_ARMA).state * 20, 2)
resultado("servo 130° = pulso ~1,94 ms", pulso == 1.94, 1.94, pulso)

print("-- Wi-Fi --")
srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Controle)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}"


def post(txt):
    req = urllib.request.Request(url + "/cmd", data=txt.encode(), method="POST")
    with urllib.request.urlopen(req) as r:
        return r.status


pagina = urllib.request.urlopen(url + "/").read().decode()
resultado("GET / entrega o controle.html", "<title>Carrinho</title>" in pagina, "controle.html", pagina[:15])
resultado("POST /cmd responde 204", post("G") == 204, 204, "204" if motores() == (C, V) else "?")
checar("Wi-Fi: G = curva frente-esquerda", (C, V))
post("Sx")
checar("Wi-Fi: 'Sx' para", (0.0, 0.0))
checar_arma("Wi-Fi: 'Sx' ataca", 180)
post("b")
checar_arma("Wi-Fi: b recolhe", 130)
srv.shutdown()

print("-- segurança --")
enviar("x")
celular.close()
t.join(1)
checar("desconectou -> para", (0.0, 0.0))
checar_arma("desconectou -> recolhe arma", 130)

app.receber(b"I")
checar("receber: 'I' em bytes", (V, C))
app.receber(b"F"); app.parar()
checar("parar() -> para", (0.0, 0.0))

app.TIMEOUT_S = 0.3
threading.Thread(target=app.watchdog, daemon=True).start()
app.processar("F")
time.sleep(0.6)
checar("watchdog para sem comandos", (0.0, 0.0))
app.processar("x")
time.sleep(0.6)
checar_arma("watchdog recolhe a arma sem comandos", 130)

print("\nRESULTADO:", "TUDO OK" if falhas == 0 else f"{falhas} falha(s)")
sys.exit(1 if falhas else 0)
