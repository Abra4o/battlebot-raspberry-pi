# BattleBot com Raspberry Pi

Versão para Raspberry Pi do projeto
[BattleBot Arduino (Robótica Prática)](https://roboticapratica.com.br/projeto/battlebot-arduino.html):
mesma ponte H L298N, mesmo servo de ataque, mesma velocidade e as mesmas letras do app roboBT.

## Arquivos
| Arquivo | Para quê |
|---------|----------|
| `app.py` | Roda no Raspberry Pi: recebe os comandos por Bluetooth, move os motores e o servo |
| `controle.html` | Controle do celular (Chrome no Android, via Bluetooth BLE) |
| `simulador_pc.py` | Visual no PC: o robô anda e ataca na tela, sem precisar do Pi |
| `teste_pc.py` | Teste automático da lógica no PC |
| `abrir_controle_demo.bat` | Abre o controle do celular no PC, em modo demonstração |

**Passo a passo:** [💻 PC](#-passo-a-passo-no-pc-windows) · [📱 Celular](#-passo-a-passo-no-celular-android) · [🍓 Raspberry Pi](#-raspberry-pi-instalar)

---

## 💻 Passo a passo no PC (Windows)

No PC dá para ver o robô andando, testar o controle e rodar os testes, **sem o Raspberry Pi**.

### 1. Instalar o Python (só na primeira vez)
1. Baixe em https://www.python.org/downloads/ (3.10 ou mais novo).
2. Na instalação, marque **"Add python.exe to PATH"**.
3. Confira no PowerShell: `python --version`

### 2. Baixar o projeto
Com o Git:
```powershell
gh repo clone Abra4o/battlebot-raspberry-pi
cd battlebot-raspberry-pi
```
Ou no GitHub: botão verde **Code → Download ZIP**, extraia e abra o PowerShell dentro da pasta
(na pasta, clique com o botão direito → **Abrir no Terminal**).

### 3. Criar o ambiente e instalar a biblioteca (só na primeira vez)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install gpiozero
```
Se der erro de "execução de scripts desabilitada", rode uma vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e ative de novo.
Quando ativado, aparece `(venv)` no começo da linha.

### 4. Rodar
Sempre ative o ambiente antes: `.\venv\Scripts\Activate.ps1`

| O que | Comando | Como usar |
|-------|---------|-----------|
| Simulador (robô na tela) | `python simulador_pc.py` | Setas ou WASD movem (duas juntas = curva), **espaço** = ataque |
| Testes automáticos | `python teste_pc.py` | Tem que terminar com `RESULTADO: TUDO OK` |
| Controle do celular no PC | dois cliques em `abrir_controle_demo.bat` | Clique nos botões ou use setas/espaço; aparece a letra enviada |

Dica: no controle aberto no Chrome, aperte **F12** e depois **Ctrl+Shift+M** para ver no tamanho de celular.

---

## 📱 Passo a passo no celular (Android)

Escolha **um** dos dois apps. iPhone não funciona com nenhum dos dois.

### Opção A: app roboBT (o app do projeto original)
Use com o Pi rodando `--uart` (HC-06) ou `--serial` (Bluetooth do Pi).
1. Baixe o APK **roboBT** indicado na
   [página do projeto](https://roboticapratica.com.br/projeto/battlebot-arduino.html).
2. Abra o APK e permita **"Instalar apps desconhecidos"** quando o Android pedir.
3. Ligue o robô e rode o `app.py` no Pi (veja [Raspberry Pi: rodar](#-raspberry-pi-rodar)).
4. No celular: **Configurações → Bluetooth → Parear novo dispositivo**:
   - modo `--uart`: escolha **HC-06** (senha **1234**);
   - modo `--serial`: escolha o **Raspberry Pi** (`raspberrypi`) e confirme o código nos dois lados.
5. Abra o roboBT, conecte no dispositivo pareado e dirija.

### Opção B: controle novo (`controle.html`), sem instalar nada
Use com o Pi rodando `sudo python3 app.py` (modo BLE).
1. **Colocar o controle na internet** (só uma vez). O Chrome só libera Bluetooth em página https:
   1. No PC, copie o `controle.html` para uma pasta nova e renomeie a cópia para `index.html`.
   2. Entre em https://app.netlify.com/drop (é grátis) e arraste essa pasta.
   3. Ele gera um link `https://...netlify.app`. Guarde esse link.
2. No celular, ative **Bluetooth** e **Localização**.
3. Abra o link no **Chrome**.
4. Menu **⋮ → Adicionar à tela inicial**. Vira um ícone, como um app.
5. Ligue o robô e rode `sudo python3 app.py` no Pi.
6. Abra o ícone → **Conectar via Bluetooth** → escolha **Carrinho** → **Parear**.
7. A tela fica cheia e deitada. Dirija:
   - polegar esquerdo **▲ / ▼**, polegar direito **◀ ▶** (juntos = curva andando);
   - **⚔ ATAQUE** no meio: segurou = ataca, soltou = recolhe;
   - soltou as setas, desconectou ou saiu do app = o robô para.

Para testar só a tela no celular, sem o robô, abra o link com `?demo` no final
(ex.: `https://seu-site.netlify.app/?demo`).

---

## Ligações: Arduino → Raspberry Pi (numeração BCM)

**O Pi trabalha com 3,3 V nos pinos.** Nunca ligue 5 V direto num GPIO.

| L298N / peça | Arduino (projeto) | Raspberry Pi |
|--------------|-------------------|--------------|
| ENA (motor esquerdo) | D11 | GPIO12 (pino 32) — tire o jumper do ENA |
| IN1 | D9 | GPIO17 (pino 11) |
| IN2 | D8 | GPIO18 (pino 12) |
| ENB (motor direito) | D5 | GPIO13 (pino 33) — tire o jumper do ENB |
| IN3 | D7 | GPIO22 (pino 15) |
| IN4 | D6 | GPIO23 (pino 16) |
| Servo (sinal, fio laranja) | D10 | GPIO24 (pino 18) |
| Servo (+ vermelho / − marrom) | 5V / GND | 5 V **externo** (ou 5V do L298N) / GND |
| GND do L298N | GND | GND (pino 6) — **obrigatório ligar o GND junto** |

- Motor esquerdo em OUT1/OUT2, direito em OUT3/OUT4. Pilhas no 12V/GND do L298N.
- **Não** alimente motores nem servo pelo 5V do Pi (ele reinicia quando o servo puxa corrente).
- Os sinais de 3,3 V do Pi funcionam no L298N e no servo.

### Bluetooth: escolha um
**A) Usar o HC-06 do projeto** (o app roboBT do projeto funciona igual):

| HC-06 | Raspberry Pi |
|-------|--------------|
| VCC | 5V (pino 2) |
| GND | GND (pino 14) |
| TXD | GPIO15 / RXD (pino 10) |
| RXD | GPIO14 / TXD (pino 8) |

Ative o UART: `sudo raspi-config` → Interface Options → Serial Port →
*login shell*: **Não**, *hardware serial*: **Sim** → reinicie.

**B) Sem HC-06**: usar o Bluetooth que já vem no Pi (3, 4, 5, Zero W).

