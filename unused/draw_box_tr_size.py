import numpy as np
import matplotlib
from matplotlib.lines import Line2D

matplotlib.use("agg")
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd

# plt.style.use('seaborn')


fig, ax = plt.subplots(figsize=(10, 5))

df = pd.read_csv("../final_result.tsv", sep="\t")

df_long = pd.melt(df, "Training set size", var_name="Methods", value_name="PCC")
# plt.style.use('seaborn-whitegrid')
# sns.set(style="whitegrid")
sns.boxplot(x="Training set size", hue="Methods", y="PCC", data=df_long, ax=ax, palette="Set2", fliersize=0)
sns.stripplot(x="Training set size", hue="Methods", y="PCC", data=df_long, ax=ax,
              jitter=0.1, palette="Set2", dodge=True, linewidth=1, size=5)
plt.axhline(y=0.281487788960181, color='brown', linestyle='--')
# sns.barplot(x="Training set size", hue="Methods", y="PCC", data=df_long, palette="Set2", saturation=0.5, linewidth=1, edgecolor="0.2", ax=ax)
# # Shrink current axis by 20%
# box = ax.get_position()
# ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
#
# # Put a legend to the right of the current axis
# ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

handles, labels = ax.get_legend_handles_labels()
labels[1] = "Baseline"
handles[1] = Line2D([0], [0], color='brown', linewidth=3, linestyle='dashed')
# When creating the legend, only use the first two elements
# to effectively remove the last two.
l = plt.legend(handles, labels)

plt.savefig("box.png")
