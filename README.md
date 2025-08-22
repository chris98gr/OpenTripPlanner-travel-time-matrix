# Opentripplanner 2.7.0 travel-time matrix (OD matrix)

This repository provides a script to automatically calculate a travel time matrix
for a set of origin and destination points, using OpenTripPlanner. 
The resulting travel time matrix can also be turned into a typical OD matrix, by restructuring the data. 

The script can be used to calculate the matrix for a single starting time of the day or several times within a specified time frame of the day.


# OpenTripPlanner Instance

The script uses an OpenTripPlanner Instance to calculate the travel-time matrix. It was developed and tested 
using a Docker Container running OpenTripPlanner (version 2.7.0). (Assuming there's no changes to the GraphQL API 
it should work with later versions as well)

Information on how to set up and run a local Instance of OpenTripPlanner can be found at https://docs.opentripplanner.org/en/v2.7.0/Basic-Tutorial/


# Using the script

The script reads origin and destination points from separate csv files in the workfiles directory. 
These files should contain the X (longitude) and Y (latitude) coordinate of the points in separate columns as well as 
a fid-column containing a unique ID for each point. (Two examples are provided within the workfiles
directory)

Before starting the script, the parameters for the calculations need to be set within the
OTP-gqlClient.py file.

1. OTP Host information:

    The OTP-HOST variable needs to be set to the IP-Address and Port of the OpenTripPlanner Instance as a String.
    (e.g. if Opentripplanner is set up locally as described in the Tutorial mentioned above, it should be
    set to "localhost:8080")

2. OTP Parameters:

    For the calculations, the script also needs several parameters for the OTP-queries to set the 
    departure time(s) and search window for the routing requests:

   1. DATE_STR: A string representing the Date for the calculations in the format "YYYY-MM-DD" 
   2. TIMEZONE_STR: A string representing the timezone of the study area in the format "+hh:mm"
   3. ED_START_STR: A string representing the start of the time frame for the earliest departure times.
        If only a single departure time per origin/destination pair should be used, the variable should be set to that value. Format: "hh:mm:ss"
   4. ED_END_STR: A string representing the end of the time frame for the earliest departure times.
        If only a single departure time per origin/destination pair should be used, this value should be the same as ED_START_STR. Format: "hh:mm:ss"
   5. STEPSIZE: The stepsize for the earliest departure time in minutes. If set to 10, for example, the script will
        calculate routes for ED_START_STR, ED_START_STR+10min, ED_START_STR+20min, ... until reaching ED_END_STR
        (if only a single departure time should be used, this variable can be ignored)
   6. SEARCH_WINDOW: A string representing the search window for the OTP-queries. (duration between earliest-departure-time and latest-departure-time) 

3. Workfiles and results-file:

    The origins and destinations for the calculations are read from separate csv files. Both files should be placed in the workfiles directory. The names
    of the origin and destination file, as well as the name of the file containing the results, need to be provided in the following parameters:

   1. DESTINATIONS: The name of the csv file containing the destinations
   2. ORIGINS: The name of the csv file containing the origins
   3. CONNECTIONS: Name of the file to put the results in. This file will be stored within the results directory when the script has finished.


After setting all the parameters and setting up an OpenTripPlanner instance, the OTP-gqlClient.py script can be run to start the calculations.
To monitor the progress, the script will print progress messages to the terminal.

When the calculations are done, the results can be found in the "results" directory.

# Results

The results of the calculations are put out as csv files in the "results" directory.
The script creates one file containing the data for successfully calculated connections and 
one file containing the routing errors, where OTP did not calculate a connection.

1. In the results file with the successful calculations, each row represents a connection of two points.
    It contains the following columns:
   1. origin_id: The unique id of the origin point (fid from the origins workfile).
   2. dest_id: The unique id of the destination point (fid from the dests workfile).
   3. dep_time: The (actual) departure time of the connection.
   4. arr_time: The (actual) arrival time of the connection.
   5. travel_time: The travel time of the connection (in minutes).

2. In the errors.csv file, the script stores pairs of origin and destination, where no connection
    was returned by OTP. It contains the origin and destination IDs and some additional details, 
    explaining why no connection was found.