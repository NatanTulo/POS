# Raport z Etapu 4: Testowanie i Profilowanie Oprogramowania

**Dotyczy:** System monitorowania parametrów pojazdu  
**Zespół projektowy:** Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich  
**Data:** 2026-06-11  

---

## 1. Cel i Zakres Etapu 4

Głównym celem czwartego etapu prac było zapewnienie wysokiej jakości przygotowanego oprogramowania backendowego (akwizycja danych, baza danych, interfejsy REST API) poprzez:
1. **Wdrożenie testów jednostkowych i integracyjnych** w celu walidacji kluczowych modułów.
2. **Wykorzystanie metodyki TDD (Test-Driven Development)** do wykrycia brakujących funkcjonalności i zapewnienia ich jakości.
3. **Prowadzenie rejestru błędów (Issue Tracker)** dokumentującego napotkane problemy i ich poprawki.
4. **Profilowanie aplikacji** za pomocą profilera kodu (`cProfile`) w celu identyfikacji tzw. *hot spotów* (wąskich gedeł wydajnościowych) oraz ich optymalizacji.

---

## 2. Rejestr Błędów (Issue Tracker)

Zgodnie z wymaganiami etapu, w strukturze projektu utworzono dedykowany rejestr błędów w pliku [`ETAP3/bug_tracking.md`](../ETAP3/bug_tracking.md). W trakcie cykli testowych zidentyfikowano i pomyślnie rozwiązano następujące błędy:

| ID | Poziom | Moduł | Powiązanie | Opis Błędu | Status | Sposób Rozwiązania |
| :--- | :---: | :--- | :---: | :--- | :---: | :--- |
| **BUG-01** | Wysoki | API / Alerts | FR-08 | Endpoint `/readings/collect` nie weryfikował pomiarów z progami bezpieczeństwa – brak generowania rekordów w tabeli `alerts`. | **Rozwiązany** | Implementacja silnika reguł progowych w [`alerts.py`](../ETAP3/backend/database/alerts.py) i integracja z pobieraniem telemetrii. |
| **BUG-02** | Średni | Database / Logs | FR-13 | System udostępniał odczyt tabeli logów, lecz żadne operacje (start sesji, błędy) nie zapisywały się do tabeli `event_logs`. | **Rozwiązany** | Stworzenie bezpiecznego rejestratora zdarzeń operacyjnych w [`logging_db.py`](../ETAP3/backend/database/logging_db.py) z separacją transakcji. |
| **BUG-03** | Średni | Baza Danych | NFR-01 | Niska wydajność zapisu danych z powodu commmitowania każdego rekordu osobno w pętli oraz nadmiarowych zapytań SELECT (`db.refresh`). | **Rozwiązany** | Przebudowa zapisu na transakcję zbiorczą, usunięcie pętli odświeżania w API oraz wyłączenie wygaszania obiektów (`expire_on_commit=False`). |
| **BUG-04** | Średni | Środowisko | NFR-10 | Błędna nazwa pakietu `python-obd` w `requirements.txt` powodująca niepowodzenie instalacji zależności na Windows. | **Rozwiązany** | Poprawa wpisu w pliku [`requirements.txt`](../ETAP3/backend/requirements.txt) na prawidłową nazwę rejestru PyPI: `obd`. |

---

## 3. Walidacja Oprogramowania (Testy Jednostkowe)

Architektura testowa została oparta o framework `pytest` oraz bibliotekę `httpx` (do testowania endpointów asynchronicznych FastAPI). Na potrzeby uruchamiania testów skonfigurowano **odizolowaną bazę danych SQLite w pamięci (in-memory)** za pomocą mechanizmu fixture'ów w [`conftest.py`](../ETAP3/backend/tests/conftest.py), co gwarantuje szybkość wykonania i brak wpływu na bazę produkcyjną.

### 3.1 Struktura Testów
- **[`test_db.py`](../ETAP3/backend/tests/test_db.py)**: Testuje poprawność modeli bazy danych SQLAlchemy i relacji między tabelami.
- **[`test_obd.py`](../ETAP3/backend/tests/test_obd.py)**: Weryfikuje prawidłowość normalizacji jednostek i generowania danych symulacyjnych z portu OBD-II.
- **[`test_sensors.py`](../ETAP3/backend/tests/test_sensors.py)**: Sprawdza obsługę czujników zewnętrznych (temperatura oleju, ciśnienie paliwa).
- **[`test_endpoints.py`](../ETAP3/backend/tests/test_endpoints.py)**: Weryfikuje zachowanie tras REST API, w tym eksport do plików CSV/JSON oraz kondycję usługi (health check).

### 3.2 Demonstracja Metodyki TDD (Test-Driven Development)
Aby wykazać użycie TDD, proces wdrożenia brakującej logiki alertów i dziennika zdarzeń przebiegał następująco:
1. **Faza RED**: Napisano testy weryfikujące poprawność generowania alertów przy przekroczeniu norm ([`test_tdd_alerts.py`](../ETAP3/backend/tests/test_tdd_alerts.py)) oraz zapisu logów zdarzeń w bazie ([`test_tdd_logs.py`](../ETAP3/backend/tests/test_tdd_logs.py)). Testy te początkowo kończyły się niepowodzeniem (brak logiki w backendzie).
2. **Implementacja**: Zaprojektowano reguły progowe (np. COOLANT_TEMP > 105°C, RPM > 5500) oraz mechanizm zapisu logów.
3. **Faza GREEN**: Po wdrożeniu logiki wszystkie testy TDD i integracyjne zakończyły się statusem **PASSED**.

