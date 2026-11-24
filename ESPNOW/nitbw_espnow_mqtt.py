"""
NIT Bibliothek: ESPNOW MQTT-Helfer fuer Mini-Broker
Fuer ESP32 mit MicroPython

Version:    2.1.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-05

Ergaenzt nitbw_espnow.py um einfache Broker/Client-Helfer
fuer das Protokoll "nitbw-mqtt-lite-broker".

Robustheit (ab 2.1.0):
- Fremde oder kaputte Funknachrichten (kein JSON, kein Dictionary,
  anderes Protokoll) werden ignoriert, Broker und Clients laufen weiter.
- Clients merken sich ihre Abos und koennen sie erneuern
  (erneuere_abos(), automatisch mit abo_erneuern_ms).
- Der Broker meldet seinen Start per Broadcast ("broker_start"),
  Clients erneuern daraufhin automatisch ihre Abos.
"""

import json
import time


class ESPNowMQTT:
    """Hilfsfunktionen fuer Broker- und Client-Beispiele."""

    PROTO = "nitbw-mqtt-lite-broker"

    # Nachrichtentypen, die nur vom Broker an Clients gehen.
    # Ein Broker beantwortet diese nie (verhindert Endlos-Ping-Pong,
    # wenn mehrere Broker im selben Raum laufen).
    _CLIENT_TYPEN = ("ack", "connack", "deliver", "broker_start")

    def __init__(self, esp, broker_mac=None, require_connect=False, abo_erneuern_ms=None):
        """
        Args:
            esp: Initialisiertes ESPNow-Objekt
            broker_mac: MAC des Brokers (Client-Betrieb). Bei None arbeitet
                das Objekt als Broker und meldet seinen Start per Broadcast.
            require_connect: Broker akzeptiert subscribe/publish/unsubscribe
                erst nach erfolgreichem connect.
            abo_erneuern_ms: Nur Client: Wenn gesetzt (z. B. 60000), erneuert
                receive() die Abos automatisch nach dieser Zeit.
                None = keine automatische Erneuerung.
        """
        self.esp = esp
        self.broker_mac = broker_mac
        self.require_connect = require_connect
        self.abo_erneuern_ms = abo_erneuern_ms

        # Broker-Daten
        self._subscriptions = {}
        self._clients_by_mac = {}
        self._mac_by_client_id = {}

        # Client-Daten
        self._abos = []
        self._client_id = None
        self._letzte_erneuerung_ms = time.ticks_ms()

        if broker_mac is None:
            self.broker_start()

    # ================================================================
    # Client-Helfer
    # ================================================================

    def subscribe(self, topic_filter):
        """
        Sendet ein Subscribe an den Broker und merkt sich das Abo.

        Returns:
            True = Broker hat Empfang bestaetigt, False = keine Bestaetigung.
            Das Abo wird in beiden Faellen gemerkt und spaeter erneuert.
        """
        self._require_broker_mac()
        self._require_topic(topic_filter)

        if topic_filter not in self._abos:
            self._abos.append(topic_filter)

        return self._sende_an_broker({
            "_proto": self.PROTO,
            "type": "subscribe",
            "topic": topic_filter,
        })

    def unsubscribe(self, topic_filter):
        """Sendet ein Unsubscribe an den Broker und vergisst das Abo."""
        self._require_broker_mac()
        self._require_topic(topic_filter)

        if topic_filter in self._abos:
            self._abos.remove(topic_filter)

        return self._sende_an_broker({
            "_proto": self.PROTO,
            "type": "unsubscribe",
            "topic": topic_filter,
        })

    def publish(self, topic, payload):
        """
        Sendet ein Publish an den Broker.

        Returns:
            True = Broker hat Empfang bestaetigt, False = keine Bestaetigung.
        """
        self._require_broker_mac()
        self._require_topic(topic)

        return self._sende_an_broker({
            "_proto": self.PROTO,
            "type": "publish",
            "topic": topic,
            "payload": payload,
        })

    def erneuere_abos(self):
        """
        Sendet alle gemerkten Abos erneut an den Broker.

        Wurde vorher connect_id() benutzt, wird zuerst die Anmeldung
        wiederholt (noetig, wenn der Broker require_connect=True nutzt).
        Doppelte Abos sind unschaedlich: Der Broker speichert je Filter
        eine Menge von Clients, es entstehen keine doppelten Nachrichten.

        Returns:
            Anzahl der erneuerten Abos.
        """
        self._require_broker_mac()
        self._letzte_erneuerung_ms = time.ticks_ms()

        # "erneuerung": True -> Broker antwortet nicht mit ack/connack,
        # damit regelmaessige Erneuerungen das Programm nicht stoeren.
        if self._client_id is not None:
            self._sende_an_broker({
                "_proto": self.PROTO,
                "type": "connect",
                "client_id": self._client_id,
                "erneuerung": True,
            })

        for topic_filter in self._abos:
            self._sende_an_broker({
                "_proto": self.PROTO,
                "type": "subscribe",
                "topic": topic_filter,
                "erneuerung": True,
            })

        return len(self._abos)

    def resubscribe(self):
        """Englischer Alias fuer erneuere_abos()."""
        return self.erneuere_abos()

    def list_abos(self):
        """Gibt die gemerkten Abos dieses Clients zurueck."""
        return list(self._abos)

    def connect_id(self, client_id, timeout_ms=800, max_nachrichten=4):
        """
        Meldet einen Client-Namen beim Broker an und wartet auf connack.

        Returns:
            (ok, reason, client_id)
            ok: True bei erfolgreicher Anmeldung
            reason: z. B. "ok", "id_in_use", "invalid_id", "kein connack"
            client_id: vom Broker bestaetigte ID (oder None)
        """
        self._require_broker_mac()
        self._require_client_id(client_id)

        # Merken, damit erneuere_abos() die Anmeldung wiederholen kann.
        self._client_id = client_id

        self._sende_an_broker({
            "_proto": self.PROTO,
            "type": "connect",
            "client_id": client_id,
        })

        geprueft = 0
        while geprueft < max_nachrichten:
            msg_type, data, _sender = self.receive(timeout_ms=timeout_ms)
            if msg_type is None:
                break

            if msg_type == "connack":
                ok = bool(data.get("ok"))
                reason = data.get("reason")
                bestaetigte_id = data.get("client_id")

                if reason is None:
                    reason = "ok" if ok else "abgelehnt"

                return ok, reason, bestaetigte_id

            geprueft += 1

        return False, "kein connack", None

    def receive(self, timeout_ms=80, nur_nicht_none=False, wartezeit_ms=None):
        """
        Empfaengt genau eine Nachricht.

        Args:
            timeout_ms: Wartezeit pro Empfangsversuch in Millisekunden.
            nur_nicht_none: Wenn True, wird intern weiter gewartet,
                bis eine Nachricht empfangen wurde.
            wartezeit_ms: Maximale Gesamtwartezeit in Millisekunden, wenn
                `nur_nicht_none=True`. `None` bedeutet unbegrenzt warten.

        Returns:
            (msg_type, data, sender)
            msg_type ist z. B. "deliver", "ack", "connack", "broker_start",
            "other" oder None.
            "other": Nachricht in fremdem Protokoll oder kein gueltiges JSON;
            data ist dann das Dictionary bzw. der Rohtext.
            "broker_start": Der eigene Broker wurde neu gestartet; die Abos
            wurden bereits automatisch erneuert.
        """
        start_ms = None
        if nur_nicht_none and wartezeit_ms is not None:
            start_ms = time.ticks_ms()

        while True:
            self._pruefe_abo_erneuerung()

            data, roh, sender = self._empfange(timeout_ms)
            if sender is None:
                if nur_nicht_none:
                    if start_ms is not None:
                        vergangen_ms = time.ticks_diff(time.ticks_ms(), start_ms)
                        if vergangen_ms >= wartezeit_ms:
                            return None, None, None
                    continue
                return None, None, None

            if data is None:
                # Kein JSON oder kein Dictionary (z. B. esp.send(mac, "Hallo"))
                return "other", roh, sender

            if data.get("_proto") != self.PROTO:
                return "other", data, sender

            msg_type = data.get("type")

            if msg_type == "broker_start":
                if self._ist_eigener_broker(sender):
                    if self._abos or self._client_id is not None:
                        self.erneuere_abos()
                    return "broker_start", data, sender
                # broker_start eines anderen Brokers im Raum
                return "other", data, sender

            return msg_type, data, sender

    def zeige_nachrichten(
        self,
        max_nachrichten=8,
        timeout_ms=80,
        zeige_fremdprotokoll=False,
        nur_nicht_none=True,
        wartezeit_ms=None,
    ):
        """
        Zeigt empfangene Deliver/ACK-Nachrichten direkt auf der Konsole.

        Args:
            nur_nicht_none: Wenn True, wird standardmaessig mindestens auf die
                erste Nachricht gewartet.
            wartezeit_ms: Maximale Gesamtwartezeit in Millisekunden fuer die
                erste Nachricht. `None` bedeutet unbegrenzt warten.
                Weitere Empfangsversuche laufen mit normalem Timeout.
        """
        anzahl = 0
        while anzahl < max_nachrichten:
            warte_auf_erste = nur_nicht_none and anzahl == 0
            msg_type, data, sender = self.receive(
                timeout_ms=timeout_ms,
                nur_nicht_none=warte_auf_erste,
                wartezeit_ms=wartezeit_ms if warte_auf_erste else None,
            )
            if msg_type is None:
                break

            if msg_type == "deliver":
                topic = data.get("topic")
                payload = data.get("payload")
                original_sender = data.get("sender")
                print("Empfangen [{}] von {}: {}".format(topic, original_sender, payload))

            elif msg_type == "ack":
                print("Broker-ACK:", data.get("message"))

            elif msg_type == "broker_start":
                print("Broker wurde neu gestartet, Abos erneuert.")

            elif msg_type == "other":
                if zeige_fremdprotokoll:
                    print("Ignoriere Fremdprotokoll von {}: {}".format(sender, data))

            else:
                print("Unbekannter Typ vom Broker:", msg_type)

            anzahl += 1

    def zeige_json(
        self,
        max_nachrichten=1,
        timeout_ms=80,
        include_sender=False,
        include_broker_mac=False,
        zeige_fremdprotokoll=False,
        nur_nicht_none=True,
        wartezeit_ms=None,
    ):
        """
        Liefert empfangene Deliver-Nachrichten als reduzierte JSON-Objekte.

        Returns:
            Bei `max_nachrichten=1` ein Dictionary mit mindestens:
            - topic
            - payload

            Optional zusaetzlich:
            - sender (urspruenglicher Publisher)
            - broker_mac (MAC des Brokers als Sender der Deliver-Nachricht)

            Bei `max_nachrichten>1` eine Liste solcher Dictionaries.

            Mit `nur_nicht_none=True` wird standardmaessig mindestens auf die
            erste Nachricht gewartet. Mit `wartezeit_ms` kann diese Wartezeit
            begrenzt werden. Weitere Empfangsversuche laufen mit normalem
            `timeout_ms`.
        """
        nachrichten = []
        anzahl = 0

        while anzahl < max_nachrichten:
            warte_auf_erste = nur_nicht_none and anzahl == 0
            msg_type, data, sender = self.receive(
                timeout_ms=timeout_ms,
                nur_nicht_none=warte_auf_erste,
                wartezeit_ms=wartezeit_ms if warte_auf_erste else None,
            )
            if msg_type is None:
                break

            if msg_type == "deliver":
                eintrag = {
                    "topic": data.get("topic"),
                    "payload": data.get("payload"),
                }

                if include_sender:
                    eintrag["sender"] = data.get("sender")

                if include_broker_mac:
                    eintrag["broker_mac"] = sender

                nachrichten.append(eintrag)

            elif msg_type == "other":
                if zeige_fremdprotokoll:
                    print("Ignoriere Fremdprotokoll von {}: {}".format(sender, data))

            anzahl += 1

        if max_nachrichten == 1:
            if nachrichten:
                return nachrichten[0]
            return None

        return nachrichten

    # ================================================================
    # Broker-Helfer
    # ================================================================

    def broker_start(self):
        """
        Meldet per Broadcast, dass der Broker (neu) gestartet wurde.

        Clients mit dieser Broker-MAC erneuern daraufhin automatisch ihre
        Abos. Wird im Konstruktor aufgerufen, wenn keine broker_mac
        uebergeben wurde.

        Returns:
            True, wenn die Meldung gesendet werden konnte.
        """
        return self._sende_sicher(self.esp.BROADCAST_MAC, {
            "_proto": self.PROTO,
            "type": "broker_start",
        })

    def add_subscription(self, sender_mac, topic_filter):
        """
        Merkt ein Topic-Filter fuer einen Client.

        Returns:
            True, wenn das Abo neu ist, False, wenn es schon bestand.
        """
        self._require_topic(topic_filter)

        if topic_filter not in self._subscriptions:
            self._subscriptions[topic_filter] = set()

        # Je Filter eine Menge (set) von Client-MACs: Ein doppeltes
        # Subscribe (z. B. durch erneuere_abos()) traegt den Client nicht
        # zweimal ein und erzeugt daher keine doppelten Nachrichten.
        clients = self._subscriptions[topic_filter]
        if sender_mac in clients:
            return False

        clients.add(sender_mac)
        return True

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
        return self._sende_sicher(sender_mac, {
            "_proto": self.PROTO,
            "type": "ack",
            "message": text,
        })

    def send_connack(self, sender_mac, ok, reason="ok", client_id=None):
        """Sendet die Antwort auf connect mit Status und optionaler Client-ID."""
        paket = {
            "_proto": self.PROTO,
            "type": "connack",
            "ok": bool(ok),
            "reason": reason,
        }

        if client_id is not None:
            paket["client_id"] = client_id

        return self._sende_sicher(sender_mac, paket)

    def list_clients(self):
        """Liefert aktuelle Broker-Client-Zuordnung als Liste fuer Debug-Zwecke."""
        eintraege = []
        for mac, daten in self._clients_by_mac.items():
            eintraege.append({
                "mac": mac,
                "client_id": daten.get("client_id"),
            })
        return eintraege

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
            # Fehler bei einem Client stoppen nicht die Weiterleitung
            # an die anderen.
            self._sende_sicher(client_mac, {
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

        Fremde oder kaputte Nachrichten (kein JSON, kein Dictionary,
        anderes Protokoll) werden ignoriert; der Broker laeuft weiter.

        Returns:
            True, wenn eine gueltige Broker-Nachricht verarbeitet wurde,
            sonst False.
        """
        data, roh, sender = self._empfange(timeout_ms)
        if sender is None:
            return False

        if data is None:
            print("Ignoriere ungueltige Nachricht von {}: {}".format(sender, roh))
            return False

        if data.get("_proto") != self.PROTO:
            print("Ignoriere Fremdprotokoll von {}: {}".format(sender, data))
            return False

        try:
            return self._verarbeite_broker_nachricht(data, sender)
        except Exception as exc:
            # Letzte Sicherung: Ein Fehler bei einer einzelnen Nachricht
            # darf den Broker nicht beenden.
            print("Fehler bei Nachricht von {}: {}".format(sender, exc))
            return False

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

    def _verarbeite_broker_nachricht(self, data, sender):
        msg_type = data.get("type")
        erneuerung = bool(data.get("erneuerung"))

        if msg_type in self._CLIENT_TYPEN:
            # z. B. ack oder broker_start eines anderen Brokers im Raum:
            # nicht beantworten, sonst entsteht ein Endlos-Ping-Pong.
            return False

        if msg_type == "connect":
            client_id = data.get("client_id")

            if not self._is_client_id(client_id):
                self.send_connack(sender, False, reason="invalid_id")
                return True

            andere_mac = self._mac_by_client_id.get(client_id)
            if andere_mac and andere_mac != sender:
                self.send_connack(sender, False, reason="id_in_use")
                return True

            neu = not self._is_connected(sender) or \
                self._clients_by_mac[sender].get("client_id") != client_id
            self._register_client(sender, client_id)

            if neu:
                print("Connect von {} als {}".format(sender, client_id))
            if not erneuerung:
                self.send_connack(sender, True, reason="ok", client_id=client_id)
            return True

        if self.require_connect and not self._is_connected(sender):
            self.send_ack(sender, "connect erforderlich")
            return True

        if msg_type == "subscribe":
            topic_filter = data.get("topic")
            if self._is_topic(topic_filter):
                neu = self.add_subscription(sender, topic_filter)
                if neu:
                    print("Subscribe von {} auf {}".format(sender, topic_filter))
                if not erneuerung:
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

    def _empfange(self, timeout_ms):
        """
        Empfaengt eine Nachricht, ohne bei ungueltigem Inhalt abzustuerzen.

        Returns:
            (data, roh, sender)
            - keine Nachricht:           (None, None, None)
            - gueltiges JSON-Dictionary: (dict, roh, sender)
            - sonstiger Inhalt:          (None, roh, sender)
        """
        roh, sender = self.esp.receive(timeout_ms=timeout_ms, decode=True)
        if roh is None:
            return None, None, None

        try:
            data = json.loads(roh)
        except Exception:
            return None, roh, sender

        if not isinstance(data, dict):
            return None, roh, sender

        return data, roh, sender

    def _sende_an_broker(self, paket):
        return self.esp.send_json(self.broker_mac, paket)

    def _sende_sicher(self, mac, paket):
        """Sendet und faengt Fehler ab (Broker darf nicht abstuerzen)."""
        try:
            return self.esp.send_json(mac, paket)
        except Exception as exc:
            print("Senden an {} fehlgeschlagen: {}".format(mac, exc))
            return False

    def _pruefe_abo_erneuerung(self):
        if self.abo_erneuern_ms is None or not self.broker_mac:
            return
        if not self._abos and self._client_id is None:
            return

        vergangen_ms = time.ticks_diff(time.ticks_ms(), self._letzte_erneuerung_ms)
        if vergangen_ms >= self.abo_erneuern_ms:
            try:
                self.erneuere_abos()
            except Exception as exc:
                print("Abo-Erneuerung fehlgeschlagen:", exc)

    def _ist_eigener_broker(self, sender):
        if not self.broker_mac or sender is None:
            return False
        try:
            return self.esp._normalize_mac_str(self.broker_mac) == sender
        except Exception:
            return False

    def _require_broker_mac(self):
        if not self.broker_mac:
            raise ValueError("broker_mac ist nicht gesetzt")

    def _require_topic(self, topic):
        if not self._is_topic(topic):
            raise ValueError("topic/topic_filter muss ein nicht-leerer String sein")

    def _require_client_id(self, client_id):
        if not self._is_client_id(client_id):
            raise ValueError("client_id muss ein nicht-leerer String sein")

    @staticmethod
    def _is_topic(topic):
        return isinstance(topic, str) and bool(topic.strip())

    @staticmethod
    def _is_client_id(client_id):
        if not isinstance(client_id, str):
            return False

        text = client_id.strip()
        return bool(text) and len(text) <= 32

    def _register_client(self, sender_mac, client_id):
        alter_eintrag = self._clients_by_mac.get(sender_mac)
        if alter_eintrag:
            alte_id = alter_eintrag.get("client_id")
            if alte_id in self._mac_by_client_id:
                del self._mac_by_client_id[alte_id]

        self._clients_by_mac[sender_mac] = {"client_id": client_id}
        self._mac_by_client_id[client_id] = sender_mac

    def _is_connected(self, sender_mac):
        return sender_mac in self._clients_by_mac


__all__ = ["ESPNowMQTT"]
