import network
import socket
from time import sleep
from machine import Pin

# CONFIGURAR: establecer SSID, PASSWORD y la IP/PUERTO del servidor (PC)
SSID = "HONOR 90"
PASSWORD = "yacolomoco"
SERVER_IP = "10.231.183.144"      # IP del PC que ejecuta el servidor
SERVER_PORT = 8001

# Pines en la Pico W
pinA = Pin(27, Pin.OUT)   # A -> bit más significativo de las 3 (GP27)
pinB = Pin(26, Pin.OUT)   # B -> bit medio (GP26)
pinC = Pin(22, Pin.OUT)   # C -> bit menos significativo (GP22)
pinEnable = Pin(21, Pin.OUT)  # Enable (GP21) -> depende del bit enviado por el servidor

def connect_wifi(ssid=SSID, password=PASSWORD, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("WiFi ya conectado, IP:", wlan.ifconfig()[0])
        return True
    print("Conectando a WiFi...", ssid)
    wlan.connect(ssid, password)
    t = timeout
    while not wlan.isconnected() and t > 0:
        print("Esperando conexión... ({}s)".format(t))
        sleep(1)
        t -= 1
    if wlan.isconnected():
        print("Conectado. IP:", wlan.ifconfig()[0])
        return True
    print("No se pudo conectar al WiFi")
    return False

def aplicar_bits(bits4: str):
    """Recibe una cadena de 4 caracteres '0'/'1' en orden A,B,C,Enable.
    Ajusta GP27, GP26, GP22 y GP21 según corresponda.
    """
    if not bits4:
        print("Bits vacíos")
        return
    # normalizar a exactamente 4 bits (si llegan más, tomar los primeros 4; si menos, rellenar a la izquierda)
    filtered = ''.join(ch for ch in bits4 if ch in '01')
    if len(filtered) < 4:
        filtered = filtered.zfill(4)
    bits = filtered[:4]
    a, b, c, e = bits[0], bits[1], bits[2], bits[3]
    try:
        pinA.value(1 if a == '1' else 0)
        pinB.value(1 if b == '1' else 0)
        pinC.value(1 if c == '1' else 0)
        pinEnable.value(1 if e == '1' else 0)
        print("Aplicado bits:", bits, "-> A:", a, "B:", b, "C:", c, "Enable:", e)
    except Exception as ex:
        print("Error aplicando bits:", ex)

def run_client(server_ip=SERVER_IP, server_port=SERVER_PORT):
    if not connect_wifi():
        return
    addr = (server_ip, server_port)
    while True:
        s = None
        try:
            s = socket.socket()
            s.settimeout(10)
            print("Intentando conectar a", addr)
            s.connect(addr)
            s.settimeout(None)  # bloqueo mientras espera datos
            print("Conectado al servidor", addr)
            # enviar saludo opcional para handshake
            try:
                s.sendall(b"Hola, este mensaje es enviado desde la raspy :)")
            except Exception:
                pass

            while True:
                data = s.recv(256)
                if not data:
                    print("Servidor cerró la conexión")
                    break
                msg = data.decode().strip()
                # extraer sólo '0'/'1' y aplicar directamente (se espera 4 bits: A B C Enable)
                bits_only = ''.join(ch for ch in msg if ch in '01')
                # si el servidor envía exactamente 4 caracteres '0'/'1', quedan A B C E
                if bits_only:
                    aplicar_bits(bits_only)
        except Exception as e:
            print("Error de socket / conexión:", e)
        finally:
            try:
                if s:
                    s.close()
            except:
                pass
        print("Reintentando en 5 segundos...")
        sleep(5)

if __name__ == "__main__":
    run_client()
