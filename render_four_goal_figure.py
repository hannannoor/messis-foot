"""Plot aggregate results only; never read provided match media or labels."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent.parent
external=json.loads((root/'external-reference/reports/final-heldout.json').read_text())
local=json.loads((root/'analysis/tactical-validated/tactical_report.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(11,4.7))
fig.patch.set_facecolor('#fafafa')
colors=['#9aa7b3','#176b87']
labels=['Baseline','Frozen candidate']
for j,kind in enumerate(('baseline','selected')):
    values=[external['matches'][m]['natural'][kind]['metrics']['spell_f1_mean'] for m in ('J03WR9','J03WN1')]
    positions=[i+(j-.5)*.34 for i in range(2)]
    bars=axes[0].bar(positions,values,.32,label=labels[j],color=colors[j])
    axes[0].bar_label(bars,fmt='%.3f',padding=4,fontsize=10)
axes[0].set_xticks([0,1],['J03WR9','J03WN1'])
axes[0].set_ylim(0,.65)
axes[0].set_ylabel('Official spellF1 (higher is better)')
axes[0].set_title('External provider-reference tests',loc='left',fontweight='bold')
axes[0].legend(frameon=False,fontsize=9,loc='upper left')
values=[100*local[k]['labels']['X']/local[k]['active_frames'] for k in ('before','after')]
bars=axes[1].bar(labels,values,.55,color=colors)
axes[1].bar_label(bars,fmt='%.2f%%',padding=5,fontsize=11)
axes[1].set_ylim(0,85)
axes[1].set_ylabel('Undecided frames (%)')
axes[1].set_title('Local coverage: correctness unmeasured',loc='left',fontweight='bold')
for ax in axes:
    ax.spines[['top','right']].set_visible(False)
    ax.yaxis.grid(True,alpha=.15)
    ax.set_axisbelow(True)
fig.suptitle('More assignments; independent quality validation still needed',x=.06,ha='left',fontsize=15,fontweight='bold')
fig.text(.06,.03,'External inactive coordinates are usually frozen, which may inflate stoppage results.\nTeam-only spellF1 slightly regressed on both tests. No challenge video or ground truth was used.',fontsize=10,color='#5b3c25')
fig.subplots_adjust(left=.07,right=.98,top=.79,bottom=.24,wspace=.37)
destination=root/'analysis/tactical-validation-overview.png'
fig.savefig(destination,dpi=170,facecolor=fig.get_facecolor())
print(destination)
