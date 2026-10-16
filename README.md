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

## 1. Testar no PC (sem o Pi)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install gpiozero
python simulador_pc.py   # setas/WASD movem, espaço = ataque
python teste_pc.py       # teste automático
```

## 2. Instalar no Raspberry Pi
```bash
sudo apt update
sudo apt install -y python3-gpiozero python3-serial python3-dbus python3-gi bluez pigpio python3-pigpio
sudo systemctl enable --now pigpiod
sudo pip3 install bluezero --break-system-packages
```
O `pigpio` deixa o servo firme (sem tremer). Para usar, rode com
`sudo GPIOZERO_PIN_FACTORY=pigpio python3 app.py ...`.

## 3. Rodar: escolha o modo

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
O Web Bluetooth só funciona em página **https**: arraste o `controle.html` (renomeado para
`index.html`) em https://app.netlify.com/drop, abra o link no Chrome do celular →
⋮ → **Adicionar à tela inicial**.

### controle.html
- Celular deitado: polegar esquerdo **▲ / ▼**, polegar direito **◀ ▶**, **⚔ ATAQUE** no meio.
- ▲ + ▶ juntos = curva andando. Só ◀ ou ▶ = gira no lugar.
- Segurou ATAQUE = servo vai a 180°; soltou = volta a 130°.
- Soltou as setas, desconectou, saiu do app ou ficou 0,6 s sem comando = para.

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
`@reboot sleep 10 && GPIOZERO_PIN_FACTORY=pigpio python3 /home/pi/carrinho-raspi/app.py --uart`
