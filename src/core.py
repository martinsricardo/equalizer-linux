"""Core logic for Linux Equalizer: configuration, presets, PipeWire generation, and systemd management."""

import json
import math
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .presets import BANDS_SPEC, DEFAULT_PRESETS

CONFIG_DIR = Path(os.environ.get("EQUALIZER_CONFIG_DIR", Path.home() / ".config" / "equalizer-linux"))
CONFIG_FILE = CONFIG_DIR / "config.json"
PRESETS_FILE = CONFIG_DIR / "presets.json"
PIPEWIRE_CONF_FILE = CONFIG_DIR / "pipewire-filter.conf"
SERVICE_NAME = "equalizer-linux.service"
SINK_NODE_NAME = "effect_input.equalizer_linux"
SOURCE_NODE_NAME = "effect_output.equalizer_linux"


def ensure_config_dir():
    """Ensure the configuration directory and required files exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not PRESETS_FILE.exists():
        save_presets(DEFAULT_PRESETS)
    if not CONFIG_FILE.exists():
        initial_config = {
            "enabled": True,
            "active_preset": "Plano (Flat)",
            "preamp": 0.0,
            "gains": [0.0] * len(BANDS_SPEC),
        }
        save_config(initial_config)


def load_presets() -> Dict[str, Any]:
    """Load all presets (built-in + user-saved)."""
    ensure_config_dir()
    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as f:
            presets = json.load(f)
            # Ensure default presets are always present
            for k, v in DEFAULT_PRESETS.items():
                if k not in presets:
                    presets[k] = v
            return presets
    except Exception:
        return dict(DEFAULT_PRESETS)


def save_presets(presets: Dict[str, Any]):
    """Save presets to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2, ensure_ascii=False)


def save_custom_preset(name: str, gains: List[float], preamp: float = 0.0, description: str = ""):
    """Save or update a custom user preset."""
    presets = load_presets()
    presets[name] = {
        "description": description or f"Preset personalizado {name}",
        "gains": [round(float(g), 1) for g in gains],
        "preamp": round(float(preamp), 1),
        "custom": True,
    }
    save_presets(presets)


def delete_custom_preset(name: str) -> bool:
    """Delete a custom preset. Cannot delete built-in presets."""
    if name in DEFAULT_PRESETS:
        return False
    presets = load_presets()
    if name in presets:
        del presets[name]
        save_presets(presets)
        return True
    return False


def load_config() -> Dict[str, Any]:
    """Load user configuration."""
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if "gains" not in cfg or len(cfg["gains"]) != len(BANDS_SPEC):
                cfg["gains"] = [0.0] * len(BANDS_SPEC)
            if "enabled" not in cfg:
                cfg["enabled"] = True
            if "preamp" not in cfg:
                cfg["preamp"] = 0.0
            if "active_preset" not in cfg:
                cfg["active_preset"] = "Plano (Flat)"
            return cfg
    except Exception:
        return {
            "enabled": True,
            "active_preset": "Plano (Flat)",
            "preamp": 0.0,
            "gains": [0.0] * len(BANDS_SPEC),
        }


def save_config(config: Dict[str, Any]):
    """Save user configuration to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_physical_default_sink() -> Tuple[Optional[str], Optional[int]]:
    """Find the active physical (hardware) audio sink node name and ID."""
    try:
        out = subprocess.check_output(["pw-dump"], stderr=subprocess.DEVNULL)
        nodes = json.loads(out)
        hardware_sinks = []
        for n in nodes:
            props = n.get("info", {}).get("props", {})
            if props.get("media.class") == "Audio/Sink":
                name = props.get("node.name", "")
                if "equalizer" in name.lower() or "easyeffects" in name.lower():
                    continue
                if props.get("node.virtual", False):
                    continue
                priority = int(props.get("priority.session", 0))
                hardware_sinks.append((priority, name, n.get("id")))
        if hardware_sinks:
            hardware_sinks.sort(key=lambda x: x[0], reverse=True)
            return hardware_sinks[0][1], hardware_sinks[0][2]
    except Exception:
        pass
    return None, None


def restore_physical_default_sink() -> bool:
    """Restore physical hardware sink as default in WirePlumber."""
    _, phys_id = get_physical_default_sink()
    if phys_id is not None:
        try:
            res = subprocess.run(
                ["wpctl", "set-default", str(phys_id)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return res.returncode == 0
        except Exception:
            pass
    return False


def generate_pipewire_filter_conf(gains: List[float]) -> str:
    """Generate the PipeWire SPA-JSON configuration file for the equalizer filter chain."""
    filter_entries = []
    for spec, gain in zip(BANDS_SPEC, gains):
        entry = (
            f'                        {{ type = {spec["type"]}  '
            f'freq = {spec["freq"]:.1f}  '
            f'gain = {gain:.1f}  '
            f'q = {spec["q"]:.1f} }}'
        )
        filter_entries.append(entry)

    filters_block = "\n".join(filter_entries)

    target_name, _ = get_physical_default_sink()
    target_prop = f'\n                target.object    = "{target_name}"' if target_name else ""

    conf_template = f"""# Configuração do Equalizador PipeWire gerada automaticamente pelo equalizer-linux
