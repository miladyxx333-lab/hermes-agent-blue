---
name: law_mx
description: Massive Generator of Mexican legal documents based on 900+ templates from derechoenmexico.mx.
version: 1.1.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [legal, mexico, derecho, contratos, demandas, automation, massive-database, constitution]
    category: legal
    requires_toolsets: [terminal, file]
---

# ⚖ Law MX: Massive Mexican Legal Document Generator

This skill is powered by a massive database of **899+ professional legal templates** scraped from `derechoenmexico.mx`.

## ◈ Capabilities

1. **Massive Library**: Access to nearly 900 templates including almost every possible legal scenario in Mexico (Sucesiones, Divorcios, Contratos Mercantiles, Amparos, etc.).
2. **Standardized Extraction**: Models are cleaned from web artifacts (ads, sidebars) to provide pure legal text.
3. **Drafting Power**: Hermes can now draft almost any legal document used in Mexican jurisdiction.
4. **Marco Constitucional Supremo**: Has access to the complete text of the Constitución Política de los Estados Unidos Mexicanos (CPEUM) in `data/CPEUM.txt` for legal fundamentation and interpretation.
5. **Índice de 300 Leyes Federales**: Has an index of 300 Federal Laws of Mexico (`data/justia_leyes_index.json`) and their corresponding table of contents in `data/leyes_federales/`, which helps the agent identify specific laws and follow links to check corresponding articles when drafting documents.


## 📋 Document Categories
- **Civil**: Arrendamiento, Compraventa, Usucapión, Sucesiones.
- **Familiar**: Alimentos, Divorcios, Custodia, Nulidad de Matrimonio.
- **Mercantil**: Sociedades Anónimas, Títulos de Crédito, Asambleas, Fusiones.
- **Laboral**: Renuncias, Despidos, Contratos Individuales, Liquidaciones.
- **Amparo**: Demandas de amparo directo e indirecto.

## How to Use

### List Document Types
```bash
python3 scripts/doc_generator.py list
```

### Search and Generate
Hermes will search the database for the most relevant template based on your request and will then help you fill it.

```bash
python3 scripts/doc_generator.py generate --template carta_poder --data '{"EL QUE SUSCRIBE": "Juan Perez", "EL APODERADO": "Maria Lopez"}' --output carta_poder_final.txt
```

## Data Source
- All 900+ templates are sourced and synchronized from **[derechoenmexico.mx](https://derechoenmexico.mx/)**.
- **Constitución Política de los Estados Unidos Mexicanos**: Downloaded from the official [diputados.gob.mx](https://www.diputados.gob.mx/LeyesBiblio/pdf/CPEUM.pdf) website and parsed into plain text (`data/CPEUM.txt`).
- **Leyes Federales**: Scraped from **[mexico.justia.com](https://mexico.justia.com/federales/leyes/)**, containing an index of 300+ federal laws and their tables of contents.

## ⚠ Warning
*   **Context**: Use the `list` command or ask Hermes to search the `templates.json` for the exact key (slug) of the document.
*   **Legal Validity**: Always review generated drafts with a licensed Mexican attorney.
