# This is part 1 of a code-clean version of the project:
# https://www.kaggle.com/czz1403/dm13-1204880-python
# original report written in Chinese

# %% packages & filter warnings

import re
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

# %% supporting function 1
# turning number strings to int format
# the original demostrative collection of 2004 data is integrated to collection of data of other years

def num_process(array):

    converted = [int(re.sub(" ", "", num)) for num in array]

    return converted

# %% supporting function 2
# converting riding name infos, keeping English names & use short dash "-" only

def rdname_process(column):

    names = [re.sub("\x97", "-", rd).split("/")[0] for rd in column]

    return names

# %% main loading data function

def load_table12(url):

    raw = pd.read_html(url, match='Avalon')[0]

    # set up column names
    if raw.columns[0]: # headers of 2008 & 2011 forms could be read directly
        colnames = [colname[0].split('-')[0] for colname in raw.columns]
    else: # headers of 2004 & 2016 forms could not be loaded directly
        colnames = [colname.split('-')[0] for colname in raw.iloc[1].tolist()]

    colnames[4:] = ['Vote Count', 'Vote %', 'Majority Count', 'Majority %']
    raw.columns = colnames

    # select columns
    df = raw[[
        'Electoral district',
        'Candidate and affiliation',
        'Vote Count',
        'Vote %',
    ]]

    # filter irrelevant information
    df = df.loc[~df['Vote Count'].isnull()]
    df = df.loc[df['Vote Count'] != df['Vote %']]
    df = df.loc[df['Vote Count'] != 'No./Nbre']
    df = df.reset_index(drop=True)

    df['Vote Count'] = num_process(df['Vote Count'])

    df['Electoral district'] = df['Electoral district'].fillna(method='pad')
    df['Electoral district'] = rdname_process(df['Electoral district'])

    return df

# %% urls of the table 12s

url_04 = 'https://www.elections.ca/scripts/ovr2004/23/table12.html'
url_06 = 'https://www.elections.ca/scripts/OVR2006/25/table12.html'
url_08 = 'https://www.elections.ca/scripts/OVR2008/31/table12.html'
url_11 = 'https://www.elections.ca/scripts/ovr2011/34/table12.html'

# %% load data and create pandas dataframes

df_04 = load_table12(url_04) # 1685 rows
df_06 = load_table12(url_06) # 1634 rows
df_08 = load_table12(url_08) # 1601 rows
df_11 = load_table12(url_11) # 1587 rows

# %% electoral district name list urls, for all 4 election years

rdurl_04, rdurl_06, rdurl_08, rdurl_11 = [
    f'https://www.elections.ca/content.aspx?section=res&dir=rep/off/{i}gedata&document=byed&lang=e' \
    for i in range(38, 42)
]

# %% function for creation of electoral disctrict name tables
# collect info for all 4 election years to check changes of ED names between federal elections

def get_riding_list(rdurl):

    rd_list = pd.read_html(rdurl)
    # read_html will return a list composed of 13 dataframes convering 1 province or terrtory each
    # calling concat() method to concatenate the pro/ter dfs into the nationwide df
    rddf = pd.concat(rd_list).iloc[:, :2].reset_index().iloc[:, 1:]
    rddf.columns = ['Code', 'Ridings']
    rddf['Ridings'] = [re.sub('–', '-', rd) for rd in rddf['Ridings'].tolist()]
    rddf = rddf.set_index('Code')

    return rddf

# %% collect ED names

rd_04 = get_riding_list(rdurl_04)
rd_06 = get_riding_list(rdurl_06)
rd_08 = get_riding_list(rdurl_08)
rd_11 = get_riding_list(rdurl_11)

# change the name of columns in different dfs, for checking of
rd_04.columns = ['2004 Ridings']
rd_06.columns = ['2006 Ridings']
rd_08.columns = ['2008 Ridings']
rd_11.columns = ['2011 Ridings']

# %% name checking dataframe

compare_rd = rd_04.join([rd_06, rd_08, rd_11])

# calculate the different instances of ED names for each ED code, on the original pages
compare_rd['namecount'] = [compare_rd.iloc[ind].nunique() for ind in range(len(compare_rd))]
compare_rd.loc[compare_rd['namecount'] > 1]

