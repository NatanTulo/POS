# Specyfikacja Techniczna i Plan Realizacji Projektu

**Dotyczy:** System Monitorowania parametrów pojazdu
**Zespół projektowy:** Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich

---

## 1. Repozytorium i Kontrola Wersji

Do zarządzania kodem źródłowym oraz śledzenia błędów (Issue Tracker) wybrana została platforma **GitHub**. 

* **Maintainer (Osoba odpowiedzialna za porządek):** Natan Tułodziecki
* **Strategia branchowania:** GitHub Flow (główna gałąź `main`, funkcjonalności tworzone na odrębnych gałęziach `feature/*`, poprawki na `bugfix/*`).
* **Środowisko IDE:** Visual Studio Code / PyCharm / WebStorm (w zależności od preferencji członków zespołu, konfiguracje środowiskowe np. `.vscode` dodane do `.gitignore`).

### 1.1 Struktura Repozytorium
Repozytorium zostanie podzielone tak, aby zachować wymaganą separację modułów (NFR-08):

    /vehicle-monitoring-system
    ├── /backend                 # Logika API, akwizycja danych, obsługa OBD
    │   ├── /api                 # Endpointy (FR-12)
    │   ├── /obd                 # Moduł komunikacji z adapterem ELM327 (FR-02)
    │   ├── /sensors             # Moduł czujników dodatkowych (FR-03)
    │   └── /database            # Modele danych i skrypty migracyjne
    ├── /frontend                # Kod interfejsu graficznego (React/Vue)
    │   ├── /src/components      # Komponenty UI (wykresy, tabele)
    │   └── /src/views           # Główne widoki (Dashboard, Historia, Alerty)
    ├── /docs                    # Dokumentacja projektu
    │   ├── /diagrams            # Diagramy UML (komponentów, klas, aktywności itp.)
    │   └── specyfikacja.md      # Główna specyfikacja
    ├── /assets                  # Grafiki UI, ikony, logotypy
    ├── /tests                   # Testy jednostkowe i integracyjne
    ├── .gitignore               # Wykluczenia plików
    ├── docker-compose.yml       # Konfiguracja wdrożeniowa
    └── README.md                # Opis projektu i instrukcja uruchomienia

## 2. Analiza Bibliotek i Narzędzi

System musi obsługiwać integrację z OBD, szybki zapis do bazy danych oraz działanie na systemach Windows i Linux (NFR-10).

### 2.1 Backend (Język: Python)
* **Framework API:** `FastAPI` – szybki, nowoczesny framework, idealny do asynchronicznej obsługi strumieniowania danych w czasie rzeczywistym i udostępniania endpointów dla GUI.
* **Biblioteka OBD:** `python-obd` – gotowe narzędzie do komunikacji ze standardowymi adapterami (np. ELM327) przez porty szeregowe / Bluetooth, realizujące założenia akwizycji danych.
* **Baza danych:** `SQLite` (dla uproszczenia wariantu lokalnego) lub `PostgreSQL` + `TimescaleDB` (optymalizacja dla zapisów szeregów czasowych/timestampów zgodnie z FR-06 i NFR-11).

### 2.2 Frontend (Język: JavaScript/TypeScript)
* **Framework UI:** `React.js` – popularna biblioteka umożliwiająca dynamiczne renderowanie i odświeżanie bez przeładowywania (FR-07).
* **Wizualizacja danych:** `Chart.js` lub `Recharts` – biblioteki do rysowania wykresów w czasie rzeczywistym dla parametrów silnika.

## 3. Modele UML

Zgodnie z wymaganiami, architektura systemu została zamodelowana z wykorzystaniem języka UML:

1. **Diagram komponentów:** Obrazuje podział systemu na moduł odczytu OBD, bazę danych, moduł API i GUI.
2. **Diagram klas:** Przedstawia struktury danych, w tym model `SensorReading` dla odczytów i kodów błędów DTC.
3. **Diagram aktywności:** Reprezentuje logikę walidacji i normalizacji danych z czujników (FR-04, FR-05) oraz generowania alertów.
4. **Diagram sekwencji:** Ilustruje przebieg komunikacji od inicjalizacji sesji, przez odczyt, po wyświetlenie alertu.
5. **Diagram wdrożenia:** Pokazuje rozlokowanie artefaktów na komputerze lokalnym / serwerze oraz połączenie z pojazdem.

*Pliki SVG z diagramami znajdują się w folderze `docs/diagrams/`.*

## 4. Harmonogram i Podział Prac (Gantt/Sprints)

Projekt został podzielony na 5 dwutygodniowych sprintów.

### 4.1 Podział ról w zespole
* **Natan Tułodziecki:** Projekt architektury, konfiguracja repozytorium (Maintainer), moduł API i bazy danych (Backend).
* **Maksymilian Szmigiel:** Tworzenie interfejsu graficznego użytkownika (GUI), wizualizacja danych na wykresach na żywo (Frontend).
* **Paweł Reich:** Integracja sprzętowa (adapter OBD i dodatkowe czujniki), mechanizmy normalizacji danych oraz testy wydajnościowe (Backend/Sprzęt).

### 4.2 Harmonogram (Sprinty)

* **Sprint 1 (Tydzień 1-2): Setup i Architektura**
  * Konfiguracja repozytorium GitHub, środowisk IDE.
  * Opracowanie ostatecznych schematów UML.
  * Postawienie szkieletów aplikacji backendowej i frontendowej (Hello World).
* **Sprint 2 (Tydzień 3-4): Akwizycja Danych**
  * [Paweł] Nawiązanie stabilnego połączenia z adapterem ELM327 (FR-01).
  * [Paweł] Odczyt i normalizacja RPM, MAP/MAF, temperatury (FR-02, FR-04).
  * [Natan] Zapis surowych danych i agregatów do bazy (FR-06).
* **Sprint 3 (Tydzień 5-6): Widoki Live i API**
  * [Natan] Opracowanie endpointów API m.in. dla `GET /sessions/{id}/readings` (FR-12).
  * [Maksymilian] Podłączenie GUI do API, renderowanie danych na żywo bez przeładowywania (FR-07).
* **Sprint 4 (Tydzień 7-8): Alerty, Historia i DTC**
  * [Maksymilian] Implementacja interfejsu do analizy historii i porównywania sesji (FR-09).
  * [Natan] Logika reguł progowych, generowanie alertów i wylistowanie kodów DTC (FR-08, FR-10).
* **Sprint 5 (Tydzień 9-10): Szlifowanie i Testy**
  * Implementacja eksportu danych do CSV/JSON (FR-11).
  * Audyt NFR (wymagań niefunkcjonalnych), optymalizacja opóźnień poniżej 2 s (NFR-01).
  * Zabezpieczenie systemu i przygotowanie finalnej dokumentacji (NFR-05, FR-13).
