# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 11:20:46 2021

@author: crisj
"""

import ee
from ee_plugin import Map
import time
from datetime import datetime

def get_Sentinel1_img(Latitude,Longitude,date1, date2,Direction,orbit_No):
    """
    Function to filter the Sentinel-1 Imagery from GEE. 
    Retrieves the VV polarisation in IW mode for the GRD product type. It filters the imagery for the 
    specified location, dates, pass direction and Orbit number.

    Parameters
    ----------
    Latitude : float
        DESCRIPTION.
    Longitude : float
        DESCRIPTION.
    date1 : Date in EE format 
        Pre-flood date.
    date2 : Date in EE format
        Post-flood date.
    Direction : String
        Ascending or Descending.
    orbit_No : int
        Relative orbit.

    Returns
    -------
    The Sentinel-1 image and its ID.

    """
    sentinel1 = (ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterDate(date1, date2)
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
            #.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
            .filter(ee.Filter.eq('orbitProperties_pass', Direction))
            .filter(ee.Filter.eq('relativeOrbitNumber_start', orbit_No))); 
              
    sentinel1 = sentinel1.filterBounds(ee.Geometry.Point(float(Longitude),float(Latitude)))
    
    recent = sentinel1.sort('system:time_start', False)
    lista = recent.toList(20)
    sentinel1_info=lista.getInfo()
    Images_in_collection=[]
    for i in range(len(sentinel1_info)):
        Images_in_collection.append(sentinel1_info[i]['id'])
    img_ID=Images_in_collection[0]
    img_ = ee.Image(Images_in_collection[0])
    return(img_,img_ID)
    
def get_img_date(a):
    """ Extract image date from ID """
    b=a.split(sep='_')
    b1=b[5].split(sep='T')
    b2=b1[0]
    return(datetime.strptime(b2, "%Y%m%d"))

# Locations
##############################
######### England ############
##############################
#dates_pre_flood =['2020-02-10','2020-02-24'] # dates 
#dates_post_flood=['2020-02-24','2020-03-15']
#map_center=[52.669613,-2.632745] 
#Direction = "DESCENDING"
#orbit_No  = 154# 
##Direction = "ASCENDING"
##orbit_No  = 30# 

##############################
######### Myanmar ############
##############################
dates_pre_flood =['2015-03-15','2015-03-25'] # dates Myanmar
dates_post_flood=['2015-09-01','2015-09-08']
map_center=[24.65,94.86]
Direction = "ASCENDING" # Myanmar
orbit_No  = 143


names=['Pre flooding image','Post flooding image']
Latitude  = map_center[0]
Longitude = map_center[1]
Map.setCenter(Longitude,Latitude, 13)

# Pre flood
date1 = ee.Date(dates_pre_flood[0])
date2 = ee.Date(dates_pre_flood[1])
# filter collection for the specified conditions
img_pre_flood,img_ID = get_Sentinel1_img(Latitude,Longitude,date1,date2,Direction,orbit_No) 

VV_pre=img_pre_flood.select('VV')   # VV polarisation
date_pre_flood=get_img_date(img_ID) # extract date

# Repeat for Post flood
date1 = ee.Date(dates_post_flood[0])
date2 = ee.Date(dates_post_flood[1])
img_post_flood,img_ID = get_Sentinel1_img(Latitude,Longitude,date1,date2,Direction,orbit_No)
VV_post=img_post_flood.select('VV') # 
date_post_flood= get_img_date(img_ID)

print("Date pre flooding event: " +str(date_pre_flood))
print("Date post flooding event: "+str(date_post_flood))
# Maps
Map.addLayer(VV_pre,  {'min': [-30], 'max': [0]}, 'VV Pre_flood '+str(date_pre_flood))
Map.addLayer(VV_post, {'min': [-30], 'max': [0]}, 'VV Post_flood '+str(date_post_flood))

#RGB of change
RGB=VV_pre.addBands(VV_post)
RGB=RGB.addBands(VV_post)
Map.addLayer(RGB, {'min': [-20,-20,-20], 'max': [0,0,0]}, 'RGB: [pre,post,post]')

#Threshold smoothed radar intensities to identify "flooded" areas.
Smoothing_radius = 100
Diff_upper_threshold=-4 # in dBs, threshold of 4 dB to separate flood/no flood
diff_smoothed = (VV_post.focal_median(Smoothing_radius, 'circle', 'meters')
.subtract(VV_pre.focal_median(Smoothing_radius, 'circle', 'meters'))) # filter 
diff_thresholded = diff_smoothed.lt(Diff_upper_threshold)
Map.addLayer(diff_thresholded.updateMask(diff_thresholded), {'palette':["0000FF"]},'Flooded areas mask') # mask
