"""
NIT Bibliothek: ESPNOW - Einfache Funknachrichten zwischen ESP32-Boards
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-04

Kapselt die native ESP-NOW API mit einfacher MAC- und Datenbehandlung.
Ermoeglicht String/JSON-Kommunikation fuer Unterricht und schnelle Prototypen.
"""

import json
import network
import espnow


class ESPNow:
    """
    Vereinfacht ESP-NOW Kommunikation auf dem ESP32.

    Unterstuetzte Hardware:
    - ESP32 mit MicroPython und ESP-NOW-Unterstuetzung
    - Gegenstelle: weiteres ESP32-Board mit ESP-NOW

    Schnittstelle: WLAN (ESP-NOW)
    """

    BROADCAST_MAC = "FF:FF:FF:FF:FF:FF"

    def __init__(self):
        self._wlan = None
        self._esp = None
        self._peers = set()
        self._on_receive = None
        self._subscriptions = {}
        self.init()

    # ================================================================
    # Grundfunktionen
    # ================================================================

    def init(self):
        """Initialisiert WLAN (STA) und ESP-NOW."""
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(True)

        # ESP-NOW benoetigt aktives WLAN, aber keine Verbindung.
        try:
            self._wlan.disconnect()
        except Exception:
            pass

        self._esp = espnow.ESPNow()
        self._esp.active(True)
        return True

    def add_peer(self, mac):
        """
        Fuegt einen Peer hinzu.

        Args:
            mac: MAC-Adresse als String, z. B. "AA:BB:CC:DD:EE:FF"
        """
        mac_str = self._normalize_mac_str(mac)
        mac_bytes = self._mac_str_to_bytes(mac_str)

        if mac_str in self._peers:
            return False

        try:
            self._esp.add_peer(mac_bytes)
        except OSError as exc:
            msg = str(exc)
            # Je nach Firmware kommt hier z. B. "ESP_ERR_ESPNOW_EXIST".
            if "EXIST" in msg:
                self._peers.add(mac_str)
                return False
            raise OSError("Peer konnte nicht hinzugefuegt werden: {}".format(mac_str))

        self._peers.add(mac_str)
        return True

    def send(self, mac, data):
        """
        Sendet Daten an einen Peer.

        Args:
            mac: Ziel-MAC als String (AA:BB:CC:DD:EE:FF)
            data: bytes, str, dict, list, int, float oder bool
        """
        mac_str = self._normalize_mac_str(mac)
        mac_bytes = self._mac_str_to_bytes(mac_str)
        payload = self._to_bytes(data)

        # Peer automatisch anlegen, falls noch nicht vorhanden.
        self._ensure_peer(mac_str)

        try:
            self._esp.send(mac_bytes, payload)
        except OSError:
            raise OSError("Senden fehlgeschlagen. Peer nicht gefunden oder Funkproblem: {}".format(mac_str))

        return True

    def receive(self, timeout_ms=None, decode=True):
        """
        Empfaengt eine Nachricht.

        Args:
            timeout_ms: Timeout in Millisekunden (None = blockend)
            decode: Bei True Rueckgabe als UTF-8 String (wenn moeglich)

        Returns:
            (msg, sender_mac)
            msg ist None, wenn keine Nachricht empfangen wurde.
        """
        if timeout_ms is None:
            sender, msg = self._esp.recv()
        else:
            try:
                sender, msg = self._esp.recv(timeout_ms)
            except TypeError:
                # Fallback fuer Firmware-Varianten ohne Timeout-Argument.
                sender, msg = self._esp.recv()

        if not msg:
            return None, None

        sender_mac = self._mac_bytes_to_str(sender)

        if decode:
            try:
                msg = msg.decode("utf-8")
            except Exception:
                pass

        return msg, sender_mac

    def get_mac(self):
        """Gibt die eigene MAC-Adresse als String zurueck."""
        return self._mac_bytes_to_str(self._wlan.config("mac"))

    # ================================================================
    # Komfortfunktionen
    # ================================================================

    def send_json(self, mac, data_dict):
        """Sendet ein Dictionary als JSON."""
        if not isinstance(data_dict, dict):
            raise TypeError("send_json erwartet ein Dictionary")
        return self.send(mac, json.dumps(data_dict))

    def receive_json(self, timeout_ms=None):
        """
        Empfaengt JSON und konvertiert zu dict.

        Returns:
            (dict_msg, sender_mac) oder (None, None)
        """
        msg, sender = self.receive(timeout_ms=timeout_ms, decode=True)
        if msg is None:
            return None, None

        try:
            data = json.loads(msg)
        except ValueError:
            raise ValueError("Empfangene Nachricht ist kein gueltiges JSON")

        if not isinstance(data, dict):
            raise ValueError("JSON ist gueltig, aber kein Dictionary")

        return data, sender

    def on_receive(self, callback):
        """
        Registriert einen Callback fuer eingehende Nachrichten.

        Der Callback wird aufgerufen als:
            callback(msg, sender_mac)

        Hinweis:
        Die Funktion ist firmware-abhaengig. Falls die eingesetzte
        MicroPython-Version kein IRQ fuer ESP-NOW bietet, wird ein
        NotImplementedError geworfen.
        """
        if not callable(callback):
            raise TypeError("callback muss eine Funktion sein")

        if not hasattr(self._esp, "irq"):
            raise NotImplementedError(
                "on_receive wird von dieser Firmware nicht unterstuetzt")

        self._on_receive = callback

        def _irq_handler(_):
            while True:
                msg, sender = self.receive(timeout_ms=0, decode=True)
                if msg is None:
                    break
                self._on_receive(msg, sender)

        self._esp.irq(_irq_handler)
        return True

    def broadcast(self, data):
        """Sendet Daten als Broadcast an alle erreichbaren ESP-NOW-Geraete."""
        return self.send(self.BROADCAST_MAC, data)

    # ================================================================
    # MQTT-light (brokerlos) ueber ESP-NOW
    # ================================================================

    def publish(self, mac, topic, payload=None, subtopic=None):
        """
        Sendet eine MQTT-aehnliche Publish-Nachricht an einen Peer.

        Args:
            mac: Ziel-MAC als String
            topic: Haupttopic, z. B. "schule"
            payload: JSON-serialisierbare Nutzdaten
            subtopic: Optionales Untertopic, z. B. "raum1/temp"
        """
        full_topic = self._build_topic(topic, subtopic)
        paket = {
            "_proto": "nitbw-mqtt-lite",
            "topic": full_topic,
            "payload": payload,
        }
        return self.send_json(mac, paket)

    def broadcast_publish(self, topic, payload=None, subtopic=None):
        """Sendet eine MQTT-aehnliche Publish-Nachricht als Broadcast."""
        return self.publish(self.BROADCAST_MAC, topic, payload=payload, subtopic=subtopic)

    def subscribe(self, topic, callback=None, subtopic=None):
        """
        Abonniert ein Topic oder Topic-Filter.

        Unterstuetzt einfache Wildcards:
        - "+" fuer genau eine Topic-Ebene
        - "#" am Ende fuer alle folgenden Ebenen

        Args:
            topic: Topic oder Topic-Filter
            callback: Optionaler Handler callback(topic, payload, sender_mac)
            subtopic: Optionales Untertopic
        """
        full_topic = self._build_topic(topic, subtopic)

        if callback is not None and not callable(callback):
            raise TypeError("callback muss eine Funktion sein")

        if full_topic not in self._subscriptions:
            self._subscriptions[full_topic] = []

        if callback is not None and callback not in self._subscriptions[full_topic]:
            self._subscriptions[full_topic].append(callback)

        return full_topic

    def submit(self, topic, callback=None, subtopic=None):
        """
        Alias fuer subscribe().

        Hinweis:
        Manche Unterrichtsmaterialien verwenden "submit" statt "subscribe".
        """
        return self.subscribe(topic, callback=callback, subtopic=subtopic)

    def unsubscribe(self, topic, callback=None, subtopic=None):
        """
        Entfernt ein Topic-Abo oder einen einzelnen Callback.

        Returns:
            True, wenn etwas entfernt wurde, sonst False.
        """
        full_topic = self._build_topic(topic, subtopic)
        callbacks = self._subscriptions.get(full_topic)
        if callbacks is None:
            return False

        if callback is None:
            del self._subscriptions[full_topic]
            return True

        if callback in callbacks:
            callbacks.remove(callback)
            if not callbacks:
                del self._subscriptions[full_topic]
            return True

        return False

    def receive_publish(self, timeout_ms=None):
        """
        Empfaengt genau eine MQTT-aehnliche Publish-Nachricht.

        Returns:
            (topic, payload, sender_mac) oder (None, None, None)
        """
        data, sender = self._receive_dict(timeout_ms=timeout_ms)
        if not self._is_publish_message(data):
            return None, None, None

        return data["topic"], data.get("payload"), sender

    def poll_subscriptions(self, timeout_ms=0):
        """
        Empfaengt eine Nachricht und verteilt sie an passende Abos.

        Callback-Signatur:
            callback(topic, payload, sender_mac)

        Returns:
            (topic, payload, sender_mac) bei passender Publish-Nachricht,
            sonst (None, None, None)
        """
        topic, payload, sender = self.receive_publish(timeout_ms=timeout_ms)
        if topic is None:
            return None, None, None

        for topic_filter, callbacks in self._subscriptions.items():
            if self._topic_matches(topic_filter, topic):
                for callback in callbacks:
                    callback(topic, payload, sender)

        return topic, payload, sender

    def list_subscriptions(self):
        """Gibt alle aktuell abonnierten Topic-Filter zurueck."""
        return sorted(list(self._subscriptions.keys()))

    # ================================================================
    # Hilfsfunktionen
    # ================================================================

    def scan_peers(self):
        """
        Gibt bekannte Peers zurueck.

        ESP-NOW besitzt kein aktives Discovery wie Bluetooth.
        In der Praxis werden MAC-Adressen im Unterricht manuell verteilt.
        """
        return sorted(list(self._peers))

    # ================================================================
    # Interne Helfer
    # ================================================================

    def _ensure_peer(self, mac_str):
        if mac_str not in self._peers:
            self.add_peer(mac_str)

    def _receive_dict(self, timeout_ms=None):
        msg, sender = self.receive(timeout_ms=timeout_ms, decode=True)
        if msg is None:
            return None, None

        if isinstance(msg, dict):
            return msg, sender

        if not isinstance(msg, str):
            return None, sender

        try:
            data = json.loads(msg)
        except ValueError:
            return None, sender

        if isinstance(data, dict):
            return data, sender

        return None, sender

    def _build_topic(self, topic, subtopic=None):
        if not isinstance(topic, str):
            raise TypeError("topic muss ein String sein")

        teile = [topic]
        if subtopic is not None:
            if not isinstance(subtopic, str):
                raise TypeError("subtopic muss ein String sein")
            teile.append(subtopic)

        full_topic = "/".join(teile)
        full_topic = full_topic.strip().strip("/")
        if not full_topic:
            raise ValueError("topic darf nicht leer sein")

        return full_topic

    def _is_publish_message(self, data):
        if not isinstance(data, dict):
            return False
        if data.get("_proto") != "nitbw-mqtt-lite":
            return False
        topic = data.get("topic")
        if not isinstance(topic, str) or not topic:
            return False
        return True

    def _topic_matches(self, topic_filter, topic):
        filter_levels = topic_filter.split("/")
        topic_levels = topic.split("/")

        i = 0
        while i < len(filter_levels):
            f_level = filter_levels[i]

            if f_level == "#":
                return i == len(filter_levels) - 1

            if i >= len(topic_levels):
                return False

            t_level = topic_levels[i]
            if f_level != "+" and f_level != t_level:
                return False

            i += 1

        return i == len(topic_levels)

    def _to_bytes(self, data):
        if isinstance(data, bytes):
            return data
        if isinstance(data, bytearray):
            return bytes(data)
        if isinstance(data, str):
            return data.encode("utf-8")
        if isinstance(data, (dict, list)):
            return json.dumps(data).encode("utf-8")
        if isinstance(data, (int, float, bool)):
            return str(data).encode("utf-8")
        raise TypeError("Datentyp nicht unterstuetzt: {}".format(type(data)))

    def _normalize_mac_str(self, mac):
        if not isinstance(mac, str):
            raise TypeError("MAC-Adresse muss ein String sein")

        mac = mac.strip().upper().replace("-", ":")

        teile = mac.split(":")
        if len(teile) != 6:
            raise ValueError("Ungueltige MAC-Adresse: {}".format(mac))

        for teil in teile:
            if len(teil) != 2:
                raise ValueError("Ungueltige MAC-Adresse: {}".format(mac))
            try:
                int(teil, 16)
            except ValueError:
                raise ValueError("Ungueltige MAC-Adresse: {}".format(mac))

        return mac

    def _mac_str_to_bytes(self, mac):
        mac = self._normalize_mac_str(mac)
        return bytes(int(teil, 16) for teil in mac.split(":"))

    def _mac_bytes_to_str(self, mac_bytes):
        return ":".join("{:02X}".format(b) for b in mac_bytes)


__all__ = ["ESPNow"]
