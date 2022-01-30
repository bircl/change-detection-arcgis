# Change Detection Tool arcGIS
Arcmap plugin for land cover change detection analysis based on Sentinel-2 and Landsat-8 satellite images - Written in Python, using ArcPy.

## Aim

This script assesses alteration in LULC

The overall objective of this script is to shorten tedious operations in change detection for urbanization measurements and provide basic information.
Products from this script are expected to provide a fast and straightforward classification results. 

## Methods

![flowchart](/screenshots/flowchart.png)

#### Part 1 Preprocess Tool
In the first part, the script creates random training points and extracts iso cluster classification values to these points in order to aid user decision in class definition for training areas.

![flowchart](/screenshots/preprocess.png)

#### Part 2 Classify Rasters Tool
The second part can only be performed after the training sites are completed by the user. In this part, a set of geoprocessing tools defines class names and utilizes spectral signatures from training sites to perform maximum likelihood classification

![flowchart](/screenshots/classification.png)

## Parameters

A complete list of parameters that need to be specified, required parameters for part 1 and part 2 given as follows:\
Main Folder: the main folder including folders of multi-temporal scenes.\
Clip Feature: A study area\
Number of Samples: An integer that specifies how many sampling points need to be generated within the study area to train data\
Number of Classes: An integer that specifies how many classes are desired to be classified.\
Classes: A string that defines classes names with a comma separator.\
Buffer Points: A checkmark field indicating if the user wants to buffer random points.\

#### Recommendation
Landsat-8 Level-2 scenes are recommended\
Subfolders under the main folder do not need to be preprocessed by the user before running this script. Raw Landsat-8 bands in each temporal folder will be read by the script and processed.

## Case Study

![flowchart](/screenshots/main_folder.png)

![flowchart](/screenshots/result_map.png)

![flowchart](/screenshots/result_chart.png)
