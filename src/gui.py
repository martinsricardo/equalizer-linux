"""Modern graphical user interface for Linux Equalizer using Tkinter."""

import math
import os
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import List, Optional

from .core import (
    apply_settings,
    delete_custom_preset,
    disable_autostart,
    enable_autostart,
    is_service_enabled,
    is_service_running,
    load_config,
    load_presets,
    save_custom_preset,
)
from .presets import BANDS_SPEC, DEFAULT_PRESETS

# Dark Theme Palette
THEME = {
    "bg_dark": "#121418",
    "bg_card": "#1c2028",
    "bg_card_lighter": "#252b36",
    "accent_cyan": "#00d2ff",
    "accent_blue": "#3a86ff",
    "accent_green": "#10b981",
    "accent_orange": "#f59e0b",
    "accent_red": "#ef4444",
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#2d3748",
    "grid_line": "#263040",
}


class EqualizerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Equalizador Linux")
        self.root.geometry("860x650")
        self.root.minsize(780, 580)
        self.root.configure(bg=THEME["bg_dark"])

        self.config = load_config()
        self.presets = load_presets()

        self.band_vars: List[tk.DoubleVar] = []
        self.val_labels: List[tk.Label] = []
        self.preamp_var = tk.DoubleVar(value=self.config.get("preamp", 0.0))
        self.enabled_var = tk.BooleanVar(value=self.config.get("enabled", True))
        self.autostart_var = tk.BooleanVar(value=is_service_enabled())

        self.apply_timer = None
        self._init_styles()
        self._build_ui()
        self._load_current_values()

    def _init_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Configure dark Combobox
        style.configure(
            "Dark.TCombobox",
            fieldbackground=THEME["bg_card_lighter"],
            background=THEME["bg_card"],
            foreground=THEME["text_primary"],
            arrowcolor=THEME["accent_cyan"],
            bordercolor=THEME["border"],
            darkcolor=THEME["bg_card"],
            lightcolor=THEME["bg_card"],
        )

        # Configure dark Checkbutton
        style.configure(
            "Dark.TCheckbutton",
            background=THEME["bg_dark"],
            foreground=THEME["text_primary"],
            font=("Ubuntu", 10),
        )

    def _build_ui(self):
        # 1. Top Header Bar
        header = tk.Frame(self.root, bg=THEME["bg_dark"], padx=18, pady=12)
        header.pack(fill=tk.X)

        title_frame = tk.Frame(header, bg=THEME["bg_dark"])
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        title_lbl = tk.Label(
            title_frame,
            text="🎚️ EQUALIZADOR LINUX",
            font=("Ubuntu", 16, "bold"),
            fg=THEME["accent_cyan"],
            bg=THEME["bg_dark"],
        )
        title_lbl.pack(anchor="w")

        self.status_lbl = tk.Label(
            title_frame,
            text="● Ativo em segundo plano",
            font=("Ubuntu", 9),
            fg=THEME["accent_green"],
            bg=THEME["bg_dark"],
        )
        self.status_lbl.pack(anchor="w", pady=(2, 0))

        # Top Right Controls (Power/Bypass switch)
        btn_frame = tk.Frame(header, bg=THEME["bg_dark"])
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.power_btn = tk.Button(
            btn_frame,
            text="LIGADO" if self.enabled_var.get() else "BYPASS",
            font=("Ubuntu", 10, "bold"),
            bg=THEME["accent_green"] if self.enabled_var.get() else THEME["accent_red"],
            fg="#ffffff",
            activebackground=THEME["accent_cyan"],
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._toggle_power,
        )
        self.power_btn.pack(side=tk.RIGHT)

        # 2. Preset Selection Bar
        preset_bar = tk.Frame(self.root, bg=THEME["bg_card"], padx=18, pady=10, relief="solid", bd=1)
        preset_bar.pack(fill=tk.X, padx=14, pady=(0, 10))

        lbl_preset = tk.Label(
            preset_bar,
            text="Preset:",
            font=("Ubuntu", 10, "bold"),
            fg=THEME["text_primary"],
            bg=THEME["bg_card"],
        )
        lbl_preset.pack(side=tk.LEFT, padx=(0, 8))

        self.preset_combo = ttk.Combobox(
            preset_bar,
            style="Dark.TCombobox",
            state="readonly",
            values=list(self.presets.keys()),
            width=28,
            font=("Ubuntu", 10),
        )
        self.preset_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        # Preset action buttons
        btn_save = tk.Button(
            preset_bar,
            text="💾 Guardar Novo",
            font=("Ubuntu", 9),
            bg=THEME["bg_card_lighter"],
            fg=THEME["text_primary"],
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._save_preset_dialog,
        )
        btn_save.pack(side=tk.LEFT, padx=4)

        btn_del = tk.Button(
            preset_bar,
            text="🗑️ Eliminar",
            font=("Ubuntu", 9),
            bg=THEME["bg_card_lighter"],
            fg=THEME["text_secondary"],
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._delete_current_preset,
        )
        btn_del.pack(side=tk.LEFT, padx=4)

        btn_reset = tk.Button(
            preset_bar,
            text="↺ Redefinir (0 dB)",
            font=("Ubuntu", 9),
            bg=THEME["bg_card_lighter"],
            fg=THEME["accent_orange"],
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._reset_flat,
        )
        btn_reset.pack(side=tk.RIGHT, padx=4)

        # 3. Audio Curve Visualizer Canvas
        vis_frame = tk.Frame(self.root, bg=THEME["bg_card"], padx=10, pady=8, relief="solid", bd=1)
        vis_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        self.canvas = tk.Canvas(
            vis_frame,
            bg=THEME["bg_dark"],
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self._draw_curve())

        # 4. EQ Sliders Frame
        sliders_card = tk.Frame(self.root, bg=THEME["bg_card"], padx=14, pady=10, relief="solid", bd=1)
        sliders_card.pack(fill=tk.X, padx=14, pady=(0, 10))

        sliders_inner = tk.Frame(sliders_card, bg=THEME["bg_card"])
        sliders_inner.pack(fill=tk.X, expand=True)

        # 10 Band Faders
        for i, spec in enumerate(BANDS_SPEC):
            fader_col = tk.Frame(sliders_inner, bg=THEME["bg_card"])
            fader_col.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=2)

            # Gain readout at top
            v_var = tk.DoubleVar(value=0.0)
            self.band_vars.append(v_var)

            lbl_val = tk.Label(
                fader_col,
                text=" 0.0 dB",
                font=("Ubuntu", 8, "bold"),
                fg=THEME["accent_cyan"],
                bg=THEME["bg_card"],
            )
            lbl_val.pack(pady=(0, 2))
            self.val_labels.append(lbl_val)

            # Vertical scale (-15 to +15)
            scale = tk.Scale(
                fader_col,
                from_=15.0,
                to=-15.0,
                resolution=0.5,
                orient=tk.VERTICAL,
                variable=v_var,
                showvalue=False,
                bg=THEME["bg_card_lighter"],
                troughcolor=THEME["bg_dark"],
                activebackground=THEME["accent_cyan"],
                highlightthickness=0,
                bd=0,
                width=16,
                length=150,
                sliderrelief="flat",
                cursor="hand2",
                command=lambda val, idx=i: self._on_slider_change(idx, val),
            )
            scale.pack(fill=tk.Y, pady=2)
            # Double-click resets band to 0.0
            scale.bind("<Double-Button-1>", lambda e, idx=i: self._reset_single_band(idx))

            # Freq label
            lbl_freq = tk.Label(
                fader_col,
                text=spec["label"],
                font=("Ubuntu", 9, "bold"),
                fg=THEME["text_primary"],
                bg=THEME["bg_card"],
            )
            lbl_freq.pack(pady=(2, 0))

            # Description (e.g., Graves, Agudos)
            lbl_desc = tk.Label(
                fader_col,
                text=spec["desc"][:7],
                font=("Ubuntu", 7),
                fg=THEME["text_muted"],
                bg=THEME["bg_card"],
            )
            lbl_desc.pack()

        # Separator between bands and Preamp
        sep = tk.Frame(sliders_inner, width=2, bg=THEME["border"])
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=6)

        # Preamp Fader Column
        preamp_col = tk.Frame(sliders_inner, bg=THEME["bg_card"])
        preamp_col.pack(side=tk.LEFT, expand=False, fill=tk.BOTH, padx=4)

        self.preamp_val_lbl = tk.Label(
            preamp_col,
            text=f"{self.preamp_var.get():+.1f} dB",
            font=("Ubuntu", 8, "bold"),
            fg=THEME["accent_orange"],
            bg=THEME["bg_card"],
        )
        self.preamp_val_lbl.pack(pady=(0, 2))

        preamp_scale = tk.Scale(
            preamp_col,
            from_=15.0,
            to=-15.0,
            resolution=0.5,
            orient=tk.VERTICAL,
            variable=self.preamp_var,
            showvalue=False,
            bg=THEME["bg_card_lighter"],
            troughcolor=THEME["bg_dark"],
            activebackground=THEME["accent_orange"],
            highlightthickness=0,
            bd=0,
            width=16,
            length=150,
            sliderrelief="flat",
            cursor="hand2",
            command=self._on_preamp_change,
        )
        preamp_scale.pack(fill=tk.Y, pady=2)
        preamp_scale.bind("<Double-Button-1>", lambda e: self._reset_preamp())

        lbl_preamp = tk.Label(
            preamp_col,
            text="Preamp",
            font=("Ubuntu", 9, "bold"),
            fg=THEME["accent_orange"],
            bg=THEME["bg_card"],
        )
        lbl_preamp.pack(pady=(2, 0))

        lbl_preamp_desc = tk.Label(
            preamp_col,
            text="Ganho",
            font=("Ubuntu", 7),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
        )
        lbl_preamp_desc.pack()

        # 5. Bottom Status and Autostart Bar
        bottom_bar = tk.Frame(self.root, bg=THEME["bg_dark"], padx=18, pady=8)
        bottom_bar.pack(fill=tk.X)

        cb_autostart = ttk.Checkbutton(
            bottom_bar,
            text="Iniciar automaticamente com o computador (Systemd)",
            style="Dark.TCheckbutton",
            variable=self.autostart_var,
            command=self._toggle_autostart,
        )
        cb_autostart.pack(side=tk.LEFT)

        tip_lbl = tk.Label(
            bottom_bar,
            text="💡 O equalizador continua a funcionar após fechar a janela",
            font=("Ubuntu", 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_dark"],
        )
        tip_lbl.pack(side=tk.RIGHT)

    def _load_current_values(self):
        """Load values from config into controls."""
        gains = self.config.get("gains", [0.0] * 10)
        for i, val in enumerate(gains):
            self.band_vars[i].set(val)
            self._update_label(i, val)

        self.preamp_var.set(self.config.get("preamp", 0.0))
        self.preamp_val_lbl.config(text=f"{self.preamp_var.get():+.1f} dB")

        active_preset = self.config.get("active_preset", "Plano (Flat)")
        if active_preset in self.presets:
            self.preset_combo.set(active_preset)
        else:
            self.preset_combo.set("Personalizado")

        self._update_status_display()
        self.root.after(50, self._draw_curve)

    def _update_label(self, idx: int, val: float):
        sign = "+" if val > 0 else ""
        color = THEME["accent_cyan"] if val != 0 else THEME["text_secondary"]
        self.val_labels[idx].config(text=f"{sign}{val:4.1f} dB", fg=color)

    def _on_slider_change(self, idx: int, val: str):
        v = float(val)
        self._update_label(idx, v)
        self._draw_curve()
        self._schedule_apply()

    def _on_preamp_change(self, val: str):
        v = float(val)
        self.preamp_val_lbl.config(text=f"{v:+.1f} dB")
        self._schedule_apply()

    def _reset_single_band(self, idx: int):
        self.band_vars[idx].set(0.0)
        self._update_label(idx, 0.0)
        self._draw_curve()
        self._schedule_apply()

    def _reset_preamp(self):
        self.preamp_var.set(0.0)
        self.preamp_val_lbl.config(text=" 0.0 dB")
        self._schedule_apply()

    def _schedule_apply(self):
        """Debounce applying settings to avoid flooding PipeWire while dragging sliders."""
        if self.apply_timer:
            self.root.after_cancel(self.apply_timer)
        self.apply_timer = self.root.after(150, self._apply_now)

    def _apply_now(self):
        gains = [round(v.get(), 1) for v in self.band_vars]
        self.config["gains"] = gains
        self.config["preamp"] = round(self.preamp_var.get(), 1)
        self.config["enabled"] = self.enabled_var.get()
        apply_settings(self.config)
        self._update_status_display()

    def _toggle_power(self):
        new_state = not self.enabled_var.get()
        self.enabled_var.set(new_state)
        self.config["enabled"] = new_state
        self.power_btn.config(
            text="LIGADO" if new_state else "BYPASS",
            bg=THEME["accent_green"] if new_state else THEME["accent_red"],
        )
        self._apply_now()

    def _toggle_autostart(self):
        if self.autostart_var.get():
            enable_autostart()
        else:
            disable_autostart()

    def _on_preset_selected(self, event=None):
        name = self.preset_combo.get()
        if name in self.presets:
            p = self.presets[name]
            gains = p.get("gains", [0.0] * 10)
            for i, g in enumerate(gains):
                self.band_vars[i].set(g)
                self._update_label(i, g)
            preamp = p.get("preamp", 0.0)
            self.preamp_var.set(preamp)
            self.preamp_val_lbl.config(text=f"{preamp:+.1f} dB")
            self.config["active_preset"] = name
            self._draw_curve()
            self._apply_now()

    def _reset_flat(self):
        for i in range(len(self.band_vars)):
            self.band_vars[i].set(0.0)
            self._update_label(i, 0.0)
        self.preamp_var.set(0.0)
        self.preamp_val_lbl.config(text=" 0.0 dB")
        self.preset_combo.set("Plano (Flat)")
        self.config["active_preset"] = "Plano (Flat)"
        self._draw_curve()
        self._apply_now()

    def _save_preset_dialog(self):
        name = simpledialog.askstring("Guardar Preset", "Nome do novo preset:", parent=self.root)
        if name and name.strip():
            name = name.strip()
            gains = [round(v.get(), 1) for v in self.band_vars]
            preamp = round(self.preamp_var.get(), 1)
            save_custom_preset(name, gains, preamp)
            self.presets = load_presets()
            self.preset_combo.config(values=list(self.presets.keys()))
            self.preset_combo.set(name)
            self.config["active_preset"] = name
            self._apply_now()

    def _delete_current_preset(self):
        name = self.preset_combo.get()
        if name in DEFAULT_PRESETS:
            messagebox.showinfo("Informação", "Não é possível eliminar os presets padrão do sistema.", parent=self.root)
            return
        if messagebox.askyesno("Confirmar", f"Tem a certeza de que deseja eliminar o preset '{name}'?", parent=self.root):
            delete_custom_preset(name)
            self.presets = load_presets()
            self.preset_combo.config(values=list(self.presets.keys()))
            self._reset_flat()

    def _update_status_display(self):
        running = is_service_running()
        if not self.enabled_var.get():
            self.status_lbl.config(text="○ Desativado (Modo Bypass - Áudio Direto)", fg=THEME["text_muted"])
        elif running:
            self.status_lbl.config(text="● Ativo em segundo plano (PipeWire DSP)", fg=THEME["accent_green"])
        else:
            self.status_lbl.config(text="○ Serviço parado", fg=THEME["accent_red"])

    def _draw_curve(self):
        """Draw a smooth frequency response curve on the canvas."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 50 or h < 50:
            return

        self.canvas.delete("all")

        # Range: -15 dB to +15 dB
        y_zero = h / 2.0
        db_scale = (h - 40) / 30.0  # 30 dB total range

        # Grid lines (+12, +6, 0, -6, -12 dB)
        for db in [12, 6, 0, -6, -12]:
            y = y_zero - (db * db_scale)
            color = THEME["border"] if db == 0 else THEME["grid_line"]
            dash = () if db == 0 else (4, 4)
            width = 1.5 if db == 0 else 1
            self.canvas.create_line(0, y, w, y, fill=color, dash=dash, width=width)
            self.canvas.create_text(
                16, y - 6, text=f"{db:+} dB", fill=THEME["text_muted"], font=("Ubuntu", 7)
            )

        # Calculate points for 10 bands
        margin_x = 35
        usable_w = w - (margin_x * 2)
        n = len(self.band_vars)
        step_x = usable_w / (n - 1)

        points = []
        for i, var in enumerate(self.band_vars):
            x = margin_x + (i * step_x)
            db_val = var.get()
            y = y_zero - (db_val * db_scale)
            points.append((x, y))

            # Vertical dotted guideline
            self.canvas.create_line(x, 0, x, h, fill=THEME["grid_line"], dash=(2, 4))

        # Generate a smooth Catmull-Rom spline through points
        dense_points = []
        num_dense = 150
        for step in range(num_dense + 1):
            t_global = step / num_dense * (n - 1)
            idx = int(t_global)
            if idx >= n - 1:
                idx = n - 2
                t = 1.0
            else:
                t = t_global - idx

            p0 = points[max(0, idx - 1)]
            p1 = points[idx]
            p2 = points[min(n - 1, idx + 1)]
            p3 = points[min(n - 1, idx + 2)]

            # Catmull-Rom interpolation for y
            t2 = t * t
            t3 = t2 * t
            y_interp = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            x_interp = margin_x + (t_global * step_x)
            dense_points.append((x_interp, y_interp))

        # Draw filled gradient/polygon under curve
        poly_coords = [dense_points[0][0], y_zero]
        for px, py in dense_points:
            poly_coords.extend([px, py])
        poly_coords.extend([dense_points[-1][0], y_zero])

        fill_color = "#142c3d" if self.enabled_var.get() else "#1c2229"
        self.canvas.create_polygon(poly_coords, fill=fill_color, outline="")

        # Draw zero line on top of fill
        self.canvas.create_line(0, y_zero, w, y_zero, fill=THEME["border"], width=1.5)

        # Draw response line
        line_coords = []
        for px, py in dense_points:
            line_coords.extend([px, py])

        curve_color = THEME["accent_cyan"] if self.enabled_var.get() else THEME["text_muted"]
        self.canvas.create_line(line_coords, fill=curve_color, width=2.5, smooth=True)

        # Draw control node dots
        for i, (px, py) in enumerate(points):
            r = 4.5
            dot_color = THEME["accent_cyan"] if self.enabled_var.get() else THEME["text_muted"]
            self.canvas.create_oval(
                px - r, py - r, px + r, py + r, fill=dot_color, outline="#ffffff", width=1.5
            )


def launch_gui():
    """Launch the Tkinter Equalizer application."""
    root = tk.Tk()
    app = EqualizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
