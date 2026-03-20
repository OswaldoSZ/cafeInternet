import customtkinter as ctk
import threading
import time
import socket
import requests
import psutil
import os
import ctypes
from PIL import Image, ImageDraw, ImageFilter, ImageTk
import tkinter as tk

# ─── CONFIG ───────────────────────────────────────────────────────────────────
try:
    from config import API_BASE_URL, INACTIVITY_MINUTES, APPS_TO_CLOSE, DEV_MODE
    INACTIVITY_TIMEOUT = INACTIVITY_MINUTES * 60
except ImportError:
    API_BASE_URL       = "http://localhost:8000"
    INACTIVITY_TIMEOUT = 20 * 60
    APPS_TO_CLOSE      = []
    DEV_MODE           = True

PC_NAME = socket.gethostname()

# ─── TEMA ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Paleta clara
BG_BASE      = "#eef2fb"
CARD_BG      = "#ffffff"
CARD_BORDER  = "#dde3f0"
INPUT_BG     = "#f4f6fd"
INPUT_BORDER = "#c8d0e8"
ACCENT       = "#ffa401"
ACCENT_DARK  = "#e6920a"
ACCENT_LIGHT = "#fff8e6"
TEXT_DARK    = "#1e293b"
TEXT_MID     = "#64748b"
TEXT_LIGHT   = "#94a3b8"
SUCCESS      = "#10b981"
WARNING      = "#f59e0b"
ERROR        = "#ef4444"
ERROR_LIGHT  = "#fef2f2"


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS — imagen de fondo y logo
# ══════════════════════════════════════════════════════════════════════════════
def _make_background(w, h):
    """Genera imagen de fondo con gradiente y círculos suaves."""
    img = Image.new("RGB", (w, h), "#eef2fb")
    draw = ImageDraw.Draw(img)

    for y in range(h):
        t = y / h
        r = int(238 + (220 - 238) * t)
        g = int(242 + (230 - 242) * t)
        b = int(251 + (245 - 251) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw   = ImageDraw.Draw(overlay)
    circles = [
        (int(w * 0.15), int(h * 0.20), int(w * 0.22), (255, 164,   1, 18)),
        (int(w * 0.85), int(h * 0.15), int(w * 0.18), (255, 200,  80, 14)),
        (int(w * 0.05), int(h * 0.75), int(w * 0.25), (255, 220, 120, 18)),
        (int(w * 0.90), int(h * 0.80), int(w * 0.16), (230, 146,  10, 12)),
        (int(w * 0.50), int(h * 0.90), int(w * 0.30), (255, 180,  50,  9)),
        (int(w * 0.30), int(h * 0.50), int(w * 0.10), (255, 210, 100, 22)),
        (int(w * 0.72), int(h * 0.48), int(w * 0.12), (255, 190,  60, 18)),
    ]
    for cx, cy, r, color in circles:
        odraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    overlay = overlay.filter(ImageFilter.GaussianBlur(min(w, h) // 14))
    base    = img.convert("RGBA")
    merged  = Image.alpha_composite(base, overlay).convert("RGB")

    # Puntos de grilla muy sutiles
    d2 = ImageDraw.Draw(merged)
    step = max(30, w // 50)
    for x in range(0, w, step):
        for y in range(0, h, step):
            d2.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(180, 192, 220))

    return merged


def _make_logo(size=96):
    """Genera logo de monitor con gradiente azul."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fondo circular con gradiente radial
    half = size // 2
    for r in range(half, 0, -1):
        t  = r / half
        cr = int(59  + (96  - 59)  * t)
        cg = int(130 + (165 - 130) * t)
        cb = int(246 + (250 - 246) * t)
        draw.ellipse(
            [half - r, half - r, half + r, half + r],
            fill=(cr, cg, cb, 255),
        )

    # Sombra suave alrededor
    shadow = img.filter(ImageFilter.GaussianBlur(4))
    result = Image.new("RGBA", (size + 8, size + 8), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(result)
    s_draw.ellipse([2, 2, size + 6, size + 6], fill=(59, 130, 246, 40))
    result = result.filter(ImageFilter.GaussianBlur(3))
    result.paste(img, (4, 4), img)
    img = result

    # Icono monitor (blanco sobre azul)
    draw  = ImageDraw.Draw(img)
    off   = 4  # offset por shadow padding
    mx    = size // 2 + off
    my    = size // 2 + off
    sw    = int(size * 0.48)
    sh    = int(size * 0.32)
    # pantalla redondeada
    draw.rounded_rectangle(
        [mx - sw//2, my - sh//2, mx + sw//2, my + sh//2 - 4],
        radius=4, fill="white"
    )
    # base del monitor
    draw.rectangle([mx - 5, my + sh//2 - 4, mx + 5, my + sh//2 + 4], fill="white")
    draw.rectangle([mx - 10, my + sh//2 + 2, mx + 10, my + sh//2 + 6], fill="white")
    # líneas decorativas dentro de pantalla
    lx = mx - sw//2 + 6
    ly = my - sh//2 + 7
    lw = sw - 12
    draw.rectangle([lx, ly,      lx + int(lw*0.65), ly + 4],      fill=(147, 197, 253, 200))
    draw.rectangle([lx, ly + 8,  lx + int(lw*0.85), ly + 12],     fill=(147, 197, 253, 160))
    draw.rectangle([lx, ly + 16, lx + int(lw*0.45), ly + 20],     fill=(147, 197, 253, 140))

    return img


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA DE LOGIN
# ══════════════════════════════════════════════════════════════════════════════
class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.on_login_success = on_login_success
        self._bg_photo = None
        self._logo_img = None
        self._active_tab = "login"
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Fondo canvas ──
        self._canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._on_resize)

        # ── Panel central ──
        self._panel = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=20,
            border_width=1,
            border_color=CARD_BORDER,
            width=440,
        )
        self._panel.place(relx=0.5, rely=0.5, anchor="center")
        self._panel.grid_columnconfigure(0, weight=1)

        # Logo
        logo_pil = Image.open("logo.png").convert("RGBA")
        self._logo_img = ctk.CTkImage(light_image=logo_pil, size=(200, 120))
        ctk.CTkLabel(self._panel, image=self._logo_img, text="").grid(
            row=0, column=0, pady=(36, 0)
        )

        # Nombre del negocio
        ctk.CTkLabel(
            self._panel,
            text="",
            font=("Georgia", 26, "bold"),
            text_color=TEXT_DARK,
        ).grid(row=1, column=0, pady=(10, 2))

        # ── Tabs ──
        tab_bar = ctk.CTkFrame(self._panel, fg_color=INPUT_BG, corner_radius=10)
        tab_bar.grid(row=2, column=0, padx=36, pady=(16, 0), sticky="ew")
        tab_bar.grid_columnconfigure((0, 1), weight=1)

        self._tab_login_btn = ctk.CTkButton(
            tab_bar, text="Iniciar sesión",
            font=("Helvetica", 13, "bold"),
            height=38, corner_radius=8,
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="white",
            command=self._show_login_tab,
        )
        self._tab_login_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        self._tab_reg_btn = ctk.CTkButton(
            tab_bar, text="Registrarse",
            font=("Helvetica", 13, "bold"),
            height=38, corner_radius=8,
            fg_color="transparent", hover_color=CARD_BORDER, text_color=TEXT_MID,
            command=self._show_register_tab,
        )
        self._tab_reg_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        # Separador
        ctk.CTkFrame(self._panel, fg_color=CARD_BORDER, height=1, corner_radius=0).grid(
            row=3, column=0, sticky="ew", pady=(16, 0)
        )

        # ── Contenedor de formularios ──
        self._form_container = ctk.CTkFrame(self._panel, fg_color="transparent")
        self._form_container.grid(row=4, column=0, padx=36, pady=(20, 0), sticky="ew")
        self._form_container.grid_columnconfigure(0, weight=1)

        self._build_login_form()
        self._build_register_form()
        self._show_login_tab()

        # Footer
        footer = ctk.CTkFrame(self._panel, fg_color="#f8faff", corner_radius=0)
        footer.grid(row=5, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer, text=f"PC: {PC_NAME}",
            font=("Helvetica", 11), text_color=TEXT_LIGHT,
        ).grid(row=0, column=0, pady=(12, 0))

        if DEV_MODE:
            ctk.CTkLabel(
                footer,
                text="⚙  Modo desarrollo — cualquier usuario funciona",
                font=("Helvetica", 11), text_color=WARNING,
            ).grid(row=1, column=0, pady=(4, 12))
        else:
            ctk.CTkFrame(footer, fg_color="transparent", height=12).grid(row=1, column=0)

    def _build_login_form(self):
        self._login_frame = ctk.CTkFrame(self._form_container, fg_color="transparent")
        self._login_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self._login_frame, text="Usuario",
            font=("Helvetica", 12, "bold"), text_color=TEXT_MID, anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.user_entry = ctk.CTkEntry(
            self._login_frame, placeholder_text="Escribe tu usuario",
            font=("Helvetica", 14), height=46, corner_radius=10,
            fg_color=INPUT_BG, border_color=INPUT_BORDER, border_width=1,
            text_color=TEXT_DARK, placeholder_text_color=TEXT_LIGHT,
        )
        self.user_entry.grid(row=1, column=0, sticky="ew")
        self.user_entry.bind("<Return>", lambda e: self._do_login())

        ctk.CTkLabel(self._login_frame, text="Contraseña",
            font=("Helvetica", 12, "bold"), text_color=TEXT_MID, anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=(18, 6))

        self.pass_entry = ctk.CTkEntry(
            self._login_frame, placeholder_text="••••••••", show="•",
            font=("Helvetica", 14), height=46, corner_radius=10,
            fg_color=INPUT_BG, border_color=INPUT_BORDER, border_width=1,
            text_color=TEXT_DARK, placeholder_text_color=TEXT_LIGHT,
        )
        self.pass_entry.grid(row=3, column=0, sticky="ew")
        self.pass_entry.bind("<Return>", lambda e: self._do_login())

        self.error_label = ctk.CTkLabel(
            self._login_frame, text="",
            font=("Helvetica", 12), text_color=ERROR,
        )
        self.error_label.grid(row=4, column=0, pady=(10, 0))

        self.login_btn = ctk.CTkButton(
            self._login_frame, text="Iniciar sesión",
            font=("Helvetica", 14, "bold"), height=48, corner_radius=10,
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="white",
            command=self._do_login,
        )
        self.login_btn.grid(row=5, column=0, sticky="ew", pady=(16, 20))

    def _build_register_form(self):
        self._register_frame = ctk.CTkFrame(self._form_container, fg_color="transparent")
        self._register_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self._register_frame, text="Usuario",
            font=("Helvetica", 12, "bold"), text_color=TEXT_MID, anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.reg_user_entry = ctk.CTkEntry(
            self._register_frame, placeholder_text="Elige un nombre de usuario",
            font=("Helvetica", 14), height=46, corner_radius=10,
            fg_color=INPUT_BG, border_color=INPUT_BORDER, border_width=1,
            text_color=TEXT_DARK, placeholder_text_color=TEXT_LIGHT,
        )
        self.reg_user_entry.grid(row=1, column=0, sticky="ew")

        ctk.CTkLabel(self._register_frame, text="Contraseña",
            font=("Helvetica", 12, "bold"), text_color=TEXT_MID, anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=(18, 6))

        self.reg_pass_entry = ctk.CTkEntry(
            self._register_frame, placeholder_text="••••••••", show="•",
            font=("Helvetica", 14), height=46, corner_radius=10,
            fg_color=INPUT_BG, border_color=INPUT_BORDER, border_width=1,
            text_color=TEXT_DARK, placeholder_text_color=TEXT_LIGHT,
        )
        self.reg_pass_entry.grid(row=3, column=0, sticky="ew")

        ctk.CTkLabel(self._register_frame, text="Confirmar contraseña",
            font=("Helvetica", 12, "bold"), text_color=TEXT_MID, anchor="w",
        ).grid(row=4, column=0, sticky="w", pady=(18, 6))

        self.reg_pass2_entry = ctk.CTkEntry(
            self._register_frame, placeholder_text="••••••••", show="•",
            font=("Helvetica", 14), height=46, corner_radius=10,
            fg_color=INPUT_BG, border_color=INPUT_BORDER, border_width=1,
            text_color=TEXT_DARK, placeholder_text_color=TEXT_LIGHT,
        )
        self.reg_pass2_entry.grid(row=5, column=0, sticky="ew")
        self.reg_pass2_entry.bind("<Return>", lambda e: self._do_register())

        self.reg_error_label = ctk.CTkLabel(
            self._register_frame, text="",
            font=("Helvetica", 12), text_color=ERROR,
        )
        self.reg_error_label.grid(row=6, column=0, pady=(10, 0))

        self.reg_btn = ctk.CTkButton(
            self._register_frame, text="Crear cuenta",
            font=("Helvetica", 14, "bold"), height=48, corner_radius=10,
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="white",
            command=self._do_register,
        )
        self.reg_btn.grid(row=7, column=0, sticky="ew", pady=(16, 20))

    # ── Tabs ─────────────────────────────────────────────────────────────────
    def _show_login_tab(self):
        self._active_tab = "login"
        self._register_frame.grid_remove()
        self._login_frame.grid(row=0, column=0, sticky="ew")
        self._tab_login_btn.configure(fg_color=ACCENT, text_color="white")
        self._tab_reg_btn.configure(fg_color="transparent", text_color=TEXT_MID)

    def _show_register_tab(self):
        self._active_tab = "register"
        self._login_frame.grid_remove()
        self._register_frame.grid(row=0, column=0, sticky="ew")
        self._tab_reg_btn.configure(fg_color=ACCENT, text_color="white")
        self._tab_login_btn.configure(fg_color="transparent", text_color=TEXT_MID)

    # ── Resize ───────────────────────────────────────────────────────────────
    def _on_resize(self, event):
        w, h = event.width, event.height
        if w < 10 or h < 10:
            return
        bg = _make_background(w, h)
        self._bg_photo = ImageTk.PhotoImage(bg)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw", image=self._bg_photo)

    # ── Login ────────────────────────────────────────────────────────────────
    def _do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not username or not password:
            self._show_error("Completa todos los campos")
            return

        self.login_btn.configure(state="disabled", text="Verificando...")
        self.error_label.configure(text="")

        if DEV_MODE:
            fake_data = {"session_id": "dev-session-001", "username": username}
            self.after(500, lambda: self.on_login_success(fake_data))
            return

        threading.Thread(
            target=self._api_login, args=(username, password), daemon=True
        ).start()

    def _api_login(self, username, password):
        try:
            resp = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={"username": username, "password": password, "pc_name": PC_NAME},
                timeout=8,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.after(0, lambda: self.on_login_success(data))
            else:
                msg = resp.json().get("detail", "Usuario o contraseña incorrectos")
                self.after(0, lambda: self._show_error(msg))
        except requests.ConnectionError:
            self.after(0, lambda: self._show_error("Sin conexión con el servidor"))
        except Exception as e:
            self.after(0, lambda: self._show_error(f"Error: {e}"))
        finally:
            self.after(0, lambda: self.login_btn.configure(
                state="normal", text="Iniciar sesión"
            ))

    def _show_error(self, msg):
        self.error_label.configure(text=f"⚠  {msg}")

    # ── Register ─────────────────────────────────────────────────────────────
    def _do_register(self):
        username = self.reg_user_entry.get().strip()
        password = self.reg_pass_entry.get().strip()
        password2 = self.reg_pass2_entry.get().strip()

        if not username or not password or not password2:
            self._show_reg_error("Completa todos los campos")
            return

        if len(username) < 3:
            self._show_reg_error("El usuario debe tener al menos 3 caracteres")
            return

        if len(password) < 4:
            self._show_reg_error("La contraseña debe tener al menos 4 caracteres")
            return

        if password != password2:
            self._show_reg_error("Las contraseñas no coinciden")
            return

        self.reg_btn.configure(state="disabled", text="Creando cuenta...")
        self.reg_error_label.configure(text="")

        if DEV_MODE:
            self.after(500, lambda: self._show_reg_success())
            return

        threading.Thread(
            target=self._api_register, args=(username, password), daemon=True
        ).start()

    def _api_register(self, username, password):
        try:
            resp = requests.post(
                f"{API_BASE_URL}/auth/register",
                json={"username": username, "password": password},
                timeout=8,
            )
            if resp.status_code in (200, 201):
                self.after(0, self._show_reg_success)
            else:
                msg = resp.json().get("detail", "Error al crear la cuenta")
                self.after(0, lambda: self._show_reg_error(msg))
        except requests.ConnectionError:
            self.after(0, lambda: self._show_reg_error("Sin conexión con el servidor"))
        except Exception as e:
            self.after(0, lambda: self._show_reg_error(f"Error: {e}"))
        finally:
            self.after(0, lambda: self.reg_btn.configure(
                state="normal", text="Crear cuenta"
            ))

    def _show_reg_error(self, msg):
        self.reg_error_label.configure(text=f"⚠  {msg}", text_color=ERROR)

    def _show_reg_success(self):
        self.reg_btn.configure(state="normal", text="Crear cuenta")
        self.reg_error_label.configure(
            text="✓  Cuenta creada, ya puedes iniciar sesión",
            text_color=SUCCESS,
        )
        self.reg_user_entry.delete(0, "end")
        self.reg_pass_entry.delete(0, "end")
        self.reg_pass2_entry.delete(0, "end")
        self.after(1500, self._show_login_tab)


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA DE SESIÓN ACTIVA
# ══════════════════════════════════════════════════════════════════════════════
class SessionScreen(ctk.CTkFrame):
    def __init__(self, parent, user_data, on_logout):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.user_data  = user_data
        self.on_logout  = on_logout
        self.session_id = user_data.get("session_id")
        self.username   = user_data.get("username", "Usuario")

        self.start_time         = time.time()
        self.running            = True
        self.warned_inactivity  = False
        self._bg_photo          = None

        self._build_ui()
        self._start_timers()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Fondo
        self._canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._on_resize)

        # Panel central
        panel = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=20,
            border_width=1,
            border_color=CARD_BORDER,
            width=460,
        )
        panel.place(relx=0.5, rely=0.5, anchor="center")
        panel.grid_columnconfigure(0, weight=1)

        # Header con nombre
        header = ctk.CTkFrame(panel, fg_color=ACCENT, corner_radius=0,
                               width=460, height=80)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"Hola, {self.username} 👋",
            font=("Georgia", 20, "bold"),
            text_color="white",
        ).grid(row=0, column=0, pady=(14, 2))

        ctk.CTkLabel(
            header,
            text="Tu sesión está activa",
            font=("Helvetica", 12),
            text_color="#ffe0a0",
        ).grid(row=1, column=0, pady=(0, 14))

        # Tiempo de sesión
        t_frame = ctk.CTkFrame(panel, fg_color=ACCENT_LIGHT, corner_radius=12)
        t_frame.grid(row=1, column=0, padx=32, pady=(28, 0), sticky="ew")
        t_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            t_frame,
            text="TIEMPO DE SESIÓN",
            font=("Helvetica", 11, "bold"),
            text_color=ACCENT,
        ).grid(row=0, column=0, pady=(16, 4))

        self.time_label = ctk.CTkLabel(
            t_frame,
            text="00:00:00",
            font=("Courier New", 48, "bold"),
            text_color=ACCENT_DARK,
        )
        self.time_label.grid(row=1, column=0, pady=(0, 16))

        # Inactividad
        i_frame = ctk.CTkFrame(panel, fg_color=INPUT_BG, corner_radius=12,
                                border_width=1, border_color=CARD_BORDER)
        i_frame.grid(row=2, column=0, padx=32, pady=(16, 0), sticky="ew")
        i_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            i_frame,
            text="INACTIVIDAD",
            font=("Helvetica", 11, "bold"),
            text_color=TEXT_MID,
        ).grid(row=0, column=0, pady=(14, 4))

        self.inact_label = ctk.CTkLabel(
            i_frame,
            text="0:00 / 20:00",
            font=("Courier New", 20, "bold"),
            text_color=TEXT_DARK,
        )
        self.inact_label.grid(row=1, column=0)

        self.inact_bar = ctk.CTkProgressBar(
            i_frame, width=340, height=8, corner_radius=4,
            fg_color=CARD_BORDER, progress_color=SUCCESS,
        )
        self.inact_bar.grid(row=2, column=0, pady=(8, 16))
        self.inact_bar.set(0)

        # Botón cerrar sesión
        self.logout_btn = ctk.CTkButton(
            panel,
            text="Cerrar sesión",
            font=("Helvetica", 14, "bold"),
            height=48,
            corner_radius=10,
            fg_color="white",
            border_width=1,
            border_color=ERROR,
            hover_color=ERROR_LIGHT,
            text_color=ERROR,
            command=self._manual_logout,
        )
        self.logout_btn.grid(row=3, column=0, padx=32, pady=(20, 0), sticky="ew")

        # Aviso inactividad
        self.warning_label = ctk.CTkLabel(
            panel, text="",
            font=("Helvetica", 12),
            text_color=WARNING,
        )
        self.warning_label.grid(row=4, column=0, pady=(10, 24))

    def _on_resize(self, event):
        w, h = event.width, event.height
        if w < 10 or h < 10:
            return
        bg = _make_background(w, h)
        self._bg_photo = ImageTk.PhotoImage(bg)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw", image=self._bg_photo)

    # ── Timers ───────────────────────────────────────────────────────────────
    def _start_timers(self):
        self._tick()

    def _tick(self):
        if not self.running:
            return

        elapsed = int(time.time() - self.start_time)
        h, rem  = divmod(elapsed, 3600)
        m, s    = divmod(rem, 60)
        self.time_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")

        inactive = int(_get_idle_seconds())
        pct      = min(inactive / INACTIVITY_TIMEOUT, 1.0)
        im, is_  = divmod(inactive, 60)
        tm, ts   = divmod(INACTIVITY_TIMEOUT, 60)
        self.inact_label.configure(text=f"{im}:{is_:02d} / {tm}:{ts:02d}")
        self.inact_bar.set(pct)

        if pct > 0.75:
            self.inact_bar.configure(progress_color=ERROR)
        elif pct > 0.5:
            self.inact_bar.configure(progress_color=WARNING)
        else:
            self.inact_bar.configure(progress_color=SUCCESS)

        remaining = INACTIVITY_TIMEOUT - inactive
        if remaining <= 300 and not self.warned_inactivity:
            self.warned_inactivity = True
            self.warning_label.configure(
                text=f"⚠  Cierre automático por inactividad en {remaining // 60} min"
            )
        elif remaining > 300:
            self.warned_inactivity = False
            self.warning_label.configure(text="")

        if inactive >= INACTIVITY_TIMEOUT:
            self._auto_logout()
            return

        self.after(1000, self._tick)

    # ── Logout ───────────────────────────────────────────────────────────────
    def _manual_logout(self):
        self._do_logout(reason="manual")

    def _auto_logout(self):
        self._do_logout(reason="inactivity")

    def _do_logout(self, reason="manual"):
        if not self.running:
            return
        self.running = False
        duration = int(time.time() - self.start_time)
        self.logout_btn.configure(state="disabled", text="Cerrando sesión...")
        threading.Thread(
            target=self._api_logout, args=(duration, reason), daemon=True
        ).start()

    def _api_logout(self, duration, reason):
        try:
            requests.post(
                f"{API_BASE_URL}/sessions/close",
                json={
                    "session_id": self.session_id,
                    "duration_seconds": duration,
                    "logout_reason": reason,
                    "pc_name": PC_NAME,
                },
                timeout=8,
            )
        except Exception:
            pass
        finally:
            self.after(0, lambda: self._cleanup_and_logout(reason))

    def _cleanup_and_logout(self, reason):
        _close_user_apps()
        self.on_logout(reason)


# ══════════════════════════════════════════════════════════════════════════════
#  WIDGET FLOTANTE DE SESIÓN
# ══════════════════════════════════════════════════════════════════════════════
class SessionWidget(ctk.CTkToplevel):
    """Ventanita flotante que se muestra en la esquina durante la sesión."""

    WIDGET_W = 240
    WIDGET_H = 220

    def __init__(self, user_data, on_logout):
        super().__init__()
        self.on_logout  = on_logout
        self.session_id = user_data.get("session_id")
        self.username   = user_data.get("username", "Usuario")

        self.start_time        = time.time()
        self.running           = True
        self.warned_inactivity = False
        self._dragging         = False
        self._drag_x           = 0
        self._drag_y           = 0

        # ── Configuración de ventana ──
        self.title("")
        self.overrideredirect(True)          # Sin bordes ni barra de título
        self.attributes("-topmost", True)    # Siempre encima
        self.attributes("-alpha", 0.95)      # Ligeramente transparente
        self.configure(fg_color=CARD_BG)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        # Posición: esquina inferior derecha
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = sw - self.WIDGET_W - 16
        y  = sh - self.WIDGET_H - 48    # 48 para dejar espacio a la barra de tareas
        self.geometry(f"{self.WIDGET_W}x{self.WIDGET_H}+{x}+{y}")

        self._build_ui()
        self._start_timers()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Header arrastrable ──
        header = ctk.CTkFrame(self, fg_color=ACCENT, corner_radius=0, height=36)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"● {self.username}",
            font=("Helvetica", 12, "bold"),
            text_color="white",
        ).grid(row=0, column=0, sticky="w", padx=12)

        # Arrastrar con el header
        header.bind("<ButtonPress-1>",   self._drag_start)
        header.bind("<B1-Motion>",       self._drag_move)
        for child in header.winfo_children():
            child.bind("<ButtonPress-1>", self._drag_start)
            child.bind("<B1-Motion>",     self._drag_move)

        # ── Tiempo ──
        self.time_label = ctk.CTkLabel(
            self,
            text="00:00:00",
            font=("Courier New", 32, "bold"),
            text_color=ACCENT_DARK,
        )
        self.time_label.grid(row=1, column=0, pady=(10, 0))

        # ── Inactividad ──
        inact_frame = ctk.CTkFrame(self, fg_color="transparent")
        inact_frame.grid(row=2, column=0, padx=16, sticky="ew")
        inact_frame.grid_columnconfigure(0, weight=1)

        self.inact_label = ctk.CTkLabel(
            inact_frame,
            text="Inactividad: 0:00",
            font=("Helvetica", 10),
            text_color=TEXT_MID,
        )
        self.inact_label.grid(row=0, column=0, sticky="w")

        self.inact_bar = ctk.CTkProgressBar(
            inact_frame, height=5, corner_radius=3,
            fg_color=CARD_BORDER, progress_color=SUCCESS,
        )
        self.inact_bar.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        self.inact_bar.set(0)

        # ── Mensaje recordatorio ──
        ctk.CTkLabel(
            self,
            text="💡 Recuerda cerrar sesión\nantes de irte",
            font=("Helvetica", 10),
            text_color=TEXT_MID,
            justify="center",
        ).grid(row=3, column=0, padx=16, pady=(8, 0))

        # ── Botón cerrar sesión ──
        self.logout_btn = ctk.CTkButton(
            self,
            text="Cerrar sesión",
            font=("Helvetica", 11, "bold"),
            height=32,
            corner_radius=8,
            fg_color="white",
            border_width=1,
            border_color=ERROR,
            hover_color=ERROR_LIGHT,
            text_color=ERROR,
            command=self._manual_logout,
        )
        self.logout_btn.grid(row=4, column=0, padx=16, pady=(6, 12), sticky="ew")

    # ── Arrastrar ────────────────────────────────────────────────────────────
    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    # ── Timers ───────────────────────────────────────────────────────────────
    def _start_timers(self):
        self._tick()

    def _tick(self):
        if not self.running:
            return

        elapsed = int(time.time() - self.start_time)
        h, rem  = divmod(elapsed, 3600)
        m, s    = divmod(rem, 60)
        self.time_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")

        inactive = int(_get_idle_seconds())
        pct      = min(inactive / INACTIVITY_TIMEOUT, 1.0)
        im, is_  = divmod(inactive, 60)
        self.inact_label.configure(text=f"Inactividad: {im}:{is_:02d}")
        self.inact_bar.set(pct)

        if pct > 0.75:
            self.inact_bar.configure(progress_color=ERROR)
        elif pct > 0.5:
            self.inact_bar.configure(progress_color=WARNING)
        else:
            self.inact_bar.configure(progress_color=SUCCESS)

        if inactive >= INACTIVITY_TIMEOUT:
            self._auto_logout()
            return

        self.after(1000, self._tick)

    # ── Logout ───────────────────────────────────────────────────────────────
    def _manual_logout(self):
        self._do_logout(reason="manual")

    def _auto_logout(self):
        self._do_logout(reason="inactivity")

    def _do_logout(self, reason="manual"):
        if not self.running:
            return
        self.running = False
        duration = int(time.time() - self.start_time)
        self.logout_btn.configure(state="disabled", text="Cerrando...")
        threading.Thread(
            target=self._api_logout, args=(duration, reason), daemon=True
        ).start()

    def _api_logout(self, duration, reason):
        try:
            requests.post(
                f"{API_BASE_URL}/sessions/close",
                json={
                    "session_id": self.session_id,
                    "duration_seconds": duration,
                    "logout_reason": reason,
                    "pc_name": PC_NAME,
                },
                timeout=8,
            )
        except Exception:
            pass
        finally:
            self.after(0, lambda: self._finish_logout(reason))

    def _finish_logout(self, reason):
        _close_user_apps()
        self.on_logout(reason)


# ══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES DEL SISTEMA
# ══════════════════════════════════════════════════════════════════════════════
def _get_idle_seconds():
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
    return millis / 1000.0


def _close_user_apps():
    if DEV_MODE:
        print("[DEV] Se cerrarían las apps del usuario (omitido en dev mode)")
        return
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if proc.info["name"].lower() in APPS_TO_CLOSE:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  APP PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class CyberCafeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CyberCafé" + (" [DEV MODE]" if DEV_MODE else ""))
        self.configure(fg_color=BG_BASE)

        if DEV_MODE:
            self.geometry("1000x680")
            self.resizable(True, True)
        else:
            self.attributes("-fullscreen", True)
            self.attributes("-topmost", True)
            self.resizable(False, False)
            self.protocol("WM_DELETE_WINDOW", lambda: None)
            self.bind("<Alt-F4>", lambda e: "break")

        self._current_screen = None
        self._show_login()

    def _show_login(self):
        if self._current_screen:
            self._current_screen.destroy()
        screen = LoginScreen(self, on_login_success=self._on_login)
        screen.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._current_screen = screen

    def _on_login(self, user_data):
        if self._current_screen:
            self._current_screen.destroy()
        # Ocultar ventana principal durante la sesión
        self.withdraw()
        # Abrir widget flotante
        self._widget = SessionWidget(user_data, on_logout=self._on_logout)

    def _on_logout(self, reason):
        if hasattr(self, "_widget") and self._widget:
            try:
                self._widget.destroy()
            except Exception:
                pass
            self._widget = None
        # Volver a mostrar la ventana de login
        self.deiconify()
        self._show_login()


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = CyberCafeApp()
    app.mainloop()