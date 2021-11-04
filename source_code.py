# -*- #################
"""
Created on Sun Oct  4 14:05:13 2020

@author: birkaN
the script creates random training points and extracts iso cluster classification values to these 
points in order to aid user decision in class definition for training areas
"""

import arcpy
import os
from arcpy import env
import math

try:
    arcpy.CheckOutExtension("spatial")
    arcpy.env.overwriteOutput = True

    mainFolder   = arcpy.GetParameterAsText(0)
    clipFeature  = arcpy.GetParameterAsText(1)
    numberSamples = arcpy.GetParameterAsText(2)
    numberClasses = arcpy.GetParameterAsText(3)

    #######list subfolder of the main folder###########
    listSubFolders =  os.listdir(mainFolder)
    if len(listSubFolders)>1: ### Chech if there is multisubfolders
        arcpy.AddMessage("{0} scenes have been defined".format(len(listSubFolders)))
    else:
        arcpy.AddError("Multi-temporal analysis cannot be runned with one scenes!, Please add more")
    #######generate random point in polygon given####
    arcpy.CreateRandomPoints_management(os.path.join(mainFolder,listSubFolders[0]), 'randomPoints', clipFeature , '', numberSamples, '', 'POINT')
    arcpy.AddMessage("Adding fields ...")  
    ##add classname field
    arcpy.AddField_management(os.path.join(mainFolder,listSubFolders[0],'randomPoints.shp'), 'classname', 'TEXT', field_length=15)
    ##add buffer distance field
    arcpy.AddField_management(os.path.join(mainFolder,listSubFolders[0],'randomPoints.shp'), "BUFF_DIST", 'LONG', )

    ##add clip folder under subfolders
    arcpy.AddMessage("Creating a list of bands...")
    rasterList = [] #create list of rasters
    for index,sub in enumerate(listSubFolders):
        ##create clip folder
        if not os.path.exists(os.path.join(mainFolder,sub, 'clip')):
            arcpy.AddMessage("Creating clip folders....")
            os.makedirs(os.path.join(mainFolder,sub, 'clip'))
        ##save list of rasters
        env.workspace = os.path.join(mainFolder,sub)
        rasterList.append(arcpy.ListRasters("*band*", "TIF"))
        arcpy.AddMessage("Rasters are listed successfully")
        ##project random point to level2 landsat-8 images reference system
        if index == 0:
            env.workspace = os.path.join(mainFolder,sub) #set the first subfolder as environment
            desc = arcpy.Describe(rasterList[0][0]) #assign first band to be described
            sr =  desc.spatialReference #get spatial reference
            cellsize = desc.meanCellHeight # get cell size
            ##project random points and study area
            arcpy.AddMessage("Projecting points...")
            arcpy.Project_management('randomPoints.shp','randomPointsproj.shp', sr) # project random points to raster spatial reference
            arcpy.Delete_management('randomPoints.shp')
            ##snap points to cell center
            arcpy.AddMessage("Snapping points to cell centers...")
            arcpy.Buffer_analysis('randomPointsproj.shp', 'randPBuff.shp',  str(cellsize/2*math.sqrt(2)+30) + " METERS") #buff random points to maximum disorientation distance
            arcpy.Clip_management(os.path.join(mainFolder,sub,rasterList[0][0]), '#' , "buffraster.tif", 'randPBuff.shp', 0, "ClippingGeometry") #clip polygon buffered
            arcpy.RasterToPoint_conversion("buffraster.tif", 'celltopoints.shp') #convert raster clipped to points
            arcpy.Snap_edit('randomPointsproj.shp', [['celltopoints.shp', "END", cellsize*math.sqrt(2)], ['celltopoints.shp', "END", cellsize*math.sqrt(2)]])    ##snap random points to cell centers
            arcpy.ErasePoint_edit('randomPointsproj.shp', clipFeature, "OUTSIDE") #remove points that are outside of study area
            arcpy.AddMessage("Points have been snapped!")
            arcpy.Delete_management('randomPoints.shp')
            arcpy.Delete_management('celltopoints.shp')
            #arcpy.Delete_management("buffraster.tif")
            arcpy.Delete_management('randPBuff.shp')
        arcpy.AddMessage("Clipping tiles...")
        ##clip rasters
        for r in rasterList[index]:
            arcpy.Clip_management(os.path.join(mainFolder,sub,r), '#' , os.path.join(mainFolder,sub,'clip',r), clipFeature, 0, "ClippingGeometry" )
        ##compose bands
        arcpy.env.workspace = os.path.join(mainFolder,sub,'clip')
        compositeBand = rasterList[index][3] + ';' + rasterList[index][2] +  ';' +  rasterList[index][1] + ';' + rasterList[index][4] + ';' + rasterList[index][5] + ';' + rasterList[index][6] + ';' + rasterList[index][0]
        arcpy.CompositeBands_management(compositeBand , 'compbandsall'+ sub + '.tif')
        ##unsupervised Classification
        arcpy.AddMessage("Unsupervised Classification...")
        unsupervised = arcpy.sa.IsoClusterUnsupervisedClassification(compositeBand, numberClasses, 50 , 15)
        unsupervised.save('Unsupervised'+ listSubFolders[index] + '.tif')
        ##extract grid value to point
        arcpy.sa.ExtractValuesToPoints(os.path.join(mainFolder,listSubFolders[0],'randomPointsproj.shp'), 'Unsupervised'+ sub + '.tif','randomPoints' + sub + '.shp', 'NONE' , 'VALUE_ONLY')
