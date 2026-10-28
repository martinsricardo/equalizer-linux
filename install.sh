#!/usr/bin/env bash
set -e

# ==============================================================================
# Script de Instalação do Equalizador Linux
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DEST="$HOME/.local/bin"
SYSTEMD_DEST="$HOME/.config/systemd/user"
DESKTOP_DEST="$HOME/.local/share/applications"
ICON_DEST="$HOME/.local/share/icons/hicolor/scalable/apps"
CONFIG_DEST="$HOME/.config/equalizer-linux"

echo "============================================================"
echo "          Instalação do Equalizador para Linux              "
echo "============================================================"

# 1. Verificação de dependências
echo "▶ A verificar dependências do sistema..."
for cmd in python3 pipewire wpctl; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "❌ Erro: O comando '$cmd' não foi encontrado. Por favor instale-o antes de continuar."
        exit 1
    fi
done

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "⚠️ Aviso: O módulo Python Tkinter não está instalado."
    echo "  Para usar a interface gráfica, instale com: sudo apt install python3-tk"
fi
echo "✔ Dependências básicas verificadas."

# 2. Criação das pastas necessárias
echo "▶ A preparar diretórios de utilizador..."
mkdir -p "$BIN_DEST"
mkdir -p "$SYSTEMD_DEST"
mkdir -p "$DESKTOP_DEST"
mkdir -p "$ICON_DEST"
mkdir -p "$CONFIG_DEST"

# 3. Inicializar configurações e ficheiro PipeWire inicial
echo "▶ A gerar ficheiros de configuração padrão..."
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from src.core import ensure_config_dir, load_config, write_pipewire_conf
ensure_config_dir()
cfg = load_config()
write_pipewire_conf(cfg['gains'])
print('Configurações inicializadas com sucesso.')
"

# 4. Instalar o executável
echo "▶ A instalar o binário equalizer-linux em $BIN_DEST..."
ln -sf "$SCRIPT_DIR/equalizer-linux" "$BIN_DEST/equalizer-linux"
chmod +x "$BIN_DEST/equalizer-linux"

# 5. Instalar o serviço systemd
echo "▶ A instalar o serviço systemd de utilizador..."
cp "$SCRIPT_DIR/systemd/equalizer-linux.service" "$SYSTEMD_DEST/equalizer-linux.service"
systemctl --user daemon-reload
systemctl --user enable equalizer-linux.service
systemctl --user restart equalizer-linux.service

# 6. Instalar o atalho no menu de aplicações e ícone
echo "▶ A registar atalho no ambiente de trabalho..."
cp "$SCRIPT_DIR/assets/equalizer-linux.svg" "$ICON_DEST/equalizer-linux.svg"
cp "$SCRIPT_DIR/equalizer-linux.desktop" "$DESKTOP_DEST/equalizer-linux.desktop"

# Atualizar cache de ícones e aplicações se as ferramentas existirem
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DEST" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo ""
echo "============================================================"
echo "✔ INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "============================================================"
echo "• O equalizador está ATIVO e a correr em segundo plano."
echo "• Foi ativado no systemd: arranca automaticamente ao ligar o PC."
echo ""
echo "Como usar:"
echo "  1. Pelo Menu de Aplicações do Linux: pesquise por 'Equalizador Linux'"
echo "  2. Pelo Terminal (Interface Gráfica): equalizer-linux gui"
echo "  3. Pelo Terminal (Linha de Comandos):"
echo "     - equalizer-linux status"
echo "     - equalizer-linux preset 'Bass Boost'"
echo "     - equalizer-linux set 63 +5.0"
echo "     - equalizer-linux bypass"
echo "============================================================"

# Verificar estado
"$SCRIPT_DIR/equalizer-linux" status || true
