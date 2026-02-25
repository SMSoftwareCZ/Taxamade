# Taxamade

**Taxamade** je Python skript určený pro snadné a spolehlivé parsování CSV souborů
získaných jako výstup od brokerů. Projekt automatizuje čištění dat, převody formátů
a přípravu výstupů pro další zpracování (např. účetnictví, reporting nebo daňové podklady).

---

## ✨ Funkce skriptu

- Načtení CSV souborů z výstupu brokera
- Ořezání nadbytečných řádků (např. hlaviček či metadat)
- ///Nahrazení oddělovačů (např. `;` → `,`)
- Normalizace formátu dat a čísel
- Export očištěného a strukturovaného datového souboru

---

## 🚀 Použití

1. Umístěte CSV soubor z brokera do pracovního adresáře.
2. pro FIO je defaultni nazev Obchody.csv
3. Nainstalujte použité knihovny

```bash
pip install pandas numpy xlsxwriter

4. Spusťte skript:

```bash
python taxamade.py