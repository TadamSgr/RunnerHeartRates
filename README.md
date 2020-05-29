# Applying KMLShape Clustering to Runners’ Heart Rate Data
Garmin Data Collected By Dr. Reed Ferber, processed and analysed with KMLShape
Authors: Luke Larter, Shilpa Gohil, Trevor Seeger

The data for this project is part of an active study, and therefore cannot be posted. 

## Research Questions:
1) As a proof of concept of our chosen clustering method, we will see how well our algorithm is able to differentiate runs from different individuals based on heart rate, assessed via ground truthing

2) We will investigate the pattern of clustering across our whole dataset and test how the data clusters based on different metrics of heart rate over time


## Methods
Data were clustered over one and two hours of running, and two hours revealed lower rand scores. We then ran the KMLShape package on the two hour window on 1 to 10 clusters. 
The attached code is intended to clean the data in python, then KMLShape was applied in R to cluster the heart rate trajectories of participants during their runs. 


## Limitations: 
We could not include both random and fixed effects in clustering analyses using KMLShape
There is no method that we could find to determine which number of clusters is the best, therefore we performed an ad hoc comparison of the Fréchet distances between each trajectory and their assigned cluster. 
Computational power limited us to 10 clusters.

## Future analyses
Learn and work with ‘kml3d’ in R in order to cluster on multiple variables, so as to incorporate additional features into trajectory clustering, and incorporate other variables with heart rate into some sort of index 
Develop profiles with predictive capabilities and warnings for runners
E.g. Changing between clusters, or deviating from normal pattern could indicate risk

Future things to investigate within our method:
Tradeoff of coarseness of data and race duration; which is optimal?
Are certain time intervals better at clustering? E.g. earlier vs. later. In run
Determine exactly which aspects of heart rate trajectories are most amenable to clustering 
