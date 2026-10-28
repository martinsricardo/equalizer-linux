"""Default equalizer presets and frequency band definitions."""

BANDS_SPEC = [
    {"index": 0, "freq": 31.0,   "type": "bq_lowshelf",  "q": 1.0, "label": "31 Hz",  "desc": "Sub-graves"},
    {"index": 1, "freq": 63.0,   "type": "bq_peaking",   "q": 1.4, "label": "63 Hz",  "desc": "Graves"},
    {"index": 2, "freq": 125.0,  "type": "bq_peaking",   "q": 1.4, "label": "125 Hz", "desc": "Médio-graves"},
    {"index": 3, "freq": 250.0,  "type": "bq_peaking",   "q": 1.4, "label": "250 Hz", "desc": "Corpo"},
    {"index": 4, "freq": 500.0,  "type": "bq_peaking",   "q": 1.4, "label": "500 Hz", "desc": "Médios"},
    {"index": 5, "freq": 1000.0, "type": "bq_peaking",   "q": 1.4, "label": "1 kHz",  "desc": "Médios altos"},
    {"index": 6, "freq": 2000.0, "type": "bq_peaking",   "q": 1.4, "label": "2 kHz",  "desc": "Presença"},
    {"index": 7, "freq": 4000.0, "type": "bq_peaking",   "q": 1.4, "label": "4 kHz",  "desc": "Clareza"},
    {"index": 8, "freq": 8000.0, "type": "bq_peaking",   "q": 1.4, "label": "8 kHz",  "desc": "Agudos"},
    {"index": 9, "freq": 16000.0, "type": "bq_highshelf", "q": 1.0, "label": "16 kHz", "desc": "Brilho / Ar"},
]

DEFAULT_PRESETS = {
    "Plano (Flat)": {
        "description": "Som sem alterações (resposta de frequência neutra)",
        "gains": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "preamp": 0.0
    },
    "Reforço de Graves (Bass Boost)": {
        "description": "Graves encorpados e profundos para música moderna",
        "gains": [6.0, 5.0, 3.5, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "preamp": -1.5
    },
    "Super Graves (Extreme Bass)": {
        "description": "Graves potentes e com impacto máximo",
        "gains": [9.0, 7.5, 5.0, 2.0, 0.0, -1.0, 0.0, 0.0, 1.0, 1.5],
        "preamp": -3.0
    },
    "Reforço de Agudos (Treble Boost)": {
        "description": "Acentuação de agudos e brilho em sons e pratos",
        "gains": [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.5, 4.5, 6.0, 7.0],
        "preamp": -1.5
    },
    "Rock": {
        "description": "Curva clássica em V com graves fortes e guitarras nítidas",
        "gains": [4.5, 3.0, 1.5, 0.0, -1.0, -0.5, 1.5, 3.0, 4.0, 4.5],
        "preamp": -1.0
    },
    "Pop": {
        "description": "Voz limpa e presente com graves redondos e agradáveis",
        "gains": [1.5, 2.5, 3.5, 2.0, 0.0, -1.0, 0.5, 2.0, 3.0, 3.5],
        "preamp": -1.0
    },
    "Eletrónica / Dance (EDM)": {
        "description": "Sub-graves pulsantes e altas frequências brilhantes",
        "gains": [6.5, 5.5, 2.0, 0.0, -1.5, 1.0, 1.5, 3.5, 5.0, 5.5],
        "preamp": -2.0
    },
    "Voz / Podcasts / Diálogos": {
        "description": "Corte de ruídos graves e destaque para frequências da fala",
        "gains": [-3.0, -2.0, -0.5, 1.0, 3.0, 3.5, 3.0, 1.5, 0.0, -1.5],
        "preamp": 0.0
    },
    "Jazz": {
        "description": "Equilíbrio orgânico e quente para instrumentos acústicos",
        "gains": [3.0, 2.0, 1.0, 1.5, -1.0, -1.0, 0.0, 1.5, 2.5, 3.0],
        "preamp": 0.0
    },
    "Heavy Metal": {
        "description": "Graves secos, médios escavados e ataque de guitarras",
        "gains": [5.0, 4.0, 1.5, -1.5, -2.5, -1.0, 2.0, 4.0, 5.0, 4.0],
        "preamp": -1.5
    },
    "Gaming (Passos & Efeitos)": {
        "description": "Atenua estrondos e amplia sons de passos e movimentação",
        "gains": [-2.0, -1.0, 0.5, 1.0, 2.0, 4.0, 5.0, 4.5, 3.0, 2.0],
        "preamp": 0.0
    },
    "Acústico": {
        "description": "Calor suave para violão, cordas e gravações acústicas",
        "gains": [3.0, 2.5, 1.5, 1.0, 1.0, 1.5, 2.0, 3.0, 3.5, 3.0],
        "preamp": -0.5
    }
}