# %% check for differences in ED names on the Election Canada ED list pages and Table 12s for each election
# previous check returns 0 record, meaning the ED names listed on "rdurls" are same
# nevertheless, Table 12s (collected previously) may use different sets of ED names

# standardized ED code - ED name dictionary
# useful for calling out pandas.Series.map() method later
rd_dict = rd_11.to_dict()['2011 Ridings']

# standardized ED name set
set_rd = set(rd_11['2011 Ridings'].tolist())

# Table 12 ED name sets for all 4 years
set_04 = set(df_04['Electoral district'].tolist())
set_06 = set(df_06['Electoral district'].tolist())
set_08 = set(df_08['Electoral district'].tolist())
set_11 = set(df_11['Electoral district'].tolist())

# check for differences
diff_04 = list(set_04.difference(set_rd))
diff_06 = list(set_06.difference(set_rd))
diff_08 = list(set_08.difference(set_rd))
diff_11 = list(set_11.difference(set_rd))

diff_04, diff_06, diff_08, diff_11

# %% renaming "Northwest Territories" as "Western Arctic"
# the mistake is presented for all election years
# applies to stardardized dict & set, as well as original df (just in case)

rd_dict[61001] = 'Western Arctic'
rd_11['2011 Ridings'] = rd_11['2011 Ridings'].replace('Northwest Territories', 'Western Arctic')
set_rd = set(rd_dict.values())

# %% create 2004 ED name dictionary
# most ED name changes occured between 2004 and 2006 elections
# useful for calling map() method on 2004 data later

dict_04 = rd_04.to_dict()['2004 Ridings']

corr_list = [
    (10002, 'Bonavista-Exploits'),
    (10006, 'St. John\'s North'),
    (10007, 'St. John\'s South'),
    (12007, 'North Nova'),
    (13004, 'Fundy'),
    (13008, 'St. Croix-Belleisle'),
    (24004, 'Argenteuil-Mirabel'),
    (24007, 'Beauport'),
    (24013, 'Charlesbourg'),
    (24014, 'Charlevoix-Montmorency'),
    (24031, 'Laurier'),
    (24035, 'Longueuil'),
    (24041, 'Matapédia-Matane'),
    (24046, 'Nunavik-Eeyou'),
    (24051, 'Portneuf'),
    (24054, 'Richelieu'),
    (24056, 'Rimouski-Témiscouata'),
    (24058, 'Rivière-du-Loup-Montmagny'),
    (24060, 'Roberval'),
    (35012, 'Carleton-Lanark'),
    (35014, 'Clarington-Scugog-Uxbridge'),
    (35026, 'Grey-Bruce-Owen Sound'),
    (35046, 'Middlesex-Kent-Lambton'),
    (46002, 'Charleswood-St. James'),
    (46004, 'Dauphin-Swan River'),
    (47003, 'Churchill River'),
    (48001, 'Athabasca'),
    (48003, 'Calgary North Centre'),
    (48006, 'Calgary South Centre'),
    (48011, 'Edmonton-Beaumont'),
    (59007, 'Dewdney-Alouette'),
    (59010, 'Kamloops-Thompson'),
    (59011, 'Kelowna'),
    (59018, 'North Okanagan-Shuswap'),
    (59026, 'Southern Interior'),
    (59036, 'West Vancouver-Sunshine Coast'),
    (61001, 'Western Arctic'),
] # list of all ED names needed to be corrected

for key, value in corr_list:
    dict_04[key] = value

# %% test the effect of 2004 ED name correction
# Returning an empty list proves that: every ED in 2004 dict is changed to their 2006-2011 names

set_04_new = set(dict_04.values())
diff_exam = list(set_04.difference(set_04_new))
diff_exam

# %% replace the ED names in major dfs with ED codes

# swap keys and values in dicts
mapping_dict_sta = dict(zip(rd_dict.values(), rd_dict.keys()))
mapping_dict_04 = dict(zip(dict_04.values(), dict_04.keys()))

# 2004 dict for 2004 data
df_04['Electoral district'] = df_04['Electoral district'].map(mapping_dict_04)
# standard dict for data of other years
df_06['Electoral district'] = df_06['Electoral district'].map(mapping_dict_sta)
df_08['Electoral district'] = df_08['Electoral district'].map(mapping_dict_sta)
df_11['Electoral district'] = df_11['Electoral district'].map(mapping_dict_sta)

