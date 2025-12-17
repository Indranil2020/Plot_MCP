import matplotlib
matplotlib.use('Agg') # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import io
import base64
import traceback

import numpy as np

class PlotEngine:
    def __init__(self):
        pass


    def execute_code(self, code, data_path, dpi=300, format='png'):
        # Reset figure
        plt.clf()
        plt.close('all')
        
        # Setup fonts (robust handling)
        self._setup_fonts()
        
        # Load data
        if data_path and isinstance(data_path, str):
            if data_path.endswith('.csv'):
                df = pd.read_csv(data_path)
            elif data_path.endswith('.json'):
                df = pd.read_json(data_path)
            else:
                df = pd.DataFrame()
        else:
            df = pd.DataFrame()

        # Create a safe execution environment
        # We inject plt and pandas, and the dataframe
        local_vars = {"df": df, "plt": plt, "pd": pd, "sns": sns, "np": np}
        
        # Execute the code
        exec(code, {}, local_vars)
        
        # Get the current figure after code execution
        fig = plt.gcf()
        
        # Apply styling to ensure all visual details are visible
        self._apply_styling_to_figure(fig)

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format=format, dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        
        if format == 'png':
            # For PNG, we can return base64 for preview
            plot_data = base64.b64encode(buf.getvalue()).decode('utf-8')
            # Extract metadata for interactive elements
            metadata = self._extract_plot_metadata(fig)
            plt.close(fig)
            return {
                "image": plot_data,
                "metadata": metadata,
                "buffer": buf # Return buffer for potential download
            }
        else:
            # For other formats (PDF, SVG), just return the buffer content
            plt.close(fig)
            return {
                "buffer": buf,
                "metadata": {}
            }

    def _setup_fonts(self):
        """Robustly setup fonts and matplotlib rcParams, falling back if custom fonts are missing"""
        import os
        from matplotlib import font_manager
        
        # List of desired fonts
        font_files = [
            '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf',
            '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf',
            '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Italic.ttf',
            '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold_Italic.ttf'
        ]
        
        fonts_found = False
        for font_file in font_files:
            if os.path.exists(font_file):
                font_manager.fontManager.addfont(font_file)
                fonts_found = True
                    
        if fonts_found:
            plt.rcParams['font.family'] = 'Times New Roman'
        else:
            # Fallback to a serif font if Times New Roman isn't available
            plt.rcParams['font.family'] = 'serif'
        
        # Apply the comprehensive matplotlib settings as requested
        l_w = 2.5
        f_s = 25
        
        plt.rcParams.update({
            'axes.linewidth': l_w,          # Thickness of the axis lines
            'xtick.major.width': l_w,       # Thickness of major ticks on x-axis
            'ytick.major.width': l_w,       # Thickness of major ticks on y-axis
            'xtick.minor.width': 1.5,       # Thickness of minor ticks on x-axis
            'ytick.minor.width': 1.5,       # Thickness of minor ticks on y-axis
            'xtick.major.size': 8,          # Length of major ticks on x-axis
            'ytick.major.size': 8,          # Length of major ticks on y-axis
            'xtick.minor.size': 4,          # Length of minor ticks on x-axis
            'ytick.minor.size': 4,          # Length of minor ticks on y-axis
            'xtick.labelsize': f_s,         # Font Size of x-axis tick labels
            'ytick.labelsize': f_s,         # Font Size of y-axis tick labels
            'axes.labelsize': f_s,          # Font Size of axis labels
            'legend.fontsize': f_s,         # Font Size of legend
            'axes.titlesize': f_s,          # Font Size of axis titles
            'figure.titlesize': f_s,        # Font Size of figure titles
            'xtick.direction': 'in',        # X-axis ticks point inward
            'ytick.direction': 'in',        # Y-axis ticks point inward
            'xtick.top': True,              # Show ticks on top axis
            'xtick.bottom': True,           # Show ticks on bottom axis (default)
            'ytick.left': True,             # Show ticks on left axis (default)
            'ytick.right': True,            # Show ticks on right axis
            'axes.grid.which': 'both',      # Grid lines at both major and minor ticks
            # Ensure all spines are visible
            'axes.spines.left': True,
            'axes.spines.bottom': True,
            'axes.spines.top': True,
            'axes.spines.right': True,
        })
    
    def _apply_styling_to_figure(self, fig):
        """Apply styling to all axes in the figure to ensure visual details are visible"""
        for ax in fig.axes:
            # Enable minor ticks
            ax.minorticks_on()
            
            # Ensure all spines are visible and styled
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(2.5)
            
            # Apply tick parameters
            ax.tick_params(axis='both', which='major', direction='in', 
                          length=8, width=2.5, labelsize=25)
            ax.tick_params(axis='both', which='minor', direction='in', 
                          length=4, width=1.5)
            
            # Ensure ticks on all sides
            ax.tick_params(top=True, bottom=True, left=True, right=True,
                          labeltop=False, labelbottom=True, labelleft=True, labelright=False)

    def _extract_plot_metadata(self, fig):
        """Extract bounding boxes for interactive elements"""
        metadata = []
        
        # Get renderer
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        
        # Helper to get bbox in relative coordinates (0-1)
        def get_relative_bbox(artist, label_type):
            bbox = artist.get_window_extent(renderer)
            # Transform to figure coordinates (0-1)
            inv = fig.transFigure.inverted()
            bbox_fig = bbox.transformed(inv)
            return {
                "type": label_type,
                "text": artist.get_text() if hasattr(artist, 'get_text') else "",
                "bbox": [bbox_fig.x0, bbox_fig.y0, bbox_fig.width, bbox_fig.height]
            }

        for i, ax in enumerate(fig.axes):
            # Title
            if ax.get_title():
                metadata.append(get_relative_bbox(ax.title, "title"))
            
            # X Label
            if ax.get_xlabel():
                metadata.append(get_relative_bbox(ax.xaxis.label, "xlabel"))
            
            # Y Label
            if ax.get_ylabel():
                metadata.append(get_relative_bbox(ax.yaxis.label, "ylabel"))
            
            # Legend
            legend = ax.get_legend()
            if legend:
                # Legend doesn't have simple text, but we can make the whole box clickable
                bbox = legend.get_window_extent(renderer)
                inv = fig.transFigure.inverted()
                bbox_fig = bbox.transformed(inv)
                metadata.append({
                    "type": "legend",
                    "text": "Legend",
                    "bbox": [bbox_fig.x0, bbox_fig.y0, bbox_fig.width, bbox_fig.height]
                })
                
        return metadata
