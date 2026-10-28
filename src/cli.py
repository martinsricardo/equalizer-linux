"""Command-line interface for Linux Equalizer."""

import argparse
import sys
from typing import List

from .core import (
    apply_settings,
    disable_autostart,
    enable_autostart,
    is_service_enabled,
    is_service_running,
    load_config,
    load_presets,
    restart_service,
    save_config,
    start_service,
    stop_service,
)
from .presets import BANDS_SPEC


def print_ascii_bar(gain: float, min_val: float = -15.0, max_val: float = 15.0, width: int = 24) -> str:
    """Format gain as a visual ASCII meter."""
    mid = width // 2
    clamped = max(min_val, min(max_val, gain))
    pos = int(((clamped - min_val) / (max_val - min_val)) * (width - 1))

    chars = ["-"] * width
    chars[mid] = "|"
    if pos < mid:
        for i in range(pos, mid):
            chars[i] = "■"
    elif pos > mid:
        for i in range(mid + 1, pos + 1):
            chars[i] = "■"
    else:
        chars[mid] = "■"

    sign = "+" if gain > 0 else ""
    return f"[{''.join(chars)}] {sign}{gain:4.1f} dB"


def cmd_status():
    """Print the status of equalizer and current frequency bands."""
    config = load_config()
    running = is_service_running()
    enabled = is_service_enabled()

    status_str = "\033[92m● ATIVO\033[0m (Em execução)" if running else "\033[91m○ INATIVO\033[0m (Parado)"
    autostart_str = "\033[92mAtivado\033[0m (Inicia com o sistema)" if enabled else "\033[93mDesativado\033[0m"
    bypass_str = "\033[91mSIM (Som direto)\033[0m" if not config.get("enabled", True) else "\033[92mNÃO (Equalizador aplicado)\033[0m"

    print("=" * 60)
    print("           EQUALIZADOR DE SOM PARA LINUX")
    print("=" * 60)
    print(f"  Estado do Serviço:   {status_str}")
    print(f"  Arranque no Boot:    {autostart_str}")
    print(f"  Bypass (Desativado): {bypass_str}")
    print(f"  Preset Atual:        \033[1m{config.get('active_preset', 'Custom')}\033[0m")
    print(f"  Preamp / Ganho:      {config.get('preamp', 0.0):+.1f} dB")
    print("-" * 60)
    print("  Bandas de Frequência:")

    gains = config.get("gains", [0.0] * 10)
    for spec, gain in zip(BANDS_SPEC, gains):
        lbl = spec["label"].rjust(6)
        desc = spec["desc"].ljust(12)
        meter = print_ascii_bar(gain)
        print(f"   [{spec['index']}] {lbl} ({desc}): {meter}")
    print("=" * 60)


def cmd_list_presets():
    """List available presets."""
    presets = load_presets()
    config = load_config()
    current = config.get("active_preset", "")

    print("Presets Disponíveis:")
    print("-" * 50)
    for name, data in presets.items():
        mark = "▶ " if name == current else "  "
        desc = data.get("description", "")
        custom_tag = " [Personalizado]" if data.get("custom") else ""
        print(f"{mark}\033[1m{name}\033[0m{custom_tag}")
        if desc:
            print(f"     {desc}")
        gains_str = ", ".join(f"{g:+.1f}dB" for g in data.get("gains", []))
        print(f"     Bandas: {gains_str}")
        print()


def cmd_preset(name: str):
    """Activate a preset."""
    presets = load_presets()

    # Case-insensitive search
    match_key = None
    for k in presets.keys():
        if k.lower() == name.lower() or name.lower() in k.lower():
            match_key = k
            break

    if not match_key:
        print(f"Erro: Preset '{name}' não encontrado.")
        print("Use 'equalizer-linux list-presets' para ver os disponíveis.")
        sys.exit(1)

    preset_data = presets[match_key]
    config = load_config()
    config["active_preset"] = match_key
    config["gains"] = list(preset_data["gains"])
    config["preamp"] = float(preset_data.get("preamp", 0.0))
    config["enabled"] = True

    if apply_settings(config):
        print(f"Preset ativado com sucesso: \033[1m{match_key}\033[0m")
    else:
        print(f"Configuração gravada, mas o serviço não pôde ser reiniciado.")


def cmd_set_band(target: str, gain: float):
    """Set gain of a specific band by index or frequency label."""
    config = load_config()
    gains = config.get("gains", [0.0] * 10)

    # Check if target is an index
    try:
        idx = int(target)
        if 0 <= idx < len(BANDS_SPEC):
            gains[idx] = float(gain)
            config["gains"] = gains
            config["active_preset"] = "Personalizado"
            apply_settings(config)
            print(f"Banda {idx} ({BANDS_SPEC[idx]['label']}) ajustada para {gain:+.1f} dB")
            return
    except ValueError:
        pass

    # Check by frequency label
    target_clean = target.lower().replace("hz", "").replace("k", "000").strip()
    matched = False
    for spec in BANDS_SPEC:
        freq_str = str(int(spec["freq"]))
        label_clean = spec["label"].lower().replace("hz", "").replace("k", "000").replace(" ", "")
        if target_clean in [freq_str, label_clean]:
            idx = spec["index"]
            gains[idx] = float(gain)
            config["gains"] = gains
            config["active_preset"] = "Personalizado"
            apply_settings(config)
            print(f"Banda {spec['label']} ajustada para {gain:+.1f} dB")
            matched = True
            break

    if not matched:
        print(f"Banda inválida: '{target}'. Use um índice de 0 a 9 ou frequência (ex: 63, 1k, 8000).")
        sys.exit(1)


