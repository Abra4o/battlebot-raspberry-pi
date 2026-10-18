# BattleBot com Raspberry Pi

Versão para Raspberry Pi do projeto
[BattleBot Arduino (Robótica Prática)](https://roboticapratica.com.br/projeto/battlebot-arduino.html):
mesma ponte H L298N, mesmo servo de ataque, mesma velocidade e as mesmas letras do app roboBT.

## Arquivos
| Arquivo | Para quê |
|---------|----------|
| `app.py` | Roda no Raspberry Pi: recebe os comandos (Wi-Fi ou Bluetooth), move os motores e o servo |
| `controle.html` | Controle do celular via Wi-Fi (o próprio Pi entrega a página) |
| `simulador_pc.py` | Visual no PC: o robô anda e ataca na tela, sem precisar do Pi |
| `teste_pc.py` | Teste automático da lógica no PC |
| `abrir_controle_demo.bat` | Abre o controle do celular no PC, em modo demonstração |

**Passo a passo:** [📶 Wi-Fi do zero](#-passo-a-passo-wi-fi-do-zero-ao-carrinho-andando) · [💻 PC](#-passo-a-passo-no-pc-windows) · [📱 Celular](#-passo-a-passo-no-celular) · [🍓 Raspberry Pi](#-raspberry-pi-instalar)

---

## 📶 Passo a passo Wi-Fi: do zero ao carrinho andando

Resumo: o Pi cria uma rede Wi-Fi chamada `Carrinho`, o celular entra nela e abre `http://10.42.0.1`
no navegador. Não precisa instalar app nem ter internet. Funciona em Android e iPhone.

### 1. Preparar o cartão SD (no PC, só na primeira vez)
1. Instale o **Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. Escolha o seu Pi, o sistema **Raspberry Pi OS (64-bit)** e o cartão SD.
3. Em **Editar configurações** (ou "Personalizar"):
   - nome do host: `raspberrypi`; usuário: `pi` e uma senha;
   - **Wi-Fi da sua casa** (nome e senha) e país `BR`;
   - aba **Serviços**: marque **Ativar SSH** (com senha).
4. Grave, coloque o cartão no Pi e ligue. Espere uns 2 minutos.

### 2. Entrar no Pi pelo PC
O PC precisa estar no mesmo Wi-Fi de casa. No PowerShell:
```powershell
ssh pi@raspberrypi.local
```
Responda `yes` na primeira vez e digite a senha. Se não achar, veja o IP do Pi no app/página do roteador
e use `ssh pi@<ip>`.

### 3. Instalar o projeto (no Pi, só na primeira vez)
```bash
sudo apt update
sudo apt install -y git gh python3-gpiozero python3-serial pigpio python3-pigpio
sudo systemctl enable --now pigpiod
gh auth login                                  # repositório privado: entre com sua conta do GitHub
gh repo clone Abra4o/battlebot-raspberry-pi
cd battlebot-raspberry-pi
```

### 4. Primeiro teste, ainda no Wi-Fi de casa
1. Monte as ligações (veja [Ligações](#ligações-arduino--raspberry-pi-numeração-bcm)) e ligue as pilhas do L298N.
2. No Pi:
   ```bash
   cd ~/battlebot-raspberry-pi
   sudo GPIOZERO_PIN_FACTORY=pigpio python3 app.py
   ```
   Ele mostra o endereço, por ex. `http://192.168.0.23`.
3. Com o celular **no mesmo Wi-Fi de casa**, abra esse endereço no navegador e toque **▶ Dirigir**.
4. Funcionou? `Ctrl+C` no Pi para parar.

### 5. Fazer o Pi criar a rede `Carrinho` (só uma vez)
Assim o carrinho funciona em qualquer lugar (sala de aula, arena), sem roteador.

> ⚠️ Ao ligar a rede `Carrinho`, o Pi **sai do Wi-Fi de casa** e o SSH cai. É normal.

```bash
sudo nmcli connection add type wifi ifname wlan0 con-name Carrinho autoconnect yes ssid Carrinho \
  802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared \
  wifi-sec.key-mgmt wpa-psk wifi-sec.psk carrinho123
sudo nmcli connection modify Carrinho connection.autoconnect-priority 100
sudo nmcli connection up Carrinho
```
Para trocar nome/senha, mude `ssid Carrinho` e `wifi-sec.psk carrinho123` (senha com 8+ caracteres).

Para entrar de novo no Pi: conecte o PC na rede `Carrinho` e rode `ssh pi@10.42.0.1`.

### 6. Rodar sozinho quando o Pi ligar (só uma vez)
Conectado no Pi (`ssh pi@10.42.0.1`):
```bash
sudo crontab -e
```
Escolha o editor `nano` (opção 1), vá até o fim e adicione a linha:
```
@reboot sleep 10 && GPIOZERO_PIN_FACTORY=pigpio python3 /home/pi/battlebot-raspberry-pi/app.py
```
Salve com `Ctrl+O`, `Enter`, `Ctrl+X`. Reinicie: `sudo reboot`.
(Se o seu usuário não for `pi`, troque `/home/pi` pelo seu.)

### 7. Dirigir (todo dia)
1. Ligue o Pi e as pilhas. Espere uns 30 s.
2. No celular: **Wi-Fi → `Carrinho`** (senha `carrinho123`). Se avisar "sem internet", escolha **manter conectado**.
3. Abra **`http://10.42.0.1`** no Chrome ou Safari. Na primeira vez, adicione à tela inicial
   (Android: **⋮ → Adicionar à tela inicial**; iPhone: **Compartilhar → Adicionar à Tela de Início**).
4. Toque **▶ Dirigir**:
   - polegar esquerdo **▲ / ▼**, polegar direito **◀ ▶** (juntos = curva andando);
   - **⚔ ATAQUE**: segurou = ataca, soltou = recolhe;
   - **Parar**, sair do app ou perder o Wi-Fi = o robô para e recolhe a arma.

### Deu problema?
| Sintoma | O que fazer |
|---------|-------------|
| A rede `Carrinho` não aparece | Espere 1 min após ligar. Confira com `nmcli connection show --active` (via cabo/monitor) |
| Página não abre | Confirme que o celular está na rede `Carrinho` e digite `http://` (não `https://`). Desligue os dados móveis |
| "sem conexão com o carrinho" | O `app.py` não está rodando. Rode na mão: `sudo python3 ~/battlebot-raspberry-pi/app.py` |
| `Address already in use` | O `app.py` já está rodando (pelo crontab). Pare com `sudo pkill -f app.py` |
| Robô para sozinho às vezes | Wi-Fi fraco. Fique mais perto; o Pi para por segurança após 0,6 s sem sinal |
| Voltar para o Wi-Fi de casa | `sudo nmcli connection down Carrinho` e `sudo nmcli connection modify Carrinho autoconnect no` |

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

## 📱 Passo a passo no celular

Escolha **um** dos dois. O controle Wi-Fi (opção B) funciona em Android e iPhone; o roboBT só no Android.

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

### Opção B: controle novo pelo Wi-Fi (`controle.html`), sem instalar nada
Use com o Pi rodando `sudo python3 app.py` (modo Wi-Fi). O Pi entrega a página e recebe os comandos.
Passo a passo completo, incluindo configurar o Pi: [📶 Wi-Fi do zero](#-passo-a-passo-wi-fi-do-zero-ao-carrinho-andando).
1. Deixe o celular e o Pi na **mesma rede Wi-Fi**. Duas formas:
   - **Pi como roteador (recomendado na arena):** o Pi cria a rede `Carrinho`
     (veja [Wi-Fi do Pi](#wi-fi-do-pi)). No celular, entre na rede `Carrinho` (senha `carrinho123`).
     Se o Android avisar "sem internet", escolha **manter conectado**.
   - **Rede de casa/roteador:** Pi e celular conectados no mesmo Wi-Fi.
2. Ligue o robô e rode `sudo python3 app.py` no Pi. Ele mostra o endereço, por ex.:
   `http://10.42.0.1` (Pi como roteador) ou `http://192.168.0.23` (rede de casa).
3. Abra esse endereço no navegador do celular (Chrome ou Safari).
4. Menu **⋮ → Adicionar à tela inicial** (no iPhone: **Compartilhar → Adicionar à Tela de Início**).
5. Toque **▶ Dirigir**. A tela fica cheia e deitada (no Android). Dirija:
   - polegar esquerdo **▲ / ▼**, polegar direito **◀ ▶** (juntos = curva andando);
   - **⚔ ATAQUE** no meio: segurou = ataca, soltou = recolhe;
   - soltou as setas, tocou **Parar**, saiu do app ou caiu o Wi-Fi = o robô para e recolhe a arma
     (o Pi para sozinho se ficar 0,6 s sem receber nada do celular).

Para testar só a tela no celular, sem o robô, abra o link com `?demo` no final
(ex.: `http://10.42.0.1/?demo`).

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

### Conexão: escolha uma
**Wi-Fi** (controle.html): não precisa ligar nada, usa o Wi-Fi do Pi (3, 4, 5, Zero W/2 W).
Veja [Wi-Fi do Pi](#wi-fi-do-pi).

**Bluetooth A) Usar o HC-06 do projeto** (o app roboBT do projeto funciona igual):

| HC-06 | Raspberry Pi |
|-------|--------------|
| VCC | 5V (pino 2) |
| GND | GND (pino 14) |
| TXD | GPIO15 / RXD (pino 10) |
| RXD | GPIO14 / TXD (pino 8) |

Ative o UART: `sudo raspi-config` → Interface Options → Serial Port →
*login shell*: **Não**, *hardware serial*: **Sim** → reinicie.

**Bluetooth B) Sem HC-06**: usar o Bluetooth que já vem no Pi (3, 4, 5, Zero W).

---

## 🍓 Raspberry Pi: instalar
```bash
gh auth login                                  # só na primeira vez (repositório privado)
gh repo clone Abra4o/battlebot-raspberry-pi
cd battlebot-raspberry-pi
sudo apt update
sudo apt install -y python3-gpiozero python3-serial bluez pigpio python3-pigpio
sudo systemctl enable --now pigpiod
```
O modo Wi-Fi usa só a biblioteca padrão do Python (nada extra para instalar).
O `pigpio` deixa o servo firme (sem tremer). Para usar, rode com
`sudo GPIOZERO_PIN_FACTORY=pigpio python3 app.py ...`.

## 🍓 Raspberry Pi: rodar
Escolha o modo de acordo com o app do celular:

| Modo | Comando | Celular |
|------|---------|---------|
| HC-06 ligado no Pi | `sudo python3 app.py --uart` | App **roboBT** do projeto (pareie com "HC-06", PIN 1234) |
| Bluetooth do Pi + app do projeto | `sudo python3 app.py --serial` | App **roboBT**, pareado com o Raspberry Pi |
| Wi-Fi + controle novo | `sudo python3 app.py` | Navegador em `http://<ip do Pi>` |

**Modo `--serial`** precisa preparar o Bluetooth do Pi uma vez:
```bash
sudo sed -i 's|^ExecStart=.*bluetoothd$|& -C|' /lib/systemd/system/bluetooth.service
sudo systemctl daemon-reload && sudo systemctl restart bluetooth
sudo sdptool add SP
```

### Wi-Fi do Pi
- **Pi como roteador** (rede `Carrinho`, Pi em `http://10.42.0.1`): veja o
  [passo 5 do Wi-Fi do zero](#5-fazer-o-pi-criar-a-rede-carrinho-só-uma-vez).
- **Rede de casa:** configure o Wi-Fi no Raspberry Pi Imager ou com `sudo nmtui`.
  O endereço aparece ao rodar o `app.py` (ou com `hostname -I`). Também dá para usar `http://raspberrypi.local`.

A porta é a 80 (`PORTA_WIFI` no `app.py`), por isso o `sudo`.

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
- Ao desconectar (modos Wi-Fi e `--serial`), o robô **para e recolhe a arma**. O Arduino continuava andando.
- No modo `--uart` (HC-06) o Pi não sabe quando o celular desconecta, assim como o Arduino.

## Iniciar junto com o Pi
`sudo crontab -e` e adicione (sem nada no fim = Wi-Fi; ou coloque `--uart` / `--serial`):
`@reboot sleep 10 && GPIOZERO_PIN_FACTORY=pigpio python3 /home/pi/battlebot-raspberry-pi/app.py`
