# Instrukcja kompilacji PDF

## 1. Wymagania
- Zainstalowany **Node.js** (z `npm` i `npx`).
- Dostęp do internetu przy pierwszym uruchomieniu `npx` (pobranie paczek).
- Pliki wejściowe:
  - `specyfikacja_funkcjonalna.md`
  - `pdf-style.css`
  - `diagrams\*.mmd`


## 2. Generowanie diagramów Mermaid do SVG
```powershell
npx -y @mermaid-js/mermaid-cli -i "diagrams\diagram_komponentow.mmd" -o "diagrams\diagram_komponentow.svg"
npx -y @mermaid-js/mermaid-cli -i "diagrams\diagram_klas.mmd" -o "diagrams\diagram_klas.svg"
npx -y @mermaid-js/mermaid-cli -i "diagrams\diagram_aktywnosci.mmd" -o "diagrams\diagram_aktywnosci.svg"
npx -y @mermaid-js/mermaid-cli -i "diagrams\diagram_sekwencji.mmd" -o "diagrams\diagram_sekwencji.svg"
npx -y @mermaid-js/mermaid-cli -i "diagrams\diagram_wdrozenia.mmd" -o "diagrams\diagram_wdrozenia.svg"
```

## 3. Kompilacja markdown -> PDF (ze stylem)
```powershell
npx -y md-to-pdf "specyfikacja_funkcjonalna.md" --stylesheet "pdf-style.css"
```

Po tej komendzie powstanie plik:
- `specyfikacja_funkcjonalna.pdf`