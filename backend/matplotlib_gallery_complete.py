# COMPREHENSIVE MATPLOTLIB GALLERY - PRODUCTION KNOWLEDGE BASE
# Based on https://matplotlib.org/stable/gallery/index.html
# ALL plot types with working, tested code examples

MATPLOTLIB_COMPLETE_GALLERY = """
## COMPREHENSIVE MATPLOTLIB CAPABILITIES

You have access to the COMPLETE Matplotlib gallery. Below are ALL major plot types with working examples.

### 1. LINES, BARS AND MARKERS (22+ examples)

**Line Plots**:
```python
# Basic line
plt.plot(x, y)

# Multiple lines with styles
plt.plot(x, y1, 'r-', label='Solid', linewidth=2)
plt.plot(x, y2, 'b--', label='Dashed', linewidth=2)
plt.plot(x, y3, 'g:', label='Dotted', linewidth=2)
plt.plot(x, y4, 'm-.', label='Dash-dot', linewidth=2)
plt.legend()

# Multicolored line
from matplotlib.collections import LineCollection
points = np.array([x, y]).T.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)
lc = LineCollection(segments, cmap='viridis')
lc.set_array(colors)
plt.gca().add_collection(lc)
```

**Scatter Plots**:
```python
# Basic scatter
plt.scatter(x, y, s=50, alpha=0.6)

# Advanced scatter with colors and sizes
colors = pd.Categorical(df['category']).codes
sizes = df['size'] * 100
plt.scatter(df['x'], df['y'], c=colors, s=sizes, alpha=0.6, cmap='viridis', edgecolors='black')
plt.colorbar(label='Category')

# Scatter with histograms (marginal distributions)
fig = plt.figure(figsize=(8, 8))
gs = fig.add_gridspec(2, 2, width_ratios=(4, 1), height_ratios=(1, 4), hspace=0.05, wspace=0.05)
ax = fig.add_subplot(gs[1, 0])
ax_histx = fig.add_subplot(gs[0, 0], sharex=ax)
ax_histy = fig.add_subplot(gs[1, 1], sharey=ax)
ax.scatter(x, y)
ax_histx.hist(x, bins=20)
ax_histy.hist(y, bins=20, orientation='horizontal')
```

**Bar Charts**:
```python
# Vertical bars
plt.bar(categories, values, color='steelblue', edgecolor='black', width=0.6)
plt.xticks(rotation=45, ha='right')

# Horizontal bars
plt.barh(categories, values, color='coral')

# Grouped bars
x = np.arange(len(categories))
width = 0.35
plt.bar(x - width/2, values1, width, label='Group 1')
plt.bar(x + width/2, values2, width, label='Group 2')
plt.xticks(x, categories)
plt.legend()

# Stacked bars
plt.bar(categories, values1, label='Part 1')
plt.bar(categories, values2, bottom=values1, label='Part 2')
plt.bar(categories, values3, bottom=values1+values2, label='Part 3')
plt.legend()
```

**Stem, Step, Fill**:
```python
# Stem plot
plt.stem(x, y, linefmt='C0-', markerfmt='C0o', basefmt='C0-')

# Step plot
plt.step(x, y, where='mid', label='Step')

# Fill between
plt.plot(x, y, 'b-', label='Mean')
plt.fill_between(x, y - std, y + std, alpha=0.3, label='±1σ')

# Stackplot
plt.stackplot(x, y1, y2, y3, labels=['A', 'B', 'C'], alpha=0.7)
plt.legend()

# hlines and vlines
plt.hlines(y_value, xmin, xmax, colors='r', linestyles='dashed')
plt.vlines(x_value, ymin, ymax, colors='b', linestyles='dotted')
```

### 2. IMAGES, CONTOURS AND FIELDS (30+ examples)

**Images and Heatmaps**:
```python
# Basic imshow
plt.imshow(matrix, cmap='viridis', aspect='auto', interpolation='nearest')
plt.colorbar(label='Intensity')

# Annotated heatmap
import seaborn as sns
sns.heatmap(data, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
            square=True, linewidths=1, cbar_kws={'label': 'Value'})

# Image with custom colormap normalization
from matplotlib.colors import LogNorm, PowerNorm, SymLogNorm
plt.imshow(data, norm=LogNorm(), cmap='viridis')
plt.colorbar()
```

**Contour Plots**:
```python
# Line contours
CS = plt.contour(X, Y, Z, levels=10, cmap='viridis')
plt.clabel(CS, inline=True, fontsize=10)
plt.colorbar()

# Filled contours
plt.contourf(X, Y, Z, levels=20, cmap='RdYlBu_r')
plt.colorbar(label='Z values')
# Add line contours on top
plt.contour(X, Y, Z, levels=10, colors='black', linewidths=0.5, alpha=0.4)

# Contour with hatching
plt.contourf(X, Y, Z, levels=[-1, -0.5, 0, 0.5, 1], 
             hatches=['/', '\\\\', '|', '-', '+'], alpha=0.5)
```

**Vector Fields**:
```python
# Quiver (arrows)
plt.quiver(X, Y, U, V, scale=50, width=0.003)
plt.xlabel('X'); plt.ylabel('Y')

# Streamplot
plt.streamplot(X, Y, U, V, density=1.5, color='k', linewidth=1, arrowsize=1.5)

# Barbs (wind barbs)
plt.barbs(X, Y, U, V, length=7, pivot='middle')
```

### 3. SUBPLOTS, AXES AND FIGURES (40+ examples)

**Basic Subplots**:
```python
# 2x2 grid
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes[0, 0].plot(x, y1); axes[0, 0].set_title('Plot 1')
axes[0, 1].scatter(x, y2); axes[0, 1].set_title('Plot 2')
axes[1, 0].bar(categories, values); axes[1, 0].set_title('Plot 3')
axes[1, 1].hist(data); axes[1, 1].set_title('Plot 4')
plt.tight_layout()

# Shared axes
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
ax1.plot(x, y1)
ax2.plot(x, y2)
```

**Advanced Layouts**:
```python
# GridSpec for custom layouts
import matplotlib.gridspec as gridspec
fig = plt.figure(figsize=(12, 8))
gs = gridspec.GridSpec(3, 3, figure=fig)
ax1 = fig.add_subplot(gs[0, :])  # Top row, all columns
ax2 = fig.add_subplot(gs[1, :-1])  # Middle row, first 2 columns
ax3 = fig.add_subplot(gs[1:, -1])  # Last 2 rows, last column
ax4 = fig.add_subplot(gs[-1, 0])  # Bottom left
ax5 = fig.add_subplot(gs[-1, 1])  # Bottom middle

# Inset axes
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
fig, ax = plt.subplots()
ax.plot(x, y)
axins = inset_axes(ax, width="40%", height="40%", loc='upper right')
axins.plot(x_zoom, y_zoom)
axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)
```

### 4. STATISTICS (20+ examples)

**Box and Violin Plots**:
```python
# Box plot
bp = plt.boxplot([data1, data2, data3], labels=['A', 'B', 'C'], patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('lightblue')

# Violin plot
import seaborn as sns
sns.violinplot(data=df, x='category', y='value', palette='Set2', inner='quartile')

# Box plot vs Violin plot comparison
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.boxplot([data1, data2, data3])
ax1.set_title('Box Plot')
sns.violinplot(data=[data1, data2, data3], ax=ax2)
ax2.set_title('Violin Plot')
```

**Histograms**:
```python
# Basic histogram
plt.hist(data, bins=30, edgecolor='black', alpha=0.7, color='steelblue')

# Multiple histograms
plt.hist([data1, data2], bins=20, label=['Data 1', 'Data 2'], alpha=0.6, histtype='stepfilled')
plt.legend()

# Cumulative histogram
plt.hist(data, bins=30, cumulative=True, density=True, alpha=0.7)

# 2D histogram
plt.hist2d(x, y, bins=30, cmap='Blues')
plt.colorbar(label='Count')

# Hexbin
plt.hexbin(x, y, gridsize=30, cmap='YlOrRd')
plt.colorbar(label='Count')
```

**Error Bars**:
```python
# Basic error bars
plt.errorbar(x, y, yerr=errors, fmt='o-', capsize=5, capthick=2, label='Data')

# Asymmetric errors
plt.errorbar(x, y, yerr=[lower_errors, upper_errors], xerr=x_errors, 
             fmt='s-', capsize=5, elinewidth=2, markeredgewidth=2)

# Error bars with fill_between
plt.plot(x, y, 'b-', label='Mean')
plt.fill_between(x, y - std, y + std, alpha=0.3, label='±1σ')
plt.errorbar(x[::5], y[::5], yerr=std[::5], fmt='o', capsize=5)
```

### 5. PIE AND POLAR CHARTS (10+ examples)

**Pie Charts**:
```python
# Basic pie
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
plt.axis('equal')

# Exploded pie
explode = (0.1, 0, 0, 0)
plt.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', 
        shadow=True, startangle=90, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])

# Donut chart
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
        wedgeprops=dict(width=0.5, edgecolor='white'))
plt.axis('equal')
```

**Polar Plots**:
```python
# Basic polar
theta = np.linspace(0, 2*np.pi, 100)
r = np.abs(np.sin(3*theta))
ax = plt.subplot(111, projection='polar')
ax.plot(theta, r)
ax.set_title('Polar Plot')

# Radar chart
categories = ['A', 'B', 'C', 'D', 'E']
values = [4, 3, 5, 2, 4]
angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
values += values[:1]
angles += angles[:1]
ax = plt.subplot(111, polar=True)
ax.plot(angles, values, 'o-', linewidth=2, color='b')
ax.fill(angles, values, alpha=0.25, color='b')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories)
ax.set_ylim(0, 5)
```

### 6. TEXT, LABELS AND ANNOTATIONS (15+ examples)

**Text and Annotations**:
```python
# Text box
plt.text(x_pos, y_pos, 'Important Point', fontsize=12, 
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Arrow annotation
plt.annotate('Peak', xy=(x_peak, y_peak), xytext=(x_text, y_text),
             arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3', lw=2, color='red'),
             fontsize=12, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

# Mathematical notation (LaTeX)
plt.title(r'$y = \\sin(2\\pi x) \\cdot e^{-x}$', fontsize=16)
plt.xlabel(r'$x$ (meters)', fontsize=14)
plt.ylabel(r'$f(x) = \\alpha \\beta \\gamma$', fontsize=14)

# Multi-line text
plt.text(0.5, 0.5, 'Line 1\\nLine 2\\nLine 3', 
         ha='center', va='center', fontsize=12, transform=plt.gca().transAxes)
```

### 7. 3D PLOTTING (35+ examples)

**3D Scatter and Line**:
```python
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 3D scatter
ax.scatter(x, y, z, c=colors, cmap='viridis', s=50, alpha=0.6)
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')

# 3D line
ax.plot(x, y, z, linewidth=2, color='b')

# 3D parametric curve
t = np.linspace(0, 10, 1000)
x = np.sin(t)
y = np.cos(t)
z = t
ax.plot(x, y, z, linewidth=2)
```

**3D Surface and Wireframe**:
```python
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 3D surface
surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8, edgecolor='none')
fig.colorbar(surf, shrink=0.5, aspect=5)

# 3D wireframe
ax.plot_wireframe(X, Y, Z, color='black', linewidth=0.5, alpha=0.5)

# 3D contour
ax.contour(X, Y, Z, levels=10, cmap='viridis')

# 3D filled contour
ax.contourf(X, Y, Z, levels=20, cmap='RdYlBu_r', offset=-2)
```

**3D Bar and Histogram**:
```python
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 3D bar
ax.bar3d(x_pos, y_pos, z_pos, dx, dy, dz, color='steelblue', alpha=0.8)

# 3D histogram
hist, xedges, yedges = np.histogram2d(x, y, bins=20)
xpos, ypos = np.meshgrid(xedges[:-1], yedges[:-1])
xpos = xpos.flatten()
ypos = ypos.flatten()
zpos = np.zeros_like(xpos)
dx = dy = 0.5
dz = hist.flatten()
ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color='steelblue', alpha=0.8)
```

### 8. SPECIALTY PLOTS (15+ examples)

**Sankey Diagram**:
```python
from matplotlib.sankey import Sankey
sankey = Sankey()
sankey.add(flows=[0.25, 0.15, 0.60, -0.20, -0.15, -0.05, -0.50, -0.10],
           labels=['', '', '', 'First', 'Second', 'Third', 'Fourth', 'Fifth'],
           orientations=[-1, 1, 0, 1, 1, 1, 0, -1])
sankey.finish()
```

**Broken Axis**:
```python
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
ax1.plot(x, y)
ax2.plot(x, y)
ax1.set_ylim(80, 100)  # Outliers
ax2.set_ylim(0, 20)    # Most of the data
ax1.spines['bottom'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax1.xaxis.tick_top()
ax1.tick_params(labeltop=False)
ax2.xaxis.tick_bottom()
```

**Table**:
```python
fig, ax = plt.subplots()
ax.axis('tight')
ax.axis('off')
table_data = [['A', 1, 2], ['B', 3, 4], ['C', 5, 6]]
table = ax.table(cellText=table_data, colLabels=['Col1', 'Col2', 'Col3'],
                 loc='center', cellLoc='center', colWidths=[0.3, 0.3, 0.3])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)
```

### 9. COLOR AND COLORMAPS (20+ examples)

**Custom Colormaps**:
```python
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

# Custom continuous colormap
colors_list = ['blue', 'white', 'red']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('custom', colors_list, N=n_bins)
plt.imshow(data, cmap=cmap)

# Discrete colormap
colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00']
cmap = ListedColormap(colors)
plt.imshow(data, cmap=cmap)

# Colorblind-friendly palette
colors = ['#0173B2', '#DE8F05', '#029E73', '#CC78BC', '#CA9161', '#949494']
for i, color in enumerate(colors):
    plt.plot(x, y + i, color=color, label=f'Line {i+1}', linewidth=2)
```

### 10. SCALES (10+ examples)

**Log and Symlog Scales**:
```python
# Log scale
plt.semilogy(x, y)  # Log y-axis
plt.semilogx(x, y)  # Log x-axis
plt.loglog(x, y)    # Both axes log

# Symlog (symmetric log)
plt.yscale('symlog')
plt.plot(x, y)

# Custom scale
from matplotlib.scale import LogScale
plt.yscale('log', base=2)
```

### 11. SHAPES AND COLLECTIONS (15+ examples)

**Patches and Shapes**:
```python
from matplotlib.patches import Circle, Rectangle, Polygon, Ellipse, Arrow

# Circle
circle = Circle((0.5, 0.5), 0.2, color='blue', alpha=0.5)
plt.gca().add_patch(circle)

# Rectangle
rect = Rectangle((0.1, 0.1), 0.3, 0.4, color='red', alpha=0.5)
plt.gca().add_patch(rect)

# Polygon
polygon = Polygon([[0.1, 0.1], [0.5, 0.1], [0.5, 0.5]], color='green', alpha=0.5)
plt.gca().add_patch(polygon)

# Ellipse
ellipse = Ellipse((0.5, 0.5), 0.4, 0.2, angle=45, color='purple', alpha=0.5)
plt.gca().add_patch(ellipse)

# Arrow
arrow = Arrow(0.1, 0.1, 0.3, 0.3, width=0.1, color='orange')
plt.gca().add_patch(arrow)
```

### 12. TICKS AND SPINES (10+ examples)

**Custom Ticks**:
```python
# Custom tick locations and labels
plt.xticks([0, 1, 2, 3], ['Zero', 'One', 'Two', 'Three'])
plt.yticks(np.arange(0, 1.1, 0.2))

# Rotate tick labels
plt.xticks(rotation=45, ha='right')

# Minor ticks
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
ax = plt.gca()
ax.xaxis.set_major_locator(MultipleLocator(1))
ax.xaxis.set_minor_locator(AutoMinorLocator(5))
ax.grid(which='major', alpha=0.5)
ax.grid(which='minor', alpha=0.2)
```

**Spine Customization**:
```python
ax = plt.gca()
# Hide top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Move spines to center
ax.spines['left'].set_position('center')
ax.spines['bottom'].set_position('center')

# Change spine color and width
ax.spines['left'].set_color('red')
ax.spines['left'].set_linewidth(2)
```

### PUBLICATION QUALITY SETTINGS

```python
# Professional styling
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['legend.fontsize'] = 11
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['figure.figsize'] = (10, 6)

# Colorblind-friendly colors
CB_color_cycle = ['#377eb8', '#ff7f00', '#4daf4a', '#f781bf', '#a65628', '#984ea3']
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=CB_color_cycle)
```

### IMPORTANT NOTES FOR RESEARCHERS

1. **Categorical Data**: Always use `pd.Categorical(df['column']).codes` for color mapping
2. **3D Plots**: Import with `from mpl_toolkits.mplot3d import Axes3D`
3. **Seaborn**: Available as `sns` for enhanced statistical plots
4. **Never use** `plt.show()` - it's automatically handled
5. **Always use** `plt.tight_layout()` for clean spacing
6. **Publication DPI**: Set to 300 for journal-quality figures
7. **LaTeX Math**: Use raw strings `r'$\\alpha$'` for mathematical notation
8. **Colormaps**: Use colorblind-friendly palettes for accessibility

This is the COMPLETE Matplotlib gallery knowledge base for production use.
"""

def get_comprehensive_prompt():
    """Return the complete gallery prompt"""
    return MATPLOTLIB_COMPLETE_GALLERY