# Não edite manualmente enquanto o serviço estiver ativo.

context.properties = {{
    log.level = 0
}}

context.spa-libs = {{
    audio.convert.* = audioconvert/libspa-audioconvert
    support.*       = support/libspa-support
}}

context.modules = [
    {{ name = libpipewire-module-rt
        flags = [ ifexists nofail ]
    }}
    {{ name = libpipewire-module-protocol-native }}
    {{ name = libpipewire-module-client-node }}
    {{ name = libpipewire-module-adapter }}
    {{ name = libpipewire-module-filter-chain
        args = {{
            node.description = "Equalizador Linux"
            media.name       = "Equalizador Linux"
            filter.graph = {{
                nodes = [
                    {{
                        type   = builtin
                        name   = eq
                        label  = param_eq
                        config = {{
                            filters = [
{filters_block}
                            ]
                        }}
                    }}
                ]
            }}
            audio.channels = 2
            audio.position = [ FL FR ]
            capture.props = {{
                node.name        = "{SINK_NODE_NAME}"
                media.class      = Audio/Sink
                priority.session = 1500
                priority.driver  = 1500
            }}
            playback.props = {{
                node.name        = "{SOURCE_NODE_NAME}"
                node.passive     = true{target_prop}
            }}
        }}
    }}
]
"""
    return conf_template


def write_pipewire_conf(gains: List[float]) -> Path:
    """Write the PipeWire filter configuration file to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = generate_pipewire_filter_conf(gains)
    with open(PIPEWIRE_CONF_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return PIPEWIRE_CONF_FILE


# Systemd Service Management
def is_service_running() -> bool:
    """Check if the equalizer systemd user service is currently active."""
    try:
        res = subprocess.run(
            ["systemctl", "--user", "is-active", SERVICE_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.stdout.strip() == "active"
    except Exception:
        return False


def is_service_enabled() -> bool:
    """Check if the equalizer systemd user service is enabled for startup."""
    try:
        res = subprocess.run(
            ["systemctl", "--user", "is-enabled", SERVICE_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.stdout.strip() == "enabled"
    except Exception:
        return False


def enable_autostart() -> bool:
    """Enable the equalizer service to start on user login / computer boot."""
    try:
        res = subprocess.run(
            ["systemctl", "--user", "enable", SERVICE_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def disable_autostart() -> bool:
    """Disable automatic startup."""
    try:
        res = subprocess.run(
            ["systemctl", "--user", "disable", SERVICE_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def start_service() -> bool:
    """Start the equalizer service."""
    try:
        res = subprocess.run(
            ["systemctl", "--user", "start", SERVICE_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def stop_service() -> bool:
    """Stop the equalizer service and restore the physical default sink."""
    restore_physical_default_sink()
    try:
        res = subprocess.run(
            ["systemctl", "--user", "stop", SERVICE_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def restart_service() -> bool:
    """Restart the equalizer service."""
    try:
        res = subprocess.run(
            ["systemctl", "--user", "restart", SERVICE_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def find_equalizer_sink_id() -> Optional[int]:
    """Find the PipeWire node ID for the equalizer sink."""
    try:
        out = subprocess.check_output(["pw-dump"], stderr=subprocess.DEVNULL)
        nodes = json.loads(out)
        for node in nodes:
            props = node.get("info", {}).get("props", {})
            if props.get("node.name") == SINK_NODE_NAME:
                return node.get("id")
    except Exception:
        pass
    return None


def set_default_sink() -> bool:
    """Set the equalizer sink as default output device in WirePlumber."""
    sink_id = find_equalizer_sink_id()
    if sink_id is not None:
        try:
            res = subprocess.run(
                ["wpctl", "set-default", str(sink_id)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return res.returncode == 0
        except Exception:
            pass
    return False


def apply_preamp_volume(preamp_db: float):
    """Apply preamp as volume adjustment to the equalizer sink."""
    sink_id = find_equalizer_sink_id()
    if sink_id is not None:
        try:
            # Linear factor = 10^(dB / 20)
            linear_vol = max(0.0, min(1.5, 10.0 ** (preamp_db / 20.0)))
            subprocess.run(
                ["wpctl", "set-volume", str(sink_id), f"{linear_vol:.2f}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception:
            pass


def apply_settings(config: Dict[str, Any]) -> bool:
    """
    Apply configuration:
    1. Write pipewire-filter.conf (flat 0 dB if bypassed)
    2. Start or restart service
    3. Update default sink & preamp volume
    """
    save_config(config)

    is_enabled = config.get("enabled", True)
    if is_enabled:
        active_gains = config["gains"]
        preamp = config.get("preamp", 0.0)
    else:
        # Bypass mode: maintain audio stream alive with transparent 0.0 dB pass-through
        active_gains = [0.0] * len(BANDS_SPEC)
        preamp = 0.0

    write_pipewire_conf(active_gains)

    if is_service_running():
        success = restart_service()
    else:
        success = start_service()

    if success:
        apply_preamp_volume(preamp)
        set_default_sink()

    return success
