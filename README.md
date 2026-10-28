# Equalizador de Som para Linux (Equalizer Linux)

Um equalizador de som gráfico de **10 bandas** leve, moderno e robusto para Linux (Ubuntu, Debian, Fedora, Arch, etc.), construído nativamente sobre o **PipeWire Filter-Chain**.

Fica a correr continuamente em **segundo plano** com consumo praticamente nulo de recursos (0% CPU) e **arranca logo que o computador liga**, aplicando o processamento de áudio a todas as aplicações (Spotify, YouTube, navegadores, jogos, leitores multimédia) sem qualquer latência ou cortes.

---

## 🚀 Características Principais

- ⚡ **Nativo e Ultra-Leve:** Processamento de áudio digital (DSP) em C diretamente dentro do grafo de som do PipeWire (`libpipewire-module-filter-chain` com `param_eq`). Não consome memória desnecessária nem CPU.
- 🔄 **Arranque Automático com o Computador:** Integrado através de um serviço de utilizador do `systemd` (`equalizer-linux.service`). Assim que inicia sessão, o equalizador já está ativo e a funcionar.
- 🎚️ **10 Bandas de Frequência:**
  - `31 Hz` (Sub-graves)
  - `63 Hz` (Graves)
  - `125 Hz` (Médio-graves)
  - `250 Hz` (Corpo / Resonância)
  - `500 Hz` (Médios)
  - `1 kHz` (Médios altos)
  - `2 kHz` (Presença)
  - `4 kHz` (Clareza)
  - `8 kHz` (Agudos)
  - `16 kHz` (Brilho / Ar)
- 📊 **Interface Gráfica Moderna (GUI):**
  - Tema escuro de alto contraste.
  - Curva de resposta de frequência desenhada em tempo real (Catmull-Rom spline).
  - Faders verticais (-15 dB a +15 dB) com duplo clique para repor a zero.
  - Controlo de ganho geral (Preamp).
  - Pode fechar a janela quando quiser: o equalizador continuará a correr em segundo plano!
- 🎵 **Presets Prontos e Personalizados:**
  - *Plano (Flat)*, *Reforço de Graves (Bass Boost)*, *Super Graves (Extreme)*, *Reforço de Agudos (Treble Boost)*, *Rock*, *Pop*, *Eletrónica / Dance (EDM)*, *Voz & Podcasts*, *Jazz*, *Heavy Metal*, *Gaming (Passos)* e *Acústico*.
  - Capacidade de criar, guardar e eliminar os seus próprios presets com nomes personalizados.
- 🖥️ **Controlo Completo por Terminal (CLI):** Pode alterar presets, ajustar frequências ou ativar/desativar o equalizador através de comandos simples ou scripts.

---

## 📥 Instalação Rápida (1 Comando)

No diretório do projeto, execute o script de instalação:

```bash
./install.sh
```

O instalador irá:
1. Validar as ferramentas de áudio (`pipewire`, `wpctl`, `python3`).
2. Criar a pasta de configurações em `~/.config/equalizer-linux`.
3. Instalar o comando `equalizer-linux` em `~/.local/bin/`.
4. Registar e ativar o serviço no `systemd --user` para arranque automático.
5. Criar o atalho no menu de aplicações do ambiente gráfico (GNOME, KDE, XFCE, etc.).
6. Iniciar o equalizador imediatamente.

---

## 🎧 Como Usar

### 1. Pela Interface Gráfica

- Abra o menu de aplicações do seu Linux e pesquise por **Equalizador Linux**;
- Ou execute no terminal:
  ```bash
  equalizer-linux
  # ou
  equalizer-linux gui
  ```

> **Dica:** Pode fechar a janela da interface gráfica a qualquer momento. O áudio continuará a ser processado normalmente em segundo plano.

### 2. Pela Linha de Comandos (CLI)

Se preferir usar o terminal, o `equalizer-linux` disponibiliza vários comandos práticos:

#### Ver o estado atual e medidor visual das bandas:
```bash
equalizer-linux status
```

#### Ativar um preset:
```bash
equalizer-linux preset "Bass Boost"
equalizer-linux preset Rock
equalizer-linux preset "Voz / Podcasts / Diálogos"
```

#### Listar todos os presets disponíveis:
```bash
equalizer-linux list-presets
```

#### Ajustar uma frequência específica:
```bash
# Ajustar a banda 63 Hz para +5.0 dB
equalizer-linux set 63 +5.0

# Ajustar a banda de 1 kHz para -2.0 dB
equalizer-linux set 1k -2.0

# Ajustar pelo índice da banda (0 a 9)
equalizer-linux set 0 +6.0
```

#### Ajustar o ganho geral (Preamp):
```bash
equalizer-linux preamp -2.0
```

#### Alternar Modo Bypass (ativar / desativar temporariamente):
```bash
equalizer-linux bypass
```

#### Ligar / Desligar o arranque automático no boot:
```bash
equalizer-linux autostart on
equalizer-linux autostart off
```

#### Controlar o serviço de segundo plano:
```bash
equalizer-linux restart
equalizer-linux stop
equalizer-linux start
```

---

## 🛠️ Como Funciona nos Bastidores

1. **PipeWire Filter-Chain:** O PipeWire cria um nó virtual de áudio (`effect_input.equalizer_linux`).
2. **Prioridade de Áudio:** O nó tem prioridade `1500`, fazendo com que o WirePlumber encaminhe automaticamente todo o áudio do sistema para o equalizador, e deste para a sua placa de som ou auscultadores predefinidos.
3. **Systemd User Service:** O ficheiro `~/.config/systemd/user/equalizer-linux.service` assegura que:
   - Arranca logo após o `pipewire.service` no início de sessão do utilizador.
   - Reinicia automaticamente caso haja alguma interrupção.
   - Se alterar qualquer valor na interface, a configuração em `~/.config/equalizer-linux/pipewire-filter.conf` é atualizada e recarregada em menos de 50 milissegundos sem falhas audíveis.

---

## 🗑️ Desinstalação

Se algum dia desejar remover o equalizador:

```bash
./uninstall.sh
```

O script irá parar o serviço, remover o arranque automático do systemd e limpar os atalhos e binários.
