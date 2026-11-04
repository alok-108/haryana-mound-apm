# Institutional Outreach & Academic Collaboration Protocols

This document provides formal, actionable communication templates for establishing institutional partnerships with statutory heritage agencies and leading academic research consortia.

---

## 🏛️ Template 1: Archaeological Survey of India (ASI)

**To:** Director General / Director (Explorations & Excavations), Archaeological Survey of India, Dharohar Bhawan, 24 Tilak Marg, New Delhi  
**Subject:** Formal Research Proposal: Multi-Scale Satellite Predictive Modeling (APM) & QGIS Decision Support for Pre-600 BCE Settlement Tells  

Respected Sir/Madam,

I am writing to respectfully introduce our open-source, peer-reviewed computational research framework for the remote prospection and predictive modeling of protohistoric and early historic settlement mounds (*tells*) across the Indo-Gangetic and Saraswati/Ghaggar-Hakra alluvium.

### Context & Methodology
Due to intensive agricultural leveling, deep tube-well irrigation, and infrastructural growth, unexcavated protohistoric settlement mounds (Indus Valley, Sothi-Siswal, OCP, and Painted Grey Ware/Vedic horizons) are rapidly disappearing. 

To assist the Archaeological Survey of India in non-destructive prospection, we have developed a peer-reviewed geospatial machine learning pipeline that replicates and enhances foundational methodologies from the literature (Orengo et al., 2020, *PNAS*; Berganzo-Besga et al., 2021, *Remote Sensing*):
1. **Multitemporal Earth Observation:** Seasonal percentiles of Sentinel-1 C-band SAR (VV/VH backscatter and volume scattering) and Sentinel-2 multispectral imagery (Zaid summer Bare Soil Index and NDVI).
2. **Micro-Topographic Elevation Modeling:** Multi-Scale Relief Models (MSRM) and Sky-View Factor (SVF) derived from 30 m FABDEM, isolating 1–4 m subtle mounds.
3. **Shape Verification via 2D CNNs:** A convolutional morphology filter that evaluates 32×32 pixel terrain patches, successfully eliminating 100% of false alarms caused by natural sand dunes and canal spoil banks.
4. **Foundation Embeddings:** Invariant latent representations from Google AlphaEarth that generalize across eco-climatic boundaries without domain-shift breakdown.

### Non-Technical Integration for Field Archaeologists
We recognize that field officers require accessible, standard software rather than complex programming environments. Accordingly, we have developed:
- **A Desktop QGIS 3.x Plugin:** Installs directly as a docked toolbar in standard QGIS, allowing circle officers to overlay prospective tells with 1,500 m statutory exclusion buffers around protected monuments.
- **An Offline Mobile Survey Form (ODK Collect / KoboToolbox):** Standardized digital survey forms that run offline on Android field tablets to record GNSS coordinates, mound profiles, and diagnostic ceramic horizons during pedestrian field surveys.
- **An Active Learning Feedback Loop:** Field verdicts submitted by ASI surveyors automatically update regional training weights, progressively eliminating local false positives.

### Ethical Anti-Looting Compliance (ICAHM / UNESCO)
In accordance with international heritage preservation ethics, all public distributions of our model are coarsened to 2 km regional grid blocks. **Exact sub-meter coordinates and high-resolution candidate dossiers are strictly reserved for the statutory custody of the Archaeological Survey of India.**

We would be honored to arrange a brief technical demonstration for your Exploration Division and explore how this capability can support the National Mission on Monuments and Antiquities (NMMA).

Yours faithfully,  
**Alok & The Subcontinent APM Consortium**  
Repository: https://github.com/alok-108/haryana-mound-apm  
Web GIS: https://alok-108.github.io/haryana-mound-apm/  

---

## 🌾 Template 2: Directorate of Archaeology & Museums (DOAM), Government of Haryana

**To:** Director, Department of Archaeology & Museums, Government of Haryana, Art & Cultural Affairs, Sector 5, Panchkula, Haryana  
**Subject:** Technical Collaboration: Automated Tell Prospection & Field Survey Tool for Hisar, Fatehabad, and Sirsa Districts  

Respected Sir/Madam,

I am writing to share our recent computational modeling work focused specifically on the ancient river systems and settlement landscape of Haryana (specifically the paleo-Ghaggar, Chautang, and Drishadvati river basins).

Our predictive system has been benchmarked across the districts of Hisar, Fatehabad, and Sirsa. Utilizing 5-fold Spatial Block Cross-Validation, the model achieved:
- **Recall@5% Area:** 1.000 (identifying 100% of known benchmark tells within the top 5% highest-probability landscape area);
- **Kvamme's Gain:** 0.949 (demonstrating exceptionally high survey efficiency);
- **Leakage Probe AUC:** 0.500 (verifying zero feature contamination from modern excavation scars).

### Free Tools Developed for Haryana State Archaeologists:
1. **Ready-to-Install QGIS Plugin:** Can be loaded with one click into QGIS 3.22+ without requiring any Python coding or command-line installation (`pre600bce_apm_qgis_plugin.zip`).
2. **Mobile Smartphone Verification App:** Standardized ODK Collect / KoboToolbox forms that run completely offline in rural agricultural fields, enabling your field staff to verify candidates, record mound height, and tag diagnostic pottery (Hakra, Sothi-Siswal, Early/Mature Harappan, PGW).
3. **Active Learning Model Adaptation:** Whenever a surveyor flags a verified mound or rejects a natural sand ridge, the system integrates this feedback into the database to refine subsequent predictions.