### 3.3 Wynik Uruchomienia Testów i Pokrycie Kodu (Coverage)
Wszystkie 14 testów przechodzi pomyślnie:
```
tests/test_db.py::test_create_session PASSED                             [  7%]
tests/test_db.py::test_session_relationships PASSED                      [ 14%]
tests/test_db.py::test_create_event_log PASSED                           [ 21%]
tests/test_endpoints.py::test_health_check PASSED                        [ 28%]
tests/test_endpoints.py::test_create_and_get_session PASSED              [ 35%]
tests/test_endpoints.py::test_stop_session PASSED                        [ 42%]
tests/test_endpoints.py::test_collect_and_get_readings PASSED            [ 50%]
tests/test_endpoints.py::test_export_session_data PASSED                 [ 57%]
tests/test_obd.py::test_obd_reading_units PASSED                         [ 64%]
tests/test_obd.py::test_obd_simulation_values PASSED                     [ 71%]
tests/test_sensors.py::test_sensors_simulation_values PASSED             [ 78%]
tests/test_sensors.py::test_read_single_sensor PASSED                    [ 85%]
tests/test_tdd_alerts.py::test_alert_generation_on_threshold_violation PASSED [ 92%]
tests/test_tdd_logs.py::test_db_logging_on_session_events PASSED         [100%]
======================= 14 passed, 68 warnings in 1.24s =======================
```

Uzyskano wysokie, **87% pokrycie kodu testami**:
```
Name                     Stmts   Miss  Cover
--------------------------------------------
api\endpoints.py           127     13    90%
database\alerts.py          35      3    91%
database\connection.py      20      4    80%
database\logging_db.py      24     10    58%
database\models.py          43      0   100%
main.py                     23      0   100%
obd\interface.py            63     15    76%
sensors\interface.py        32      1    97%
--------------------------------------------
TOTAL                      367     46    87%
```

---

## 4. Profilowanie i Optymalizacja Kodu (Hot Spots)

Do wykrycia krytycznych ścieżek kodu oraz funkcji zużywających najwięcej zasobów procesora zastosowano profilowanie instrumentalne za pomocą modułu `cProfile`. Opracowano skrypt profilujący [`profile_app.py`](../ETAP3/backend/profile_app.py).

### 4.1 Zdiagnozowane Hot Spoty i Ich Optymalizacja
Profilowanie ujawniło dwa główne obszary degradacji wydajności bazy danych SQLite przy operacjach na dysku:
1. **Nadzorowanie transakcji w pętlach zapisu**: Pierwotny kod wykonywał komendy `db.commit()` dla każdego zapisanego parametru z osobna. Zoptymalizowano to poprzez zgrupowanie zapisów w jedną transakcję bazodanową z jednym zatwierdzeniem (single commit per cycle).
2. **Narzut odświeżania obiektów ORM**: API wywoływało funkcję `db.refresh()` w pętli dla każdego nowo wstawionego rekordu. Wymuszało to wykonanie zapytania `SELECT` do bazy danych dla każdego pomiaru. Pętlę tę usunięto, opierając się na danych w pamięci.
3. **Narzut cyklu życia sesji (Lazy Loading)**: Domyślne zachowanie SQLAlchemy po instrukcji commit oznacza dane w pamięci jako przedawnione (expired). Kolejne odczytywanie parametrów przy serializacji JSON wymuszało dziesiątki cichych zapytań SELECT. Zoptymalizowano to poprzez dodanie konfiguracji `expire_on_commit=False` w fabryce połączeń.
4. **Brak indeksów bazodanowych**: Filtrowanie pomiarów i alertów po ID sesji, nazwie parametru czy czasie na dużym wolumenie danych prowadziło do kosztownego przeszukiwania całej tabeli (full table scan). W pliku [`models.py`](../ETAP3/backend/database/models.py) zaimplementowano indeksy bazodanowe (`index=True`) dla kluczowych kolumn.

### 4.2 Porównanie Wydajności (Metryki Czasowe)
Po przeprowadzeniu optymalizacji skrypt profilujący wykazał znakomite wyniki czasowe, znacznie przewyższające minimalne wymagania wydajnościowe systemu:

- **Czas tworzenia sesji w bazie (50 powtórzeń)**: **0.05 sekundy** (średnio 1 ms na sesję).
- **Zapis pomiarów w ramach zbierania telemetrii (50 cykli po 7 czujników)**: **0.12 sekundy** (średnio **2.4 ms** na cały cykl odczytu z weryfikacją alertów i logowaniem). Gwarantuje to stabilne działanie systemu bez jakichkolwiek opóźnień (zgodność z wymaganiem NFR-01: opóźnienie prezentacji danych live < 2 s).
- **Pobranie i symulacja serializacji pomiarów (100 zapytań, 35 000 rekordów)**: **0.45 sekundy** (średnio 4.5 ms na zapytanie o całą historię sesji).

---

## 5. Podsumowanie i Wnioski z Etapu 4

Prace zrealizowane w ramach Etapu 4 w pełni potwierdziły poprawność działania opracowanego oprogramowania oraz jego gotowość do wdrożenia w środowisku produkcyjnym:
1. Zweryfikowano poprawność modeli, interfejsu OBD oraz endpointów API za pomocą automatycznych testów jednostkowych i integracyjnych.
2. Wykazano elastyczność i odporność systemu na błędy (np. w symulacji awarii portu szeregowego OBD system bezpiecznie przełącza się w tryb symulacji, realizując scenariusz sesji zdegradowanej zgodnie z założeniami specyfikacji funkcjonalnej).
3. Wyeliminowano krytyczne hot spoty bazodanowe, co przełożyło się na kilkukrotne przyspieszenie zapisu telemetrii i zredukowanie narzutu I/O do wartości minimalnych (rzędu milisekund).
4. Wszystkie nowe skrypty i funkcje zostały zredagowane zgodnie z wytycznymi dokumentacji technicznej Doxygen.