# doublecheck result of replacement
# returns a list of 4 zeros for all ED names being validly replaced
[
    df_04['Electoral district'].isna().sum(),
    df_06['Electoral district'].isna().sum(),
    df_08['Electoral district'].isna().sum(),
    df_11['Electoral district'].isna().sum()
]

# %% function converting table 12 data into major party vote counts df
# Effect of df being created by this function:
# 1st column contains ED codes;
# 2nd-5th columns are vote counts for 4 major parties in the ED.
# vote counts are set as 0 where a major party does not have a candidate in the ED (for instance, BQ in provinces other than Quebec)

def get_vote_count(df_detail): # 定义生成函数

    rdno_list = df_detail['Electoral district'].unique().tolist()

    # initialize the new df, use party abbreviations as temporary column names
    count_df = pd.DataFrame(
        np.zeros((len(rdno_list), 5)),
        columns=[
            'District',
            'Liberal',
            'Conservative',
            'N.D.P.',
            'Bloc Qu',
        ]
    )
    count_df['District'] = rdno_list

    # BQ is addressed as such for:
    # - "Bloc" may be identified as part of candidate names, while
    # - Québécois contains the French special letter é
    parties = [
        'Liberal',
        'Conservative',
        'N.D.P.',
        'Bloc Qu'
    ]

    for rd in rdno_list:
        rd_data = df_detail[df_detail['Electoral district'] == rd]

        for party in parties:

            # replacing the value on the corresponding location in the new df with vote counts
            for i in range(len(rd_data)):

                if party in rd_data['Candidate and affiliation'].iloc[i]:

                    count_df[party].loc[count_df['District'] == rd] = rd_data['Vote Count'].iloc[i]

                # 2008 & 2011 data uses a different form of abbreviation for NDP
                elif 'NDP' in rd_data['Candidate and affiliation'].iloc[i]:

                    count_df['N.D.P.'].loc[count_df['District'] == rd] = rd_data['Vote Count'].iloc[i]

    # update column names
    count_df.columns = [
        'District',
        'Liberal',
        'Conservative',
        'NDP',
        'BQ',
    ]

    return count_df

# %% create party vote count dfs for all years

data_04 = get_vote_count(df_04)
data_06 = get_vote_count(df_06)
data_08 = get_vote_count(df_08)
data_11 = get_vote_count(df_11)

# %% load supplement information for table 11 provided by Election Canada
# The table contains info about total votes casted in the EDs and counts of voters registered to vote
# "Valid ballots" counts are selected in preference to "Total ballots cast", to ensure validity of calculation results

def load_table11(url):

    t11 = pd.read_html(url, match='Avalon')[0]

    # set up column names
    if t11.columns[0]: # headers of 2008 & 2011 forms could be read directly
        colnames = [colname[0].split('-')[0].strip() for colname in t11.columns]
    else: # headers of 2004 & 2016 forms could not be loaded directly
        colnames = [colname.split('-')[0] for colname in t11.iloc[1].tolist()]

    colnames[4: 6] = ['Valid Ballots Count', 'Valid Ballots %']
    t11.columns = colnames

    # select columns
    cols = [
        'Electoral district',
        'Electors on the lists',
        'Valid Ballots Count',
        'Valid Ballots %',
    ]
    t11 = t11[cols]

    # filter irrelevant information
    t11 = t11.loc[~t11['Valid Ballots Count'].isnull()]
    t11 = t11[t11['Valid Ballots Count'] != t11['Valid Ballots %']]
    t11 = t11[t11['Valid Ballots Count'] != 'No./Nbre']
    t11 = t11[t11['Electoral district'] != 'Totals/Totaux']
    t11 = t11.iloc[:-1, :-1].reset_index(drop=True)

    t11['Electors on the lists'] = num_process(t11['Electors on the lists'])
    t11['Valid Ballots Count'] = num_process(t11['Valid Ballots Count'])
    t11['Electoral district'] = rdname_process(t11['Electoral district'])

    if "Fundy" in t11['Electoral district'].unique().tolist(): # use 2004 ED code/name dict if 2004 ED name identified
        t11['Electoral district'] = t11['Electoral district'].map(mapping_dict_04)
    else:
        t11['Electoral district'] = t11['Electoral district'].map(mapping_dict_sta)

    # set final col names
    t11.columns = [
        'District',
        'Total Voters',
        'Total Votes',
    ]

    return t11

