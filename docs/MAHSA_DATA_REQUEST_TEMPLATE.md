# Academic Data Request Letter Template: MAHSA / TwoRains Project

**To:** Prof. Cameron A. Petrie (`cap59@cam.ac.uk`), Dr. Adam S. Green (`adam.green@york.ac.uk`), Dr. Hector A. Orengo (`horengo@icac.cat`)  
**Cc:** Dr. Aftab Alam (`aftab.aihc@bhu.ac.in`), Prof. R.N. Singh (`prof.rnsingh@gmail.com`)  
**Subject:** Academic Data Request: Ground-confirmed archaeological site records for spatial ML evaluation in Haryana (Hisar, Fatehabad, Sirsa)

Dear Prof. Petrie, Dr. Green, Dr. Orengo, and Colleagues,

I am writing to request access to a subset of digitized archaeological survey records and historical map-mound features from the TwoRains project and the Mapping Archaeological Heritage in South Asia (MAHSA) database for an academic, open-source computational study on archaeological predictive modelling.

### Research Objective
Our study rigorously evaluates how much published satellite mound-detection performance survives under **variogram-sized buffered spatial block cross-validation** and **Area-of-Applicability (AoA) masking** (Meyer & Pebesma, 2021). We are benchmark-testing whether recent 64-dimensional self-supervised satellite embeddings (Google AlphaEarth Foundations, 10 m) and Positive-Unlabelled learning (`SAR-nnPU`) provide measurable lift on **low-relief and ploughed-out mounds ($< 1.0\text{ m}$ residual relief)** compared to multi-temporal Sentinel-1/2 random-forest baselines (following Orengo et al., 2020).

To prevent label-provenance circularity and excavation-scar leakage, we specifically require ground-confirmed sites to be separated from unverified historical map symbols, and protected/excavated monuments to be evaluated as a separate diagnostic stratum.

### Geographic Scope & Requested Fields
We are focusing strictly on three contiguous districts in Haryana: **Hisar, Fatehabad, and Sirsa** (Ghaggar-Hakra and relict Chautang interfluve). We request tabular/vector records containing:

1. **Spatial Coordinates & Precision:** Centroid coordinates (WGS84 / UTM 43N) along with positional accuracy class (e.g., RTK/DGPS, handheld GPS, toposheet-derived, village-centroid).
2. **Ground Confirmation Status:** Explicit boolean flag indicating whether the feature was visited and confirmed as an extant archaeological site during TwoRains pedestrian surveys (e.g., Green et al., 2019) or remains an unverified Survey of India (SOI) 1-inch map symbol.
3. **Mound Morphology & Relief:** Estimated mound height or categorical relief class (e.g., prominent $\ge 1.5\text{ m}$ vs. low-relief/ploughed $< 1.0\text{ m}$).
4. **Chronological Horizon(s):** Multi-label ceramic/chronological affiliations (Early/Mature/Late Harappan, Painted Grey Ware, Early Historic).
5. **Discovery Modality:** Survey discovery pathway (e.g., systematic pedestrian survey, historical map hachure, chance find).
6. **Protection / Excavation Status:** Whether the site has active ASI/State protection, perimeter fencing, or open excavation trenches.

### Data Governance, Anti-Looting & Ethics Commitment
We strictly adhere to Indian antiquities governance and anti-looting principles:
- **No Public Coordinate Release:** Exact coordinates will be stored exclusively on encrypted institutional storage. All public outputs, code repositories, and publication maps will aggregate candidate predictions strictly to coarse **Uber H3 Resolution 5/6 hexagons ($\sim 36\text{–}250\text{ km}^2$) with $k$-anonymity suppression ($n \ge 5$)**.
- **No Invasive / Fieldwork Claims:** The project is an independent computational evaluation prototype; no unauthorized surface collection or excavation will be conducted without formal statutory permission from the Archaeological Survey of India (ASI) / Haryana State Department of Archaeology and a recognized institutional partner.
- **Academic Attribution:** Full citation of TwoRains and MAHSA publications and datasets will be maintained, and we welcome collaboration or co-authorship on the resulting spatial evaluation manuscript.

Please let me know the appropriate formal data-sharing agreement (DSA) or research application form required by the MAHSA project. Thank you very much for your time and guidance.

Sincerely,  
**[Your Name / Institutional Affiliation]**  
**[Contact Information]**
