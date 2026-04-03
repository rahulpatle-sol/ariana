"""
main.py — ARIANA v2
Anime-style UI · Always-on mic · Stop button · Draggable · WhatsApp remote
"""
import tkinter as tk
from tkinter import font as tkfont
import threading, time, json, os, sys, math, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.ai_brain import AiBrain
from modules import voice, ops
from modules.whatsapp import setup as wa_setup, start_server as wa_start

CONFIG = os.path.expanduser("~/.ariana2.json")

# ── Palette ────────────────────────────────────────────────────
C = {
    "bg":       "#0d0618",
    "surface":  "#150d27",
    "card":     "#1e1035",
    "purple":   "#c084fc",
    "purple2":  "#a855f7",
    "pink":     "#f472b6",
    "cyan":     "#67e8f9",
    "text":     "#f3e8ff",
    "dim":      "#9d7ec9",
    "green":    "#4ade80",
    "red":      "#f87171",
    "border":   "#2d1855",
}

# ══════════════════════════════════════════════════════════════
class AnimeAvatar(tk.Canvas):
    """Anime-style girl avatar — headphones, expressive eyes"""

    def __init__(self, parent, w=220, h=250):
        super().__init__(parent, width=w, height=h,
                         bg=C["bg"], highlightthickness=0)
        self.W, self.H = w, h
        self.cx = w // 2
        self.cy = h // 2 - 10
        self.state = "idle"       # idle | speaking | thinking | happy | wink
        self._t = 0               # animation tick
        self._blink = 0
        self._eye_x = 0
        self._eye_y = 0
        self._mouth_phase = 0
        self._particles = []

        self._tick()

    # ── Draw ────────────────────────────────────────────────────
    def _draw(self):
        self.delete("all")
        cx, cy = self.cx, self.cy
        t = self._t
        bob = math.sin(t * 0.05) * 4   # breathing bob

        # ── GLOW rings ────────────────────────────────────────
        for i in range(4, 0, -1):
            r = 70 + i * 8
            alpha = int(20 + i * 8)
            col = self._hex_fade(C["purple2"], alpha)
            self.create_oval(cx-r, cy-r+bob, cx+r, cy+r+bob,
                             outline=col, width=1 if i > 1 else 2)

        # ── HAIR (back, long) ─────────────────────────────────
        # Back hair bulk
        self.create_oval(cx-55, cy-65+bob, cx+55, cy+70+bob,
                         fill="#1c0d3d", outline="#2a1558", width=1)
        # Left long hair strand
        self.create_polygon(
            cx-55, cy-20+bob, cx-70, cy+20+bob,
            cx-72, cy+90+bob, cx-50, cy+110+bob,
            cx-30, cy+80+bob, cx-42, cy+40+bob,
            fill="#1c0d3d", outline="", smooth=True)
        # Right long hair strand
        self.create_polygon(
            cx+55, cy-20+bob, cx+70, cy+20+bob,
            cx+72, cy+90+bob, cx+50, cy+110+bob,
            cx+30, cy+80+bob, cx+42, cy+40+bob,
            fill="#1c0d3d", outline="", smooth=True)

        # ── NECK ──────────────────────────────────────────────
        self.create_rectangle(cx-13, cy+58+bob, cx+13, cy+82+bob,
                              fill="#fdddd0", outline="")

        # ── SHOULDERS / OUTFIT ────────────────────────────────
        # Hoodie / jacket
        self.create_arc(cx-65, cy+65+bob, cx+65, cy+150+bob,
                        start=0, extent=180,
                        fill="#3b1fa3", outline=C["purple"], width=2)
        # Hoodie pocket/detail
        self.create_rectangle(cx-18, cy+80+bob, cx+18, cy+95+bob,
                              fill="#2d1880", outline=C["purple2"], width=1)
        # Collar
        self.create_polygon(
            cx-12, cy+62+bob, cx+12, cy+62+bob,
            cx+8, cy+76+bob, cx, cy+80+bob, cx-8, cy+76+bob,
            fill="#fdddd0", outline="")

        # ── HEADPHONES ────────────────────────────────────────
        # Band over head
        self.create_arc(cx-48, cy-72+bob, cx+48, cy-5+bob,
                        start=0, extent=180,
                        outline="#1a1a2e", width=8, style="arc")
        self.create_arc(cx-45, cy-70+bob, cx+45, cy-7+bob,
                        start=0, extent=180,
                        outline="#a855f7", width=3, style="arc")
        # Left cup
        self.create_oval(cx-58, cy-25+bob, cx-40, cy+5+bob,
                         fill="#0f0f1f", outline="#a855f7", width=2)
        self.create_oval(cx-55, cy-22+bob, cx-43, cy+2+bob,
                         fill="#1a0a40", outline="")
        self.create_text(cx-49, cy-10+bob, text="♫", fill=C["purple"], font=("Arial",7))
        # Right cup
        self.create_oval(cx+40, cy-25+bob, cx+58, cy+5+bob,
                         fill="#0f0f1f", outline="#a855f7", width=2)
        self.create_oval(cx+43, cy-22+bob, cx+55, cy+2+bob,
                         fill="#1a0a40", outline="")
        self.create_text(cx+49, cy-10+bob, text="♫", fill=C["purple"], font=("Arial",7))

        # ── FACE ──────────────────────────────────────────────
        self.create_oval(cx-44, cy-52+bob, cx+44, cy+62+bob,
                         fill="#fdddd0", outline="#f4b8a0", width=1)
        # Face shadow/contour
        self.create_arc(cx+5, cy-30+bob, cx+42, cy+40+bob,
                        start=270, extent=100,
                        outline="#f0a898", width=1, style="arc")

        # ── EARS ──────────────────────────────────────────────
        self.create_oval(cx-54, cy-8+bob, cx-40, cy+14+bob,
                         fill="#fdddd0", outline="#f4b8a0")
        self.create_oval(cx+40, cy-8+bob, cx+54, cy+14+bob,
                         fill="#fdddd0", outline="#f4b8a0")
        # Earrings
        self.create_oval(cx-50, cy+12+bob, cx-44, cy+20+bob,
                         fill=C["pink"], outline=C["purple"], width=1)
        self.create_oval(cx+44, cy+12+bob, cx+50, cy+20+bob,
                         fill=C["pink"], outline=C["purple"], width=1)

        # ── EYEBROWS ──────────────────────────────────────────
        by = cy - 20 + bob
        raise_ = -5 if self.state=="surprised" else (-3 if self.state=="thinking" else 0)
        # Left brow (slightly arched)
        self.create_line(cx-30, by+raise_+4, cx-20, by+raise_+1,
                         cx-10, by+raise_, fill="#2d1558", width=3, smooth=True)
        # Right brow
        self.create_line(cx+10, by+raise_, cx+20, by+raise_+1,
                         cx+30, by+raise_+4, fill="#2d1558", width=3, smooth=True)

        # ── EYES ──────────────────────────────────────────────
        ey = cy - 3 + bob
        ox, oy = self._eye_x * 3, self._eye_y * 2

        for sign, ex in [(-1, cx-17), (1, cx+17)]:
            # Wink check
            is_wink = (self.state == "wink" and sign == 1)

            if self._blink > 0 or is_wink:
                # Closed eye — curved line
                self.create_arc(ex-12, ey-3, ex+12, ey+8,
                                start=0, extent=180,
                                outline="#2d1558", width=3, style="arc")
            else:
                # Eye white (large anime style)
                self.create_oval(ex-13, ey-11, ex+13, ey+11,
                                 fill="white", outline="#e8d0f8")
                # Iris — big, expressive
                self.create_oval(ex-9+ox, ey-9+oy, ex+9+ox, ey+9+oy,
                                 fill="#7c3aed", outline="#4c1d95", width=1)
                # Pupil
                self.create_oval(ex-4+ox, ey-4+oy, ex+4+ox, ey+4+oy,
                                 fill="#0d0020", outline="")
                # Catchlight (anime sparkle)
                self.create_oval(ex-7+ox, ey-7+oy, ex-3+ox, ey-3+oy,
                                 fill="white", outline="")
                self.create_oval(ex+2+ox, ey-5+oy, ex+5+ox, ey-2+oy,
                                 fill="white", outline="")
                # Iris rim
                self.create_oval(ex-9+ox, ey-9+oy, ex+9+ox, ey+9+oy,
                                 fill="", outline=C["purple"], width=1)

            # Eyelashes — thick top
            self.create_line(ex-14, ey-10, ex+14, ey-10,
                             fill="#150830", width=4)
            # Corner lash
            self.create_line(ex-13, ey-9, ex-16, ey-13,
                             fill="#150830", width=2)
            self.create_line(ex+13, ey-9, ex+16, ey-13,
                             fill="#150830", width=2)

        # ── NOSE ──────────────────────────────────────────────
        ny = cy + 14 + bob
        self.create_arc(cx-7, ny, cx+7, ny+8,
                        start=0, extent=180, outline="#e8a898", width=2, style="arc")

        # ── MOUTH ─────────────────────────────────────────────
        my = cy + 30 + bob
        mp = self._mouth_phase

        if self.state == "speaking":
            # Animated talking mouth
            o = abs(math.sin(mp)) * 8
            self.create_oval(cx-12, my-o*0.3, cx+12, my+o,
                             fill="#c0405a", outline="#8b1a35", width=1)
            if o > 3:
                self.create_oval(cx-8, my, cx+8, my+o*0.6,
                                 fill="#e87090", outline="")
                # Teeth
                self.create_rectangle(cx-7, my-o*0.2, cx+7, my+2,
                                      fill="white", outline="")
        elif self.state in ("happy", "wink"):
            # Big smile
            self.create_arc(cx-16, my-10, cx+16, my+12,
                            start=200, extent=140, outline=C["pink"], width=3, style="arc")
            # Smile lines
            self.create_line(cx-16, my+2, cx-20, my-4,
                             fill=C["pink"], width=1)
            self.create_line(cx+16, my+2, cx+20, my-4,
                             fill=C["pink"], width=1)
        else:
            # Soft neutral smile
            self.create_arc(cx-14, my-6, cx+14, my+10,
                            start=210, extent=120, outline="#d46080", width=2, style="arc")

        # ── BLUSH ─────────────────────────────────────────────
        if self.state in ("happy", "speaking", "wink"):
            for bx in [cx-34, cx+22]:
                self.create_oval(bx, cy+20+bob, bx+24, cy+32+bob,
                                 fill="#ffb3c8", outline="", stipple="gray50")

        # ── HAIR FRONT ────────────────────────────────────────
        # Main bang cover
        self.create_arc(cx-50, cy-80+bob, cx+50, cy-20+bob,
                        start=0, extent=180, fill="#1c0d3d", outline="")
        # Bangs — asymmetric anime style
        bang_pts = [
            (cx-50, cy-55+bob, cx-35, cy-28+bob, 0),   # left bang
            (cx-30, cy-72+bob, cx-12, cy-35+bob, 1),   # mid-left
            (cx-5,  cy-76+bob, cx+18, cy-30+bob, 2),   # center
            (cx+15, cy-72+bob, cx+35, cy-28+bob, 3),   # mid-right
        ]
        for x1,y1,x2,y2,i in bang_pts:
            w = 22-i*2
            self.create_oval(x1, y1, x1+w, y2,
                             fill="#1c0d3d", outline="")

        # Hair shine
        self.create_arc(cx-30, cy-68+bob, cx+5, cy-40+bob,
                        start=20, extent=60, outline="#3d1a7a", width=2, style="arc")

        # ── PARTICLES (when speaking/happy) ───────────────────
        for px, py, pr, palpha in self._particles:
            col = C["purple"] if random.random()>0.5 else C["pink"]
            self.create_oval(px-pr, py-pr, px+pr, py+pr,
                             fill=col, outline="")

        # ── NAME ──────────────────────────────────────────────
        self.create_text(cx, self.H-18, text="✦  A R I A N A  ✦",
                         fill=C["purple"], font=("Segoe UI", 9, "bold"))

    # ── State setters ───────────────────────────────────────────
    def set_state(self, state):
        self.state = state
        if state in ("happy","speaking"):
            self._spawn_particles()

    def _spawn_particles(self):
        self._particles = []
        cx, cy = self.cx, self.cy
        for _ in range(6):
            angle = random.uniform(0, math.pi*2)
            dist = random.uniform(50, 90)
            self._particles.append([
                cx + math.cos(angle)*dist,
                cy + math.sin(angle)*dist,
                random.uniform(2, 5),
                1.0
            ])

    # ── Animations ─────────────────────────────────────────────
    def _tick(self):
        self._t += 1

        # Blink
        if self._blink > 0:
            self._blink -= 1

        # Random blink
        if self._t % random.randint(80,160) == 0:
            self._blink = 4

        # Speaking mouth
        if self.state == "speaking":
            self._mouth_phase += 0.4

        # Particle decay
        self._particles = [
            [p[0]+random.uniform(-1,1), p[1]-1.5, p[2]*0.92, p[3]*0.85]
            for p in self._particles if p[3] > 0.1
        ]

        self._draw()
        self.after(50, self._tick)

    def track_eyes(self, mx, my):
        try:
            rx = self.winfo_rootx() + self.cx
            ry = self.winfo_rooty() + self.cy - 10
            dx = max(-1, min(1, (mx-rx)/400))
            dy = max(-1, min(1, (my-ry)/300))
            self._eye_x = dx
            self._eye_y = dy
        except Exception:
            pass

    @staticmethod
    def _hex_fade(hex_col, alpha):
        """Return hex with alpha approximation using RGB blend with bg"""
        r,g,b = int(hex_col[1:3],16), int(hex_col[3:5],16), int(hex_col[5:7],16)
        a = alpha/255
        br,bg2,bb = 0x0d,0x06,0x18
        nr = int(r*a + br*(1-a))
        ng = int(g*a + bg2*(1-a))
        nb = int(b*a + bb*(1-a))
        return f"#{nr:02x}{ng:02x}{nb:02x}"