def cmd_preamp(gain: float):
    """Set preamp gain."""
    config = load_config()
    config["preamp"] = float(gain)
    apply_settings(config)
    print(f"Preamp ajustado para {gain:+.1f} dB")


def cmd_bypass(state: str = None):
    """Toggle or set bypass mode."""
    config = load_config()
    if state is None:
        new_enabled = not config.get("enabled", True)
    else:
        new_enabled = state.lower() not in ["1", "true", "on", "yes", "sim"]

    config["enabled"] = new_enabled
    apply_settings(config)
    if new_enabled:
        print("Equalizador \033[92mATIVADO\033[0m")
    else:
        print("Equalizador \033[93mEM BYPASS (Desativado)\033[0m - Áudio direto sem processamento")


def cmd_autostart(state: str = None):
    """Configure system autostart."""
    if state is None:
        current = is_service_enabled()
        target = not current
    else:
        target = state.lower() in ["1", "true", "on", "yes", "sim", "ativar"]

    if target:
        if enable_autostart():
            print("Arranque automático \033[92mATIVADO\033[0m (O equalizador iniciará logo que o computador ligar).")
        else:
            print("Erro ao ativar arranque automático no systemd.")
    else:
        if disable_autostart():
            print("Arranque automático \033[93mDESATIVADO\033[0m.")
        else:
            print("Erro ao desativar arranque automático no systemd.")


def run_cli(args: List[str]):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="equalizer-linux",
        description="Equalizador de som para Linux em segundo plano (PipeWire)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # status
    subparsers.add_parser("status", help="Mostra o estado do serviço e das bandas")

    # presets
    subparsers.add_parser("list-presets", help="Lista todos os presets disponíveis")
    p_preset = subparsers.add_parser("preset", help="Ativa um preset")
    p_preset.add_argument("name", help="Nome do preset (ex: 'Bass Boost', 'Rock')")

    # set band
    p_set = subparsers.add_parser("set", help="Ajusta o ganho de uma banda")
    p_set.add_argument("band", help="Índice (0-9) ou frequência (ex: 63, 1k, 8000)")
    p_set.add_argument("gain", type=float, help="Ganho em dB (-15.0 a +15.0)")

    # preamp
    p_preamp = subparsers.add_parser("preamp", help="Ajusta o ganho do preamp")
    p_preamp.add_argument("gain", type=float, help="Ganho do preamp em dB")

    # bypass
    p_bypass = subparsers.add_parser("bypass", help="Ativa ou desativa bypass")
    p_bypass.add_argument("state", nargs="?", default=None, help="on/off (ou omita para alternar)")

    # autostart
    p_autostart = subparsers.add_parser("autostart", help="Configura arranque no boot")
    p_autostart.add_argument("state", nargs="?", default=None, help="on/off (ou omita para alternar)")

    # service controls
    subparsers.add_parser("start", help="Inicia o serviço em segundo plano")
    subparsers.add_parser("stop", help="Para o serviço em segundo plano")
    subparsers.add_parser("restart", help="Reinicia o serviço")

    # gui
    subparsers.add_parser("gui", help="Abre a interface gráfica do equalizador")

    parsed = parser.parse_args(args)

    if parsed.command == "status":
        cmd_status()
    elif parsed.command == "list-presets":
        cmd_list_presets()
    elif parsed.command == "preset":
        cmd_preset(parsed.name)
    elif parsed.command == "set":
        cmd_set_band(parsed.band, parsed.gain)
    elif parsed.command == "preamp":
        cmd_preamp(parsed.gain)
    elif parsed.command == "bypass":
        cmd_bypass(parsed.state)
    elif parsed.command == "autostart":
        cmd_autostart(parsed.state)
    elif parsed.command == "start":
        if start_service():
            print("Serviço iniciado com sucesso.")
        else:
            print("Falha ao iniciar o serviço.")
    elif parsed.command == "stop":
        if stop_service():
            print("Serviço parado com sucesso.")
        else:
            print("Falha ao parar o serviço.")
    elif parsed.command == "restart":
        if restart_service():
            print("Serviço reiniciado com sucesso.")
        else:
            print("Falha ao reiniciar o serviço.")
    elif parsed.command == "gui":
        from .gui import launch_gui
        launch_gui()
    else:
        # Default: if no command passed and DISPLAY exists, launch GUI; otherwise print status
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            from .gui import launch_gui
            launch_gui()
        else:
            cmd_status()
