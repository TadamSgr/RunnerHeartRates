#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
from scipy.stats import iqr
import time


# Loading in data and cleaning etc.:

# In[2]:


data=pd.read_csv("garmindata.csv")


# In[3]:


drop=["record.position_lat[semicircles]", "record.position_long[semicircles]", "Year", "Date", "DataSource", 'Unnamed: 0', 'Unnamed: 0.1']
data=data.drop(drop, 1 )


# In[4]:


dataclean=data[data['record.heart_rate[bpm]'] >=10]
#removing presumed malfunctions 


# In[5]:


datar=data.groupby("filename").max()
toremove=datar[datar['record.speed[m/s]'] >= 10]
#determine which runs have unrealisticly high top speeds


# In[6]:


#print(toremove.index.unique()) #find runs with speeds above our threshold


# In[7]:


remove=['1995_20170708_garmindata.csv', '1995_20170916_garmindata.csv',
        '1997_20171002_garmindata.csv', '1998_20170706_garmindata.csv',
        '1998_20170718_garmindata.csv', '2069_20180927_garmindata.csv',
        '2070_20180805_garmindata.csv'] 
#list of ones to remove


# In[8]:


for i in range(len(remove)):
    dataclean=dataclean[dataclean['filename'] != remove[i]]
#loop to remove them


# In[9]:


dataclean.rename(columns={'record.timestamp[s]': 'time'}, inplace=True)


# In[262]:


#dataclean.head(20)


# Function to calculate values for moving window:
# 
# - start : which timepoint you want to begin on
# - stop : the last timepoint you want to include 
# - 'Step' : corresponds to window size. if you want to average over timepoints 50-100, set as 50 etc.
# - column : which variable you are interested in. will likely be 'record.heart_rate[bpm]'
# 
# - In the dataframe that this spits out each time interval is given a label that is the end time for that window. e.g. a moving window average labelled as 650 will be the average from 600 to 650 if the size of the window was set as 50. 
# - This calculates a bunch of statistics each run, so if you want to speed things up a bit you can comment out the statistics you aren't interested in and just tweak the output to reflect that. 
# - The way this is set up, the windows overlap sequentially by 50% to make it somewhat of a moving average (i believe Joon, or maybe Trevor suggested this), i.e. if your window size was 10, youd have 10-20, then 15-25, 20-30 etc. You can alter this in the code by messing with the halfstep thing, and can have non-overlapping windows if you just remove halfstep and replace the halfstep in the loop with step.
# 
# 
# 
# - iqr and variance show some weird patterns; I think tis may be because the number of datapoints included in each window varies (due to missing timestamps), so this may mess with our ability to use this. Although I guess you could take a random 50% of timestamps for each window instead? causing the number of timepoints to be the same for each window... but might be getting overly complicated... 

# In[32]:


#labels each summary with q, so 650 mmeans summary from 600-650
def movingWindow (df, start, stop, step, column):
    
    halfstep=int(step*0.8) #######0.5 is default, 0.8 for 1 min overlap for 5 min window
    drop=[]
    columns=['record.altitude[m]', 'record.distance[m]', 'record.speed[m/s]', 'record.heart_rate[bpm]', 'SubjectID']
    for i in range(len(columns)):
        if columns[i] != column:
            drop.append(columns[i])
    df=df.drop(drop, 1)
    runList=np.ndarray.tolist(df.filename.unique())
    newDF=[]
    n=[]
    for i in range(start, stop+1-step, halfstep): ######
        n.append(i)

    for i in range(len(runList)):                 #cycles through each run
        temp=df[df['filename'] == runList[i]]     #makes temporary dataframe of just that run
        temp.reset_index(inplace = True)
    
        for j in range(len(n)):
            p=n[j]
            q=p+step 
            #Could add an IF statement here that puts a NaN if e.g. half of the values in the window range are missing..
            #but I haven't done so.
            smax = temp.query('@p <= time < @q').max()[column]
            smin = temp.query('@p <= time < @q').min()[column]
            smean = temp.query('@p <= time < @q').mean()[column]
            svar = temp.query('@p <= time < @q').var()[column]
            siqr = iqr(temp.query('@p <= time < @q')[column])
            row=[runList[i], q, smax, smin, smean, svar, siqr]
            newDF.append(row)

    newDF=pd.DataFrame(newDF)
    newDF.columns=['filename', 'SummaryRange', 'max', 'min', 'mean', 'variance', 'iqr']
    newDF=newDF.groupby(["filename"]).apply(lambda x: x.sort_values(["SummaryRange"], ascending = True)).reset_index(drop=True)
    return(newDF)


# If you haven't commented out some of the statistics in the function above, this is a function to only keep the metric you want, and to transpose dataframe to be kmlshape friendly. If you commented out any of the statistics in the moving window loop, just need to tweak this code so that all it does is transpose the dataframe.
# 
# stat: the one you want to keep, e.g. want to keep the mean, put in 'mean'

# In[11]:


def chooseStat(df, stat):
    
    drop=[]
    columns=['max', 'min', 'mean', 'variance', 'iqr']
    for i in range(len(columns)):
        if columns[i] != stat:
            drop.append(columns[i])
    df=df.drop(drop, 1)
    
    df=df.dropna()
    df=df.reset_index().pivot_table(index='filename', columns='SummaryRange', values=stat)
    df.reset_index(inplace = True)
    print(df.shape, 'rows, columns before removing NaNs') #runners with missing values are dropped, at longer races, this
    df=df.dropna()                                      #can reduce the sample size substantially
    print(df.shape, 'rows, columns after removing NaNs')
    
    df.rename(columns={'filename':'id'}, inplace=True)
    
    return(df)


