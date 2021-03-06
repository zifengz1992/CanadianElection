# This is part 2 of a code-clean version of the project:
# https://www.kaggle.com/czz1403/dm13-1204880-python
# original report written in Chinese

# %% packages & filter warnings

import re
import numpy as np
import pandas as pd
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')

# %% load data using csv files generated by part 1
# files are generated after running 01_data_collection.py under the same path

data_04 = pd.read_csv("./2004.csv")
data_06 = pd.read_csv("./2006.csv")
data_08 = pd.read_csv("./2008.csv")
data_11 = pd.read_csv("./2011.csv")
rd_dict = pd.read_csv("./ridings.csv").set_index('Code').to_dict()['2011 Ridings']

# %% prepare Ontario data as machine learning dataset
# Ontario has 106 EDs between 2004-2011, the most of all prov/terr
# only province that has a ED count that might be meaningful for machine learning model
# usage of ML here is for pure demostration. From my point of view, ML & prediction does not fit the theme of election analysis best, as a matter of fact

dt_on = data_08[data_08['Province']=='ON']

dt_on['Turnout'] = dt_on['Total Votes'] / dt_on['Total Voters'] * 100
dt_on['08_support'] = dt_on['Conservative'] / dt_on['Total Votes'] * 100
dt_on['08_LIB'] = dt_on['Liberal'] / dt_on['Total Votes'] * 100
dt_on['08_NDP'] = dt_on['NDP'] / dt_on['Total Votes'] * 100
dt_on['08_Elected'] = dt_on['Elected'].map({'Conservative': 0, 'Liberal': 1, 'NDP': 2})

# set 2011 conservative party support rate in all EDs as target
# being the only right wing leaning major party, conservative support rate is least affected by minor factors
dt_on['Target'] = data_11[data_11['Province']=='ON']['Conservative'] /\
                  data_11[data_11['Province']=='ON']['Total Votes'] * 100

dt_on = dt_on[['District', 'Turnout', '08_Elected', '08_support', '08_LIB', '08_NDP', 'Target']].reset_index(drop=True)

dt_on

# %% Clustering the "types" of EDs with clustering ML model
# EDs normally has typical patterns of supporting major parties, based on the sociodemograpical conditions

from sklearn.cluster import KMeans

x = dt_on.iloc[:, 2:-1] # use major party support rates as x set

km = KMeans(n_clusters=3) # KMeans clusters model
cls = km.fit_predict(x)
cls

# %% to ensure the results could be repeated, use tags generated on the first run of the model
# subsequent run of models shows that the clusters remains roughly the same, with only variations in tags (order of 0, 1, 2), however

cls = [0, 1, 2, 2, 1, 0, 0, 0, 2, 2, 2, 2, 2, 2, 1, 0, 0, 2, 0, 2, 2, 0,
       0, 0, 2, 2, 0, 2, 2, 2, 1, 1, 1, 2, 2, 0, 0, 2, 0, 2, 2, 1, 0, 0,
       0, 2, 0, 0, 0, 0, 0, 2, 2, 2, 2, 1, 0, 2, 0, 2, 1, 1, 2, 0, 0, 2,
       2, 1, 2, 2, 2, 0, 2, 2, 0, 2, 0, 2, 1, 0, 0, 0, 0, 0, 2, 2, 2, 1,
       2, 1, 1, 1, 0, 1, 1, 0, 1, 2, 2, 0, 1, 1, 0, 2, 0, 0]

# add cluster tag to the data
dt_on['Riding_type'] = cls
dt_on = dt_on[['District', 'Riding_type', 'Turnout', '08_Elected', '08_support', '08_LIB', '08_NDP', 'Target']]
dt_on

# %% train-test split with stratified sampling
# ensure that each type of riding has similar representation in train set and test set

import random
from math import floor

# stratification
cls1 = dt_on[dt_on['Riding_type']==0]['District'].tolist()
cls2 = dt_on[dt_on['Riding_type']==1]['District'].tolist()
cls3 = dt_on[dt_on['Riding_type']==2]['District'].tolist()

