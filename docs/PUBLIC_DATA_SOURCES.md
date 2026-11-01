# Public Archaeological Data Sources: Haryana Pilot (Hisar, Fatehabad, Sirsa)

This document provides complete documentation of the open-access and published ground-truth archaeological records incorporated into `haryana-mound-apm`.

Researchers can reproduce and run the entire computational APM benchmark immediately using these open-source records without waiting for external Data Sharing Agreements (DSAs).

---

## 1. Statutory Monument Registries

### A. Archaeological Survey of India (ASI) Centrally Protected Monuments
The following sites are statutory monuments protected under the Ancient Monuments and Archaeological Sites and Remains (AMASR) Act 1958:
- **Rakhigarhi (Mounds 1–7), Hisar District (Narnaund Tehsil):** One of the largest urban Harappan metropolitan centers (~100–350 ha). Prominent mounds rising up to ~17 m above local alluvium. Extensive excavations by ASI (Amarendra Nath, 1997–2000) and Deccan College (Vasant Shinde, 2013–2016). *Evaluated in the held-out protected/excavated stratum.*
- **Banawali Mound, Fatehabad District:** Fortified Harappan citadel and lower town with bipartite division on the dry bed of the Saraswati/Ghaggar. Prominent relief ~10.5 m. Excavated by R.S. Bisht (1974–1977, 1983–1987). *Evaluated in the held-out protected/excavated stratum.*
- **Ther Mound (Sirsa Stupa / Ancient Sarsuti), Sirsa District:** Massive composite multi-period settlement mound rising ~13 m over Sirsa city. Harappan, Painted Grey Ware (PGW), Northern Black Polished Ware (NBPW), Kushan, and Early Medieval phases with Buddhist stupa remains. Excavations by Cunningham (1882) and ASI surveys. *Evaluated in the held-out protected/excavated stratum.*
- **Hansi Fort (Asigarh), Hisar District:** Multi-period fortification and residential mound rising ~16 m. Contains early historic, Rajput, and Sultanate/Mughal occupational strata. Excavated by ASI (2004–2005).

### B. Haryana State Directorate of Archaeology and Museums Protected Sites
- **Agroha Mound, Hisar District:** Type-site of the ancient *Agreya Janapada* mint and Buddhist stupa complex. Prominent mound rising ~15 m. Excavated by H.L. Srivastava (1938–1939) and State Department of Archaeology (1978–1981).
- **Kunal Early Harappan Mound, Fatehabad District (Ratia Tehsil):** Pre-Harappan (Hakra Ware) and Early Harappan settlement with ceremonial silver tiaras and micro-steatite bead workshops. Relief ~3.5 m. Excavated by J.S. Khatri and M. Acharya (1995–1999) and Acharya et al. (2017).
- **Bhirrana Mound, Fatehabad District:** Continuously stratified Hakra Ware to Late Harappan settlement on the Saraswati paleobank. Relief ~5.2 m. Excavated by L.S. Rao et al. (2003–2006).

---

## 2. Published Fieldwork Monographs & Regional Gazetteers

Unexcavated rural mounds and low-relief scatters were harvested from verified academic fieldwork publications:

1. **Suraj Bhan (1975):** *Excavation at Mitathal (1968) and other Explorations in the Sutlej-Yamuna Divide*. Kurukshetra University.
   - Ground-confirmed sites: **Siswal** (Type site of Siswal Ware, ~2.5 m mound), **Barwala Mound** (~8 m), **Salimpur** (~0.7 m low-relief), **Sikanderpur** (~2.8 m), **Ellenabad** (~2.1 m).
2. **Singh, R.N., Petrie, C.A. et al. (2018):** *Survey and excavations at Lohari Ragho, Hisar District, Haryana*. Puratattva 48: 104–119.
   - Ground-confirmed sites: **Lohari Ragho I** (~2.2 m mound) and **Lohari Ragho II** (~0.8 m low-relief mound).
3. **Petrie, C.A., Singh, R.N. et al. (2017):** *Walking the interfluves: investigating the palaeogeography of the Ghaggar-Hakra and Indus Civilisation settlement distributions in north-west India*. Quaternary International 437: 103–118.
   - Ground-confirmed sites: **Masudpur I** (~1.4 m mound), **Masudpur VII** (~0.6 m low-relief), **Kajal Heri** (~1.8 m).
4. **Joshi, J.P., Madhu Bala, and Jammwal, K.G. (1984):** *Exploration in Gujarat, Haryana and Punjab*. Puratattva.
   - Ground-confirmed sites: **Bhatu Kalan** (~0.9 m low-relief mound), **Dhangar** (~0.85 m low-relief mound), **Jamal** (~0.95 m low-relief mound).
5. **Possehl, G.L. (1999):** *Indus Age: The Beginnings*. Oxford & IBH Publishing.
   - Systematic inventory of regional Harappan sites in NW India.

---

## 3. Historical Survey of India (SOI) Map Mounds (Weak Labels)

Historical 1-inch toposheets surveyed between 1905 and 1935 depict distinct geomorphic symbols for elevated topography:
- **Hachured relief symbols** (`toposheet_symbol`)
- **Form-line contours**
- **Spot heights**

Following Berganzo-Besga et al. (2023) and Green et al. (2019), these map features represent a mixture of extant mounds, ploughed-out mounds, natural sand dunes (*tibba*), and canal spoil banks. Under our Phase 2 methodology, unverified map mounds are **strictly segregated** from training positives and background, and evaluated as an independent weak-label test stratum (`results/weak_label_soi_mounds.csv`).

---

## 4. Usage Instructions

To export the canonical public site inventory to CSV:
```bash
python -c "from src.public_data_curator import export_public_sites_to_csv; export_public_sites_to_csv()"
```

To regenerate the processed feature tables and execute the entire benchmark:
```bash
python -c "from src.feature_generator import build_and_save_benchmark_datasets; build_and_save_benchmark_datasets()"
python -m scripts.run_benchmark --data-dir data/processed --spatial-unit both
python -m scripts.generate_plots
```
