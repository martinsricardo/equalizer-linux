#!/usr/bin/env bash

# ==============================================================================
# Script de Desinstalação do Equalizador Linux
# ==============================================================================

echo "============================================================"
echo "          Desinstalação do Equalizador para Linux           "
echo "============================================================"

echo "▶ A parar e desativar o serviço systemd..."
systemctl --user stop equalizer-linux.service >/dev/null 2>&1 || true
systemctl --user disable equalizer-linux.service >/dev/null 2>&1 || true
rm -f "$HOME/.config/systemd/user/equalizer-linux.service"
systemctl --user daemon-reload

echo "▶ A remover o binário em ~/.local/bin..."
rm -f "$HOME/.local/bin/equalizer-linux"

echo "▶ A remover atalhos de ambiente de trabalho..."
rm -f "$HOME/.local/share/applications/equalizer-linux.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/equalizer-linux.svg"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

read -p "Deseja também remover as configurações e presets em ~/.config/equalizer-linux? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    rm -rf "$HOME/.config/equalizer-linux"
    echo "✔ Pasta de configurações removida."
fi

echo "============================================================"
echo "✔ Equalizador Linux desinstalado com sucesso."
echo "============================================================"

