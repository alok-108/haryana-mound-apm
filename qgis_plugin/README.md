# Pre-600 BCE Subcontinent APM Discovery GIS - QGIS Plugin

Official desktop QGIS plugin for the **Pan-Subcontinent Pre-600 BCE Archaeological Predictive Modeling (APM)** engine.

Designed specifically for **non-technical field archaeologists, heritage surveyors, and university research teams** to view, query, and verify unexcavated protohistoric tell anomalies directly inside standard QGIS (v3.22+ LTR).

---

## 🚀 Installation (Two Easy Ways)

### Option 1: Direct 1-Click Install via ZIP (Recommended)
1. Download [pre600bce_apm_qgis_plugin.zip](https://alok-108.github.io/haryana-mound-apm/pre600bce_apm_qgis_plugin.zip).
2. Open **QGIS**.
3. In the top menu, go to **`Plugins` → `Manage and Install Plugins...`**.
4. In the left panel, click **`Install from ZIP`**.
5. Select the downloaded `pre600bce_apm_qgis_plugin.zip` and click **Install Plugin**.
6. The plugin toolbar icon 🏺 and docked panel will appear in QGIS!

---

### Option 2: Add Custom QGIS Plugin Repository (Automatic Updates)
1. Open **QGIS** → **`Plugins` → `Manage and Install Plugins...`**.
2. Click **`Settings`** on the left panel.
3. Under **Plugin Repositories**, click **`Add...`**.
4. Enter:
   - **Name:** `Subcontinent Pre-600 BCE APM Repository`
   - **URL:** `https://alok-108.github.io/haryana-mound-apm/plugins.xml`
5. Click **OK**.
6. Switch to the **`All`** tab in the plugin manager, search for **`Pre-600 BCE APM`**, and click **Install Plugin**!

---

## 🛠️ Features inside QGIS

1. **Load High-Confidence Discovery Tells:**
   - 1-click loading of verified candidate tells (with predicted culture, estimated relief, and calibrated Bayesian presence probability).
2. **Statutory 1,500 m Exclusion Buffers:**
   - Visualizes exact 1,500 m legal buffer rings around all 97 registered monuments to guarantee zero overlap with documented heritage.
3. **Multi-Sensor Basemap Integration:**
   - Automatically loads high-resolution satellite imagery (ESRI World Imagery, Google Satellite) and topographic layers underneath candidate locations.
4. **Mobile ODK / KoboToolbox Integration:**
   - Direct button to export standardized mobile survey forms for offline pedestrian ground-truthing in rural field locations.

---

## 🛡️ Anti-Looting Compliance (ICAHM / UNESCO)
Public vector distributions are coarsened to 2 km spatial units to safeguard fragile settlement mounds from illicit looting or metal-detecting. Sub-meter precision vectors are reserved exclusively for accredited statutory directorates (ASI, DOAM) and university consortia.
