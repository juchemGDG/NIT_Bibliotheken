"""
NIT Bibliothek: MQTT - Stabiler MQTT-Client fuer ESP32 mit MicroPython
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-04

Implementiert einen robusten MQTT-Client (v3.1.1) mit sauberer Fehlerbehandlung,
QoS-1-Unterstuetzung, Last-Will und optionaler automatischer Reconnect-Strategie.
"""

import socket
import struct

try:
    import ssl
except ImportError:
    ssl = None

try:
    import utime as time
except ImportError:
    import time


class MQTTException(Exception):
    """Basisklasse fuer MQTT-Fehler."""


class MQTTClient:
    """
    Einfacher und robuster MQTT-Client fuer Unterricht und Prototyping.

    Unterstuetzte Hardware:
    - ESP32 mit MicroPython
    - MQTT-Broker (z. B. Mosquitto auf Raspberry Pi)

    Schnittstelle: WLAN / TCP (optional TLS)
    """

    def __init__(
        self,
        client_id,
        server,
        port=0,
        user=None,
        password=None,
        keepalive=60,
        ssl=None,
        ssl_context=None,
        socket_timeout=5,
    ):
        if ssl_context is None and ssl is not None:
            ssl_context = ssl

        if port == 0:
            port = 8883 if ssl_context else 1883

        self.client_id = self._to_bytes(client_id, "client_id")
        self.server = server
        self.port = int(port)
        self.user = self._optional_bytes(user)
        self.pswd = self._optional_bytes(password)
        self.keepalive = int(keepalive)
        self.ssl_context = ssl_context
        self.socket_timeout = socket_timeout

        self.sock = None
        self.pid = 0
        self.cb = None
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False

        self._last_io_ms = self._ticks_ms()

        if self.keepalive < 0 or self.keepalive >= 65536:
            raise ValueError("keepalive muss zwischen 0 und 65535 liegen")

    # ================================================================
    # Oeffentliche API
    # ================================================================

    def set_callback(self, callback):
        """Setzt den Callback fuer eingehende Subscribe-Nachrichten."""
        if callback is not None and not callable(callback):
            raise TypeError("callback muss eine Funktion sein")
        self.cb = callback

    def set_last_will(self, topic, msg, retain=False, qos=0):
        """Setzt Last-Will-Nachricht fuer ungeordnetes Trennen."""
        if qos not in (0, 1, 2):
            raise ValueError("qos muss 0, 1 oder 2 sein")

        topic_b = self._to_bytes(topic, "topic")
        if not topic_b:
            raise ValueError("topic darf nicht leer sein")

        self.lw_topic = topic_b
        self.lw_msg = self._to_bytes(msg, "msg")
        self.lw_qos = qos
        self.lw_retain = bool(retain)

    def connect(self, clean_session=True):
        """
        Baut Verbindung zum Broker auf.

        Returns:
            session_present (bool)
        """
        self._open_socket()

        premsg = bytearray(b"\x10\0\0\0\0\0")
        msg = bytearray(b"\x04MQTT\x04\x02\0\0")

        sz = 10 + 2 + len(self.client_id)
        flags = (1 if clean_session else 0) << 1

        if self.user is not None:
            sz += 2 + len(self.user)
            flags |= 0x80
            if self.pswd is not None:
                sz += 2 + len(self.pswd)
                flags |= 0x40

        if self.lw_topic is not None:
            sz += 2 + len(self.lw_topic) + 2 + len(self.lw_msg)
            flags |= 0x04
            flags |= (self.lw_qos & 0x03) << 3
            if self.lw_retain:
                flags |= 0x20

        msg[6] = flags
        msg[7] = (self.keepalive >> 8) & 0xFF
        msg[8] = self.keepalive & 0xFF

        i = 1
        while sz > 0x7F:
            premsg[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        premsg[i] = sz

        self._sock_write(premsg, i + 2)
        self._sock_write(msg)
        self._send_str(self.client_id)

        if self.lw_topic is not None:
            self._send_str(self.lw_topic)
            self._send_str(self.lw_msg)

        if self.user is not None:
            self._send_str(self.user)
            if self.pswd is not None:
                self._send_str(self.pswd)

        resp = self._sock_read_exact(4)
        if resp[0] != 0x20 or resp[1] != 0x02:
            raise MQTTException("Ungueltige CONNACK vom Broker")

        if resp[3] != 0:
            raise MQTTException("Broker verweigert Verbindung, Code {}".format(resp[3]))

        self._last_io_ms = self._ticks_ms()
        return bool(resp[2] & 1)

    def disconnect(self):
        """Trennt sauber vom Broker."""
        try:
            if self.sock is not None:
                self._sock_write(b"\xe0\0")
        finally:
            self._close_socket()

    def reconnect(self, clean_session=True):
        """Schliesst alte Verbindung (falls noetig) und verbindet neu."""
        self._close_socket()
        return self.connect(clean_session=clean_session)

    def is_connected(self):
        """True, wenn aktuell ein Socket gesetzt ist."""
        return self.sock is not None

    def ping(self):
        """Sendet PINGREQ an den Broker."""
        self._ensure_connected()
        self._sock_write(b"\xc0\0")

    def publish(self, topic, msg, retain=False, qos=0):
        """
        Veroeffentlicht eine Nachricht.

        Args:
            topic: Topic als str/bytes
            msg: Payload als str/bytes/int/float/bool/dict/list
            retain: Retain-Flag
            qos: 0 oder 1
        """
        if qos not in (0, 1):
            raise ValueError("Es werden nur QoS 0 und 1 unterstuetzt")

        topic_b = self._to_bytes(topic, "topic")
        if not topic_b:
            raise ValueError("topic darf nicht leer sein")
        msg_b = self._payload_to_bytes(msg)

        pkt = bytearray(b"\x30\0\0\0")
        pkt[0] |= (qos << 1) | (1 if retain else 0)

        sz = 2 + len(topic_b) + len(msg_b)
        if qos > 0:
            sz += 2

        if sz >= 2097152:
            raise ValueError("Nachricht ist zu gross")

        i = 1
        while sz > 0x7F:
            pkt[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        pkt[i] = sz

        self._ensure_connected()
        self._sock_write(pkt, i + 1)
        self._send_str(topic_b)

        pid = 0
        if qos > 0:
            self.pid = (self.pid + 1) & 0xFFFF
            if self.pid == 0:
                self.pid = 1
            pid = self.pid
            struct.pack_into("!H", pkt, 0, pid)
            self._sock_write(pkt, 2)

        self._sock_write(msg_b)

        if qos == 1:
            self._wait_puback(pid)

    def subscribe(self, topic, qos=0):
        """Abonniert ein Topic (QoS 0 oder 1)."""
        if self.cb is None:
            raise MQTTException("Subscribe Callback fehlt. Erst set_callback() aufrufen")
        if qos not in (0, 1):
            raise ValueError("Es werden nur QoS 0 und 1 unterstuetzt")

        topic_b = self._to_bytes(topic, "topic")
        if not topic_b:
            raise ValueError("topic darf nicht leer sein")

        pkt = bytearray(b"\x82\0\0\0")
        self.pid = (self.pid + 1) & 0xFFFF
        if self.pid == 0:
            self.pid = 1

        remaining = 2 + 2 + len(topic_b) + 1
        struct.pack_into("!BH", pkt, 1, remaining, self.pid)

        self._ensure_connected()
        self._sock_write(pkt)
        self._send_str(topic_b)
        self._sock_write(bytes([qos]))

        while True:
            op = self.wait_msg()
            if op == 0x90:
                resp = self._sock_read_exact(4)
                if resp[1] != pkt[2] or resp[2] != pkt[3]:
                    raise MQTTException("SUBACK mit unpassender Packet-ID")
                if resp[3] == 0x80:
                    raise MQTTException("Broker hat Subscribe abgelehnt")
                return

    def wait_msg(self):
        """
        Wartet auf genau ein MQTT-Paket und verarbeitet es.

        Rueckgabe:
            op-Code oder None
        """
        return self._process_msg(non_blocking=False)

    def check_msg(self):
        """
        Prueft nicht-blockierend auf eine Nachricht.

        Rueckgabe:
            op-Code oder None
        """
        return self._process_msg(non_blocking=True)

    def keepalive_step(self):
        """
        Optionaler Wartungsaufruf fuer Hauptschleifen.
        Sendet PINGREQ, wenn seit laengerer Zeit nichts gesendet wurde.
        """
        if self.keepalive <= 0 or self.sock is None:
            return

        now = self._ticks_ms()
        elapsed = self._ticks_diff(now, self._last_io_ms)
        if elapsed >= (self.keepalive * 1000) // 2:
            self.ping()

    # ================================================================
    # Interne Helfer
    # ================================================================

    def _open_socket(self):
        self._close_socket()

        sock = socket.socket()
        try:
            if self.socket_timeout is not None:
                try:
                    sock.settimeout(self.socket_timeout)
                except Exception:
                    pass

            addr = socket.getaddrinfo(self.server, self.port)[0][-1]
            sock.connect(addr)

            if self.ssl_context:
                if hasattr(self.ssl_context, "wrap_socket"):
                    sock = self.ssl_context.wrap_socket(sock, server_hostname=self.server)
                else:
                    sock = ssl.wrap_socket(sock)

            self.sock = sock
            self._last_io_ms = self._ticks_ms()

        except Exception as exc:
            try:
                sock.close()
            except Exception:
                pass
            raise MQTTException("Verbindung fehlgeschlagen: {}".format(exc))

    def _close_socket(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def _send_str(self, data_bytes):
        self._sock_write(struct.pack("!H", len(data_bytes)))
        self._sock_write(data_bytes)

    def _recv_len(self):
        n = 0
        sh = 0
        while True:
            b = self._sock_read_exact(1)[0]
            n |= (b & 0x7F) << sh
            if not (b & 0x80):
                return n
            sh += 7
            if sh > 21:
                raise MQTTException("Remaining Length ist ungueltig")

    def _wait_puback(self, pid):
        while True:
            op = self.wait_msg()
            if op == 0x40:
                sz = self._sock_read_exact(1)
                if sz != b"\x02":
                    raise MQTTException("Ungueltiges PUBACK")
                rcv_pid = self._sock_read_exact(2)
                rcv_pid = (rcv_pid[0] << 8) | rcv_pid[1]
                if pid == rcv_pid:
                    return

    def _process_msg(self, non_blocking=False):
        self._ensure_connected()

        self._set_non_blocking(non_blocking)
        try:
            res = self.sock.read(1)
        except Exception:
            if non_blocking:
                self._set_non_blocking(False)
                return None
            self._set_non_blocking(False)
            raise

        self._set_non_blocking(False)

        if res is None:
            return None
        if res == b"":
            self._close_socket()
            raise OSError(-1)

        if res == b"\xd0":
            sz = self._sock_read_exact(1)[0]
            if sz != 0:
                raise MQTTException("Ungueltiges PINGRESP")
            return None

        op = res[0]
        if (op & 0xF0) != 0x30:
            return op

        sz = self._recv_len()
        topic_len_b = self._sock_read_exact(2)
        topic_len = (topic_len_b[0] << 8) | topic_len_b[1]

        topic = self._sock_read_exact(topic_len)
        sz -= topic_len + 2

        pid = None
        if op & 0x06:
            pid_b = self._sock_read_exact(2)
            pid = (pid_b[0] << 8) | pid_b[1]
            sz -= 2

        msg = self._sock_read_exact(sz)

        if self.cb is not None:
            self.cb(topic, msg)

        # QoS1 PUBACK zurueck an Broker
        if (op & 0x06) == 0x02 and pid is not None:
            pkt = bytearray(b"\x40\x02\0\0")
            struct.pack_into("!H", pkt, 2, pid)
            self._sock_write(pkt)
        elif (op & 0x06) == 0x04:
            raise MQTTException("QoS2 wird nicht unterstuetzt")

        return op

    def _sock_write(self, data, length=None):
        self._ensure_connected()
        if length is None:
            self.sock.write(data)
        else:
            self.sock.write(data, length)
        self._last_io_ms = self._ticks_ms()

    def _sock_read_exact(self, n):
        self._ensure_connected()
        out = bytearray()
        while len(out) < n:
            part = self.sock.read(n - len(out))
            if part is None:
                continue
            if part == b"":
                self._close_socket()
                raise OSError(-1)
            out.extend(part)
        self._last_io_ms = self._ticks_ms()
        return bytes(out)

    def _ensure_connected(self):
        if self.sock is None:
            raise MQTTException("Nicht verbunden. Erst connect() aufrufen")

    def _set_non_blocking(self, enabled):
        if self.sock is None:
            return

        try:
            self.sock.setblocking(not enabled)
            return
        except Exception:
            pass

        try:
            if enabled:
                self.sock.settimeout(0)
            elif self.socket_timeout is not None:
                self.sock.settimeout(self.socket_timeout)
            else:
                self.sock.settimeout(None)
        except Exception:
            pass

    def _optional_bytes(self, value):
        if value is None:
            return None
        return self._to_bytes(value, "wert")

    def _to_bytes(self, value, field_name):
        if isinstance(value, bytes):
            return value
        if isinstance(value, bytearray):
            return bytes(value)
        if isinstance(value, str):
            return value.encode("utf-8")
        raise TypeError("{} muss str, bytes oder bytearray sein".format(field_name))

    def _payload_to_bytes(self, value):
        if isinstance(value, (bytes, bytearray, str)):
            return self._to_bytes(value, "payload")
        if isinstance(value, bool):
            return b"true" if value else b"false"
        if isinstance(value, (int, float)):
            return str(value).encode("utf-8")
        if isinstance(value, dict) or isinstance(value, list):
            # Minimaler JSON-Ersatz ohne Import von json fuer kleine Firmware.
            try:
                import ujson as json
            except ImportError:
                import json
            return json.dumps(value).encode("utf-8")
        raise TypeError("payload-Typ wird nicht unterstuetzt")

    def _ticks_ms(self):
        if hasattr(time, "ticks_ms"):
            return time.ticks_ms()
        return int(time.time() * 1000)

    def _ticks_diff(self, now, last):
        if hasattr(time, "ticks_diff"):
            return time.ticks_diff(now, last)
        return now - last


__all__ = ["MQTTClient", "MQTTException"]
