import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# TODO | Remove pandas dependency

line_kwargs = {'linewidth': 1, 'markersize': 5}


# x_tick_size = 12
# y_tick_size = 14
# ax_label_size = 18
# fig_title_size = 20

def plot_decay(results, fill=True, titles=None, means=None):
    # ------------------------------------------ #
    #  Plotting prologue                         #
    # ------------------------------------------ #

    results = [results] if isinstance(results, dict) else results
    titles = titles if titles else [''] * len(results)
    means = means if means else [None] * len(results)

    # FIXME | This is all a bit of a naff hack from before the redesign,
    # FIXME | when there was a dependency on Pandas, remove as soon as possible

    for i in range(len(results)):
        del results[i]['auc_roc']  # Otherwise hampers the DataFrame conversion
        print(len(results[i]['f1']))
        results[i] = pd.DataFrame(dict(results[i]),
                                  index=range(1, len(results[i]['f1']) + 1))

    # End of naffness

    set_style()
    fig, axes = plt.subplots(1, len(results))

    axes = axes if hasattr(axes, '__iter__') else (axes,)

    # ------------------------------------------ #
    #  Subplots                                  #
    # ------------------------------------------ #

    for res, ax, title, mean in zip(results, axes, titles, means):
        plot_prf(ax, res, 0.3, neg=True)
        plot_prf(ax, res)
        if mean is not None:
            plot_cv_mean(ax, mean)
        if fill:
            fill_under_f1(ax, res)
        ax.set_title(title)

    # Legend

    add_legend(axes[0])

    # ------------------------------------------ #
    #  Plotting epilogue                         #
    # ------------------------------------------ #

    style_axes(axes, len(results[0]['f1']))
    fig.set_size_inches(4 * len(results), 4)
    plt.tight_layout()

    return plt


def set_style():
    sns.set_context('paper')
    sns.set(font='serif')

    sns.set('paper', font='serif', style='ticks', rc={
        'font.family': 'serif',
        'legend.fontsize': 'medium',
        'xtick.labelsize': 'medium',
        'ytick.labelsize': 'medium',
        'axes.labelsize': 'x-large',
        'axes.titlesize': 'x-large',
        'axes.labelpad': 6.0,
        'figure.titlesize': 'x-large',
        'text.usetex': True,
        'text.latex.unicode': True,
        'figure.figsize': (7.2, 4.45),
        'figure.dpi': 1200,
        'savefig.dpi': 1200
    })


def style_axes(axes, periods=10):
    for i, ax in enumerate(axes):
        # Labels
        ax.set_xlabel('Testing period')  # , fontsize=ax_label_size)
        # ax.set_ylabel('Score')  # , fontsize=ax_label_size)
        ax.set_ylabel('')

        # Ticks
        ax.set_xticks(range(1, periods + 1))
        ax.set_yticks(np.arange(0, 1.1, 0.1))

        if periods > 12:
            labels = [str(x + 1) if x % 3 == 0
                      else '' for x in range(periods + 1)]
        else:
            labels = [str(x + 1) for x in range(periods + 1)]

        ax.set_xticklabels(labels)

        ax.tick_params(axis='x', which='major')  # , labelsize=x_tick_size)
        ax.tick_params(axis='y', which='major')  # , labelsize=y_tick_size)

        ax.yaxis.grid(b=True, which='major', color='lightgrey', linestyle='-')

        # Axe limits
        ax.set_xlim(0, periods)
        ax.set_ylim(0, 1)

        sns.despine(ax=ax, top=True, right=True, bottom=False, left=False)


def plot_f1(ax, data, alpha=1.0, neg=False, label=None, color='dodgerblue',
            marker='o'):
    if label is None:
        label = 'F1 (gw)' if neg else 'F1 (mw)'
    color = '#BCDEFE' if neg else color
    series = data['f1_n'] if neg else data['f1']
    ax.plot(data.index, series, label=label, alpha=alpha, marker=marker,
            c=color, markeredgewidth=1, **line_kwargs)


def plot_recall(ax, data, alpha=1.0, neg=False, color='red', marker='^'):
    color = '#FDB2B3' if neg else color
    label = 'Recall (gw)' if neg else 'Recall (mw)'
    series = data['recall_n'] if neg else data['recall']
    ax.plot(data.index, series, label=label, alpha=alpha,
            marker=marker, c=color, markeredgewidth=1, **line_kwargs)


def plot_precision(ax, data, alpha=1.0, neg=False, color='orange', marker='s'):
    color = '#FEE2B5' if neg else color
    label = 'Precision (gw)' if neg else 'Precision (mw)'
    series = data['precision_n'] if neg else data['precision']
    ax.plot(data.index, series, label=label, alpha=alpha,
            marker=marker, c=color, markeredgewidth=1, **line_kwargs)


def fill_under_f1(ax, data, alpha=1, neg=False):
    label = 'F1 (gw)' if neg else 'F1 (mw)'
    series = data['f1_n'] if neg else data['f1']
    ax.fill_between(data.index, series,
                    label='AUT({}, 24 months)'.format(label),
                    alpha=alpha, facecolor='none', hatch='//',
                    edgecolor='#BCDEFE', rasterized=True)


def plot_cv_mean(ax, data, alpha=1):
    ax.axhline(y=float(data), linestyle='--', linewidth=1, c='red',
               alpha=alpha, label='F1 (10-fold CV)')


def plot_prf(ax, results, alpha=1.0, neg=False):
    plot_recall(ax, results, alpha, neg)
    plot_precision(ax, results, alpha, neg)
    plot_f1(ax, results, alpha, neg)


def add_legend(ax, loc='lower left'):
    lines = ax.get_lines()
    legend = ax.legend(frameon=True, handles=lines, loc=loc, prop={'size': 10})
    legend.get_frame().set_facecolor('#FFFFFF')
    legend.get_frame().set_linewidth(0)
    return legend


def save_images(plt, plot_name):
    plt.tight_layout()
    plt.savefig('./images/png/{}.png'.format(plot_name))
    plt.savefig('./images/pdf/{}.pdf'.format(plot_name))
    plt.savefig('./images/eps/{}.eps'.format(plot_name))