# %% collect table 11 infos

t11_04_url = 'https://www.elections.ca/scripts/OVR2004/23/table11.html'
t11_06_url = 'https://www.elections.ca/scripts/OVR2006/25/table11.html'
t11_08_url = 'https://www.elections.ca/scripts/OVR2008/31/table11.html'
t11_11_url = 'https://www.elections.ca/scripts/OVR2011/34/table11.html'

t11_04 = load_table11(t11_04_url)
t11_06 = load_table11(t11_06_url)
t11_08 = load_table11(t11_08_url)
t11_11 = load_table11(t11_11_url)

# %% merge table 11 infos with vote count df

data_04 = data_04.merge(t11_04, on='District')
data_06 = data_06.merge(t11_06, on='District')
data_08 = data_08.merge(t11_08, on='District')
data_11 = data_11.merge(t11_11, on='District')

# %% adding "others" column
# "other" column would contain count of votes casted for candidates not endorsed by any of the 4 major parties in the ED

def add_others(df):

    others = []

    for i in range(len(df)):
        others.append(
            df['Total Votes'][i] - (df['Liberal'][i] + df['Conservative'][i] + df['NDP'][i] + df['BQ'][i])
        )

    df['Others'] = others

    return df

data_04 = add_others(data_04)
data_06 = add_others(data_06)
data_08 = add_others(data_08)
data_11 = add_others(data_11)

# %% adding info of winning party - preliminary result
# Only in single digit instances had EDs been won by candidates not endorse by 4 major parties in the 4 general elections
# Therefore, preliminary results are created with comparing 4 major party voting counts and retaining the maximum
# direct comparison with "others" may generate inaccurate outcome

def add_elected(df):

    parties_df = df[['Liberal', 'Conservative', 'NDP', 'BQ']]
    df['Elected'] = parties_df.idxmax(axis=1)

    return df

data_04 = add_elected(data_04)
data_06 = add_elected(data_06)
data_08 = add_elected(data_08)
data_11 = add_elected(data_11)

# %% Correcting the few exceptions in winning party preliminary result

data_04['Elected'].loc[data_04['District'] == 59028] = 'Others'
data_06['Elected'].loc[data_06['District'] == 24051] = 'Others'
data_08['Elected'].loc[data_08['District'] == 24051] = 'Others'
data_08['Elected'].loc[data_08['District'] == 12007] = 'Others'
data_11['Elected'].loc[data_11['District'] == 59024] = 'Others'

# %% Adding province / territory info

pt_dict = {
    10: 'NL',
    11: 'PE',
    12: 'NS',
    13: 'NB',
    24: 'QC',
    35: 'ON',
    46: 'MB',
    47: 'SK',
    48: 'AB',
    59: 'BC',
    60: 'Territories',
    61: 'Territories',
    62: 'Territories',
}

def add_pt(df):

    pt = []

    for i in range(len(df)):

        key = df['District'].iloc[i] // 1000
        pt.append(pt_dict[key])

    df['Province'] = pt

    return df

data_04 = add_pt(data_04)
data_06 = add_pt(data_06)
data_08 = add_pt(data_08)
data_11 = add_pt(data_11)

# %% reordering the columns

col_list = [
    'District',
    'Province',
    'Total Voters',
    'Liberal',
    'Conservative',
    'NDP', 'BQ',
    'Others',
    'Total Votes',
    'Elected',
]

data_04 = data_04[col_list].sort_values(by='District')
data_06 = data_06[col_list].sort_values(by='District')
data_08 = data_08[col_list].sort_values(by='District')
data_11 = data_11[col_list].sort_values(by='District')

# %% outputting datasheet

data_04.to_csv("2004.csv", index=False)  # 2004 summarized datasheet
data_06.to_csv("2006.csv", index=False)  # 2006 summarized datasheet
data_08.to_csv("2008.csv", index=False)  # 2008 summarized datasheet
data_11.to_csv("2011.csv", index=False)  # 2011 summarized datasheet
rd_11.to_csv("ridings.csv", encoding='utf-8-sig')  # ED code / ED name reference sheet

# %%
