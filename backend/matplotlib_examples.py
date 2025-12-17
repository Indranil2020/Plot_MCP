# Comprehensive Matplotlib Gallery Examples
# Based on https://matplotlib.org/stable/gallery/index.html

MATPLOTLIB_GALLERY = {
    # ==================== LINES, BARS AND MARKERS ====================
    "basic_line": """
plt.plot(x, y)
plt.xlabel('X'); plt.ylabel('Y'); plt.title('Basic Line Plot')
""",
    
    "multiple_lines": """
plt.plot(x, y1, label='Line 1', linewidth=2)
plt.plot(x, y2, label='Line 2', linestyle='--')
plt.plot(x, y3, label='Line 3', linestyle=':', marker='o')
plt.legend(); plt.grid(True, alpha=0.3)
""",
    
    "scatter_basic": """
plt.scatter(x, y, s=50, alpha=0.6, c='steelblue', edgecolors='black')
plt.xlabel('X'); plt.ylabel('Y')
""",
    
    "scatter_advanced": """
colors = pd.Categorical(df['category']).codes
sizes = df['size'] * 100
plt.scatter(df['x'], df['y'], c=colors, s=sizes, alpha=0.6, cmap='viridis', edgecolors='black')
plt.colorbar(label='Category')
""",
    
    "bar_vertical": """
plt.bar(categories, values, color='steelblue', edgecolor='black', alpha=0.7)
plt.xticks(rotation=45, ha='right')
plt.ylabel('Values')
""",
    
    "bar_horizontal": """
plt.barh(categories, values, color='coral', edgecolor='black')
plt.xlabel('Values')
""",
    
    "bar_grouped": """
x = np.arange(len(categories))
width = 0.35
plt.bar(x - width/2, values1, width, label='Group 1', color='steelblue')
plt.bar(x + width/2, values2, width, label='Group 2', color='coral')
plt.xticks(x, categories)
plt.legend()
""",
    
    "bar_stacked": """
plt.bar(categories, values1, label='Part 1', color='steelblue')
plt.bar(categories, values2, bottom=values1, label='Part 2', color='coral')
plt.legend()
""",
    
    "stem_plot": """
plt.stem(x, y, linefmt='C0-', markerfmt='C0o', basefmt='C0-')
plt.xlabel('X'); plt.ylabel('Y')
""",
    
    "step_plot": """
plt.step(x, y, where='mid', label='Step plot')
plt.legend()
""",
    
    "fill_between": """
plt.plot(x, y, 'b-', label='Mean')
plt.fill_between(x, y - error, y + error, alpha=0.3, label='±1σ')
plt.legend()
""",
    
    # ==================== STATISTICAL PLOTS ====================
    "histogram": """
plt.hist(data, bins=30, edgecolor='black', alpha=0.7, color='steelblue')
plt.xlabel('Value'); plt.ylabel('Frequency')
""",
    
    "histogram_multiple": """
plt.hist([data1, data2], bins=20, label=['Dataset 1', 'Dataset 2'], alpha=0.6)
plt.legend()
""",
    
    "boxplot": """
plt.boxplot([data1, data2, data3], labels=['A', 'B', 'C'], patch_artist=True)
plt.ylabel('Values')
""",
    
    "violin_plot": """
import seaborn as sns
sns.violinplot(data=df, x='category', y='value', palette='Set2')
""",
    
    "kde_plot": """
import seaborn as sns
sns.kdeplot(data=data, fill=True, alpha=0.6)
plt.xlabel('Value'); plt.ylabel('Density')
""",
    
    "hexbin": """
plt.hexbin(x, y, gridsize=30, cmap='Blues')
plt.colorbar(label='Count')
""",
    
    "2d_histogram": """
plt.hist2d(x, y, bins=30, cmap='Blues')
plt.colorbar(label='Count')
""",
    
    # ==================== IMAGES, CONTOURS AND FIELDS ====================
    "imshow": """
plt.imshow(matrix, cmap='viridis', aspect='auto', interpolation='nearest')
plt.colorbar(label='Intensity')
""",
    
    "heatmap": """
import seaborn as sns
sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
            square=True, linewidths=1, cbar_kws={'label': 'Correlation'})
""",
    
    "contour": """
plt.contour(X, Y, Z, levels=10, cmap='viridis')
plt.colorbar(label='Z values')
plt.xlabel('X'); plt.ylabel('Y')
""",
    
    "contourf": """
plt.contourf(X, Y, Z, levels=20, cmap='RdYlBu_r')
plt.colorbar(label='Z values')
plt.contour(X, Y, Z, levels=10, colors='black', linewidths=0.5, alpha=0.4)
""",
    
    "quiver": """
plt.quiver(X, Y, U, V, scale=50)
plt.xlabel('X'); plt.ylabel('Y')
plt.title('Vector Field')
""",
    
    "streamplot": """
plt.streamplot(X, Y, U, V, density=1.5, color='k', linewidth=1)
plt.xlabel('X'); plt.ylabel('Y')
""",
    
    # ==================== SUBPLOTS AND LAYOUTS ====================
    "subplots_2x2": """
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes[0, 0].plot(x, y1); axes[0, 0].set_title('Plot 1')
axes[0, 1].scatter(x, y2); axes[0, 1].set_title('Plot 2')
axes[1, 0].bar(categories, values); axes[1, 0].set_title('Plot 3')
axes[1, 1].hist(data); axes[1, 1].set_title('Plot 4')
plt.tight_layout()
""",
    
    "subplots_shared_axes": """
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
ax1.plot(x, y1); ax1.set_title('Left')
ax2.plot(x, y2); ax2.set_title('Right')
""",
    
    "gridspec": """
import matplotlib.gridspec as gridspec
fig = plt.figure(figsize=(12, 8))
gs = gridspec.GridSpec(3, 3)
ax1 = fig.add_subplot(gs[0, :])  # Top row, all columns
ax2 = fig.add_subplot(gs[1, :-1])  # Middle row, first 2 columns
ax3 = fig.add_subplot(gs[1:, -1])  # Last 2 rows, last column
ax4 = fig.add_subplot(gs[-1, 0])  # Bottom left
ax5 = fig.add_subplot(gs[-1, 1])  # Bottom middle
""",
    
    "inset_axes": """
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
fig, ax = plt.subplots()
ax.plot(x, y)
axins = inset_axes(ax, width="40%", height="40%", loc='upper right')
axins.plot(x_zoom, y_zoom)
""",
    
    # ==================== PIE AND POLAR CHARTS ====================
    "pie_basic": """
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
plt.axis('equal')
""",
    
    "pie_exploded": """
explode = (0.1, 0, 0, 0)
plt.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', 
        shadow=True, startangle=90, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
plt.axis('equal')
""",
    
    "donut_chart": """
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
        wedgeprops=dict(width=0.5))
plt.axis('equal')
""",
    
    "polar_plot": """
theta = np.linspace(0, 2*np.pi, 100)
r = np.abs(np.sin(3*theta))
ax = plt.subplot(111, projection='polar')
ax.plot(theta, r)
""",
    
    "radar_chart": """
categories = ['A', 'B', 'C', 'D', 'E']
values = [4, 3, 5, 2, 4]
angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
values += values[:1]
angles += angles[:1]
ax = plt.subplot(111, polar=True)
ax.plot(angles, values, 'o-', linewidth=2)
ax.fill(angles, values, alpha=0.25)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories)
""",
    
    # ==================== 3D PLOTS ====================
    "3d_scatter": """
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(x, y, z, c=colors, cmap='viridis', s=50)
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
""",
    
    "3d_line": """
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(x, y, z, linewidth=2)
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
""",
    
    "3d_surface": """
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
fig.colorbar(surf, label='Z values')
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
""",
    
    "3d_wireframe": """
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_wireframe(X, Y, Z, color='black', linewidth=0.5)
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
""",
    
    "3d_bar": """
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.bar3d(x, y, z, dx, dy, dz, color='steelblue')
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
""",
    
    # ==================== TEXT AND ANNOTATIONS ====================
    "text_annotation": """
plt.plot(x, y)
plt.text(x_pos, y_pos, 'Important Point', fontsize=12, 
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
""",
    
    "arrow_annotation": """
plt.plot(x, y)
plt.annotate('Peak', xy=(x_peak, y_peak), xytext=(x_text, y_text),
             arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3', lw=2),
             fontsize=12, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
""",
    
    "math_text": """
plt.plot(x, y)
plt.title(r'$y = \\sin(2\\pi x) \\cdot e^{-x}$', fontsize=16)
plt.xlabel(r'$x$ (meters)', fontsize=14)
plt.ylabel(r'$f(x) = \\alpha \\beta$', fontsize=14)
""",
    
    # ==================== ERROR BARS ====================
    "errorbar_basic": """
plt.errorbar(x, y, yerr=errors, fmt='o-', capsize=5, capthick=2, label='Data')
plt.legend()
""",
    
    "errorbar_asymmetric": """
plt.errorbar(x, y, yerr=[lower_errors, upper_errors], fmt='s-', capsize=5)
""",
    
    "errorbar_with_fill": """
plt.plot(x, y, 'b-', label='Mean')
plt.fill_between(x, y - std, y + std, alpha=0.3, label='±1σ')
plt.errorbar(x[::5], y[::5], yerr=std[::5], fmt='o', capsize=5, label='Error bars')
plt.legend()
""",
    
    # ==================== TIME SERIES ====================
    "time_series": """
plt.plot(dates, values)
plt.gcf().autofmt_xdate()  # Rotate and align date labels
plt.xlabel('Date'); plt.ylabel('Value')
plt.title('Time Series Data')
""",
    
    "time_series_multiple": """
for column in df.columns:
    plt.plot(df.index, df[column], label=column, linewidth=2)
plt.legend()
plt.gcf().autofmt_xdate()
""",
    
    # ==================== SPECIALTY PLOTS ====================
    "sankey_diagram": """
from matplotlib.sankey import Sankey
sankey = Sankey()
sankey.add(flows=[0.25, 0.15, 0.60, -0.20, -0.15, -0.05, -0.50, -0.10],
           labels=['', '', '', 'First', 'Second', 'Third', 'Fourth', 'Fifth'],
           orientations=[-1, 1, 0, 1, 1, 1, 0, -1])
sankey.finish()
""",
    
    "broken_axis": """
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
ax1.plot(x, y)
ax2.plot(x, y)
ax1.set_ylim(80, 100)  # Outliers
ax2.set_ylim(0, 20)    # Most of the data
ax1.spines['bottom'].set_visible(False)
ax2.spines['top'].set_visible(False)
""",
    
    "table": """
fig, ax = plt.subplots()
ax.axis('tight')
ax.axis('off')
table_data = [['A', 1, 2], ['B', 3, 4], ['C', 5, 6]]
table = ax.table(cellText=table_data, colLabels=['Col1', 'Col2', 'Col3'],
                 loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
""",
    
    # ==================== STYLING ====================
    "style_seaborn": """
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['legend.fontsize'] = 11
plt.rcParams['figure.dpi'] = 300
""",
    
    "custom_colors": """
# Colorblind-friendly palette
colors = ['#0173B2', '#DE8F05', '#029E73', '#CC78BC', '#CA9161', '#949494']
for i, color in enumerate(colors):
    plt.plot(x, y + i, color=color, label=f'Line {i+1}', linewidth=2)
plt.legend()
""",
    
    "custom_colormap": """
from matplotlib.colors import LinearSegmentedColormap
colors_list = ['blue', 'white', 'red']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('custom', colors_list, N=n_bins)
plt.imshow(data, cmap=cmap)
plt.colorbar()
""",
}

