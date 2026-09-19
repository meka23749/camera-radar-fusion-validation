# Anforderungsspezifikation (Requirements Specification)

**Projekt:** Kamera-Radar-Fusion zur Hinderniserkennung – SiL-Validierung auf nuScenes
**Autor:** Steve Meka
**Version:** 0.1 (Entwurf)

---

## 1. Zweck und Kontext

Dieses Dokument spezifiziert die Anforderungen an ein Wahrnehmungssystem (Perception),
das aus Kamera- und Radardaten Hindernisse vor dem Ego-Fahrzeug erkennt, klassifiziert
und lokalisiert.

Die Validierung erfolgt als **Software-in-the-Loop (SiL)** auf aufgezeichneten,
annotierten Realdaten des öffentlichen Datensatzes **nuScenes**. Als Referenz
(Ground Truth) dienen die manuellen Annotationen des Datensatzes.

**Systemgrenze:** Das System umfasst ausschließlich die *Wahrnehmung*
(Erkennung, Klassifikation, Lokalisierung von Hindernissen). Die *Entscheidung*
über Fahrmanöver (z. B. Bremsen, Lenken) ist **nicht** Teil dieses Systems.

---

## 2. Definitionen

| Begriff | Bedeutung |
|---|---|
| Ego-Fahrzeug | Das Fahrzeug, auf dem die Sensoren montiert sind |
| Ground Truth | Manuell annotierte, als wahr angenommene Objektliste (nuScenes) |
| Recall | Anteil der real vorhandenen Objekte, die das System erkennt |
| Precision | Anteil der Systemmeldungen, die tatsächlich korrekt sind |
| Latenz | Zeit zwischen Eingang der Sensordaten und Ausgabe der Objektliste |
| SiL | Software-in-the-Loop: Test der Software gegen aufgezeichnete Daten |

---

## 3. Funktionale Anforderungen

| ID | Anforderung | Priorität |
|---|---|---|
| REQ-01 | Das System muss Hindernisse vor dem Ego-Fahrzeug aus Kamera- und Radardaten erkennen. | Muss |
| REQ-02 | Für jedes erkannte Hindernis muss das System dessen Position ausgeben (mindestens die longitudinale Distanz zum Ego-Fahrzeug). | Muss |
| REQ-06 | Für jedes erkannte Hindernis muss das System dessen Klasse ausgeben (z. B. Fahrzeug, Fußgänger, Zweirad). | Muss |
| REQ-07 | Wird ein Hindernis in der Fahrspur des Ego-Fahrzeugs in weniger als [X] m erkannt, muss das System ein Warnsignal setzen. | Optional |

---

## 4. Leistungsanforderungen (Performance)

| ID | Anforderung | Zielwert | Priorität |
|---|---|---|---|
| REQ-03 | Reichweite Kamera: Fahrzeuge müssen bis mindestens 80 m erkannt werden. | ≥ 80 m | Muss |
| REQ-04 | Reichweite Radar: Objekte müssen bis mindestens 180 m erkannt werden. | ≥ 180 m | Muss |
| REQ-05 | Reichweite Gesamtsystem: Über den von mindestens einem Sensor abgedeckten Bereich muss eine Hinderniserkennung erfolgen. | bis 180 m | Muss |
| REQ-08 | Erkennungsrate (Recall) für Fahrzeuge in weniger als 30 m Entfernung. | ≥ 0,90 | Muss |
| REQ-09 | Fehldetektionsrate begrenzen (Precision). Priorität liegt auf hohem Recall (Sicherheit), Fehldetektionen müssen jedoch begrenzt bleiben (Vermeidung von Fehlalarmen). | ≥ 0,80 | Muss |
| REQ-10 | Latenz pro Verarbeitungszyklus (Frame): Eingang Sensordaten bis Ausgabe der Objektliste. | ≤ 100 ms | Muss |

> **Hinweis zu REQ-10:** Der Zielwert von 100 ms entspricht der Echtzeitanforderung
> einer typischen ADAS-Kamera (10–30 fps). Auf der Entwicklungsumgebung (CPU ohne
> dedizierte GPU) wird dieser Wert voraussichtlich nicht erreicht; die real gemessene
> Latenz wird dokumentiert und der Zielwert auf eine geeignete Zielhardware
> (z. B. GPU/NPU, Embedded-Plattform) bezogen.

---

## 5. Schnittstellenanforderungen

| ID | Anforderung |
|---|---|
| REQ-11 | Das System muss Kamerabilder und Radardaten aus dem nuScenes-Datensatz einlesen. |
| REQ-12 | Kamera- und Radardaten müssen zeitlich synchronisiert verarbeitet werden (gleicher Zeitstempel/Frame). |
| REQ-13 | Die Ausgabe muss eine strukturierte Hindernisliste sein (Klasse, Position, ggf. Geschwindigkeit) in maschinenlesbarem Format. |

---

## 6. Qualitäts- und Prozessanforderungen

| ID | Anforderung |
|---|---|
| REQ-14 | Jede Muss-Anforderung muss durch mindestens einen automatisierten Test überprüfbar sein (Rückverfolgbarkeit Anforderung ↔ Test). |
| REQ-15 | Die Tests müssen automatisiert in einer CI/CD-Pipeline ausgeführt werden. |
| REQ-16 | Testergebnisse (Recall, Precision, Latenz) müssen reproduzierbar dokumentiert werden. |

---

## 7. Offene Punkte / Annahmen

- Konkreter Wert für [X] in REQ-07 (Warndistanz) noch festzulegen.
- Reichweiten- und Recall-Zielwerte können nach ersten Messungen auf nuScenes
  angepasst werden (Anforderungen sind iterativ; Änderungen werden versioniert).
- Radardaten von nuScenes liegen als vorverarbeitete Punktlisten vor
  (kein rohes Radarsignal).
