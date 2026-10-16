"""
Simulador visual do carrinho para rodar no PC (sem Raspberry Pi).
Usa a mesma lógica do app.py, com os pinos simulados.
Controle: botões na tela ou setas do teclado (combine para diagonais). Velocidade fixa.
Rode:  python simulador_pc.py
"""
import math
import os
import sys
import time
import tkinter as tk

from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPWMPin

Device.pin_factory = MockFactory(pin_class=MockPWMPin)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app  # noqa: E402

LARG, ALT = 640, 480
VEL_MAX = 300      # px/s com motor a 100%
BITOLA = 120       # distância efetiva entre as rodas (px) - maior = gira mais devagar
FPS = 60

WASD = {"w": "Up", "s": "Down", "a": "Left", "d": "Right"}
NOMES = {"F": "frente", "B": "trás", "L": "esquerda", "R": "direita", "S": "parado",
         "G": "frente-esq", "I": "frente-dir", "H": "trás-esq", "J": "trás-dir"}


class Simulador:
    def __init__(self, raiz):
        self.raiz = raiz
        raiz.title("Simulador do BattleBot")
        raiz.configure(bg="#1e1e1e")

        self.x, self.y, self.ang = LARG / 2, ALT / 2, -math.pi / 2
        self.rastro = []
        self.teclas = set()

        self.canvas = tk.Canvas(raiz, width=LARG, height=ALT, bg="#2b2b2b", highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=10, pady=10)
        for i in range(0, LARG, 40):
            self.canvas.create_line(i, 0, i, ALT, fill="#333")
        for j in range(0, ALT, 40):
            self.canvas.create_line(0, j, LARG, j, fill="#333")

        painel = tk.Frame(raiz, bg="#1e1e1e")
        painel.grid(row=0, column=1, padx=10, sticky="n")
        estilo = dict(width=4, height=2, font=("Segoe UI", 14), bg="#3a3a3a", fg="white",
                      activebackground="#2e7d32", relief="flat")
        grade = tk.Frame(painel, bg="#1e1e1e")
        grade.pack(pady=(20, 10))
        botoes = [("↖", "G", 0, 0), ("▲", "F", 0, 1), ("↗", "I", 0, 2),
                  ("◀", "L", 1, 0), ("■", "S", 1, 1), ("▶", "R", 1, 2),
                  ("↙", "H", 2, 0), ("▼", "B", 2, 1), ("↘", "J", 2, 2)]
        for txt, c, r, col in botoes:
            b = tk.Button(grade, text=txt, **estilo)
            if c == "S":
                b.configure(bg="#b71c1c")
            b.grid(row=r, column=col, padx=3, pady=3)
            b.bind("<ButtonPress-1>", lambda e, c=c: self.enviar(c))
            b.bind("<ButtonRelease-1>", lambda e: self.enviar("S"))

        ataque = tk.Button(painel, text="⚔ ATAQUE (espaço)", font=("Segoe UI", 12, "bold"),
                           bg="#4e1a0c", fg="white", activebackground="#e64a19", relief="flat")
        ataque.pack(fill="x", pady=(5, 0))
        ataque.bind("<ButtonPress-1>", lambda e: self.enviar("x"))
        ataque.bind("<ButtonRelease-1>", lambda e: self.enviar("b"))

        self.info = tk.Label(painel, justify="left", font=("Consolas", 11),
                             bg="#1e1e1e", fg="#ddd")
        self.info.pack(pady=15, anchor="w")
        tk.Button(painel, text="Recentralizar", command=self.centralizar,
                  bg="#3a3a3a", fg="white", relief="flat").pack(fill="x")
        tk.Label(painel, text="Setas ou WASD = mover (combine p/ diagonal)\nEspaço = ataque",
                 bg="#1e1e1e", fg="#888", justify="left").pack(pady=10, anchor="w")

        raiz.bind("<KeyPress>", self.tecla_desce)
        raiz.bind("<KeyRelease>", self.tecla_sobe)
        self.ultima = ""
        self.t_ant = time.perf_counter()
        self.passo()

    # ---- comandos: passam pela mesma função do app.py ----
    def enviar(self, c):
        self.ultima = c
        app.processar(c)

    def tecla_desce(self, e):
        k = WASD.get(e.keysym.lower(), e.keysym)
        if k == "space":
            if app.estado["arma"] != app.ARMA_ATAQUE:
                self.enviar("x")
        elif k in ("Up", "Down", "Left", "Right") and k not in self.teclas:
            self.teclas.add(k)
            self.enviar(self.comando_teclas())

    def tecla_sobe(self, e):
        k = WASD.get(e.keysym.lower(), e.keysym)
        if k == "space":
            self.enviar("b")
        elif k in self.teclas:
            self.teclas.discard(k)
            self.enviar(self.comando_teclas())

    def comando_teclas(self):
        t = self.teclas
        cima, baixo = "Up" in t, "Down" in t
        esq, dir_ = "Left" in t, "Right" in t
        if cima and esq: return "G"
        if cima and dir_: return "I"
        if baixo and esq: return "H"
        if baixo and dir_: return "J"
        if cima: return "F"
        if baixo: return "B"
        if esq: return "L"
        if dir_: return "R"
        return "S"

    def centralizar(self):
        self.x, self.y, self.ang = LARG / 2, ALT / 2, -math.pi / 2
        self.rastro.clear()

    # ---- física e desenho ----
    def passo(self):
        agora = time.perf_counter()
        dt = min(agora - self.t_ant, 0.1)
        self.t_ant = agora
        ve = app.robo.left_motor.value
        vd = app.robo.right_motor.value
        v = (ve + vd) / 2 * VEL_MAX
        w = (ve - vd) / BITOLA * VEL_MAX  # positivo = gira p/ direita (tela tem y p/ baixo)
        self.ang += w * dt
        self.x = min(max(self.x + v * math.cos(self.ang) * dt, 20), LARG - 20)
        self.y = min(max(self.y + v * math.sin(self.ang) * dt, 20), ALT - 20)
        if v or w:
            self.rastro.append((self.x, self.y))
            self.rastro = self.rastro[-400:]
        self.desenhar(ve, vd)
        self.raiz.after(1000 // FPS, self.passo)

    def desenhar(self, ve, vd):
        c = self.canvas
        c.delete("carro")
        if len(self.rastro) > 1:
            c.create_line(*[p for xy in self.rastro for p in xy], fill="#4caf50", width=2, tags="carro")

        cos, sin = math.cos(self.ang), math.sin(self.ang)

        def pt(fx, lx):  # fx = para frente, lx = para a esquerda
            return self.x + fx * cos + lx * sin, self.y + fx * sin - lx * cos

        corpo = [pt(25, 18), pt(25, -18), pt(-25, -18), pt(-25, 18)]
        c.create_polygon(*[p for xy in corpo for p in xy], fill="#1976d2", outline="white", tags="carro")
        for lado, val in ((1, ve), (-1, vd)):
            roda = [pt(12, lado * 24), pt(12, lado * 18), pt(-12, lado * 18), pt(-12, lado * 24)]
            cor = "#4caf50" if val > 0 else "#f44336" if val < 0 else "#111"
            c.create_polygon(*[p for xy in roda for p in xy], fill=cor, tags="carro")
        c.create_line(*pt(0, 0), *pt(35, 0), fill="yellow", width=3, arrow="last", tags="carro")

        # Arma (servo): recolhida = haste curta em pé; ataque = haste batendo à frente
        atacando = app.estado["arma"] == app.ARMA_ATAQUE
        ponta = pt(48, 0) if atacando else pt(22, 0)
        c.create_line(*pt(18, 0), *ponta, fill="#ff7043", width=7 if atacando else 5,
                      capstyle="round", tags="carro")
        if atacando:
            c.create_oval(ponta[0] - 9, ponta[1] - 9, ponta[0] + 9, ponta[1] + 9,
                          outline="#ffab91", width=2, tags="carro")

        pin = Device.pin_factory.pin
        self.info.configure(text=(
            f"Comando : {app.estado['cmd']} ({NOMES[app.estado['cmd']]})\n"
            f"Arma    : {app.estado['arma']}° ({'ATAQUE' if atacando else 'recolhida'})\n"
            f"Velocid.: {app.VELOCIDADE * 100:.0f}% (fixa)\n"
            f"Última  : {self.ultima!r}\n\n"
            f"Motor E : {ve:+.2f}\n"
            f"Motor D : {vd:+.2f}\n\n"
            f"IN1 {pin(17).state:.2f}  IN2 {pin(18).state:.2f}\n"
            f"IN3 {pin(22).state:.2f}  IN4 {pin(23).state:.2f}\n"
            f"ENA {pin(12).state:.0f}     ENB {pin(13).state:.0f}"))


if __name__ == "__main__":
    raiz = tk.Tk()
    Simulador(raiz)
    raiz.mainloop()
