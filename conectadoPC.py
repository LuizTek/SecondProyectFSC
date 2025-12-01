import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import random

# Servidor TCP para comunicarse con la Pico W
SERVER_HOST = "10.231.183.144"   # escuchar en todas las interfaces
SERVER_PORT = 8001

client_sock = None
client_addr = None
server_sock = None

def get_3lsb_bits(n: int) -> tuple[str, str, str]:
    """Devuelve (A, B, C) como caracteres '0'/'1'.
    A = bit más significativo de las 3 LSB, C = bit menos significativo.
    """
    b = bin(abs(n))[2:]          # sin prefijo '0b'
    bits3 = b[-3:].zfill(3)      # obtener 3 LSB y rellenar si hace falta
    return bits3[0], bits3[1], bits3[2]

def aceptar_conexiones():
    global server_sock, client_sock, client_addr
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind((SERVER_HOST, SERVER_PORT))
        server_sock.listen(1)
        app_set_status(f"Escuchando en {SERVER_HOST}:{SERVER_PORT} — esperando cliente...")
    except OSError as e:
        app_set_status(f"Error al iniciar servidor: {e}")
        return

    while True:
        try:
            sock, addr = server_sock.accept()
        except OSError:
            break
        client_sock = sock
        client_addr = addr
        app_set_status(f"Cliente conectado: {addr}")
        # recibir posible saludo inicial (no obligatorio)
        try:
            sock.settimeout(0.5)
            data = sock.recv(256)
            if data:
                print("Handshake recibido:", data.decode(errors="ignore"))
        except Exception:
            pass
        finally:
            try:
                sock.settimeout(None)
            except Exception:
                pass

def app_set_status(text: str):
    # Actualiza label en el hilo principal de Tkinter
    def _set():
        status_label.config(text=text)
    try:
        root.after(0, _set)
    except Exception:
        print(text)

def enviar_bits(bits3: str):
    global client_sock, client_addr
    if client_sock is None:
        messagebox.showerror("No conectado", "No hay cliente conectado.")
        return
    try:
        client_sock.sendall(bits3.encode())
        app_set_status(f"Enviado a {client_addr}: {bits3}")
    except Exception as e:
        messagebox.showerror("Error envío", f"No se pudo enviar: {e}")
        try:
            client_sock.close()
        except Exception:
            pass
        client_sock = None
        app_set_status("Cliente desconectado")

def on_convert(event=None):
    s = entry.get().strip()
    if s == "":
        messagebox.showwarning("Entrada vacía", "Ingrese un número entero.")
        return
    try:
        n = int(s)
    except ValueError:
        messagebox.showerror("Entrada inválida", "Ingrese un número entero válido.")
        return
    A, B, C = get_3lsb_bits(n)
    # Bit de habilitación independiente y aleatorio (0 o 1)
    enable = str(random.getrandbits(1))
    bits4 = f"{A}{B}{C}{enable}"   # orden: A B C Enable
    lbl_result.config(text=f"{n} → 3 LSB: {A}{B}{C}   →  A={A}, B={B}, C={C}   |  Enable={enable}")
    enviar_bits(bits4)

def on_close():
    try:
        if client_sock:
            client_sock.close()
    except Exception:
        pass
    try:
        if server_sock:
            server_sock.close()
    except Exception:
        pass
    root.destroy()

# --- GUI ---
root = tk.Tk()
root.title("Enviar 3 LSB a Raspberry Pico W")
root.resizable(False, False)
frm = ttk.Frame(root, padding=12)
frm.pack(fill="both", expand=True)

ttk.Label(frm, text="Número entero (base 10):").grid(column=0, row=0, sticky="w")
entry = ttk.Entry(frm, width=24)
entry.grid(column=1, row=0, padx=8, sticky="w")
entry.focus()

btn = ttk.Button(frm, text="Convertir y Enviar (3 LSB)", command=on_convert)
btn.grid(column=0, row=1, columnspan=2, pady=8)

lbl_result = ttk.Label(frm, text="Resultado: -", font=("Segoe UI", 10))
lbl_result.grid(column=0, row=2, columnspan=2, pady=6, sticky="w")

status_label = ttk.Label(frm, text=f"Listo. Servidor: {SERVER_HOST}:{SERVER_PORT}")
status_label.grid(column=0, row=3, columnspan=2, pady=6, sticky="w")

ttk.Label(frm, text="Pico W -> A:GP27  B:GP26  C:GP22  Enable:GP21").grid(column=0, row=4, columnspan=2, sticky="w")

root.protocol("WM_DELETE_WINDOW", on_close)

# start accept thread
t = threading.Thread(target=aceptar_conexiones, daemon=True)
t.start()

# permitir Enter para convertir
root.bind("<Return>", on_convert)

if __name__ == "__main__":
    root.mainloop()