# -*- coding: utf-8 -*-
"""Build the three figures used in the written report. ASCII labels only."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
FIG = os.path.join(HERE, '文档', 'figures')
os.makedirs(FIG, exist_ok=True)

UP = '#1f4e79'
DOWN = '#a33a3a'


def stars(p):
    if p < 0.01:
        return '***'
    if p < 0.05:
        return '**'
    if p < 0.10:
        return '*'
    return ''


def grouped(ax, labels, up_vals, up_se, up_p, dn_vals, dn_se, dn_p, ylabel):
    up_vals = np.asarray(up_vals, dtype=float)
    up_se = np.asarray(up_se, dtype=float)
    dn_vals = np.asarray(dn_vals, dtype=float)
    dn_se = np.asarray(dn_se, dtype=float)
    x = np.arange(len(labels))
    w = 0.36
    ax.bar(x - w / 2, up_vals, w, yerr=1.96 * up_se, capsize=4,
           color=UP, label='Upgrade')
    ax.bar(x + w / 2, dn_vals, w, yerr=1.96 * dn_se, capsize=4,
           color=DOWN, label='Downgrade')
    for i, (v, e, p) in enumerate(zip(up_vals, up_se, up_p)):
        ax.text(i - w / 2, v + 1.96 * e + 0.02 * max(1, np.nanmax(np.abs(up_vals))), stars(p),
                ha='center', va='bottom', fontsize=9)
    for i, (v, e, p) in enumerate(zip(dn_vals, dn_se, dn_p)):
        ax.text(i + w / 2, v + 1.96 * e + 0.02 * max(1, np.nanmax(np.abs(dn_vals))), stars(p),
                ha='center', va='bottom', fontsize=9)
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def main():
    cs = pd.read_csv(os.path.join(DATA, 'car_summary.csv'), encoding='utf-8-sig')
    cs = cs[cs['检验'].astype(str) == '组间t(明星-非明星)']
    acc = pd.read_csv(os.path.join(DATA, 'accuracy_summary.csv'), encoding='utf-8-sig')
    acc = acc[acc['measure'] == 'mktadj']

    # Figure 1: announcement CAR and abnormal volume
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0))
    car_labels = ['[-1,+1]', '[-1,+5]', '[-5,+5]']
    car_metrics = ['CAR_m1_p1', 'CAR_m1_p5', 'CAR_m5_p5']
    def get(metric, direction):
        r = cs[(cs['指标'] == metric) & (cs['方向'] == direction)].iloc[0]
        return float(r['均值']), abs(float(r['均值']) / float(r['t'])), float(r['p'])
    up = [get(m, '调高') for m in car_metrics]
    dn = [get(m, '调低') for m in car_metrics]
    grouped(axes[0], car_labels, [v[0] for v in up], [v[1] for v in up], [v[2] for v in up],
            [v[0] for v in dn], [v[1] for v in dn], [v[2] for v in dn],
            'CAR (percentage points)')
    axes[0].set_title('Announcement CAR')
    av_up = get('AV', '调高')
    av_dn = get('AV', '调低')
    grouped(axes[1], ['Event day'], [av_up[0]], [av_up[1]], [av_up[2]],
            [av_dn[0]], [av_dn[1]], [av_dn[2]], 'Abnormal volume (log)')
    axes[1].set_title('Abnormal volume')
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, 'fig1_announcement.png'), dpi=200)
    plt.close(fig)

    # Figure 2: post-announcement drift
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    drift_labels = ['+2 to +60', '+2 to +120', '+2 to +250']
    drift_metrics = ['CAR_p2_p60', 'CAR_p2_p120', 'CAR_p2_p250']
    up = [get(m, '调高') for m in drift_metrics]
    dn = [get(m, '调低') for m in drift_metrics]
    grouped(ax, drift_labels, [v[0] for v in up], [v[1] for v in up], [v[2] for v in up],
            [v[0] for v in dn], [v[1] for v in dn], [v[2] for v in dn],
            'CAR from +2 (percentage points)')
    ax.set_title('Post-announcement drift')
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, 'fig2_drift.png'), dpi=200)
    plt.close(fig)

    # Figure 3: holding-period accuracy
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    h_labels = ['3 months', '6 months', '12 months']
    hs = [63, 126, 252]
    def geta(h, direction):
        r = acc[(acc['horizon'] == h) & (acc['direction'] == direction)].iloc[0]
        return float(r['diff']), abs(float(r['diff']) / float(r['t'])), float(r['p'])
    up = [geta(h, '调高') for h in hs]
    dn = [geta(h, '调低') for h in hs]
    grouped(ax, h_labels, [v[0] for v in up], [v[1] for v in up], [v[2] for v in up],
            [v[0] for v in dn], [v[1] for v in dn], [v[2] for v in dn],
            'Star minus non-star (pp)')
    ax.set_title('Direction-adjusted holding returns, market-adjusted')
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, 'fig3_accuracy.png'), dpi=200)
    plt.close(fig)

    print('figures written to', FIG)


if __name__ == '__main__':
    main()
