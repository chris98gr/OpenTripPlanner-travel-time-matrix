from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime
from datetime import timedelta
import pandas as pd

#########################################################################################
#OTP Host IP and Port
OTP_HOST = "localhost:8080"         #IP and Port of the OTP instance


#Parameters for the OTP queries
DATE_STR = "2025-06-28"             #Date of the earliest departure time (format: "YYYY-MM-DD")

TIMEZONE_STR = "+02:00"             #Timezone (format: "+hh:mm")

ED_START_STR = "10:00:00"           #Start of the time window for earliest departure time (format: "hh:mm:ss")

ED_END_STR = "16:00:00"             #End of the time window for earliest departure time (format: "hh:mm:ss")
                                    #set this to the same as ED_START_STR to only get routes for that specific earliest departure time

STEPSIZE = 360                      #Stepsize for the earliest departure time (in minutes)

SEARCH_WINDOW = "PT360M"            #Search window for OTP-routing (format: "PTxHyMzS" where x -> duration in hours, y -> duration in minutes, z -> duration in seconds)

#for a more precise description of the date and time formats, check the ISO 8601 standard

#Names of the workfiles and the csv with the results
DESTINATIONS = "dests.csv"          #csv file with the destination coordinates for the analysis (needs to be in the "workfiles" directory)
ORIGINS = "origins.csv"                     #csv file with the origin coordinates for the analysis (needs to be in the "workfiles" directory)
CONNECTIONS = "example_connections.csv"     #name of the csv file to store the results in (will be saved in the "results" directory)

#########################################################################################

def plan_conn_query(origin_lon, origin_lat, dest_lon, dest_lat, departure_time):

    query_str =f"""
            query {{
                planConnection(
                    destination: {{
                        location: {{
                            coordinate: {{
                                latitude: {dest_lat},
                                longitude: {dest_lon}
                            }}
                        }}
                    }}
                    origin: {{
                        location: {{
                            coordinate: {{
                                latitude: {origin_lat},
                                longitude: {origin_lon}
                            }}
                        }}
                    }}
                    dateTime: {{ earliestDeparture: "{DATE_STR}T{departure_time}{TIMEZONE_STR}" }}
                    searchWindow: "{SEARCH_WINDOW}"
                    first: 1
                ){{
                    edges {{
                        node {{
                            start
                            end
                        }}
                    }}
                    routingErrors{{
                        code
                        description
                        inputField
                    }}
                }}
            }}
        """


    query = gql(query_str)


    return query


#read origins and destinations from csv
dest_df = pd.read_csv('workfiles/' + DESTINATIONS)
origins_df = pd.read_csv('workfiles/' +ORIGINS)

#create gql transport and client
transport = RequestsHTTPTransport(url="http://" + OTP_HOST + "/otp/gtfs/v1",
                                  verify=False,
                                  retries=1)

client = Client(transport=transport, fetch_schema_from_transport=True)

#empty dataframe to put connection data
connections_df = pd.DataFrame()

#otp debug data
routing_errors = pd.DataFrame()

#set end of time window for departure times and stepsize
ed_end = datetime.strptime(ED_END_STR,"%H:%M:%S")
if STEPSIZE < 1:
    step_size = timedelta(minutes=1)
else:
    step_size = timedelta(minutes=STEPSIZE)

#loops for origins and destinations
for origin_row in origins_df.itertuples():
    for dest_row in dest_df.itertuples():

        dep_time = datetime.strptime(ED_START_STR,"%H:%M:%S")

        #loop for different departure times
        while dep_time <= ed_end:
            #create and send graphQL query
            query = plan_conn_query(origin_row.X, origin_row.Y, dest_row.X, dest_row.Y, datetime.strftime(dep_time, "%H:%M:%S"))
            
            response = client.execute(query)
            
            #process response
            if bool(response['planConnection']['edges']):
                start_time = datetime.strptime(response['planConnection']['edges'][0]['node']['start'], '%Y-%m-%dT%H:%M:%S%z')
                end_time = datetime.strptime(response['planConnection']['edges'][0]['node']['end'], '%Y-%m-%dT%H:%M:%S%z')
                travel_time = end_time - start_time
                travel_time_sec = travel_time.total_seconds()

                new_row = pd.DataFrame({'origin_id': [origin_row.fid],
                                        'dest_id': [dest_row.fid],
                                        'dep_time': [datetime.strftime(start_time, '%Y-%m-%dT%H:%M:%S%z')],
                                        'arr_time': [datetime.strftime(end_time, '%Y-%m-%dT%H:%M:%S%z')],
                                        'travel_time': [travel_time_sec/60]})

                connections_df = pd.concat([connections_df, new_row], ignore_index=True)

            elif bool(response['planConnection']['routingErrors']):
                new_row = pd.DataFrame({'origin_id': [origin_row.fid],
                                        'dest_id': [dest_row.fid],
                                        'error': [response['planConnection']['routingErrors'][0]['code']],
                                        'description': [response['planConnection']['routingErrors'][0]['description']]})
                routing_errors = pd.concat([routing_errors, new_row], ignore_index=True)

            else:
                new_row = pd.DataFrame({'origin_id': [origin_row.fid],
                                        'dest_id': [dest_row.fid],
                                        'error': ["UNKNOWN"],
                                        'description': ["The routing result is empty, but there is no errors..."]})
                routing_errors = pd.concat([routing_errors, new_row], ignore_index=True)



            dep_time += step_size

    print("Finished origin " + str(origin_row.fid))


#save results and error-log
connections_df.to_csv('results/' + CONNECTIONS, index=False)
routing_errors.to_csv('results/' + CONNECTIONS + '_errors.csv', index=False)

print("OTP-calculations finished.")