# randomly shuffle the order of ED codes of each type
sample1 = random.Random(308).sample(cls1, len(cls1))
sample2 = random.Random(308).sample(cls2, len(cls2))
sample3 = random.Random(308).sample(cls3, len(cls3))

# generate training and testing ED code list
train_rd = cls1[:floor(len(cls1)*0.7)] + cls2[:floor(len(cls2)*0.7)] + cls3[:floor(len(cls3)*0.7)]
test_rd = cls1[floor(len(cls1)*0.7):] + cls2[floor(len(cls2)*0.7):] + cls3[floor(len(cls3)*0.7):]

# training set
x_train = dt_on[dt_on['District'].isin(train_rd)].iloc[:, :-1]
y_train = dt_on[dt_on['District'].isin(train_rd)].iloc[:, -1]

# testing set
x_test = dt_on[dt_on['District'].isin(test_rd)].iloc[:, :-1]
y_test = dt_on[dt_on['District'].isin(test_rd)].iloc[:, -1]

# %% train a polynomial regression model
# test for best i is added here as a new feature compared to the original report

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

mses = dict()

for i in range(1, 7): # test for best i
    poly_features = PolynomialFeatures(degree=i, include_bias=False)
    x_train_poly = poly_features.fit_transform(x_train)
    x_test_poly = poly_features.fit_transform(x_test)

    model = LinearRegression()
    model.fit(x_train_poly, y_train)

    y_pred = model.predict(x_test_poly)

    mses[i]=mean_squared_error(y_test, y_pred)

print(mses) # mean squared error for tested is
plt.plot(list(mses.keys()), list(mses.values())) # plotting mean squared errors paired with is

# %% train model with the best i selected
# test shows that the best i is actually 1

poly_features = PolynomialFeatures(degree=1, include_bias=False)
x_train_poly = poly_features.fit_transform(x_train)
x_test_poly = poly_features.fit_transform(x_test)

model = LinearRegression()
model.fit(x_train_poly, y_train)

y_pred = model.predict(x_test_poly)

mse_list.append(mean_squared_error(y_test, y_pred))

print(f'Mean squared error: {mean_squared_error(y_test, y_pred)}') # 输出均方差

# %% check the similarity of prediction and actual target

plt.plot(y_test.reset_index(drop=True))
plt.plot(y_pred)
plt.show()

# %% prepare 2008 data set to test on the model trained with 2011 data

dt_on_08 = data_06[data_06['Province']=='ON']

dt_on_08['Turnout'] = dt_on_08['Total Votes'] / dt_on_08['Total Voters'] * 100
dt_on_08['06_support'] = dt_on_08['Conservative'] / dt_on_08['Total Votes'] * 100
dt_on_08['06_LIB'] = dt_on_08['Liberal'] / dt_on_08['Total Votes'] * 100
dt_on_08['06_NDP'] = dt_on_08['NDP'] / dt_on_08['Total Votes'] * 100
dt_on_08['06_Elected'] = dt_on_08['Elected'].map({'Conservative': 0, 'Liberal': 1, 'NDP': 2})

dt_on_08['Target'] = data_08[data_08['Province']=='ON']['Conservative'] /\
                  data_08[data_08['Province']=='ON']['Total Votes'] * 100

dt_on_08 = dt_on_08.reset_index(drop=True)

dt_on_08['Riding_type'] = cls

dt_on_08 = dt_on_08[['District', 'Riding_type', 'Turnout', '06_Elected', '06_support', '06_LIB', '06_NDP', 'Target']]

dt_on_08

# %% run 2008 data on the 2011-data-trained model

x_08 = dt_on_08.iloc[:, :-1]
y_08 = dt_on_08.iloc[:, -1]

x_08_poly = poly_features.fit_transform(x_08)

print(f'Mean squared error: {mean_squared_error(y_08, model.predict(x_08_poly))}')

plt.plot(y_08.reset_index(drop=True))
plt.plot(model.predict(x_08_poly))
plt.show()

# the results shows that 2011-data-trained model is actually more accurate for predicting 2008 result (!?)
# however, considering the nature of election, it may be deducted that the factors determining conservative supports are roughly the same in 2008 and 2011
# which is not a result applicable to all election years. 2015 is a notable exception, for instance

# %%
