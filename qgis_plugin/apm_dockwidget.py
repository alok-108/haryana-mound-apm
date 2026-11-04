"""
PyQt5 / PyQt6 Dock Widget for the Pre-600 BCE APM QGIS Plugin.
Provides real-time telemetry inspection, layer loading, and field package exports.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Optional

try:
    from qgis.PyQt.QtCore import Qt, pyqtSignal
    from qgis.PyQt.QtGui import QColor, QFont
    from qgis.PyQt.QtWidgets import (
        QDockWidget,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    # Mock base class for non-QGIS test environments
    class QDockWidget:  # type: ignore
        def __init__(self, parent=None): pass


class APMDockWidget(QDockWidget if HAS_PYQT else object):
    """
    QGIS Dock Widget showing APM point telemetry and surveyor actions.
    """

    def __init__(self, parent=None):
        if not HAS_PYQT:
            return
        super().__init__("Pre-600 BCE Archaeological Prospection", parent)
        self.setObjectName("APMDockWidget")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Main widget container
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)

        # 1. Header Banner
        header = QLabel("🛰️ Subcontinent Pre-600 BCE APM")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet("color: #0284c7; margin-bottom: 2px;")
        self.layout.addWidget(header)

        sub_header = QLabel("GeoAI Prospective Mound Discovery & Heritage Audit")
        sub_header.setStyleSheet("color: #64748b; font-size: 10px; margin-bottom: 6px;")
        self.layout.addWidget(sub_header)

        # 2. Status Box
        self.status_box = QLabel("Ready: Click '🎯 Point Inspector' to sample terrain.")
        self.status_box.setStyleSheet(
            "background: #f1f5f9; padding: 6px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 11px;"
        )
        self.layout.addWidget(self.status_box)

        # 3. Telemetry Results Group
        self.tel_group = QGroupBox("📍 Coordinate Inspection Telemetry")
        self.tel_layout = QVBoxLayout(self.tel_group)

        self.lbl_coords = QLabel("Coordinates: --, --")
        self.lbl_status = QLabel("Classification: --")
        self.lbl_prob = QLabel("Presence Probability: --")
        self.lbl_culture = QLabel("Predicted Culture: --")
        self.lbl_paleo = QLabel("Nearest Paleochannel: --")
        self.lbl_monument = QLabel("Nearest Documented Site: --")
        self.lbl_relief = QLabel("Estimated Mound Relief: --")

        for lbl in [
            self.lbl_coords,
            self.lbl_status,
            self.lbl_prob,
            self.lbl_culture,
            self.lbl_paleo,
            self.lbl_monument,
            self.lbl_relief,
        ]:
            lbl.setStyleSheet("font-size: 11px; margin: 1px 0;")
            self.tel_layout.addWidget(lbl)

        self.layout.addWidget(self.tel_group)

        # 4. Field Protocol Box
        self.protocol_group = QGroupBox("📋 Recommended Field Protocol")
        self.proto_layout = QVBoxLayout(self.protocol_group)
        self.txt_protocol = QTextEdit()
        self.txt_protocol.setReadOnly(True)
        self.txt_protocol.setMaximumHeight(80)
        self.txt_protocol.setStyleSheet("font-size: 10px; background: #f8fafc;")
        self.proto_layout.addWidget(self.txt_protocol)
        self.layout.addWidget(self.protocol_group)

        # 5. Anti-Looting Ethics Notice
        looting_notice = QLabel(
            "🛡️ <b>Anti-Looting Policy:</b> Public vectors are coarsened to ~1.1km to protect sites from illicit treasure hunting."
        )
        looting_notice.setWordWrap(True)
        looting_notice.setStyleSheet("font-size: 9px; color: #dc2626; background: #fef2f2; padding: 6px; border-radius: 4px;")
        self.layout.addWidget(looting_notice)

        self.layout.addStretch()
        self.setWidget(self.container)

    def update_telemetry(self, data: Dict[str, object]) -> None:
        """Update the dock widget fields with coordinate scan results."""
        if not HAS_PYQT:
            return
        lat = data.get("latitude", 0.0)
        lon = data.get("longitude", 0.0)
        prob = float(data.get("calibrated_probability", 0.0)) * 100.0
        tier = data.get("confidence_tier", "")
        culture = data.get("predicted_culture", "Unknown Pre-600 BCE")
        paleo = data.get("nearest_paleochannel", "None")
        paleo_d = data.get("dist_paleochannel_km", 0.0)
        mon = data.get("nearest_known_monument", "None")
        mon_d = float(data.get("dist_to_known_monument_m", 0.0)) / 1000.0
        is_novel = bool(data.get("is_undiscovered", True))
        relief = data.get("telemetry", {}).get("estimated_relief_m", 0.0)

        self.lbl_coords.setText(f"Coordinates: <b>{lat:.4f}°N, {lon:.4f}°E</b>")
        status_str = "<span style='color:#16a34a;'>🌟 Novel Undiscovered Candidate</span>" if is_novel else "<span style='color:#dc2626;'>🏛️ Known Documented Monument</span>"
        self.lbl_status.setText(f"Classification: {status_str}")
        self.lbl_prob.setText(f"Presence Probability: <b>{prob:.1f}%</b> ({tier})")
        self.lbl_culture.setText(f"Predicted Culture: <b>{culture}</b>")
        self.lbl_paleo.setText(f"Paleochannel: <b>{paleo}</b> ({paleo_d:.2f} km)")
        self.lbl_monument.setText(f"Nearest Known Site: <b>{mon}</b> ({mon_d:.2f} km)")
        self.lbl_relief.setText(f"Estimated Relief: <b>+{relief:.1f} m</b>")

        recs = data.get("recommended_ground_check", "RTK-GNSS + Magnetic Gradiometry + diagnostic surface sherd transect.")
        self.txt_protocol.setPlainText(str(recs))
        self.status_box.setText(f"Scanned coordinate ({lat:.4f}, {lon:.4f})")
