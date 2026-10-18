# -*- coding: utf-8 -*-
"""Build the three result figures used in the slide deck. ASCII labels only."""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
OUT = os.path.join(HERE, '文档', 'figures', 'ppt')
os.makedirs(OUT, exist_ok=True)

NAVY = '#1F2A44'
RUST = '#B23A2B'
GRAY = '#6B7280'


def stars(p):
    if p < 0.01:
        return '***'
    if p < 0.05:
        return '**'
    if p < 0.10:
        return '*'
    return ''


def style_axis(ax, ylabel, labels):
    ax.axhline(0, color=NAVY, linewidth=0.9)
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, fontsize=16)
    ax.set_ylabel(ylabel, fontsize=16, labelpad=8)
    ax.tick_params(axis='both', labelsize=16, length=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRAY)
    ax.spines['bottom'].set_color(GRAY)
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.legend(frameon=False, fontsize=15, loc='upper center',
              ncol=2, bbox_to_anchor=(0.5, 1.08), handlelength=1.2)


def grouped(ax, labels, up, dn, ylabel):
    up_vals = np.array([v[0] for v in up], dtype=float)
    up_se = np.array([v[1] for v in up], dtype=float)
    up_p = np.array([v[2] for v in up], dtype=float)
    dn_vals = np.array([v[0] for v in dn], dtype=float)
    dn_se = np.array([v[1] for v in dn], dtype=float)
    dn_p = np.array([v[2] for v in dn], dtype=float)

    x = np.arange(len(labels))
    w = 0.34
    ax.bar(x - w / 2, up_vals, w, yerr=1.96 * up_se, capsize=3,
           color=NAVY, label='Upgrade', error_kw={'elinewidth': 1, 'ecolor': NAVY})
    ax.bar(x + w / 2, dn_vals, w, yerr=1.96 * dn_se, capsize=3,
           color=RUST, label='Downgrade', error_kw={'elinewidth': 1, 'ecolor': RUST})

    span = max(np.nanmax(np.abs(up_vals)), np.nanmax(np.abs(dn_vals)), 0.1)
    offset = 0.06 * span
    for xi, v, se, p in zip(x - w / 2, up_vals, up_se, up_p):
        y = v + 1.96 * se if v >= 0 else v - 1.96 * se
        va = 'bottom' if v >= 0 else 'top'
        ax.text(xi, y + (offset if v >= 0 else -offset), f'{v:+.2f}',
                ha='center', va=va, fontsize=13.5, color=NAVY, fontweight='bold')
    for xi, v, se, p in zip(x + w / 2, dn_vals, dn_se, dn_p):
        y = v + 1.96 * se if v >= 0 else v - 1.96 * se
        va = 'bottom' if v >= 0 else 'top'
        ax.text(xi, y + (offset if v >= 0 else -offset), f'{v:+.2f}',
                ha='center', va=va, fontsize=13.5, color=RUST, fontweight='bold')

    style_axis(ax, ylabel, labels)
    ymax = max(np.nanmax(up_vals + 1.96 * up_se), np.nanmax(dn_vals + 1.96 * dn_se))
    ymin = min(np.nanmin(up_vals - 1.96 * up_se), np.nanmin(dn_vals - 1.96 * dn_se))
    pad = 0.28 * (ymax - ymin if ymax > ymin else 1.0)
    ax.set_ylim(ymin - pad, ymax + pad)


def main():
    plt.rcParams.update({
        'font.family': 'Times New Roman',
        'font.size': 16,
        'text.color': NAVY,
        'axes.labelcolor': NAVY,
        'xtick.color': NAVY,
        'ytick.color': NAVY,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
    })

    cs = pd.read_csv(os.path.join(DATA, 'car_summary.csv'), encoding='utf-8-sig')
    cs = cs[cs['检验'].astype(str) == '组间t(明星-非明星)']
    acc = pd.read_csv(os.path.join(DATA, 'accuracy_summary.csv'), encoding='utf-8-sig')
    acc = acc[acc['measure'] == 'mktadj']

    def get(metric, direction):
        r = cs[(cs['指标'] == metric) & (cs['方向'] == direction)].iloc[0]
        mean = float(r['均值'])
        t = float(r['t'])
        return mean, abs(mean / t), float(r['p'])

    def geta(h, direction):
        r = acc[(acc['horizon'] == h) & (acc['direction'] == direction)].iloc[0]
        diff = float(r['diff'])
        t = float(r['t'])
        return diff, abs(diff / t), float(r['p'])

    # Figure 1: announcement CAR, differences only.
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    labels = ['[-1,+1]', '[-1,+5]', '[-5,+5]']
    metrics = ['CAR_m1_p1', 'CAR_m1_p5', 'CAR_m5_p5']
    up = [get(m, '调高') for m in metrics]
    dn = [get(m, '调低') for m in metrics]
    grouped(ax, labels, up, dn, 'CAR (percentage points)')
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(OUT, 'fig1_car.png'), dpi=300,
                bbox_inches='tight', facecolor='white')
    plt.close(fig)

    # Figure 2: post-announcement drift.
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    labels = ['+2 to +60', '+2 to +120', '+2 to +250']
    metrics = ['CAR_p2_p60', 'CAR_p2_p120', 'CAR_p2_p250']
    up = [get(m, '调高') for m in metrics]
    dn = [get(m, '调低') for m in metrics]
    grouped(ax, labels, up, dn, 'CAR from +2 (percentage points)')
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(OUT, 'fig2_drift.png'), dpi=300,
                bbox_inches='tight', facecolor='white')
    plt.close(fig)

    # Figure 3: direction-adjusted holding returns.
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    labels = ['3 months', '6 months', '12 months']
    horizons = [63, 126, 252]
    up = [geta(h, '调高') for h in horizons]
    dn = [geta(h, '调低') for h in horizons]
    grouped(ax, labels, up, dn, 'Star minus non-star (pp)')
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(OUT, 'fig3_accuracy.png'), dpi=300,
                bbox_inches='tight', facecolor='white')
    plt.close(fig)

    print('ppt figures written to', OUT)


if __name__ == '__main__':
    main()