except:  
    arcpy.AddError("This is a generic error message! An error occured,please try again!")  
    arcpy.AddMessage(arcpy.GetMessages())





import arcpy
import os
from arcpy import env

try:
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")

    mainFolder = arcpy.GetParameterAsText(0)
    classespar = str(arcpy.GetParameterAsText(1))
    bufferPoints = arcpy.GetParameterAsText(2)


    #######list subfolder of the main folder###########
    listSubFolders =  os.listdir(mainFolder)
    ##split classes with comma seperator
    classes = classespar.split(',')

    arcpy.AddMessage("Creating a list for bands...")
    rasterList = []
    for index,sub in enumerate(listSubFolders):# iterate subfolders
        env.workspace = os.path.join(mainFolder,sub)
        rasterList.append(arcpy.ListRasters("*band*", "TIF"))
        env.workspace = os.path.join(mainFolder,sub,'clip')
        arcpy.AddMessage("Updating class names...")
        ##iterate class values to update classnames
        for index2,c in enumerate(classes):
            cursor = arcpy.UpdateCursor('randomPoints' + sub + '.shp')
            row = cursor.next()
            while row:
                rastervalu = row.getValue('RASTERVALU')
                if rastervalu == index2+1:
                    row.setValue('classname' , c)
                    cursor.updateRow(row)
                row = cursor.next()
            del row,cursor
        ##Buffer points if it is checked by the user
        if bufferPoints == True:
            arcpy.Buffer_analysis(os.path.join(mainFolder,sub,'clip','randomPoints' + sub + '.shp'),'randPoints' + sub + 'buff' +'.shp', "BUFF_DIST")
        compositeBand = rasterList[index][3] + ';' + rasterList[index][2] +  ';' +  rasterList[index][1] + ';' + rasterList[index][4] + ';' + rasterList[index][5] + ';' + rasterList[index][6] + ';' + rasterList[index][0]
        if not os.path.exists(os.path.join(mainFolder,sub, 'clip','compbandsall'+ sub + '.tif')): ##if composite of bands does not exist
            ##compose all bands, first 3 bands for rgb composition
            arcpy.CompositeBands_management(compositeBand , 'compbandsall'+ sub + '.tif')
        ##create signatures
        arcpy.AddMessage("Supervised Classification...")
        if bufferPoints == True:
            arcpy.sa.CreateSignatures(compositeBand, "randPoints" + sub + 'buff' + '.shp', sub + ".gsg", "COVARIANCE", 'classname')
        else:
            arcpy.sa.CreateSignatures(compositeBand, "randomPoints" + sub + '.shp', sub + ".gsg", "COVARIANCE", 'classname')
        ##maximum likelihood classification
        mlcOut = arcpy.sa.MLClassify(compositeBand, sub + ".gsg", "0.0", "EQUAL") 
        mlcOut.save('mlc' + sub + '.tif')

except:  
    arcpy.AddError("This is a generic error message! An error occured,please try again!")  
    arcpy.AddMessage(arcpy.GetMessages())