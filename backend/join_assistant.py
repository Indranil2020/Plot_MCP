"""Suggest join keys and merge strategies for multiple datasets."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd


class JoinAssistant:
    """Analyze datasets for potential join keys and warnings."""

    def suggest_joins(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, object]:
        """Return join suggestions based on shared columns and uniqueness."""
        aliases = list(dataframes.keys())
        suggestions: List[Dict[str, object]] = []

        for i, left_alias in enumerate(aliases):
            for right_alias in aliases[i + 1 :]:
                left_df = dataframes[left_alias]
                right_df = dataframes[right_alias]
                shared = self._shared_columns(left_df, right_df)
                if not shared:
                    continue

                for column in shared:
                    left_stats = self._column_stats(left_df, column)
                    right_stats = self._column_stats(right_df, column)
                    if not self._compatible_types(left_stats["dtype"], right_stats["dtype"]):
                        continue

                    warnings = []
                    if left_stats["uniqueness"] < 0.7:
                        warnings.append(
                            f"{left_alias}.{column} has low uniqueness ({left_stats['uniqueness']:.2f})"
                        )
                    if right_stats["uniqueness"] < 0.7:
                        warnings.append(
                            f"{right_alias}.{column} has low uniqueness ({right_stats['uniqueness']:.2f})"
                        )
                    if left_stats["null_ratio"] > 0:
                        warnings.append(
                            f"{left_alias}.{column} has {left_stats['null_ratio']:.2f} null ratio"
                        )
                    if right_stats["null_ratio"] > 0:
                        warnings.append(
                            f"{right_alias}.{column} has {right_stats['null_ratio']:.2f} null ratio"
                        )

                    suggestions.append(
                        {
                            "left": left_alias,
                            "right": right_alias,
                            "key": column,
                            "join_type": "inner",
                            "left_stats": left_stats,
                            "right_stats": right_stats,
                            "warnings": warnings,
                            "example": (
                                f"merged = pd.merge({left_alias}, {right_alias}, on='{column}', how='inner')"
                            ),
                        }
                    )

        return {
            "suggestions": suggestions,
            "dataset_count": len(aliases),
        }

    def _shared_columns(self, left_df: pd.DataFrame, right_df: pd.DataFrame) -> List[str]:
        left_cols = set(left_df.columns)
        right_cols = set(right_df.columns)
        return sorted(left_cols.intersection(right_cols))

    def _column_stats(self, df: pd.DataFrame, column: str) -> Dict[str, object]:
        series = df[column]
        total = len(series)
        unique = series.nunique(dropna=True)
        uniqueness = unique / total if total else 0
        null_ratio = series.isnull().mean() if total else 0
        return {
            "dtype": str(series.dtype),
            "rows": total,
            "unique": unique,
            "uniqueness": uniqueness,
            "null_ratio": null_ratio,
        }

    def _compatible_types(self, left_dtype: str, right_dtype: str) -> bool:
        if left_dtype.startswith("int") and right_dtype.startswith("int"):
            return True
        if left_dtype.startswith("float") and right_dtype.startswith("float"):
            return True
        if left_dtype.startswith("int") and right_dtype.startswith("float"):
            return True
        if left_dtype.startswith("float") and right_dtype.startswith("int"):
            return True
        if left_dtype == "object" and right_dtype == "object":
            return True
        if "datetime" in left_dtype and "datetime" in right_dtype:
            return True
        return False
