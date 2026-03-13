"""
Beispiel fuer NIT Bibliothek: COMPASS - Sensorfusion
Zeigt: Beschleunigungssensor (ADXL345) und neigungskompensiertes Heading
Hardware: GY-261 (QMC5883L + ADXL345) am I2C-Bus

Dieses Beispiel demonstriert:
  1. Lesezugriff auf den ADXL345 Beschleunigungssensor
  2. Berechnung von Pitch (Nickwinkel) und Roll (Rollwinkel)
  3. Lagebestimmung (waagerecht, geneigt, hochkant)
  4. Vergleich: einfaches Heading vs. neigungskompensiertes Heading
  5. Kombinierten Datenabruf mit read_all()
"""

import time
from machine import I2C, Pin
from nitbw_compass import Compass, Accelerometer


# -----------------------------------------------------------------------
# Initialisierung
# -----------------------------------------------------------------------

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Kompass mit ADXL345 initialisieren (use_accel=True ist Standard)
compass = Compass(i2c, addr=0x0D, use_accel=True)

# Lokale Deklination setzen (z.B. 3 Grad 45 Minuten fuer Mitteleuropa)
compass.set_declination(degrees=3, minutes=45)

# I2C-Adressen anzeigen (zur Diagnose)
print("Gefundene I2C-Geraete:", [hex(a) for a in i2c.scan()])
print()


# -----------------------------------------------------------------------
# Teil 1: Beschleunigungssensor pruefen
# -----------------------------------------------------------------------

print("=" * 40)
print("Teil 1: Beschleunigungssensor ADXL345")
print("=" * 40)

if compass.has_accelerometer():
    print("ADXL345 gefunden!")
    print(f"  Chip-ID: {hex(compass.accel.get_device_id())}")
else:
    print("ADXL345 NICHT gefunden - pruefe Verdrahtung und Adresse.")
    print("Hinweis: SDO-Pin LOW = Adresse 0x53, HIGH = Adresse 0x1D")

print()


# -----------------------------------------------------------------------
# Teil 2: ADXL345 kalibrieren (optional, Sensor muss waagerecht liegen)
# -----------------------------------------------------------------------

print("=" * 40)
print("Teil 2: Beschleunigungssensor kalibrieren")
print("=" * 40)
print("Sensor waagerecht auf den Tisch legen, dann Enter druecken...")
# input()   # Auskommentieren um auf Benutzereingabe zu warten

if compass.has_accelerometer():
    compass.accel.calibrate(samples=50)
print()


# -----------------------------------------------------------------------
# Teil 3: Rohdaten und physikalische Werte lesen
# -----------------------------------------------------------------------

print("=" * 40)
print("Teil 3: Beschleunigungswerte lesen")
print("=" * 40)

if compass.has_accelerometer():
    # Rohwerte (ADC-Einheiten)
    rx, ry, rz = compass.accel.read_raw()
    print(f"Rohwerte (ADC): X={rx}, Y={ry}, Z={rz}")

    # Beschleunigung in g
    ax, ay, az = compass.accel.read_accel()
    print(f"Beschleunigung (g): X={ax:.3f}, Y={ay:.3f}, Z={az:.3f}")

    # Beschleunigung in m/s²
    axm, aym, azm = compass.accel.read_accel_ms2()
    print(f"Beschleunigung (m/s²): X={axm:.2f}, Y={aym:.2f}, Z={azm:.2f}")
print()


# -----------------------------------------------------------------------
# Teil 4: Lagewinkel berechnen
# -----------------------------------------------------------------------

print("=" * 40)
print("Teil 4: Lagewinkel")
print("=" * 40)

if compass.has_accelerometer():
    pitch = compass.accel.read_pitch()
    roll  = compass.accel.read_roll()
    tilt  = compass.accel.read_tilt_angle()

    print(f"Pitch (Nickwinkel): {pitch:.1f} Grad")
    print(f"Roll  (Rollwinkel): {roll:.1f} Grad")
    print(f"Gesamtneigung:      {tilt:.1f} Grad")
    print(f"Lage:               {compass.accel.read_orientation_text()}")
    print(f"Waagerecht?         {compass.accel.is_level(threshold=5.0)}")
print()


# -----------------------------------------------------------------------
# Teil 5: Einfaches vs. neigungskompensiertes Heading
# -----------------------------------------------------------------------

print("=" * 40)
print("Teil 5: Heading-Vergleich (Sensor neigen!)")
print("=" * 40)
print("Sensor etwas neigen und Werte beobachten:")
print()

for i in range(10):
    heading_einfach = compass.read_heading()
    heading_tc      = compass.read_heading_tilt_compensated()

    richtung_einfach = compass.read_heading_direction()
    richtung_tc      = compass.read_heading_tilt_compensated_direction()

    abweichung = heading_tc - heading_einfach
    # Auf -180 bis +180 normalisieren
    if abweichung > 180:
        abweichung -= 360
    elif abweichung < -180:
        abweichung += 360

    print(f"Einfach: {heading_einfach:6.1f}° ({richtung_einfach:3})  "
          f"Kompensiert: {heading_tc:6.1f}° ({richtung_tc:3})  "
          f"Diff: {abweichung:+.1f}°")
    time.sleep(0.5)

print()


# -----------------------------------------------------------------------
# Teil 6: Kombinierter Datenabruf mit read_all()
# -----------------------------------------------------------------------

print("=" * 40)
print("Teil 6: Alle Sensordaten auf einmal")
print("=" * 40)

daten = compass.read_all()

print(f"Heading (einfach):       {daten['heading']:.1f}° ({daten['direction']})")
print(f"Magnetfeld:              X={daten['mx']:.2f} mG, Y={daten['my']:.2f} mG, Z={daten['mz']:.2f} mG")
print(f"Feldstaerke:             {daten['strength']:.2f} mG")

if "heading_tc" in daten:
    print(f"Heading (kompensiert):   {daten['heading_tc']:.1f}° ({daten['direction_tc']})")
    print(f"Beschleunigung (g):      X={daten['ax']:.3f}, Y={daten['ay']:.3f}, Z={daten['az']:.3f}")
    print(f"Pitch: {daten['pitch']:.1f}°   Roll: {daten['roll']:.1f}°   Neigung: {daten['tilt']:.1f}°")
    print(f"Waagerecht: {daten['is_level']}")
print()


# -----------------------------------------------------------------------
# Teil 7: Dauermessung
# -----------------------------------------------------------------------

print("=" * 40)
print("Teil 7: Dauermessung (Strg+C zum Beenden)")
print("=" * 40)
print(f"{'Einfach':>10} {'Kompen.':>10} {'Richtung':>8} {'Pitch':>7} {'Roll':>7} {'Neigung':>8}")
print("-" * 60)

try:
    while True:
        h_einfach = compass.read_heading()
        h_tc      = compass.read_heading_tilt_compensated()
        richtung  = compass.read_heading_tilt_compensated_direction()

        if compass.has_accelerometer():
            pitch, roll = compass.accel.read_pitch_roll()
            tilt        = compass.accel.read_tilt_angle()
        else:
            pitch = roll = tilt = 0.0

        print(f"{h_einfach:>9.1f}° {h_tc:>9.1f}° {richtung:>8}  "
              f"{pitch:>6.1f}° {roll:>6.1f}° {tilt:>7.1f}°")
        time.sleep(0.3)

except KeyboardInterrupt:
    print("\nMessung beendet.")
