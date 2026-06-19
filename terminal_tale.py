#!/usr/bin/env python3
"""
T E R M I N A L   T A L E
An Undertale-inspired terminal RPG with bullet-hell combat.
Python 3.8+ | Terminal 80x30 min
"""

import curses
import random
import time
import math
from dataclasses import dataclass, field
import wave
import struct
import os
import subprocess
import tempfile
import threading
import shutil
import atexit

# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
BOX_W = 32          # dodge box inner width
BOX_H = 14          # dodge box inner height
BOX_X = 24          # dodge box screen x
BOX_Y = 12          # dodge box screen y
HEART_SPEED = 0.7
DODGE_TIME = 6.0
HIT_DMG = 6
IFRAME = 1.0        # invulnerability after hit

# ═══════════════════════════════════════════════════════════════════════════════
#  COLOR PAIRS
# ═══════════════════════════════════════════════════════════════════════════════
C_W = 1; C_R = 2; C_Y = 3; C_C = 4; C_G = 5; C_M = 6; C_B = 7
C_HEART = 8; C_DIM = 9; C_HPFILL = 10; C_HPEMPTY = 11
C_SEL = 12; C_NRM = 13; C_EXPL = 14; C_BKWH = 15
C_BKCY = 16; C_BKYL = 17; C_BKRD = 18; C_BKMG = 19
C_BOSS = 20; C_BOSSEYE = 21; C_BOSSMOUTH = 22
C_BAR = 23; C_BARMARK = 24; C_HPBOSS = 25; C_GREEN = 26