def get_examples_prompt():
    """Generate a comprehensive examples reference for the LLM"""
    return """
### Comprehensive Matplotlib Gallery Reference

You have access to ALL Matplotlib capabilities from the official gallery (https://matplotlib.org/stable/gallery/index.html):

**Lines, Bars & Markers**:
- Line plots (single/multiple, styled with markers, colors, linestyles)
- Scatter plots (with colors, sizes, transparency, colormaps)
- Bar charts (vertical/horizontal, grouped, stacked)
- Stem plots, step plots, fill_between

**Statistical Plots**:
- Histograms (single/multiple, custom bins)
- Box plots, violin plots (use seaborn)
- KDE plots, hexbin, 2D histograms

**Images, Contours & Fields**:
- Heatmaps (imshow, seaborn heatmap with annotations)
- Contour plots (filled/unfilled, with levels)
- Vector fields (quiver, streamplot)

**Subplots & Layouts**:
- Multiple plots in grids (2x2, custom GridSpec)
- Shared axes, inset axes
- Complex layouts with different sizes

**Pie & Polar Charts**:
- Pie charts (basic, exploded, donut)
- Polar plots, radar charts

**3D Plots** (use `from mpl_toolkits.mplot3d import Axes3D`):
- 3D scatter, line, surface, wireframe, bar plots

**Text & Annotations**:
- Text boxes, arrows, mathematical notation (LaTeX)
- Annotations with custom styling

**Error Bars**:
- Symmetric/asymmetric error bars
- Fill_between for confidence intervals

**Time Series**:
- Date-aware plotting with proper formatting
- Multiple time series with legends

**Specialty Plots**:
- Sankey diagrams, broken axes, tables
- Custom colormaps and styles

**Styling Best Practices**:
- Use `plt.style.use('seaborn-v0_8-whitegrid')` or similar
- Set font sizes: `plt.rcParams['font.size'] = 12`
- Use colorblind-friendly palettes: `['#0173B2', '#DE8F05', '#029E73', '#CC78BC']`
- Add `plt.tight_layout()` for clean spacing
- Set DPI for quality: `plt.rcParams['figure.dpi'] = 300`

**Important Notes**:
- For categorical colors in scatter: use `pd.Categorical(df['column']).codes`
- For 3D plots: `from mpl_toolkits.mplot3d import Axes3D`
- For seaborn: `import seaborn as sns` (already available)
- Never use `plt.show()` - it's automatically handled
"""