---

## 🍓 Raspberry Pi: instalar
```bash
gh auth login                                  # só na primeira vez (repositório privado)
gh repo clone Abra4o/battlebot-raspberry-pi
cd battlebot-raspberry-pi
sudo apt update
sudo apt install -y python3-gpiozero python3-serial python3-dbus python3-gi bluez pigpio python3-pigpio
sudo systemctl enable --now pigpiod
sudo pip3 install bluezero --break-system-packages
```
O `pigpio` deixa o servo firme (sem tremer). Para usar, rode com
`sudo GPIOZERO_PIN_FACTORY=pigpio python3 app.py ...`.

## 🍓 Raspberry Pi: rodar
Escolha o modo de acordo com o app do celular:

| Modo | Comando | Celular |
|------|---------|---------|
| HC-06 ligado no Pi | `sudo python3 app.py --uart` | App **roboBT** do projeto (pareie com "HC-06", PIN 1234) |
| Bluetooth do Pi + app do projeto | `sudo python3 app.py --serial` | App **roboBT**, pareado com o Raspberry Pi |
| Bluetooth do Pi + controle novo | `sudo python3 app.py` | `controle.html` no Chrome |

**Modo `--serial`** precisa preparar o Bluetooth do Pi uma vez:
```bash
sudo sed -i 's|^ExecStart=.*bluetoothd$|& -C|' /lib/systemd/system/bluetooth.service
sudo systemctl daemon-reload && sudo systemctl restart bluetooth
sudo sdptool add SP
```

**Modo BLE (controle.html)**: se der erro de anúncio, ative o modo experimental do BlueZ:
```bash
sudo sed -i 's|^ExecStart=.*bluetoothd.*|& --experimental|' /lib/systemd/system/bluetooth.service
sudo systemctl daemon-reload && sudo systemctl restart bluetooth
```

## Comandos (1 caractere cada)
| App roboBT | controle.html | Ação |
|-----------|---------------|------|
| `w` | `F` | frente |
| `s` | `B` | ré |
| `a` | `L` | gira à esquerda |
| `d` | `R` | gira à direita |
| `p` | `S` | parar |
| — | `G` / `I` | curva frente-esquerda / frente-direita |
| — | `H` / `J` | ré-esquerda / ré-direita |
| `x` | `x` | ataque (servo 180°) |
| `b` | `b` | recolhe arma (servo 130°) |

## Ajustes no `app.py`
- `VELOCIDADE = 120 / 255`: igual ao `velA/velB = 120` do Arduino. Aumente até `1.0` se quiser.
- `ARMA_REPOUSO = 130`, `ARMA_ATAQUE = 180`: ângulos do servo.
- `PINO_ARMA = 24`: pino do servo.
- Motor girando ao contrário: troque os fios dele no L298N.

## Diferenças em relação ao Arduino
- Ao desconectar (modos BLE e `--serial`), o robô **para e recolhe a arma**. O Arduino continuava andando.
- No modo `--uart` (HC-06) o Pi não sabe quando o celular desconecta, assim como o Arduino.

## Iniciar junto com o Pi
`sudo crontab -e` e adicione (troque `--uart` pelo seu modo):
`@reboot sleep 10 && GPIOZERO_PIN_FACTORY=pigpio python3 /home/pi/battlebot-raspberry-pi/app.py --uart`
