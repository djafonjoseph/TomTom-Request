# TomTom-Queries
 A brief program to retrieve information from TomTom Routing API for given Origin-Destination
## Contents
* [Description](#Description)
* [Utilisation](#Utilization) 
* [Auteurs](#Authors) 

## Description

This program enables the retrieval of comprehensive route information through queries to TomTom APIs. Given a specific route and departure time, it retrieves travel times under various conditions, including without traffic, with traffic, and historical travel times.

## Utilization

When launching this program, the user will need to specify 5 parameters that the program will ask for:

- Path to input data: This is a database on a closed road network. At a minimum, this database should contain three columns (source, target, geometry) where each row indicates the starting point, destination, and coordinates (longitude, latitude) of these points enclosed in a linestring object (longitude latitude, longitude latitude).

- Path to output folder: this is the path to the folder where the various outputs of the program will be stored.

- Number of routes: this is the number of routes for which you want to gather information.

- Number of waypoints: this is the number of intermediate points you want to include for each route.

- Batch size: itcontrols the program's final output size by determining the number of routes included in each output. For instance, with 100 routes and a batch size of 10, instead of one output with 100 routes, you get 10 outputs, each containing 10 routes. This method efficiently manages data volume, especially as route and waypoint numbers increase. By segmenting road information based on waypoints, output data can rapidly expand, as seen with 100 routes and 100 waypoints resulting in 10,000 lines. Using the batch size helps distribute data across multiple outputs, optimizing efficiency and scalability

- Your TomTom API key: this is your TomTom API key.

## Authors
    
* Joseph Kokouvi DJAFON

* Lucas JAVAUDIN


