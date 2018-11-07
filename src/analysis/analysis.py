# =========================================================================== #
#                                 ANALYSIS                                    #
# =========================================================================== #
'''Analysis and inference functions'''

# %%
# --------------------------------------------------------------------------- #
#                                 LIBRARIES                                   #
# --------------------------------------------------------------------------- #
import os
import sys
import inspect
sys.path.append("./src")

import itertools
from itertools import combinations
import math
import numpy as np
import pandas as pd
import scipy
from scipy import stats
from scipy.stats import kurtosis, skew
import seaborn as sns
from sklearn import preprocessing
import statistics as stat
import textwrap
import warnings
warnings.filterwarnings('ignore')

from visualization import visual
# %%
# ---------------------------------------------------------------------------- #
#                                    DESCRIBE                                  #
# ---------------------------------------------------------------------------- #


def describe_qual_df(df):
    stats = pd.DataFrame()
    cols = df.columns
    for col in cols:
        d = pd.DataFrame(df[col].describe())
        d = d.T
        d['missing'] = df[col].isna().sum()
        stats = stats.append(d)
    return stats


def describe_quant_df(df):

    stats = pd.DataFrame()
    cols = df.columns
    for col in cols:
        d = pd.DataFrame(df[col].describe())
        d = d.T
        d['skew'] = skew(df[col].notnull())
        d['kurtosis'] = kurtosis(df[col].notnull())
        d['missing'] = df[col].isna().sum()
        c = ['count', 'missing', 'min', '25%', 'mean', '50%',
             '75%', 'max', 'skew', 'kurtosis']
        stats = stats.append(d[c])
    return stats


def describe_qual_x(x):
    d = pd.DataFrame(x.describe())
    d = d.T
    d['missing'] = x.isna().sum()
    return d


def describe_quant_x(x):
    d = pd.DataFrame(x.describe())
    d = d.T
    d['skew'] = skew(x.notnull())
    d['kurtosis'] = kurtosis(x.notnull())
    d['missing'] = x.isna().sum()
    c = ['count', 'missing', 'min', '25%', 'mean', '50%',
         '75%', 'max', 'skew', 'kurtosis']

    return d[c]

# ---------------------------------------------------------------------------- #
#                             UNIVARIATE ANALYSIS                              #
# ---------------------------------------------------------------------------- #
# %%


def univariate(df):
    cols = df.columns
    for col in cols:
        if (df[col].dtype == np.dtype('int64') or
                df[col].dtype == np.dtype('float64')):
            d = describe_quant_x(df[col])
            v = visual.boxplot(df, xvar=col)
        else:
            d = describe_qual_x(df[col])
            v = visual.countplot(xvar=col, df=df)
    return d, v


# ---------------------------------------------------------------------------- #
#                               INDEPENDENCE                                   #
# ---------------------------------------------------------------------------- #


class Independence:
    "Class that performs a test of independence"

    def __init__(self):
        self._sig = 0.05
        self._x2 = 0
        self._p = 0
        self._df = 0
        self._obs = []
        self._exp = []

    def summary(self):
        print("\n*", "=" * 78, "*")
        print('{:^80}'.format("Pearson's Chi-squared Test of Independence"))
        print('{:^80}'.format('Data'))
        print('{:^80}'.format("x = " + self._xvar + " y = " + self._yvar + "\n"))
        print('{:^80}'.format('Observed Frequencies'))
        visual.print_df(self._obs)
        print("\n", '{:^80}'.format('Expected Frequencies'))
        visual.print_df(self._exp)
        results = ("Pearson's chi-squared statistic = " + str(round(self._x2, 3)) + ", Df = " +
                   str(self._df) + ", p-value = " + '{0:1.2e}'.format(round(self._p, 3)))
        print("\n", '{:^80}'.format(results))
        print("\n*", "=" * 78, "*")

    def post_hoc(self, rowwise=True, verbose=False):

        dfs = []
        if rowwise:
            rows = range(0, len(self._obs))
            for pair in list(combinations(rows, 2)):
                ct = self._obs.iloc[[pair[0], pair[1]], ]
                levels = ct.index.values
                x2, p, dof, exp = stats.chi2_contingency(ct)
                df = pd.DataFrame({'level_1': levels[0],
                                   'level_2': levels[1],
                                   'x2': x2,
                                   'N': ct.values.sum(),
                                   'p_value': p}, index=[0])
                dfs.append(df)
            self._post_hoc_tests = pd.concat(dfs)
        else:
            cols = range(0, len(self._obs.columns.values))
            for pair in list(combinations(cols, 2)):
                ct = self._obs.iloc[:, [pair[0], pair[1]]]
                levels = ct.columns.values
                x2, p, dof, exp = stats.chi2_contingency(ct)
                df = pd.DataFrame({'level_1': levels[0],
                                   'level_2': levels[1],
                                   'x2': x2,
                                   'N': ct.values.sum(),
                                   'p_value': p}, index=[0])
                dfs.append(df)
            self._post_hoc_tests = pd.concat(dfs)
        if (verbose):
            visual.print_df(self._post_hoc_tests)

        return(self._post_hoc_tests)

    def test(self, x, y, sig=0.05):
        self._x = x
        self._y = y
        self._xvar = x.name
        self._yvar = y.name
        self._n = x.shape[0]
        self._sig = sig

        ct = pd.crosstab(x, y)
        x2, p, dof, exp = stats.chi2_contingency(ct)

        self._x2 = x2
        self._p = p
        self._df = dof
        self._obs = ct
        self._exp = pd.DataFrame(exp).set_index(ct.index)
        self._exp.columns = ct.columns

        if p < sig:
            self._result = 'significant'
            self._hypothesis = 'reject'
        else:
            self._result = 'not significant'
            self._hypothesis = 'fail to reject'

        return x2, p, dof, exp

    def report(self, verbose=False):
        "Returns or prints results in APA format"
        tup = ("A Chi-square test of independence was conducted to "
               "examine the relation between " + self._xvar + " and " + self._yvar + ". "
               "The relation between the variables was " + self._result + ", "
               "X2(" + str(self._df) + ", N = ", str(self._n) + ") = " +
               str(round(self._x2, 2)) + ", p = " + '{0:1.2e}'.format(round(self._p, 3)))

        self._report = ''.join(tup)

        wrapper = textwrap.TextWrapper(width=80)
        lines = wrapper.wrap(text=self._report)
        if verbose:
            for line in lines:
                print(line)
        return(self._report)
