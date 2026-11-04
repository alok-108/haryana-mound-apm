"""
Active Learning Ground Feedback Ingestor for APM Tell Prospection.
Closes the loop between mobile field survey feedback and computational models:
1. Ingests surveyor observations from ODK / KoboToolbox mobile forms.
2. If `mound_confirmed`: Promotes candidate to verified ground truth (`train_positive`).
3. If `false_positive_*`: Converts candidate into an explicit hard-negative (`is_hard_negative=1`).
4. Re-fits models (Active Learning step) to eliminate recurring regional false positives.
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from src.subcontinent_known_monuments import SubcontinentKnownMonumentsRegistry


@dataclass
class SurveyVerificationSubmission:
    submission_id: str
    surveyor_name: str
    institution: str
    latitude: float
    longitude: float
    ground_verdict: str  # "mound_confirmed", "false_positive_dune", "false_positive_canal", "false_positive_brick_kiln", "ploughed_out_scatter"
    candidate_id: Optional[str] = None
    observed_relief_m: float = 0.0
    observed_diameter_m: float = 0.0
    observed_ceramics: Optional[List[str]] = None
    field_notes: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        if isinstance(d.get("observed_ceramics"), list):
            d["observed_ceramics"] = ";".join(d["observed_ceramics"])
        return d


class ActiveLearningFeedbackIngestor:
    """
    Manages ingestion of mobile ground verification submissions and triggers model adaptation.
    """

    def __init__(
        self,
        storage_csv: Optional[Path] = None,
        min_exclusion_distance_m: float = 1500.0,
    ) -> None:
        self.storage_csv = storage_csv or (REPO_ROOT / "data" / "field_survey" / "verified_field_submissions.csv")
        self.storage_csv.parent.mkdir(parents=True, exist_ok=True)
        self.monuments_registry = SubcontinentKnownMonumentsRegistry(min_exclusion_distance_m=min_exclusion_distance_m)

    def ingest_submission(self, sub: SurveyVerificationSubmission) -> Dict[str, object]:
        """
        Validate and store a mobile survey submission.
        """
        # 1. Enforce spatial safety check against documented monuments
        is_novel, dist_known_m, nearest_mon = self.monuments_registry.verify_is_undiscovered(sub.latitude, sub.longitude)

        # 2. Determine action
        is_confirmed = sub.ground_verdict == "mound_confirmed"
        is_false_pos = sub.ground_verdict.startswith("false_positive")
        is_scatter = sub.ground_verdict == "ploughed_out_scatter"

        row = sub.to_dict()
        row["is_outside_known_buffer"] = is_novel
        row["nearest_monument"] = nearest_mon.canonical_name
        row["dist_to_monument_m"] = round(dist_known_m, 1)
        row["active_learning_role"] = (
            "new_ground_truth_positive" if is_confirmed else
            ("hard_negative_penalty" if is_false_pos else "weak_pottery_scatter")
        )

        # Append to persistent storage
        df_row = pd.DataFrame([row])
        if self.storage_csv.exists() and self.storage_csv.stat().st_size > 0:
            df_row.to_csv(self.storage_csv, mode="a", header=False, index=False)
        else:
            df_row.to_csv(self.storage_csv, mode="w", header=True, index=False)

        return {
            "status": "INGESTED",
            "submission_id": sub.submission_id,
            "verdict": sub.ground_verdict,
            "active_learning_role": row["active_learning_role"],
            "is_outside_known_buffer": is_novel,
            "dist_to_documented_monument_m": round(dist_known_m, 1),
            "message": (
                f"Successfully ingested survey verdict '{sub.ground_verdict}' from {sub.surveyor_name} ({sub.institution})."
            ),
        }

    def load_all_submissions(self) -> pd.DataFrame:
        """Load all accumulated ground survey feedback records."""
        if not self.storage_csv.exists() or self.storage_csv.stat().st_size == 0:
            return pd.DataFrame()
        return pd.read_csv(self.storage_csv)

    def apply_active_learning_update(
        self,
        base_features_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Incorporate field survey submissions into the training feature matrix.
        Promotes verified mounds to positive training examples and adds hard negatives.
        """
        subs_df = self.load_all_submissions()
        if subs_df.empty:
            return base_features_df, {"new_positives": 0, "new_hard_negatives": 0}

        updated_df = base_features_df.copy()
        if "is_hard_negative" not in updated_df.columns:
            updated_df["is_hard_negative"] = 0

        new_pos_count = 0
        new_neg_count = 0

        for _, sub in subs_df.iterrows():
            cand_id = sub.get("candidate_id")
            verdict = sub.get("ground_verdict")

            # If matching candidate ID exists in dataframe
            if cand_id and cand_id in updated_df["site_id"].values:
                idx = updated_df[updated_df["site_id"] == cand_id].index[0]
                if verdict == "mound_confirmed":
                    updated_df.loc[idx, "y_obs"] = 1
                    updated_df.loc[idx, "is_ground_confirmed"] = True
                    updated_df.loc[idx, "discovery_modality"] = "field_survey_odk"
                    new_pos_count += 1
                elif str(verdict).startswith("false_positive"):
                    updated_df.loc[idx, "y_obs"] = 0
                    updated_df.loc[idx, "is_hard_negative"] = 1
                    new_neg_count += 1

        stats = {
            "new_positives": new_pos_count,
            "new_hard_negatives": new_neg_count,
            "total_feedback_submissions": len(subs_df),
        }
        return updated_df, stats