# ══════════════════════════════════════════════════════════════
class ArianaApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Ariana")
        self.root.geometry("400x700+30+30")
        self.root.configure(bg=C["bg"])
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        self.root.resizable(False, True)

        self.ai = AiBrain()
        self._stop_flag = False
        self._mic_on = True
        self._processing = False
        self._listen_thread = None
        self._drag_x = self._drag_y = 0

        self._load_config()
        self._build_ui()
        self._start_mic_loop()
        self._greet()

    # ── Config ──────────────────────────────────────────────────
    def _load_config(self):
        try:
            cfg = json.load(open(CONFIG))
            self.ai.groq_key = cfg.get("groq_key","")
            self.ai.mode = cfg.get("mode","groq")
            self._wa_sid = cfg.get("wa_sid","")
            self._wa_token = cfg.get("wa_token","")
            self._wa_number = cfg.get("wa_number","")
            if self._wa_sid and self._wa_token:
                wa_setup(self.ai, self._wa_sid, self._wa_token, self._wa_number)
                wa_start()
        except Exception:
            self._wa_sid = self._wa_token = self._wa_number = ""

    def _save_config(self):
        try:
            json.dump({"groq_key":self.ai.groq_key,"mode":self.ai.mode,
                       "wa_sid":getattr(self,'_wa_sid',''),
                       "wa_token":getattr(self,'_wa_token',''),
                       "wa_number":getattr(self,'_wa_number','')}, open(CONFIG,'w'))
        except Exception:
            pass

    # ── UI ──────────────────────────────────────────────────────
    def _build_ui(self):
        # ── TITLE BAR ────────────────────────────────────────
        bar = tk.Frame(self.root, bg=C["surface"], height=38)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        bar.bind("<Button-1>", self._ds)
        bar.bind("<B1-Motion>", self._dm)

        tk.Label(bar, text="✦ ARIANA", bg=C["surface"], fg=C["purple"],
                 font=("Segoe UI",11,"bold")).pack(side="left",padx=12)
        tk.Label(bar, text="", bg=C["surface"]).pack(side="left",padx=2)

        self._mode_lbl = tk.Label(bar, text="● GROQ", bg=C["surface"],
                                   fg=C["green"], font=("Segoe UI",8))
        self._mode_lbl.pack(side="left")

        for txt, cmd in [("✕",self._quit),("□",self.root.iconify),("⚙",self._settings)]:
            b = tk.Button(bar, text=txt, bg=C["surface"], fg=C["dim"],
                          bd=0, font=("Segoe UI",11), cursor="hand2",
                          activebackground=C["card"], command=cmd)
            b.pack(side="right",padx=4)
            b.bind("<Enter>", lambda e,b=b: b.config(fg=C["text"]))
            b.bind("<Leave>", lambda e,b=b: b.config(fg=C["dim"]))

        # ── AVATAR ───────────────────────────────────────────
        self.avatar = AnimeAvatar(self.root, w=400, h=250)
        self.avatar.pack()
        self.root.bind("<Motion>", lambda e: self.avatar.track_eyes(e.x_root, e.y_root))

        # ── STATUS BAR ───────────────────────────────────────
        st_frame = tk.Frame(self.root, bg=C["card"])
        st_frame.pack(fill="x", padx=8, pady=(0,4))

        self._status_dot = tk.Label(st_frame, text="●", bg=C["card"],
                                     fg=C["green"], font=("Segoe UI",8))
        self._status_dot.pack(side="left",padx=8)
        self._status_lbl = tk.Label(st_frame, text="Listening...", bg=C["card"],
                                     fg=C["dim"], font=("Segoe UI",9))
        self._status_lbl.pack(side="left")

        # Stop button
        self._stop_btn = tk.Button(st_frame, text="⏹ Stop", bg=C["red"],
                                    fg="white", font=("Segoe UI",8,"bold"),
                                    bd=0, padx=8, pady=2, cursor="hand2",
                                    command=self._stop_speaking)
        self._stop_btn.pack(side="right", padx=8, pady=3)
        self._stop_btn.config(state="disabled")

        # Mic toggle
        self._mic_btn = tk.Button(st_frame, text="🎤 ON", bg=C["purple2"],
                                   fg="white", font=("Segoe UI",8,"bold"),
                                   bd=0, padx=8, pady=2, cursor="hand2",
                                   command=self._toggle_mic)
        self._mic_btn.pack(side="right", padx=4, pady=3)

        # ── CHAT BOX ─────────────────────────────────────────
        chat_outer = tk.Frame(self.root, bg=C["border"], pady=1, padx=1)
        chat_outer.pack(fill="both", expand=True, padx=8, pady=4)

        self.chat = tk.Text(chat_outer, bg=C["surface"], fg=C["text"],
                             insertbackground=C["purple"],
                             font=("Consolas",10), relief="flat", bd=0,
                             state="disabled", wrap="word",
                             selectbackground=C["purple2"],
                             height=12)
        scroll = tk.Scrollbar(chat_outer, command=self.chat.yview,
                               bg=C["card"], troughcolor=C["surface"],
                               relief="flat", bd=0, width=6)
        self.chat.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.chat.pack(fill="both", expand=True)

        self.chat.tag_config("A", foreground=C["purple"], font=("Segoe UI",10))
        self.chat.tag_config("U", foreground=C["cyan"], font=("Segoe UI",10))
        self.chat.tag_config("S", foreground=C["green"], font=("Segoe UI",9))
        self.chat.tag_config("E", foreground=C["red"])
        self.chat.tag_config("bold", font=("Segoe UI",10,"bold"))

        # ── QUICK BUTTONS ────────────────────────────────────
        qf = tk.Frame(self.root, bg=C["bg"])
        qf.pack(fill="x", padx=8, pady=2)
        quick = [("👁","screen dekho"),("📄","pdf banao — "),("🎨","image banao — "),
                 ("💻","system info"),("📁","files dikhao ~/"),("🌐","open ")]
        for i,(icon,cmd) in enumerate(quick):
            b = tk.Button(qf, text=icon, bg=C["card"], fg=C["dim"],
                          font=("Segoe UI",12), bd=0, padx=0, pady=4,
                          cursor="hand2", width=3,
                          command=lambda c=cmd: self._quick(c))
            b.grid(row=0, column=i, padx=2, sticky="ew")
            qf.columnconfigure(i, weight=1)
            b.bind("<Enter>", lambda e,b=b: b.config(bg=C["purple2"],fg=C["text"]))
            b.bind("<Leave>", lambda e,b=b: b.config(bg=C["card"],fg=C["dim"]))

        # ── INPUT ────────────────────────────────────────────
        inp_frame = tk.Frame(self.root, bg=C["card"])
        inp_frame.pack(fill="x", padx=8, pady=(2,10))

        self._inp = tk.Entry(inp_frame, bg=C["card"], fg=C["text"],
                              insertbackground=C["purple"],
                              font=("Segoe UI",11), relief="flat",
                              bd=0)
        self._inp.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self._inp.bind("<Return>", lambda e: self._send_text())

        tk.Button(inp_frame, text="➤", bg=C["purple2"], fg="white",
                  font=("Segoe UI",12,"bold"), bd=0, padx=12, pady=6,
                  cursor="hand2",
                  command=self._send_text).pack(side="right", padx=4, pady=4)

    # ── Drag ────────────────────────────────────────────────────
    def _ds(self, e):
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()
    def _dm(self, e):
        self.root.geometry(f"+{e.x_root-self._drag_x}+{e.y_root-self._drag_y}")

    # ── Mic loop (always on) ────────────────────────────────────
    def _start_mic_loop(self):
        def _loop():
            while True:
                if not self._mic_on or self._processing:
                    time.sleep(0.5)
                    continue
                self._set_status("👂 Listening...", C["green"])
                result = voice.listen_once(timeout=6)
                if result and not result.startswith("ERROR") and not result.startswith("MIC_ERROR"):
                    if result.strip():
                        self._on_voice_input(result)
                elif result.startswith("MIC_ERROR"):
                    self._set_status("🎤 Mic not found", C["red"])
                    time.sleep(3)
        threading.Thread(target=_loop, daemon=True).start()

    def _on_voice_input(self, text):
        self._add_msg(f"🎤 {text}", "U")
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _toggle_mic(self):
        self._mic_on = not self._mic_on
        if self._mic_on:
            self._mic_btn.config(text="🎤 ON", bg=C["purple2"])
            self._set_status("👂 Listening...", C["green"])
        else:
            self._mic_btn.config(text="🎤 OFF", bg=C["card"])
            self._set_status("🔇 Mic off", C["dim"])

    def _stop_speaking(self):
        self._stop_flag = True
        voice.stop()
        self.avatar.set_state("idle")
        self._stop_btn.config(state="disabled")
        self._set_status("⏹ Stopped", C["red"])
        self.root.after(1500, lambda: self._set_status("👂 Listening...", C["green"]))

    # ── Process ─────────────────────────────────────────────────
    def _send_text(self):
        text = self._inp.get().strip()
        if not text: return
        self._inp.delete(0,"end")
        self._add_msg(f"You: {text}", "U")
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _process(self, text):
        self._processing = True
        self._stop_flag = False
        self._stop_btn.config(state="normal")
        self.avatar.set_state("thinking")
        self._set_status("🤔 Thinking...", C["purple"])

        try:
            result = ops.route(text, self.ai)
            if result is None:
                result = self.ai.chat(text)
        except Exception as e:
            result = f"Error: {e}"

        if self._stop_flag:
            self._processing = False
            return

        self._add_msg(f"Ariana: {result}", "A")
        self._stop_btn.config(state="normal")
        self.avatar.set_state("speaking")
        self._set_status("💬 Speaking...", C["pink"])

        vt = threading.Thread(target=voice.speak, args=(result,True), daemon=True)
        vt.start()
        vt.join()

        self._stop_btn.config(state="disabled")
        self.avatar.set_state("happy")
        self._set_status("👂 Listening...", C["green"])
        self._processing = False

    # ── Helpers ─────────────────────────────────────────────────
    def _add_msg(self, text, tag):
        def _do():
            self.chat.config(state="normal")
            self.chat.insert("end", text+"\n", tag)
            self.chat.see("end")
            self.chat.config(state="disabled")
        self.root.after(0, _do)

    def _set_status(self, text, color):
        def _do():
            self._status_lbl.config(text=text)
            self._status_dot.config(fg=color)
        self.root.after(0, _do)

    def _quick(self, cmd):
        if cmd.endswith(" ") or cmd.endswith("— "):
            self._inp.delete(0,"end")
            self._inp.insert(0, cmd)
            self._inp.focus()
        else:
            self._add_msg(f"You: {cmd}", "U")
            threading.Thread(target=self._process, args=(cmd,), daemon=True).start()

    def _greet(self):
        h = int(time.strftime("%H"))
        msgs = {0:"Good morning! ☀️ Ready hoon!", 12:"Hey! 🌸 Kya karna hai?", 17:"Good evening! 🌙 Bolo!"}
        msg = next(v for k,v in sorted(msgs.items()) if h >= k)
        self._add_msg(f"Ariana: {msg}", "A")
        self._add_msg("💡 Tip: Seedha bolo — 'screen dekho', 'pdf banao', 'image banao sunset'", "S")
        self.avatar.set_state("happy")
        threading.Thread(target=voice.speak, args=(msg,), daemon=True).start()

    # ── Settings ────────────────────────────────────────────────
    def _settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings"); win.geometry("400x520")
        win.configure(bg=C["surface"]); win.attributes("-topmost",True)

        tk.Label(win, text="⚙  Settings", bg=C["surface"], fg=C["purple"],
                 font=("Segoe UI",14,"bold")).pack(pady=16)

        def lbl(text): tk.Label(win,text=text,bg=C["surface"],fg=C["dim"],
                                  font=("Segoe UI",9)).pack(anchor="w",padx=20,pady=(8,0))
        def entry(var, show=None):
            e = tk.Entry(win, textvariable=var, bg=C["card"], fg=C["text"],
                         insertbackground=C["purple"], font=("Consolas",10),
                         relief="flat", bd=0, show=show)
            e.pack(fill="x", padx=20, pady=3, ipady=6)

        lbl("Groq API Key (groq.com — FREE)"); gk = tk.StringVar(value=self.ai.groq_key); entry(gk,"•")
        lbl("AI Mode")
        m = tk.StringVar(value=self.ai.mode)
        mf = tk.Frame(win,bg=C["surface"]); mf.pack(padx=20,pady=4,fill="x")
        for v,l in [("groq","🌐 Groq Online"),("ollama","💻 Ollama Offline")]:
            tk.Radiobutton(mf,text=l,variable=m,value=v,bg=C["surface"],fg=C["text"],
                           selectcolor=C["card"],activebackground=C["surface"],
                           font=("Segoe UI",10)).pack(anchor="w")

        tk.Label(win,text="─── WhatsApp Remote ───",bg=C["surface"],fg=C["border"],
                 font=("Segoe UI",9)).pack(pady=(14,0))
        lbl("Twilio Account SID"); ws=tk.StringVar(value=getattr(self,'_wa_sid','')); entry(ws)
        lbl("Twilio Auth Token"); wt=tk.StringVar(value=getattr(self,'_wa_token','')); entry(wt,"•")
        lbl("Your WhatsApp (+91...)"); wn=tk.StringVar(value=getattr(self,'_wa_number','')); entry(wn)

        def save():
            self.ai.groq_key = gk.get().strip()
            self.ai.mode = m.get()
            self._wa_sid = ws.get().strip()
            self._wa_token = wt.get().strip()
            self._wa_number = wn.get().strip()
            self._mode_lbl.config(text=f"● {m.get().upper()}")
            if self._wa_sid and self._wa_token:
                wa_setup(self.ai, self._wa_sid, self._wa_token, self._wa_number)
                wa_start()
                self._add_msg("✅ WhatsApp remote enabled! Port 5000", "S")
            self._save_config()
            self._add_msg("✅ Settings saved!", "S")
            win.destroy()

        tk.Button(win,text="Save",bg=C["purple2"],fg="white",
                  font=("Segoe UI",11,"bold"),bd=0,pady=10,
                  cursor="hand2",command=save).pack(fill="x",padx=20,pady=16)

    def _quit(self):
        self._save_config(); self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ArianaApp().run()