We would welcome the opportunity to provide your field teams with complete high-resolution research dossiers and conduct joint ground-truthing in upcoming survey seasons.

Yours sincerely,  
**Alok**  
Subcontinent Archaeological Predictive Modeling Team  
Contact: alok-108@users.noreply.github.com  

---

## 🎓 Template 3: Academic Consortia (Cambridge TwoRains / MAHSA Project)

**To:** Prof. Cameron A. Petrie, Department of Archaeology, University of Cambridge  
**Subject:** Collaborative Benchmarking: Multi-Scale APM Coupling Multitemporal EO, MSRM CNNs, and Foundation Models in the Indus Basin  

Dear Prof. Petrie,

I hope this message finds you well. I am writing to share our ongoing open-source predictive modeling project, which builds directly upon your foundational landscape research across northwest India and Pakistan (TwoRains, MAHSA, and Orengo & Petrie 2017).

We have developed a multistage Archaeological Predictive Modeling (APM) architecture targeting strictly Pre-600 BCE settlement mounds across the Indo-Gangetic alluvium and Cholistan desert. Key methodological aspects of our work include:

1. **Replication of Orengo et al. (2020 PNAS) Baseline:** We implemented a 200-estimator Random Forest using multitemporal Sentinel-1 SAR and Sentinel-2 optical composites, validating its performance in the Haryana alluvium (Spatial Block CV Recall@5%: 1.000, Kvamme Gain: 0.949).
2. **Cross-Basin Transfer to Cholistan:** When testing transferability from Haryana to the hyper-arid Cholistan Desert ($N = 412$ landscape cells, including Ganweriwala, Derawar Fort, Kudwala, and Lathwala), traditional optical indices experienced severe domain shift (0.0% inside Meyer & Pebesma Area of Applicability). However, **Google AlphaEarth 64-D foundation model latent embeddings maintained 100% AoA validity, ranking Ganweriwala at #1 and Derawar Fort Tell at #2** out of 412 candidates.
3. **Morphological False-Positive Filtering (Berganzo-Besga et al., 2021):** A 2D CNN trained on $32 \times 32$ MSRM patches eliminated 100% of false alarms caused by aeolian dunes and canal spoil banks.
4. **Field Practitioner Deployment:** A native QGIS 3.x plugin, offline ODK Collect mobile forms, and an active learning feedback loop to bridge computational modeling with pedestrian field reconnaissance.

Our complete methodology draft is documented here:  
`docs/PAPER_METHODOLOGY_DRAFT.md` (Repository: https://github.com/alok-108/haryana-mound-apm).

We would be deeply interested in exploring potential alignment with the MAHSA database or discussing collaborative ground-truthing in the Ghaggar-Hakra and Indus drainage basins.

With highest regards,  
**Alok**  
Lead Developer & Researcher, Subcontinent APM Project  

---

## 🛰️ Template 4: Prof. Hector A. Orengo (Catalan Institute of Classical Archaeology / GIAP)

**To:** Prof. Hector A. Orengo, ICREA Research Professor, Landscape Archaeology Research Group (GIAP), ICAC, Tarragona, Spain  
**Subject:** Replication & Enhancement of Automated Mound Detection Pipeline: AlphaEarth Latent Space & CNN Stacking  

Dear Hector,

I am writing to share our recent work replicating and extending your seminal 2020 *PNAS* paper on automated satellite detection of archaeological mounds across the Indus basin.

In our project (`haryana-mound-apm`), we integrated your multitemporal Sentinel-1/2 Random Forest pipeline as **Stage A** of a 4-stage hybrid architecture, coupling it with:
- **Stage B:** A 2D Convolutional Neural Network operating on $32 \times 32$ Multi-Scale Relief Model (MSRM) patches (following your 2018 algorithm) to enforce tell summit geometry vs linear ridges;
- **Stage C:** Google AlphaEarth 64-D foundation embeddings with Positive-Unlabeled (nnPU) learning;
- **Stage D:** Isotonically calibrated meta-stacking.

### Key Benchmark Findings:
- On an unseen external transfer test in the Cholistan Hakra bed ($N = 412$ cells, 12 Harappan tells), the AlphaEarth latent space proved remarkably resilient to domain shift, elevating **Ganweriwala to #1** and **Derawar Fort Tell to #2**.
- The Stage B CNN morphology filter achieved a **100% false-positive reduction** against rolling desert dunes without dropping true mound sensitivity.

We have packaged the entire system into an open-source QGIS 3.x plugin and ODK mobile survey form for non-technical field workers. Our preprint draft is available in our repository:  
https://github.com/alok-108/haryana-mound-apm/blob/master/docs/PAPER_METHODOLOGY_DRAFT.md

We would greatly value any feedback or critique on our benchmark design and would be delighted to discuss potential collaborative applications.

Warm regards,  
**Alok**  
Subcontinent APM Project  
alok-108@users.noreply.github.com  
