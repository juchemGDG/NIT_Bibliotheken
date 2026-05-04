"""
NIT Bibliothek: ESPNOW MQTT-Helfer fuer Mini-Broker
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-05

Ergaenzt nitbw_espnow.py um einfache Broker/Client-Helfer
fuer das Protokoll "nitbw-mqtt-lite-broker".
"""


class ESPNowMQTT:
    """Hilfsfunktionen fuer Broker- und Client-Beispiele."""

    PROTO = "nitbw-mqtt-lite-broker"

    def __init__(self, esp, broker_mac=None):
        self.esp = esp
        self.broker_mac = broker_mac
        self._subscriptions = {}

    # ================================================================
    # Client-Helfer
    # ================================================================

    def subscribe(self, topic_filter):
        """Sendet ein Subscribe an den Broker."""
        self._require_broker_mac()
        self._require_topic(topic_filter)

        return self.esp.send_json(self.broker_mac, {
            "_proto": self.PROTO,
            "type": "subscribe",
            "topic": topic_filter,
        })

    def unsubscribe(self, topic_filter):
        """Sendet ein Unsubscribe an den Broker."""
        self._require_broker_mac()
        self._require_topic(topic_filter)

        return self.esp.send_json(self.broker_mac, {
            "_proto": self.PROTO,
            "type": "unsubscribe",
            "topic": topic_filter,
        })

    def publish(self, topic, payload):
        """Sendet ein Publish an den Broker."""
        self._require_broker_mac()
        self._require_topic(topic)

        return self.esp.send_json(self.broker_mac, {
            "_proto": self.PROTO,
            "type": "publish",
            "topic": topic,
            "payload": payload,
        })

    def receive(self, timeout_ms=80):
        """
        Empfaengt genau eine Nachricht.

        Returns:
            (msg_type, data, sender)
            msg_type ist z. B. "deliver", "ack", "other" oder None.
        """
        data, sender = self.esp.receive_json(timeout_ms=timeout_ms)
        if data is None:
            return None, None, None

        if data.get("_proto") != self.PROTO:
            return "other", data, sender

        return data.get("type"), data, sender

    def zeige_nachrichten(self, max_nachrichten=8, timeout_ms=80, zeige_fremdprotokoll=False):
        """Zeigt empfangene Deliver/ACK-Nachrichten direkt auf der Konsole."""
        anzahl = 0
        while anzahl < max_nachrichten:
            msg_type, data, sender = self.receive(timeout_ms=timeout_ms)
            if msg_type is None:
                break

            if msg_type == "deliver":
                topic = data.get("topic")
                payload = data.get("payload")
                original_sender = data.get("sender")
                print("Empfangen [{}] von {}: {}".format(topic, original_sender, payload))

            elif msg_type == "ack":
                print("Broker-ACK:", data.get("message"))

            elif msg_type == "other":
                if zeige_fremdprotokoll:
                    print("Ignoriere Fremdprotokoll von {}: {}".format(sender, data))

            else:
                print("Unbekannter Typ vom Broker:", msg_type)

            anzahl += 1

    # ================================================================
    # Broker-Helfer
    # ================================================================

    def add_subscription(self, sender_mac, topic_filter):
        """Merkt ein Topic-Filter fuer einen Client."""
        self._require_topic(topic_filter)

        if topic_filter not in self._subscriptions:
            self._subscriptions[topic_filter] = set()

        self._subscriptions[topic_filter].add(sender_mac)

    def remove_subscription(self, sender_mac, topic_filter):
        """Entfernt ein Topic-Filter fuer einen Client."""
        if topic_filter not in self._subscriptions:
            return

        clients = self._subscriptions[topic_filter]
        if sender_mac in clients:
            clients.remove(sender_mac)

        if not clients:
            del self._subscriptions[topic_filter]

    def send_ack(self, sender_mac, text):
        """Sendet eine kurze Bestaetigung an den Client."""
        self.esp.send_json(sender_mac, {
            "_proto": self.PROTO,
            "type": "ack",
            "message": text,
        })

    def forward_publish(self, sender_mac, topic, payload, exclude_sender=True):
        """Leitet ein Publish an alle passenden Subscriber weiter."""
        empfaenger = set()

        for topic_filter, clients in self._subscriptions.items():
            if self.topic_matches(topic_filter, topic):
                for client_mac in clients:
                    empfaenger.add(client_mac)

        if exclude_sender and sender_mac in empfaenger:
            empfaenger.remove(sender_mac)

        for client_mac in empfaenger:
            self.esp.send_json(client_mac, {
                "_proto": self.PROTO,
                "type": "deliver",
                "topic": topic,
                "payload": payload,
                "sender": sender_mac,
            })

        return len(empfaenger)

    def handle_broker_message(self, timeout_ms=400):
        """
        Verarbeitet genau eine eingehende Broker-Nachricht.

        Returns:
            True, wenn eine gueltige Broker-Nachricht verarbeitet wurde,
            sonst False.
        """
        data, sender = self.esp.receive_json(timeout_ms=timeout_ms)
        if data is None:
            return False

        if data.get("_proto") != self.PROTO:
            print("Ignoriere Fremdprotokoll von {}: {}".format(sender, data))
            return False

        msg_type = data.get("type")

        if msg_type == "subscribe":
            topic_filter = data.get("topic")
            if self._is_topic(topic_filter):
                self.add_subscription(sender, topic_filter)
                print("Subscribe von {} auf {}".format(sender, topic_filter))
                self.send_ack(sender, "subscribed: {}".format(topic_filter))
            else:
                self.send_ack(sender, "ungueltiges subscribe")
            return True

        if msg_type == "unsubscribe":
            topic_filter = data.get("topic")
            if self._is_topic(topic_filter):
                self.remove_subscription(sender, topic_filter)
                print("Unsubscribe von {} auf {}".format(sender, topic_filter))
                self.send_ack(sender, "unsubscribed: {}".format(topic_filter))
            else:
                self.send_ack(sender, "ungueltiges unsubscribe")
            return True

        if msg_type == "publish":
            topic = data.get("topic")
            payload = data.get("payload")
            if self._is_topic(topic):
                print("Publish von {} auf {}: {}".format(sender, topic, payload))
                anzahl = self.forward_publish(sender, topic, payload)
                if anzahl:
                    print("Weitergeleitet an {} Client(s) fuer Topic {}".format(anzahl, topic))
                else:
                    print("Keine Empfaenger fuer Topic:", topic)
            else:
                self.send_ack(sender, "ungueltiges publish")
            return True

        print("Unbekannter Nachrichtentyp von {}: {}".format(sender, msg_type))
        self.send_ack(sender, "unbekannter type")
        return True

    @staticmethod
    def topic_matches(topic_filter, topic):
        """Prueft Topic-Wildcards (+ und #) im MQTT-Stil."""
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

    # ================================================================
    # Interne Helfer
    # ================================================================

    def _require_broker_mac(self):
        if not self.broker_mac:
            raise ValueError("broker_mac ist nicht gesetzt")

    def _require_topic(self, topic):
        if not self._is_topic(topic):
            raise ValueError("topic/topic_filter muss ein nicht-leerer String sein")

    @staticmethod
    def _is_topic(topic):
        return isinstance(topic, str) and bool(topic.strip())


__all__ = ["ESPNowMQTT"]