# Function to randomly sample same number of runs for all individuals so that all individuals are represented by the same number of runs. The number of runs is any above a certain quantile (not sure why I went for this, a concrete number may make more sense). This can be easily tweaked in the code; just set cutoff to a number; the minimum number of runs you want for an individual to be included, and this will randomly select this numebr of runs for each runner who have enough.
# 
# - quant : set as 0.25 if you want above the first quartile

# In[12]:


def randomSamp (df, quant):
    
    temp=df
    temp["subj"]=temp['id']
    temp["subj"]= temp.subj.str.split("_", expand=True,) 
    counts=temp.groupby(["subj"])["subj"].count().reset_index(name="count")
    cutoff=counts['count'].quantile(quant) #can just set as number if we want
    temp=pd.merge(temp, counts, on="subj")
    temp=temp[temp['count'] >= cutoff]
    temp=temp.drop('count', 1)

    #random sampling of each runner's runs:
    size = int(cutoff)        # sample size 
    replace = False  # with replacement
    np.random.seed(8)
    fn = lambda obj: obj.loc[np.random.choice(obj.index, size, replace),:]
    temp=temp.groupby('subj', as_index=False).apply(fn)
    runners=temp.subj.nunique()
    temp=temp.drop('subj', 1)
    temp=temp.rename_axis(index=['runner', 'run']) #will be indexed as runner and runs
    print(temp.id.nunique(), "unique runs,", cutoff, '(rounded down) runs each from', runners, 'runners')

    return(temp)


# This was me actually using the code to get a moving window from 600-2600 with a window size of 50. This was the data I used for the cluster I sent over whatsapp last night. Took me around 50 minutes to run with the whole dataset! so using subsets makes sense when just playing around/investigating.

# In[33]:


#get my overall moving average with all summary statistics:

start = time.time() #timing it to see how long it actually takes to run
MW=movingWindow(dataclean, 600, 1800, 100, 'record.heart_rate[bpm]') #first 30 mins excluded (600 timepoints is 30 minutes)
end = time.time()
#then do 1800 to 3000; is an hour too long #MW=movingWindow(dataclean, 600, 1800, 50, 'record.heart_rate[bpm]')
#then do 3000 to 4200
#4200 to 5400 
#try first 2 hours rather than 1
print(end - start)


# In[34]:


#I just made a different dataframe for each statistic to allow me to compare:

CSa=chooseStat(MW, 'max') #choose max stat only
print('...') #just to separate print statements from each function
RSa=randomSamp(CSa, 0.25) #get same number of randomly sampled runs for each runner 


# In[35]:


CSb=chooseStat(MW, 'min')
print('...')
RSb=randomSamp(CSb, 0.25)
FirstHourMin=RSb


# In[36]:


CSc=chooseStat(MW, 'mean')
print('...')
RSc=randomSamp(CSc, 0.25)
FirstHourMean=RSc


# In[37]:


CSd=chooseStat(MW, 'variance')
print('...')
RSd=randomSamp(CSd, 0.25)
FirstHourVar=RSd


# In[38]:


CSe=chooseStat(MW, 'iqr')
print('...')
RSe=randomSamp(CSe, 0.25)
FirstHourIqr=RSe


# In[26]:


#first hour:
FirstHourMax3=RSa.query('runner in [3,4,9]')
FirstHourMin3=RSb.query('runner in [3,4,9]')
FirstHourMean3=RSc.query('runner in [3,4,9]')
FirstHourVar3=RSd.query('runner in [3,4,9]')
FirstHourIqr3=RSe.query('runner in [3,4,9]')

FirstHourVar3.head()


# Can query to compare just a subset of individuals:

# In[29]:


#Can query by runner index if you want to select a certain subset of individuals, e.g. to compare just runners 4 and 5

RSasub=RSa.query('runner in [1:28]')
RSasub.head(18)


# In[39]:


#uncomment and change directory if you want to export so that you can run it through kmlshape

export_csv = FirstHourMax.to_csv (r'C:\Users\lukec\Documents\DATA\623\wearable\comparisons\FirstHourMaxT.csv', index = None, 
                               header=True)

export_csv = FirstHourMin.to_csv (r'C:\Users\lukec\Documents\DATA\623\wearable\comparisons\FirstHourMinT.csv', index = None, 
                               header=True)

export_csv = FirstHourMean.to_csv (r'C:\Users\lukec\Documents\DATA\623\wearable\comparisons\FirstHourMeanT.csv', index = None, 
                               header=True)

export_csv = FirstHourVar.to_csv (r'C:\Users\lukec\Documents\DATA\623\wearable\comparisons\FirstHourVarT.csv', index = None, 
                               header=True)

export_csv = FirstHourIqr.to_csv (r'C:\Users\lukec\Documents\DATA\623\wearable\comparisons\FirstHourIqrT.csv', index = None, 
                               header=True)


# In[30]:


data2=dataclean.groupby("filename").max()

import plotly.express as px

fig=px.box(data2, y="time")
fig.show()

#most under 5000 times


# In[31]:


export_csv = RSa.to_csv (r'C:\Users\lukec\Documents\DATA\623\wearable\comparisons\all!!.csv', index = None, 
                               header=True)


# In[ ]:


export_csv = FirstHourIqr3.to_csv (r'C:\Users\lukec\Documents\DATA\623\wearable\comparisons\First hour iqr3.csv', index = None, 
                               header=True)

