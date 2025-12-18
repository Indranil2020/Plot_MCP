"""
Intelligent Data Validator
Analyzes uploaded data and suggests appropriate plot types
Provides guidance on data formatting requirements
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class DataValidator:
    def __init__(self):
        self.plot_requirements = {
            "scatter": {
                "min_numeric_cols": 2,
                "description": "Requires at least 2 numeric columns (x, y)",
                "example": "Columns: 'x', 'y', optional 'size', 'color'"
            },
            "line": {
                "min_numeric_cols": 2,
                "description": "Requires at least 2 numeric columns (x, y)",
                "example": "Columns: 'time', 'value'"
            },
            "bar": {
                "min_cols": 2,
                "categorical": 1,
                "numeric": 1,
                "description": "Requires 1 categorical and 1 numeric column",
                "example": "Columns: 'category', 'value'"
            },
            "histogram": {
                "min_numeric_cols": 1,
                "description": "Requires at least 1 numeric column",
                "example": "Column: 'values'"
            },
            "boxplot": {
                "min_cols": 2,
                "categorical": 1,
                "numeric": 1,
                "description": "Requires 1 categorical (groups) and 1 numeric column",
                "example": "Columns: 'group', 'value'"
            },
            "heatmap": {
                "min_numeric_cols": 3,
                "description": "Requires numeric data in matrix form or 3+ numeric columns",
                "example": "Columns: multiple numeric columns or correlation matrix"
            },
            "3d_scatter": {
                "min_numeric_cols": 3,
                "description": "Requires at least 3 numeric columns (x, y, z)",
                "example": "Columns: 'x', 'y', 'z'"
            }
        }
    
    def analyze_data(self, df: pd.DataFrame) -> Dict:
        """Analyze dataframe structure and suggest plot types"""
        
        analysis = {
            "shape": df.shape,
            "columns": list(df.columns),
            "numeric_cols": [],
            "categorical_cols": [],
            "datetime_cols": [],
            "missing_values": {},
            "suggested_plots": [],
            "warnings": []
        }
        
        # Analyze each column
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                analysis["numeric_cols"].append(col)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                analysis["datetime_cols"].append(col)
            else:
                analysis["categorical_cols"].append(col)
            
            # Check for missing values
            missing = df[col].isnull().sum()
            if missing > 0:
                analysis["missing_values"][col] = missing
        
        # Suggest appropriate plot types
        num_numeric = len(analysis["numeric_cols"])
        num_categorical = len(analysis["categorical_cols"])
        num_datetime = len(analysis["datetime_cols"])
        
        if num_numeric >= 2:
            analysis["suggested_plots"].append({
                "type": "scatter",
                "confidence": 0.95,
                "reason": f"Found {num_numeric} numeric columns",
                "columns": analysis["numeric_cols"][:2]
            })
            analysis["suggested_plots"].append({
                "type": "line",
                "confidence": 0.90,
                "reason": f"Found {num_numeric} numeric columns",
                "columns": analysis["numeric_cols"][:2]
            })
        
        if num_numeric >= 3:
            analysis["suggested_plots"].append({
                "type": "3d_scatter",
                "confidence": 0.85,
                "reason": f"Found {num_numeric} numeric columns",
                "columns": analysis["numeric_cols"][:3]
            })
        
        if num_categorical >= 1 and num_numeric >= 1:
            analysis["suggested_plots"].append({
                "type": "bar",
                "confidence": 0.95,
                "reason": "Found categorical and numeric columns",
                "columns": [analysis["categorical_cols"][0], analysis["numeric_cols"][0]]
            })
            analysis["suggested_plots"].append({
                "type": "boxplot",
                "confidence": 0.80,
                "reason": "Found categorical and numeric columns",
                "columns": [analysis["categorical_cols"][0], analysis["numeric_cols"][0]]
            })
        
        if num_numeric >= 1:
            analysis["suggested_plots"].append({
                "type": "histogram",
                "confidence": 0.70,
                "reason": f"Found {num_numeric} numeric columns",
                "columns": [analysis["numeric_cols"][0]]
            })
        
        if num_datetime >= 1 and num_numeric >= 1:
            analysis["suggested_plots"].append({
                "type": "time_series",
                "confidence": 0.98,
                "reason": "Found datetime and numeric columns",
                "columns": [analysis["datetime_cols"][0], analysis["numeric_cols"][0]]
            })
        
        # Add warnings
        if analysis["missing_values"]:
            analysis["warnings"].append(
                f"Missing values detected in: {', '.join(analysis['missing_values'].keys())}"
            )
        
        if num_numeric == 0:
            analysis["warnings"].append(
                "No numeric columns found. Most plot types require numeric data."
            )
        
        return analysis
    
    def validate_for_plot_type(self, df: pd.DataFrame, plot_type: str) -> Tuple[bool, str]:
        """Validate if data is suitable for a specific plot type"""
        
        if plot_type not in self.plot_requirements:
            return True, "Plot type not in validation database"
        
        requirements = self.plot_requirements[plot_type]
        analysis = self.analyze_data(df)
        
        # Check numeric column requirements
        if "min_numeric_cols" in requirements:
            if len(analysis["numeric_cols"]) < requirements["min_numeric_cols"]:
                return False, (
                    f"{plot_type} requires at least {requirements['min_numeric_cols']} numeric columns. "
                    f"Your data has {len(analysis['numeric_cols'])}. "
                    f"{requirements['description']}. "
                    f"Example: {requirements['example']}"
                )
        
        # Check categorical column requirements
        if "categorical" in requirements:
            if len(analysis["categorical_cols"]) < requirements["categorical"]:
                return False, (
                    f"{plot_type} requires at least {requirements['categorical']} categorical column(s). "
                    f"Your data has {len(analysis['categorical_cols'])}. "
                    f"{requirements['description']}. "
                    f"Example: {requirements['example']}"
                )
        
        return True, "Data is suitable for this plot type"
    
    def suggest_data_transformation(self, df: pd.DataFrame, desired_plot: str) -> str:
        """Suggest how to transform data for a desired plot type"""
        
        analysis = self.analyze_data(df)
        
        if desired_plot == "scatter" and len(analysis["numeric_cols"]) < 2:
            return (
                "For a scatter plot, you need at least 2 numeric columns. "
                "Consider: 1) Adding a numeric column, 2) Converting categorical data to numeric, "
                "or 3) Using a different plot type like bar chart or histogram."
            )
        
        if desired_plot == "bar" and len(analysis["categorical_cols"]) == 0:
            return (
                "For a bar chart, you need at least 1 categorical column. "
                "Consider: 1) Converting a column to categorical, 2) Creating categories from numeric ranges, "
                "or 3) Using a histogram instead."
            )
        
        if desired_plot == "heatmap" and len(analysis["numeric_cols"]) < 3:
            return (
                "For a heatmap, you typically need multiple numeric columns or a correlation matrix. "
                "Consider: 1) Computing correlation between numeric columns, "
                "2) Pivoting your data to create a matrix, or 3) Using a different visualization."
            )
        
        return "Data structure looks compatible with this plot type."

    def get_plot_schema(self, plot_type: str) -> Dict[str, object]:
        """Return schema requirements for a plot type."""
        return self.plot_requirements.get(plot_type, {})

# Global instance
_validator = None

def get_validator():
    """Get or create the validator instance"""
    global _validator
    if _validator is None:
        _validator = DataValidator()
    return _validator