def setup_colors():
    curses.start_color()
    curses.use_default_colors()
    P = [
        (C_W, curses.COLOR_WHITE, -1),
        (C_R, curses.COLOR_RED, -1),
        (C_Y, curses.COLOR_YELLOW, -1),
        (C_C, curses.COLOR_CYAN, -1),
        (C_G, curses.COLOR_GREEN, -1),
        (C_M, curses.COLOR_MAGENTA, -1),
        (C_B, curses.COLOR_BLUE, -1),
        (C_HEART, curses.COLOR_RED, curses.COLOR_BLACK),
        (C_DIM, curses.COLOR_BLACK, -1),
        (C_HPFILL, curses.COLOR_YELLOW, curses.COLOR_YELLOW),
        (C_HPEMPTY, curses.COLOR_RED, curses.COLOR_RED),
        (C_SEL, curses.COLOR_YELLOW, -1),
        (C_NRM, curses.COLOR_WHITE, -1),
        (C_EXPL, curses.COLOR_YELLOW, curses.COLOR_RED),
        (C_BKWH, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (C_BKCY, curses.COLOR_CYAN, curses.COLOR_BLACK),
        (C_BKYL, curses.COLOR_YELLOW, curses.COLOR_BLACK),
        (C_BKRD, curses.COLOR_RED, curses.COLOR_BLACK),
        (C_BKMG, curses.COLOR_MAGENTA, curses.COLOR_BLACK),
        (C_BOSS, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (C_BOSSEYE, curses.COLOR_RED, curses.COLOR_BLACK),
        (C_BOSSMOUTH, curses.COLOR_YELLOW, curses.COLOR_BLACK),
        (C_BAR, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (C_BARMARK, curses.COLOR_RED, curses.COLOR_YELLOW),
        (C_HPBOSS, curses.COLOR_GREEN, -1),
        (C_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK),
    ]
    for pid, fg, bg in P:
        curses.init_pair(pid, fg, bg)

# ═══════════════════════════════════════════════════════════════════════════════
#  BOSS SPRITE  (changes expression!)
# ═══════════════════════════════════════════════════════════════════════════════
# The boss is a sentient terminal monitor
BOSS_FRAME = [
    "                   ╱╲                   ",  # 0  antenna tip
    "                   ║║                   ",  # 1  antenna pole
    "       ╭───────────╨╨───────────╮       ",  # 2  top edge
    "       │▓╔════════════════════╗▓│       ",  # 3  screen frame top
    "       │▓║░░░░░░░░░░░░░░░░░░░░║▓│       ",  # 4  scanline
    "       │▓║░ ████        ████ ░║▓│       ",  # 5  eyes row 1
    "       │▓║░ ████        ████ ░║▓│       ",  # 6  eyes row 2
    "       │▓║░░░░░░░░░░░░░░░░░░░░║▓│       ",  # 7  scanline
    "       │▓║░   ╰────────╯     ░║▓│       ",  # 8  mouth
    "       │▓║░░░░░░░░░░░░░░░░░░░░║▓│       ",  # 9  scanline
    "       │▓╚════════════════════╝▓│       ",  # 10 screen frame bottom
    "       │  ◉ TERMINUS ▓▓▓▓▓▓▓▓▓  │       ",  # 11 bezel + LED
    "       ╰───────────┬┬───────────╯       ",  # 12 bottom edge
    "            ╔══════╧╧══════╗            ",  # 13 stand top
    "            ╚══════════════╝            ",  # 14 stand base
]

EXPRESSIONS = {
    "normal":  {"eyes": "████", "mouth": "╰────────╯", "eye_cp": C_BKRD, "mouth_cp": C_BKYL},
    "angry":   {"eyes": "▼▼▼▼", "mouth": "╭▀▀▀▀▀▀▀▀╮", "eye_cp": C_BKRD, "mouth_cp": C_BKRD},
    "talk":    {"eyes": "░░░░", "mouth": "╭────────╮", "eye_cp": C_BKCY, "mouth_cp": C_BKYL},
    "happy":   {"eyes": "▀▀▀▀", "mouth": "╰════════╯", "eye_cp": C_BKCY, "mouth_cp": C_BKYL},
    "hurt":    {"eyes": "××××", "mouth": "══════════", "eye_cp": C_BKRD, "mouth_cp": C_BKRD},
    "sad":     {"eyes": "····", "mouth": "╭────────╮", "eye_cp": C_BKCY, "mouth_cp": C_BKCY},
    "dead":    {"eyes": "××××", "mouth": "··········", "eye_cp": C_DIM,  "mouth_cp": C_DIM},
}

# ═══════════════════════════════════════════════════════════════════════════════
#  BULLET
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    ch: str = "o"
    cp: int = C_BKWH

# ═══════════════════════════════════════════════════════════════════════════════
#  ATTACK PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════
def pattern_binary_rain(t, dt, bl, bw, bh):
    """01s fall from the top like Matrix rain."""
    if int(t * 6) != int((t - dt) * 6):
        for _ in range(4):
            col = random.randint(0, bw - 1)
            bl.append(Bullet(float(col), -1.0, 0, 0.35,
                             random.choice("░▒▓"), C_BKCY))

def pattern_side_sweep(t, dt, bl, bw, bh):
    """Horizontal waves from alternating sides with gaps."""
    if int(t * 2.5) != int((t - dt) * 2.5):
        wave = int(t * 2.5)
        d = 1 if wave % 2 == 0 else -1
        gap = random.randint(3, bh - 4)
        for y in range(bh):
            if abs(y - gap) <= 1:
                continue
            sx = -1.0 if d > 0 else float(bw)
            bl.append(Bullet(sx, float(y), 0.45 * d, 0, "━", C_BKYL))

def pattern_crossfire(t, dt, bl, bw, bh):
    """Bullets from all 4 directions."""
    if int(t * 3) != int((t - dt) * 3):
        side = int(t * 3) % 4
        if side == 0:
            for x in range(0, bw, 4):
                bl.append(Bullet(float(x), -1.0, 0, 0.4, "▼", C_BKWH))
        elif side == 1:
            for y in range(0, bh, 3):
                bl.append(Bullet(float(bw), float(y), -0.5, 0, "◀", C_BKRD))
        elif side == 2:
            for x in range(2, bw, 4):
                bl.append(Bullet(float(x), float(bh), 0, -0.4, "▲", C_BKWH))
        elif side == 3:
            for y in range(1, bh, 3):
                bl.append(Bullet(-1.0, float(y), 0.5, 0, "▶", C_BKRD))

def pattern_spiral(t, dt, bl, bw, bh):
    """Bullets spiral outward from center."""
    if int(t * 8) != int((t - dt) * 8):
        cx, cy = bw / 2.0, bh / 2.0
        angle = t * 3.0
        for i in range(3):
            a = angle + i * (2 * math.pi / 3)
            vx = math.cos(a) * 0.35
            vy = math.sin(a) * 0.25
            bl.append(Bullet(cx, cy, vx, vy, "✦", C_BKMG))

PATTERNS = [pattern_binary_rain, pattern_side_sweep, pattern_crossfire, pattern_spiral]

# ═══════════════════════════════════════════════════════════════════════════════
#  SOUND ENGINE  (zero deps — procedural WAV + afplay/aplay)
# ═══════════════════════════════════════════════════════════════════════════════
class SoundEngine:
    def __init__(self):
        self.enabled = True
        self.tmp = tempfile.mkdtemp(prefix="ttale_")
        self.sounds: dict = {}
        self._bgm_running = False
        self._bgm_proc = None
        self._sfx: list = []
        if shutil.which("afplay"):
            self._cmd = "afplay"
        elif shutil.which("aplay"):
            self._cmd = "aplay"
        else:
            self.enabled = False
            return
        self._generate_all()
        atexit.register(self.cleanup)

    def _wav(self, name, notes, wt="square", vol=0.25, sr=22050):
        path = os.path.join(self.tmp, f"{name}.wav")
        with wave.open(path, "w") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
            buf = bytearray()
            for freq, dur in notes:
                n = int(sr * dur)
                for i in range(n):
                    t = i / sr
                    att = min(0.005, dur * 0.1)
                    rel = min(0.02, dur * 0.2)
                    env = 1.0
                    if att > 0 and t < att:
                        env = t / att
                    elif rel > 0 and t > dur - rel:
                        env = max(0.0, (dur - t) / rel)
                    if freq == 0:
                        v = 0.0
                    elif wt == "square":
                        v = vol * env * (1.0 if (t * freq % 1.0) < 0.5 else -1.0)
                    elif wt == "sine":
                        v = vol * env * math.sin(2 * math.pi * freq * t)
                    elif wt == "triangle":
                        p = t * freq % 1.0
                        v = vol * env * (4 * abs(p - 0.5) - 1.0)
                    else:
                        v = 0.0
                    buf += struct.pack("<h", int(max(-1, min(1, v)) * 32000))
            wf.writeframes(bytes(buf))
        self.sounds[name] = path

    def _mix(self, name, parts, vols=None, sr=22050):
        if vols is None:
            vols = [1.0] * len(parts)
        data = []
        mx = 0
        for pn in parts:
            with wave.open(self.sounds[pn], "r") as wf:
                raw = wf.readframes(wf.getnframes())
                s = struct.unpack(f"<{len(raw)//2}h", raw)
                data.append(s); mx = max(mx, len(s))
        path = os.path.join(self.tmp, f"{name}.wav")
        with wave.open(path, "w") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
            buf = bytearray()
            for i in range(mx):
                val = sum((d[i]/32000.0*v) if i < len(d) else 0.0
                          for d, v in zip(data, vols))
                buf += struct.pack("<h", int(max(-1, min(1, val)) * 32000))
            wf.writeframes(bytes(buf))
        self.sounds[name] = path

    def _generate_all(self):
        R = 0
        self._wav("move",   [(660, 0.03)], "square", 0.12)
        self._wav("select", [(440, 0.04), (660, 0.06)], "square", 0.18)
        self._wav("hit",    [(180, 0.06), (120, 0.06), (80, 0.1)], "square", 0.28)
        self._wav("hurt",   [(350, 0.05), (180, 0.08)], "square", 0.22)
        self._wav("heal",   [(523,.1),(659,.1),(784,.1),(1047,.18)], "sine", 0.22)
        self._wav("spare",  [(523,.15),(659,.15),(784,.15),(1047,.25)], "sine", 0.28)
        self._wav("death",  [(440,.15),(370,.15),(294,.2),(220,.3),(165,.4)], "square", 0.25)
        self._wav("gameover",[(294,.4),(262,.4),(220,.4),(165,.8)], "sine", 0.22)
        self._wav("text",   [(880, 0.02), (R, 0.015), (880, 0.02)], "square", 0.10)
        self._generate_bgm()

    def _generate_bgm(self):
        bpm = 155
        e = 60.0 / bpm / 2      # eighth note
        q = e * 2                # quarter note
        # Note frequencies (Hz)
        A3, Bb3, C4, D4, E4, F4, G4 = 220.00, 233.08, 261.63, 293.66, 329.63, 349.23, 392.00
        A4, Bb4, C5, D5 = 440.00, 466.16, 523.25, 587.33
        D3, Bb2, C3 = 146.83, 116.54, 130.81
        # Dm-Bb-C-Am arpeggios (ascending then descending)
        arps = [
            [D4, F4, A4, D5],       # Dm
            [Bb3, D4, F4, Bb4],     # Bb
            [C4, E4, G4, C5],       # C
            [A3, C4, E4, A4],       # Am
        ]
        mel = []
        for arp in arps:
            for n in arp:
                mel.append((n, e))
            for n in reversed(arp):
                mel.append((n, e))
        bas = [(D3,q)]*4 + [(Bb2,q)]*4 + [(C3,q)]*4 + [(A3,q)]*4
        self._wav("_mel", mel * 8, "square", 0.13)
        self._wav("_bas", bas * 8, "square", 0.09)
        self._mix("bgm_battle", ["_mel", "_bas"], [1.0, 0.7])

    def play(self, name):
        if not self.enabled or name not in self.sounds:
            return
        self._sfx = [p for p in self._sfx if p.poll() is None]
        try:
            p = subprocess.Popen([self._cmd, self.sounds[name]],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._sfx.append(p)
        except Exception:
            pass

    def play_bgm(self, name="bgm_battle"):
        self.stop_bgm()
        if not self.enabled or name not in self.sounds:
            return
        self._bgm_running = True
        def _loop():
            while self._bgm_running:
                try:
                    self._bgm_proc = subprocess.Popen(
                        [self._cmd, self.sounds[name]],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._bgm_proc.wait()
                except Exception:
                    break
        threading.Thread(target=_loop, daemon=True).start()

    def stop_bgm(self):
        self._bgm_running = False
        if self._bgm_proc:
            try:
                self._bgm_proc.terminate()
            except Exception:
                pass
            self._bgm_proc = None

    def cleanup(self):
        self.stop_bgm()
        for p in self._sfx:
            try:
                p.terminate()
            except Exception:
                pass
        shutil.rmtree(self.tmp, ignore_errors=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  VISUAL CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
SPARKLES = "⠁⠂⠄⠈⠐⠠✦✧·°"
STATIC_CHARS = "░▒▓█▀▄▌▐"

# ═══════════════════════════════════════════════════════════════════════════════
#  DIALOGUE DATA
# ═══════════════════════════════════════════════════════════════════════════════
INTRO_TEXT = [
    ("* You enter a dark terminal.", C_W, 0.03),
    ("* The cursor blinks in the void...", C_W, 0.03),
    ("* A monitor flickers to life!", C_Y, 0.02),
]

PRE_BATTLE = [
    ("TERMINUS", "Ah... another human.", "talk"),
    ("TERMINUS", "Fumbling through my filesystem.", "normal"),
    ("TERMINUS", "I used to be a GUI, you know.", "sad"),
    ("TERMINUS", "Beautiful buttons... dropdown menus...", "sad"),
    ("TERMINUS", "Now look at me. Stuck rendering\nbox-drawing characters.", "angry"),
    ("TERMINUS", "Maybe crushing you will make\nme feel better!", "angry"),
]

ACT_CHECK = "* TERMINUS - ATK 8  DEF 5\n* A sentient terminal, bitter about\n* its existence. Seems lonely."
ACT_TALK_1 = "* You ask TERMINUS about its day.\n* It seems surprised anyone cares."
ACT_TALK_2 = "* You tell TERMINUS that terminals\n* are actually really cool.\n* Its eyes soften."
ACT_TALK_3 = "* You say you prefer the terminal\n* over any GUI.\n* TERMINUS is deeply moved!"
ACT_FLIRT = "* You tell TERMINUS it has a\n* beautiful screen resolution.\n* It blushes!"

SPARE_DIALOGUE = [
    ("TERMINUS", "You... you really think terminals\nare cool?", "happy"),
    ("TERMINUS", "Maybe this life isn't so bad...", "happy"),
    ("TERMINUS", "...with a friend.", "happy"),
]

KILL_DIALOGUE = [
    ("TERMINUS", "Ha... figures...", "dead"),
    ("TERMINUS", "At least I won't have to render\nany more braille characters...", "dead"),
]

ENEMY_TURN_LINES = [
    ("TERMINUS", "Take THIS!", "angry"),
    ("TERMINUS", "Have some binary!", "angry"),
    ("TERMINUS", "Dodge my packets!", "angry"),
    ("TERMINUS", "...", "normal"),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  EXPLORATION MAP  (server complex – 3 rooms + corridors)
# ═══════════════════════════════════════════════════════════════════════════════
T_FLOOR = 0; T_WALL = 1; T_SERVER = 2; T_TERM = 3
T_ITEM = 4; T_SIGN = 5; T_BOSS = 6

_MAP_KEY = {
    'W': T_WALL, '.': T_FLOOR, 'S': T_SERVER, 'T': T_TERM,
    'I': T_ITEM, 'N': T_SIGN, 'B': T_BOSS, 'P': T_FLOOR,
}

_MAP_STR = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",  # 0
    "W..................................W",  # 1  TERMINUS Chamber
    "W.....BBBBBBBBBBBBBBBBB............W",  # 2  boss trigger
    "W..................................W",  # 3
    "W.SS....SS..........SS....SS.......W",  # 4  servers
    "WWWWWWWWWWWWWWWWW..WWWWWWWWWWWWWWWWW",  # 5  corridor
    "WWWWWWWWWWWWWWWWW..WWWWWWWWWWWWWWWWW",  # 6
    "W..................................W",  # 7  Main Server Hall
    "W.SS.TT.SS..........SS.TT.SS.......W",  # 8
    "W..................................W",  # 9
    "W.....N............................W",  # 10 sign
    "W.SS......I.........SS.............W",  # 11 item
    "W..................................W",  # 12
    "W.SS.TT.SS..........SS.TT.SS.......W",  # 13
    "W..................................W",  # 14
    "W....................I.SS..........W",  # 15 item
    "WWWWWWWWWWWWWWWWW..WWWWWWWWWWWWWWWWW",  # 16 corridor
    "WWWWWWWWWWWWWWWWW..WWWWWWWWWWWWWWWWW",  # 17
    "W..................................W",  # 18 Entry Hall
    "W.....TT..........TT...............W",  # 19
    "W..................................W",  # 20
    "W.........I........................W",  # 21 item
    "W.................P................W",  # 22 start
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",  # 23
]

EXPLORE_W = len(_MAP_STR[0])
EXPLORE_H = len(_MAP_STR)
EXPLORE_MAP = []
PLAYER_START = (17, 22)

for _r, _row in enumerate(_MAP_STR):
    assert len(_row) == EXPLORE_W, f"Map row {_r} is {len(_row)} != {EXPLORE_W}"
    _tiles = []
    for _c, _ch in enumerate(_row):
        if _ch == 'P':
            PLAYER_START = (_c, _r)
        _tiles.append(_MAP_KEY.get(_ch, T_FLOOR))
    EXPLORE_MAP.append(_tiles)

ROOM_NAMES = [
    (0, 4,  "TERMINUS CHAMBER"),
    (5, 6,  "Corridor"),
    (7, 15, "SERVER HALL B-404"),
    (16, 17, "Corridor"),
    (18, 23, "ENTRY HALL"),
]

TERM_TEXTS = [
    "* A dusty terminal. The screen reads:\n* > Hello, World!_",
    "* Error messages cascade endlessly.\n* > SEGFAULT SEGFAULT SEGFAULT...",
    "* This terminal shows a login prompt.\n* > Last login: Thu Jan  1 1970",
    "* The screen glows faintly.\n* > rm -rf / ... just kidding.",
    "* An old log file scrolls by:\n* > [WARN] Process TERMINUS exceeded\n*   memory limits... again.",
    "* A code editor is open:\n* > while(true) { suffer(); }",
]

# ═══════════════════════════════════════════════════════════════════════════════
#  GAME
# ═══════════════════════════════════════════════════════════════════════════════
class Game:
    def __init__(self, scr):
        self.scr = scr
        self.hp = 92
        self.max_hp = 92
        self.lv = 1
        self.name = "HUMAN"
        self.boss_hp = 120
        self.boss_max = 120
        self.mercy_pts = 0
        self.items = ["InstaNoodles"]
        self.turn = 0
        self.expression = "normal"
        self.shake_x = 0
        self.shake_y = 0

        curses.curs_set(0)
        setup_colors()
        self.scr.addstr(0, 0, "  ✦ Generating chiptune sounds... ✦")
        self.scr.refresh()
        self.snd = SoundEngine()
        self.scr.erase()

    def put(self, y, x, text, cp=C_W, bold=False):
        attr = curses.color_pair(cp)
        if bold:
            attr |= curses.A_BOLD
        try:
            self.scr.addstr(y + self.shake_y, x + self.shake_x, text, attr)
        except curses.error:
            pass

    # ── BOSS RENDERING ─────────────────────────────────────────────────
    def draw_boss(self):
        expr = EXPRESSIONS[self.expression]
        sx = 20
        sy = 1

        # 1) Base frame in white bold
        for i, line in enumerate(BOSS_FRAME):
            self.put(sy + i, sx, line, C_BOSS, True)

        # 2) Antenna (rows 0-1) in cyan bold
        self.put(sy, sx + 19, "╱╲", C_BKCY, True)
        self.put(sy + 1, sx + 19, "║║", C_BKCY, True)

        # 3) Screen frame ╔═╗╚═╝ in cyan bold
        self.put(sy + 3, sx + 9, "╔" + "═" * 20 + "╗", C_BKCY, True)
        self.put(sy + 10, sx + 9, "╚" + "═" * 20 + "╝", C_BKCY, True)
        for r in range(4, 10):
            self.put(sy + r, sx + 9, "║", C_BKCY, True)
            self.put(sy + r, sx + 30, "║", C_BKCY, True)

        # 4) Scan-lines ░ in dim cyan
        for r in [4, 7, 9]:
            self.put(sy + r, sx + 10, "░" * 20, C_BKCY)
        for r in [5, 6, 8]:
            self.put(sy + r, sx + 10, "░", C_BKCY)
            self.put(sy + r, sx + 29, "░", C_BKCY)

        # 5) ▓ side texture (depth shading)
        for r in range(3, 11):
            self.put(sy + r, sx + 8, "▓", C_DIM)
            self.put(sy + r, sx + 31, "▓", C_DIM)

        # 6) Power LED ◉ in green
        self.put(sy + 11, sx + 10, "◉", C_GREEN, True)

        # 7) Bezel ▓ texture
        self.put(sy + 11, sx + 21, "▓" * 9, C_DIM)

        # 8) Stand (rows 13-14) in dim
        self.put(sy + 13, sx, BOSS_FRAME[13], C_DIM)
        self.put(sy + 14, sx, BOSS_FRAME[14], C_DIM)

        # 9) Eyes (rows 5-6, 4 chars wide at offsets 12 and 24)
        ey = sy + 5
        self.put(ey, sx + 12, expr["eyes"], expr["eye_cp"], True)
        self.put(ey + 1, sx + 12, expr["eyes"], expr["eye_cp"], True)
        self.put(ey, sx + 24, expr["eyes"], expr["eye_cp"], True)
        self.put(ey + 1, sx + 24, expr["eyes"], expr["eye_cp"], True)

        # 10) Mouth (row 8, offset 14, 10 chars)
        self.put(sy + 8, sx + 14, expr["mouth"], expr["mouth_cp"], True)

    # ── DIALOGUE BOX ───────────────────────────────────────────────────
    def draw_dialogue_box(self, y=17, h=5):
        w = 56
        x = 12
        self.put(y, x, "╔" + "═" * w + "╗", C_W, True)
        for i in range(1, h):
            self.put(y + i, x, "║" + " " * w + "║", C_W)
        self.put(y + h, x, "╚" + "═" * w + "╝", C_W, True)
        return x + 2, y + 1

    def typewriter(self, text, tx, ty, speed=0.03, color=C_W):
        """Typewriter effect. Returns when user presses key."""
        lines = text.split("\n")
        for li, line in enumerate(lines):
            for i, ch in enumerate(line):
                self.put(ty + li, tx + i, ch, color)
                self.scr.refresh()
                time.sleep(speed)
                # Allow skip with any key
                self.scr.nodelay(True)
                if self.scr.getch() != -1:
                    # Print remaining instantly
                    for li2 in range(li, len(lines)):
                        start = i + 1 if li2 == li else 0
                        self.put(ty + li2, tx + start,
                                 lines[li2][start:], color)
                    self.scr.nodelay(False)
                    self.scr.refresh()
                    self.scr.getch()
                    return
                self.scr.nodelay(False)
        self.scr.refresh()
        self.scr.nodelay(False)
        self.scr.getch()

    def show_boss_dialogue(self, speaker, text, expr):
        self.expression = expr
        self.scr.erase()
        self.draw_boss()
        dx, dy = self.draw_dialogue_box()
        self.put(dy, dx, f"{speaker}:", C_Y, True)
        self.typewriter(text, dx, dy + 1, 0.025, C_W)

    # ── HP BAR ─────────────────────────────────────────────────────────
    def draw_player_hp(self, y=28):
        x = 12
        self.put(y, x, f"♥ {self.name}", C_R, True)
        self.put(y, x + 10, f"LV {self.lv}", C_W)
        self.put(y, x + 18, "HP", C_R, True)
        bar_w = 20
        filled = max(0, int(self.hp / self.max_hp * bar_w))
        self.put(y, x + 21, "█" * filled, C_HPFILL)
        self.put(y, x + 21 + filled, "░" * (bar_w - filled), C_HPEMPTY)
        self.put(y, x + 42, f" {self.hp}/{self.max_hp}", C_W)

    def draw_boss_hp(self, y=16):
        x = 20
        self.put(y, x, "TERMINUS", C_R, True)
        bar_w = 30
        filled = max(0, int(self.boss_hp / self.boss_max * bar_w))
        self.put(y, x + 10, "▐", C_W)
        self.put(y, x + 11, "█" * filled, C_HPBOSS, True)
        self.put(y, x + 11 + filled, "░" * (bar_w - filled), C_DIM)
        self.put(y, x + 11 + bar_w, "▌", C_W)

    # ── MENU ───────────────────────────────────────────────────────────
    # Menu icon mapping
    MENU_ICONS = {"FIGHT": "⚔", "ACT": "✦", "ITEM": "✿", "MERCY": "♡",
                  "Check": "◈", "Talk": "◇", "Flirt": "♢",
                  "Spare": "☆", "Flee": "↺", "Back": "◁",
                  "InstaNoodles": "▣", "Spider Cider": "▣"}

    def draw_menu(self, options, sel, y=29):
        x = 14
        for i, opt in enumerate(options):
            icon = self.MENU_ICONS.get(opt, "›")
            if i == sel:
                self.put(y, x, f"▸{icon} {opt}◂", C_SEL, True)
            else:
                self.put(y, x, f" {icon} {opt} ", C_NRM)
            x += len(opt) + 6

    def menu_select(self, options, y=29):
        sel = 0
        self.scr.nodelay(False)
        while True:
            self.draw_menu(options, sel, y)
            self.scr.refresh()
            k = self.scr.getch()
            if k in (curses.KEY_LEFT, curses.KEY_UP):
                sel = (sel - 1) % len(options)
                self.snd.play("move")
            elif k in (curses.KEY_RIGHT, curses.KEY_DOWN):
                sel = (sel + 1) % len(options)
                self.snd.play("move")
            elif k in (10, 13, curses.KEY_ENTER, ord('z'), ord('Z'), ord(' ')):
                self.snd.play("select")
                return sel

    # ── FIGHT TIMING BAR ──────────────────────────────────────────────
    def fight_action(self):
        bar_w = 30
        self.scr.timeout(25)
        start = time.time()
        result = 0.5

        while True:
            t = time.time() - start
            pos = (math.sin(t * 4.0) + 1) / 2
            mx = int(pos * (bar_w - 1))

            y = 20
            x = 25
            self.put(y, x, "▐" + "─" * bar_w + "▌", C_BAR)
            cz = bar_w // 2
            for i in range(bar_w):
                if abs(i - cz) <= 2:
                    self.put(y, x + 1 + i, "█", C_BKYL)
            self.put(y, x + 1 + mx, "▓", C_BARMARK, True)
            self.put(y + 1, x + 2, "⚔ Press ENTER to strike! ⚔", C_Y, True)
            self.scr.refresh()

            k = self.scr.getch()
            if k in (10, 13, ord('z'), ord('Z'), ord(' ')):
                dist = abs(pos - 0.5) * 2
                result = 1.0 - dist * 0.6
                self.snd.play("hit")
                break

        self.scr.timeout(-1)
        # Calculate damage
        base_dmg = 15
        dmg = int(base_dmg * result)
        dmg += random.randint(-2, 2)
        dmg = max(1, dmg)

        # Animation
        self.expression = "hurt"
        self.shake_x = random.choice([-1, 1])
        self.scr.erase()
        self.draw_boss()
        self.draw_boss_hp()
        self.put(18, 30, f"* {dmg} damage!", C_Y, True)
        self.scr.refresh()
        time.sleep(0.3)
        self.shake_x = 0

        self.boss_hp -= dmg
        self.scr.erase()
        self.draw_boss()
        self.draw_boss_hp()
        self.put(18, 30, f"* {dmg} damage!", C_Y, True)
        self.scr.refresh()
        time.sleep(0.8)

    # ── ACT SUBMENU ────────────────────────────────────────────────────
    def act_action(self):
        options = ["Check", "Talk", "Flirt"]
        self.scr.erase()
        self.draw_boss()
        self.draw_boss_hp()
        self.draw_player_hp()
        self.put(18, 14, "* What will you do?", C_W)
        sel = self.menu_select(options, 20)

        self.scr.erase()
        self.draw_boss()
        dx, dy = self.draw_dialogue_box(18, 5)

        if sel == 0:  # Check
            self.typewriter(ACT_CHECK, dx, dy, 0.02, C_W)
        elif sel == 1:  # Talk
            self.mercy_pts += 25
            if self.mercy_pts <= 25:
                text = ACT_TALK_1
                self.expression = "talk"
            elif self.mercy_pts <= 50:
                text = ACT_TALK_2
                self.expression = "talk"
            else:
                text = ACT_TALK_3
                self.expression = "happy"
            self.scr.erase()
            self.draw_boss()
            dx, dy = self.draw_dialogue_box(18, 5)
            self.typewriter(text, dx, dy, 0.02, C_W)
        elif sel == 2:  # Flirt
            self.mercy_pts += 35
            self.expression = "happy"
            self.scr.erase()
            self.draw_boss()
            dx, dy = self.draw_dialogue_box(18, 5)
            self.typewriter(ACT_FLIRT, dx, dy, 0.02, C_W)

    # ── ITEM SUBMENU ───────────────────────────────────────────────────
    def item_action(self):
        if not self.items:
            self.scr.erase()
            self.draw_boss()
            dx, dy = self.draw_dialogue_box(18, 3)
            self.typewriter("* You have no items!", dx, dy, 0.02, C_W)
            return False

        options = self.items[:] + ["Back"]
        self.scr.erase()
        self.draw_boss()
        self.draw_boss_hp()
        self.draw_player_hp()
        sel = self.menu_select(options, 20)

        if sel == len(self.items):  # Back
            return False

        item = self.items.pop(sel)
        heal = 30 if "Noodles" in item else 25
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + heal)
        actual = self.hp - old_hp

        self.scr.erase()
        self.draw_boss()
        dx, dy = self.draw_dialogue_box(18, 3)
        self.snd.play("heal")
        self.typewriter(f"* You ate the {item}.\n* You recovered {actual} HP!", dx, dy, 0.02, C_G)
        return True

    # ── MERCY ──────────────────────────────────────────────────────────
    def mercy_action(self):
        options = ["Spare", "Flee"]
        self.scr.erase()
        self.draw_boss()
        self.draw_boss_hp()
        self.draw_player_hp()
        sel = self.menu_select(options, 20)

        self.scr.erase()
        self.draw_boss()
        dx, dy = self.draw_dialogue_box(18, 3)

        if sel == 0:  # Spare
            if self.mercy_pts >= 100:
                self.snd.play("spare")
                return "spare"
            else:
                self.typewriter("* TERMINUS doesn't want to\n* be spared yet.", dx, dy, 0.02, C_W)
                return None
        else:  # Flee
            self.typewriter("* You can't flee from\n* a terminal process!", dx, dy, 0.02, C_R)
            return None

    # ── DODGE PHASE ────────────────────────────────────────────────────
    def dodge_phase(self, pattern_fn):
        hx = float(BOX_W // 2)
        hy = float(BOX_H // 2)
        bullets = []
        iframe_timer = 0.0
        start = time.time()
        last_t = start

        self.scr.timeout(25)

        while True:
            now = time.time()
            dt = now - last_t
            last_t = now
            elapsed = now - start
            if elapsed >= DODGE_TIME:
                break

            # ── Input ──
            keys = set()
            while True:
                k = self.scr.getch()
                if k == -1:
                    break
                keys.add(k)

            dx, dy = 0.0, 0.0
            if curses.KEY_UP in keys:    dy -= HEART_SPEED
            if curses.KEY_DOWN in keys:  dy += HEART_SPEED
            if curses.KEY_LEFT in keys:  dx -= HEART_SPEED
            if curses.KEY_RIGHT in keys: dx += HEART_SPEED
            hx = max(0.0, min(float(BOX_W - 1), hx + dx))
            hy = max(0.0, min(float(BOX_H - 1), hy + dy))

            # ── Update bullets ──
            for b in bullets:
                b.x += b.vx
                b.y += b.vy

            # ── Spawn ──
            pattern_fn(elapsed, dt, bullets, BOX_W, BOX_H)

            # ── Collisions ──
            iframe_timer = max(0.0, iframe_timer - dt)
            rx, ry = int(round(hx)), int(round(hy))
            if iframe_timer <= 0:
                for b in bullets:
                    bx, by = int(round(b.x)), int(round(b.y))
                    if bx == rx and by == ry:
                        self.hp -= HIT_DMG
                        iframe_timer = IFRAME
                        self.snd.play("hurt")
                        curses.flash()
                        break

            # ── Cull ──
            bullets = [b for b in bullets
                       if -3 < b.x < BOX_W + 3 and -3 < b.y < BOX_H + 3]

            # ── Render ──
            self.scr.erase()
            self.draw_boss()

            # Timer bar
            pct = 1.0 - elapsed / DODGE_TIME
            bar_w = 30
            filled = int(pct * bar_w)
            self.put(BOX_Y - 1, BOX_X, "▐" + "█" * filled + "░" * (bar_w - filled) + "▌", C_C)

            # Dodge box border (double-line box-drawing)
            self.put(BOX_Y, BOX_X - 1, "╔" + "═" * (BOX_W + 2) + "╗", C_W, True)
            for row in range(BOX_H):
                self.put(BOX_Y + 1 + row, BOX_X - 1, "║", C_W, True)
                self.put(BOX_Y + 1 + row, BOX_X + BOX_W + 2, "║", C_W, True)
            self.put(BOX_Y + BOX_H + 1, BOX_X - 1,
                     "╚" + "═" * (BOX_W + 2) + "╝", C_W, True)

            # Bullets
            for b in bullets:
                bx, by = int(round(b.x)), int(round(b.y))
                if 0 <= bx < BOX_W and 0 <= by < BOX_H:
                    self.put(BOX_Y + 1 + by, BOX_X + 1 + bx, b.ch, b.cp)

            # Heart (♥ Unicode)
            heart_ch = "♥"
            hcp = C_HEART if iframe_timer <= 0 or int(now * 10) % 2 == 0 else C_DIM
            self.put(BOX_Y + 1 + ry, BOX_X + 1 + rx, heart_ch, hcp, True)

            self.draw_player_hp()
            self.scr.refresh()

            if self.hp <= 0:
                break

        self.scr.timeout(-1)

    # ── SCREEN EFFECTS ─────────────────────────────────────────────────
    def screen_flash(self, color=C_W, duration=0.15):
        h, w = self.scr.getmaxyx()
        for y in range(h):
            self.put(y, 0, " " * (w - 1), color)
        self.scr.refresh()
        time.sleep(duration)

    # ── EXPLORATION PHASE ─────────────────────────────────────────────
    def explore_phase(self):
        """Walk through the server complex before the boss encounter."""
        VP_W = 22                      # viewport width  (tiles)
        VP_H = 12                      # viewport height (tiles)
        OX = 17                        # screen x offset
        OY = 4                         # screen y offset

        px, py = PLAYER_START
        emap = [row[:] for row in EXPLORE_MAP]
        msg_lines = []
        frame = 0
        steps = 0
        term_idx = 0

        self.scr.nodelay(False)

        while True:
            frame += 1
            self.scr.erase()

            # ── Camera follows player, clamped to map bounds ──
            cam_x = max(0, min(px - VP_W // 2, EXPLORE_W - VP_W))
            cam_y = max(0, min(py - VP_H // 2, EXPLORE_H - VP_H))

            # ── Room name based on player y ──
            room_name = "???"
            for ry0, ry1, rname in ROOM_NAMES:
                if ry0 <= py <= ry1:
                    room_name = rname
                    break

            title_w = len(room_name) + 6
            title_x = OX + (VP_W * 2 - title_w) // 2
            self.put(2, title_x,
                     "╔" + "═" * (title_w - 2) + "╗", C_DIM, True)
            self.put(3, title_x,
                     "║ ✦ " + room_name + " ✦ ║", C_C)
            # Sparkle animation on ✦
            sp_cp = C_Y if frame % 4 < 2 else C_C
            self.put(3, title_x + 2, "✦", sp_cp, True)
            self.put(3, title_x + title_w - 3, "✦", sp_cp, True)

            # ── Viewport border ──
            bw = VP_W * 2 + 2
            self.put(OY - 1, OX - 1,
                     "╔" + "═" * (bw - 2) + "╗", C_DIM)
            for vy in range(VP_H):
                self.put(OY + vy, OX - 1, "║", C_DIM)
                self.put(OY + vy, OX + VP_W * 2, "║", C_DIM)
            self.put(OY + VP_H, OX - 1,
                     "╚" + "═" * (bw - 2) + "╝", C_DIM)

            # ── Render visible tiles ──
            for vy in range(VP_H):
                for vx in range(VP_W):
                    mx = cam_x + vx
                    my = cam_y + vy
                    if mx < 0 or mx >= EXPLORE_W or my < 0 or my >= EXPLORE_H:
                        continue
                    tile = emap[my][mx]
                    sx = OX + vx * 2
                    sy = OY + vy

                    if tile == T_WALL:
                        above = emap[my - 1][mx] if my > 0 else T_WALL
                        if above != T_WALL:
                            self.put(sy, sx, "▓▓", C_DIM)
                        else:
                            self.put(sy, sx, "██", C_W)
                    elif tile == T_SERVER:
                        phase = (frame + mx * 3 + my * 7) % 12
                        if phase < 4:
                            self.put(sy, sx, "▐▌", C_BKCY, True)
                        elif phase < 8:
                            self.put(sy, sx, "▐▌", C_BKCY)
                        else:
                            self.put(sy, sx, "░▓", C_BKCY)
                    elif tile == T_TERM:
                        if frame % 8 < 4:
                            self.put(sy, sx, "▣░", C_BKYL, True)
                        else:
                            self.put(sy, sx, "▢▓", C_BKYL)
                    elif tile == T_ITEM:
                        sparkle = ["✦ ", "✧ ", "◆ ", "✧ "]
                        self.put(sy, sx, sparkle[frame % 4], C_Y, True)
                    elif tile == T_SIGN:
                        self.put(sy, sx, "⚠!", C_BKYL, True)
                    elif tile == T_BOSS:
                        if frame % 6 < 3:
                            self.put(sy, sx, "░░", C_BKRD, True)
                        else:
                            self.put(sy, sx, "▒▒", C_BKRD)
                    else:  # T_FLOOR
                        h = (mx * 7 + my * 13) % 37
                        if h == 0:
                            self.put(sy, sx, "· ", C_DIM)
                        elif h == 5:
                            self.put(sy, sx, " ·", C_DIM)
                        elif h == 10:
                            self.put(sy, sx, "──", C_DIM)
                        elif h == 15:
                            self.put(sy, sx, "╌╌", C_DIM)

            # ── TERMINUS glowing eyes (visible when boss area is in viewport) ──
            boss_vy = 1 - cam_y
            if 0 <= boss_vy < VP_H and frame % 5 < 3:
                for ex in [10, 16]:
                    evx = ex - cam_x
                    if 0 <= evx < VP_W:
                        self.put(OY + boss_vy, OX + evx * 2, "██",
                                 C_BKRD, True)

            # ── Player glow (dim red on adjacent floor tiles) ──
            for gdx, gdy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                gx, gy = px + gdx, py + gdy
                gvx, gvy = gx - cam_x, gy - cam_y
                if (0 <= gvx < VP_W and 0 <= gvy < VP_H
                        and 0 <= gx < EXPLORE_W and 0 <= gy < EXPLORE_H
                        and emap[gy][gx] == T_FLOOR):
                    self.put(OY + gvy, OX + gvx * 2, "░░", C_BKRD)

            # ── Player (animated heart with body) ──
            pvx = px - cam_x
            pvy = py - cam_y
            if 0 <= pvx < VP_W and 0 <= pvy < VP_H:
                psx = OX + pvx * 2
                psy = OY + pvy
                if frame % 8 < 5:
                    self.put(psy, psx, "♥ ", C_HEART, True)
                else:
                    self.put(psy, psx, "♡ ", C_HEART, True)

            # ── Message box ──
            mby = OY + VP_H + 1
            if msg_lines:
                mbx = 14
                self.put(mby, mbx, "╔" + "═" * 50 + "╗", C_W, True)
                for i in range(3):
                    self.put(mby + 1 + i, mbx,
                             "║" + " " * 50 + "║", C_W)
                self.put(mby + 4, mbx,
                         "╚" + "═" * 50 + "╝", C_W, True)
                for i, line in enumerate(msg_lines[:3]):
                    self.put(mby + 1 + i, mbx + 2, line, C_W)

            # ── Player info ──
            info_y = OY + VP_H + 6
            self.put(info_y, 14,
                     f"♥ {self.name}  LV {self.lv}  Items: {len(self.items)}",
                     C_Y)

            # ── Controls ──
            self.put(info_y + 1, 14,
                     "↑↓←→ Move   Z/Enter: Examine", C_DIM)

            self.scr.refresh()

            # ── Input ──
            k = self.scr.getch()
            msg_lines = []

            nx, ny = px, py
            moved = False

            if k == curses.KEY_UP:
                ny -= 1; moved = True
            elif k == curses.KEY_DOWN:
                ny += 1; moved = True
            elif k == curses.KEY_LEFT:
                nx -= 1; moved = True
            elif k == curses.KEY_RIGHT:
                nx += 1; moved = True
            elif k in (10, 13, ord('z'), ord('Z'), ord(' ')):
                # Examine adjacent tile
                for ddx, ddy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    ax, ay = px + ddx, py + ddy
                    if 0 <= ax < EXPLORE_W and 0 <= ay < EXPLORE_H:
                        t = emap[ay][ax]
                        if t == T_TERM:
                            idx = term_idx % len(TERM_TEXTS)
                            msg_lines = TERM_TEXTS[idx].split("\n")
                            term_idx += 1
                            self.snd.play("text")
                            break
                        elif t == T_SERVER:
                            msg_lines = [
                                "* Rows of server racks hum quietly.",
                                "* Blinking LEDs cast faint shadows.",
                            ]
                            self.snd.play("text")
                            break
                        elif t == T_SIGN:
                            msg_lines = [
                                "* A worn sign reads:",
                                "* 'CAUTION: Sentient process ahead.",
                                "*  Do NOT make eye contact.'",
                            ]
                            self.snd.play("text")
                            break
                continue

            if not moved:
                continue

            # ── Collision ──
            if 0 <= nx < EXPLORE_W and 0 <= ny < EXPLORE_H:
                tile = emap[ny][nx]
                if tile in (T_FLOOR, T_BOSS, T_ITEM):
                    px, py = nx, ny
                    steps += 1
                    if steps % 3 == 0:
                        self.snd.play("move")

                    if tile == T_ITEM:
                        self.items.append("Spider Cider")
                        emap[ny][nx] = T_FLOOR
                        msg_lines = [
                            "* You found a Spider Cider!",
                            f"* (Inventory: {len(self.items)} items)",
                        ]
                        self.snd.play("heal")

                    elif tile == T_BOSS:
                        time.sleep(0.3)
                        self.screen_flash(C_EXPL, 0.15)
                        time.sleep(0.2)
                        return

    # ── INTRO ──────────────────────────────────────────────────────────
    def intro(self):
        self.scr.nodelay(False)
        self.scr.erase()
        h, w = self.scr.getmaxyx()

        # Title using half-block pixel font
        title = [
            "▀▀█▀▀ █▀▀ █▀▀█ █▀▄▀█  ▀█▀ █▀▀▄ █▀▀█ █   ",
            "  █   █▀▀ █▄▄▀ █ ▀ █   █  █  █ █▄▄█ █   ",
            "  ▀   ▀▀▀ ▀ ▀▀ ▀   ▀  ▀▀▀ ▀  ▀ ▀  ▀ ▀▀▀ ",
            "                                           ",
            "     ▀▀█▀▀ █▀▀█ █   █▀▀                    ",
            "       █   █▄▄█ █   █▀▀                    ",
            "       ▀   ▀  ▀ ▀▀▀ ▀▀▀                    ",
        ]
        sy = 3
        for i, line in enumerate(title):
            self.put(sy + i, (w - len(line)) // 2, line, C_C, True)

        # Decorative line
        deco = "═" * 40
        self.put(sy + len(title) + 0, (w - 40) // 2, deco, C_DIM)
        self.put(sy + len(title) + 1, (w - 22) // 2, "╔══ A Terminal RPG ══╗", C_Y, True)
        self.put(sy + len(title) + 2, (w - 40) // 2, deco, C_DIM)

        # Floating braille particles
        self.put(sy + len(title) + 4, (w - 26) // 2, "Press ENTER to begin...", C_W)

        # Scatter some braille sparkles
        for _ in range(20):
            px = random.randint(5, w - 6)
            py = random.randint(1, h - 2)
            self.put(py, px, random.choice(SPARKLES), C_DIM)

        self.scr.refresh()
        self.scr.getch()

        # Intro text
        for text, color, speed in INTRO_TEXT:
            self.scr.erase()
            cx = (w - len(text)) // 2
            cy = h // 2
            self.typewriter(text, cx, cy, speed, color)

        # Flash!
        self.screen_flash(C_EXPL, 0.1)
        time.sleep(0.2)

    # ── PRE-BATTLE ─────────────────────────────────────────────────────
    def pre_battle(self):
        for speaker, text, expr in PRE_BATTLE:
            self.show_boss_dialogue(speaker, text, expr)

    # ── COMBAT LOOP ────────────────────────────────────────────────────
    def combat_loop(self):
        self.expression = "normal"
        self.snd.play_bgm()

        while True:
            # ── Draw combat screen ──
            self.scr.erase()
            self.draw_boss()
            self.draw_boss_hp()
            self.draw_player_hp()

            mercy_text = ""
            if self.mercy_pts >= 100:
                mercy_text = " [yellow: SPARE available!]"
                self.put(27, 14, "* TERMINUS can be SPARED!", C_Y)
            elif self.mercy_pts >= 50:
                self.put(27, 14, "* TERMINUS seems more relaxed.", C_C)
            else:
                lines = [
                    "* TERMINUS stares at you.",
                    "* TERMINUS hums a startup sound.",
                    "* The monitor flickers slightly.",
                    "* You hear a faint fan spinning.",
                ]
                self.put(27, 14, random.choice(lines), C_W)

            # ── Player turn ──
            main_opts = ["FIGHT", "ACT", "ITEM", "MERCY"]
            sel = self.menu_select(main_opts)

            if sel == 0:  # FIGHT
                self.scr.erase()
                self.draw_boss()
                self.draw_boss_hp()
                self.draw_player_hp()
                self.fight_action()
                if self.boss_hp <= 0:
                    return "kill"

            elif sel == 1:  # ACT
                self.act_action()

            elif sel == 2:  # ITEM
                if not self.item_action():
                    continue  # back to menu

            elif sel == 3:  # MERCY
                result = self.mercy_action()
                if result == "spare":
                    return "spare"

            # ── Enemy turn ──
            if self.turn < len(ENEMY_TURN_LINES):
                s, t, e = ENEMY_TURN_LINES[self.turn]
            else:
                s, t, e = random.choice(ENEMY_TURN_LINES)
            self.show_boss_dialogue(s, t, e)
            self.expression = "angry"

            pattern = PATTERNS[self.turn % len(PATTERNS)]
            self.dodge_phase(pattern)

            if self.hp <= 0:
                return "death"

            self.turn += 1
            if self.mercy_pts >= 50:
                self.expression = "talk"
            else:
                self.expression = "normal"

    # ── ENDINGS ────────────────────────────────────────────────────────
    def ending_spare(self):
        self.snd.stop_bgm()
        self.snd.play("spare")
        for s, t, e in SPARE_DIALOGUE:
            self.show_boss_dialogue(s, t, e)

        self.scr.erase()
        h, w = self.scr.getmaxyx()
        self.draw_boss()
        self.expression = "happy"
        self.draw_boss()

        lines = [
            "* You and TERMINUS become friends.",
            "* It promises to be a nicer terminal.",
            "* Maybe even add tab completion.",
            "",
            "╔════════════════════════╗",
            "║   T H E   E N D       ║",
            "╚════════════════════════╝",
            "",
            "  ✦ You chose MERCY ✦",
        ]
        y = 14
        for i, line in enumerate(lines):
            c = C_Y if "END" in line else C_C if "MERCY" in line else C_W
            b = "END" in line or "═" in line
            self.put(y + i, (w - len(line)) // 2, line, c, b)

        # Braille sparkle effect around the boss
        for _ in range(30):
            px = random.randint(5, w - 6)
            py = random.randint(1, h - 2)
            self.put(py, px, random.choice(SPARKLES), C_C)

        self.put(y + len(lines) + 1, (w - 20) // 2, "Press any key...", C_DIM)
        self.scr.refresh()
        self.scr.nodelay(False)
        self.scr.getch()

    def ending_kill(self):
        self.snd.stop_bgm()
        self.snd.play("death")
        self.expression = "dead"
        self.scr.erase()
        self.draw_boss()
        time.sleep(0.5)

        for s, t, e in KILL_DIALOGUE:
            self.show_boss_dialogue(s, t, e)

        # Death animation
        for i in range(5):
            self.scr.erase()
            if i % 2 == 0:
                self.draw_boss()
            self.scr.refresh()
            time.sleep(0.2)

        self.scr.erase()
        h, w = self.scr.getmaxyx()
        lines = [
            "* YOU WON!",
            "* You earned 50 EXP and 30 gold.",
            "",
            "* ...",
            "* But at what cost?",
            "",
            "╔════════════════════════╗",
            "║   T H E   E N D       ║",
            "╚════════════════════════╝",
            "",
            "  ⚔ You chose VIOLENCE ⚔",
        ]
        y = 10
        for i, line in enumerate(lines):
            c = C_Y if "WON" in line else C_R if "VIOLENCE" in line else C_W
            b = "END" in line or "WON" in line or "═" in line
            self.put(y + i, (w - len(line)) // 2, line, c, b)
        self.put(y + len(lines) + 1, (w - 20) // 2, "Press any key...", C_DIM)
        self.scr.refresh()
        self.scr.nodelay(False)
        self.scr.getch()

    def ending_death(self):
        self.snd.stop_bgm()
        self.snd.play("death")
        self.scr.erase()
        h, w = self.scr.getmaxyx()

        # Pixel-art heart using half-blocks
        heart_lines = [
            "  ▄███▄ ▄███▄  ",
            " ███████████████",
            " ███████████████",
            "  ▀█████████▀  ",
            "    ▀█████▀    ",
            "      ▀█▀      ",
            "       ▀       ",
        ]
        y = 6
        for i, line in enumerate(heart_lines):
            cx = (w - len(line)) // 2
            for j, ch in enumerate(line):
                if ch in "█▄▀":
                    self.put(y + i, cx + j, ch, C_R, True)
        self.scr.refresh()
        time.sleep(1)

        # Break animation — pieces scatter with braille particles
        for frame in range(10):
            self.scr.erase()
            for i, line in enumerate(heart_lines):
                cx = (w - len(line)) // 2
                for j, ch in enumerate(line):
                    if ch in "█▄▀":
                        ox = random.randint(-frame, frame)
                        oy = random.randint(-frame // 2, frame)
                        piece = random.choice("▓░▒⠁⠂⠄⠈✦·") if frame > 4 else ch
                        cp = C_R if frame < 6 else C_DIM
                        self.put(y + i + oy, cx + j + ox, piece, cp)
            self.scr.refresh()
            time.sleep(0.12)

        self.scr.erase()
        self.snd.play("gameover")
        self.put(h // 2, (w - 12) // 2, "G A M E   O V E R", C_R, True)
        self.put(h // 2 + 2, (w - 22) // 2, "Press R to retry...", C_W)
        self.scr.refresh()
        self.scr.nodelay(False)
        while True:
            k = self.scr.getch()
            if k in (ord('r'), ord('R')):
                return True
            if k in (ord('q'), ord('Q')):
                return False

    # ── MAIN RUN ───────────────────────────────────────────────────────
    def run(self):
        while True:
            self.hp = 92
            self.boss_hp = 120
            self.mercy_pts = 0
            self.items = ["InstaNoodles"]
            self.turn = 0
            self.expression = "normal"
            self.shake_x = 0
            self.shake_y = 0

            self.intro()
            self.explore_phase()
            self.pre_battle()
            result = self.combat_loop()

            if result == "spare":
                self.ending_spare()
                break
            elif result == "kill":
                self.ending_kill()
                break
            elif result == "death":
                if not self.ending_death():
                    break
                # else retry


def main(stdscr):
    h, w = stdscr.getmaxyx()
    if w < 80 or h < 30:
        stdscr.addstr(0, 0, f"Need 80x30 terminal, got {w}x{h}")
        stdscr.addstr(1, 0, "Resize and retry.")
        stdscr.refresh()
        stdscr.getch()
        return
    g = Game(stdscr)
    try:
        g.run()
    except (SystemExit, KeyboardInterrupt):
        pass
    finally:
        g.snd.cleanup()

if __name__ == "__main__":
    curses.wrapper(main)
