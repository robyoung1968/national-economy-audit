import json
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker

# 1. Ingest Data directly from your workspace
with open('annual_data.json', 'r') as f:
    data = json.load(f)

# Filter for the macro 2009-2026 timeline and sort chronologically
processed_data = [row for row in data if int(row['year']) >= 2009]
processed_data.sort(key=lambda row: int(row['year']))

years = [row['year'] for row in processed_data]
# Convert Billions to Trillions for cleaner macro scaling numbers
gdp_trillions = [row['gdp_nominal'] / 1000 for row in processed_data]

# 2. Establish Palette Theme Continuity (Matches annual.html and trade matrix styles)
bg_color = '#0f172a'       # Deep Slate Canvas
card_bg = '#1e293b'        # Darker Card Containers
text_main = '#f8fafc'      # Bright text
text_muted = '#94a3b8'     # Slate gray text
accent_blue = '#38bdf8'    # Sky Blue Accent Line

# 3. Initialize Figure Workspace
fig, ax = plt.subplots(figsize=(12, 6.5))
fig.patch.set_facecolor(bg_color)
ax.set_facecolor(card_bg)

# Configure background subtle grid
ax.grid(color='#334155', linestyle='--', linewidth=0.5, alpha=0.3, zorder=0)

# 4. Plot Area Chart Elements
# Plot the primary line
ax.plot(years, gdp_trillions, color=accent_blue, linewidth=3, marker='o', markersize=6, label='Nominal GDP', zorder=3)

# Fill the area underneath the line for the modern area chart aesthetic
ax.fill_between(years, gdp_trillions, color=accent_blue, alpha=0.1, zorder=2)

# 5. Apply Axis Layout Formatting
ax.set_xticklabels(years, color=text_muted, rotation=45, fontsize=10.5)
ax.tick_params(colors=text_muted)

ax.set_title('Nominal Gross Domestic Product Trend (2009–2026)', color=text_main, fontsize=14, pad=20, weight='bold')
ax.set_ylabel('Trillions of Dollars (USD)', color=text_muted, fontsize=11, labelpad=12)

# Custom currency formatter for the Y-axis ticks to show Trillions cleanly
def trillion_format(x, pos):
    return f'${x:,.1f}T'
ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(trillion_format))

# Give slight breathing room at the top of the scale
ax.set_ylim(min(gdp_trillions) - 2, max(gdp_trillions) + 2)

# Remove harsh borders, keep slate bounds
for spine in ax.spines.values():
    spine.set_color('#334155')

# Tighten layout and render
plt.tight_layout()
plt.show()