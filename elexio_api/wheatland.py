
"""
@author: Peter Boone
email: boonepeterg@gmail.com

Some functions to pull data from the Elexio API. 

Documentation for this API can be found at https://wheatlandpca.elexiochms.com/api_documentation 
(login required)

"""

import requests
import pandas as pd
import os
import getpass


#The base url of Elexio's API
BASEURL = "https://wheatlandpca.elexiochms.com/api"

#Default location to save the files. If left blank the files will be saved in
#the current working directory of the Python script. Format like this: 
_example_location = "C:\\Users\\username\\Downloads\\elexio\\output"
#Note the use of two backslashes...this is important because python treats one 
#backslash as an escape character
DOWNLOAD_LOCATION = ""

#Default delimiter used to save the data
#This DELIMITER is no longer needed when saving to excel files. Leaving 
#it here in case we switch back. 
DELIMITER = "\t"


#these are all of the functions
__all__ = ["get_session_id",
           "download_all",
           "get_pdf_of_user",
           "get_groups",
           "get_users_in_group",
           "get_users_in_all_groups",
           "get_user",
           "get_all_users",
           "get_user_attendance",
           "get_all_attendance",
           "update_all_users"]




#The following few functions are just helper functions (hence the underscore
#before their names)
def _request_get_data(url_suffix, parameters={}):
    """Helper function to get a response with certain parameters and return the data
    """
    url = BASEURL + url_suffix
    response = requests.get(url, params=parameters)
    response.raise_for_status()
    return response.json()['data']

def _parse_names(last_name_dict):
    """Helper function to unpack the data when grouped by last name letter
    """
    big_list = []
    for last_letter, people_with_last in last_name_dict.items():
        for person in people_with_last:
            big_list.append(person)
    return big_list
    

def _get_metadata(session_id):
    """Returns a dictionary of {'text1': 'Race'} etc
    """
    meta_data = _request_get_data('/user/get_meta_data', parameters={"session_id":session_id})
    meta_date_fields = meta_data['dateFieldLabels']
    meta_text_fields = meta_data['textFieldLabels']
    meta_date_fields.update(meta_text_fields)
    return meta_date_fields


def get_session_id(username=None, password=None):
    """Posts username and password and returns a session_id string
    Prompts user for username and password
    """
    if username is not None:
        USERNAME = username
    else:
        print("Enter username and password. Press CTR-C at any time to exit")
        USERNAME = input("Username: ")
    if password is not None:
        PASSWORD = password
    else:
        PASSWORD = getpass.getpass()

    login_info = {'username':USERNAME, 'password':PASSWORD}

    for i in range(3):
        #send a request post with your info in it to receive a session_id
        session_url = BASEURL + "/user/login"
        session_response = requests.post(session_url, data=login_info)
        
        #this will raise an error if we get a 404, 401, or other error, otherwise does nothing
        #print out the error and try again            
        try:
            session_response.raise_for_status()
            break
        except requests.exceptions.HTTPError as err:
            print(err)
            print("Try username and password again")
        USERNAME = input("Username: ")        
        PASSWORD = getpass.getpass()

    #now session_response should have the session id in there if we logged in correctly
    session_json = session_response.json()
    
    
    #this is how you get the value of a key from a dictionary
    session_data = session_json['data']
    
    #get session_id
    return session_data['session_id']



def download_all(session_id, write=True, file_location=DOWNLOAD_LOCATION, 
                 filename="people_all.xlsx", delim=DELIMITER):
    """Requests all of the people and saves it in an excel file
    
    """
    
    people_data = _request_get_data("/people/all", {"session_id":session_id})
    
    #empty list to store people
    big_list = []
    
    #people_data.items() unpacks the keys and values of a dictonary
    #which we can then loop through
    for last_letter, people_with_last in people_data.items():
        for person in people_with_last:
            big_list.append(person)
    
    
    #This gets us the columns in the correct order
    ordered_columns = list(people_data['A'][0].keys())
    
    #pandas is the python package for dealing with data in columns
    data_frame = pd.DataFrame(big_list, columns=ordered_columns)
    
    #get metadata to label the csv
    meta_fields = _get_metadata(session_id)
    
    #rename columns in the dataframe
    for i in range(len(ordered_columns)):
        for field, name in meta_fields.items():
            if ordered_columns[i] == field:
                ordered_columns[i] = name
                
    data_frame.columns = ordered_columns
    
    full_path = os.path.join(file_location, filename)
    
    if write:
        #data_frame.to_csv(full_path, sep=delim)
        data_frame.to_excel(full_path)
        return
    else:
        return data_frame





    
def get_pdf_of_user(session_id, user_id, file_location=DOWNLOAD_LOCATION):
    
    url = BASEURL + '/people/' + str(user_id) 
    parameters = {"session_id": session_id, "format":"pdf"}
    
    pdf_response = requests.get(url, params=parameters)
    pdf_response.raise_for_status()
    
    filename = str(user_id) + '.pdf'
    full_path = os.path.join(file_location, filename)
    with open(full_path, 'wb') as pdf_file:
        pdf_file.write(pdf_response.content)
    return

def get_groups(session_id, write=True, file_location=DOWNLOAD_LOCATION, 
               filename="groups.xlsx", delim=DELIMITER):
    """Gets all of the groups and their descriptions, but not who is in them
    """
    
    groups_data = _request_get_data("/groups/sync", {"session_id": session_id})
    ordered_columns = list(groups_data[0].keys())
    groups_frame = pd.DataFrame(groups_data, columns=ordered_columns)
    
    #clean up the HTML in the description column. Not essential so in a try clause
    try:
        clean = groups_frame['description'].str.replace(r'<p>|</p>', '')
        groups_frame['description'] = clean
    except:
        pass
    
    if write:
        full_path = os.path.join(file_location, filename)
        groups_frame.to_excel(full_path)
        return
    else:
        return groups_frame
    
    

def get_users_in_group(session_id, group_id,  group_name=None, write=True, 
                       file_location=DOWNLOAD_LOCATION, delim=DELIMITER):
    """Gets the users in one group
    """
    url_suffix = "/groups/" + str(group_id) + "/people"
    parameters = {"session_id": session_id}
    
    group_users_data = _request_get_data(url_suffix, parameters)
    
    user_list = _parse_names(group_users_data)
    ordered_columns = user_list[0].keys()
    user_df = pd.DataFrame(user_list, columns=ordered_columns)
    
    #add a group id column and reorder the columns
    user_df['gid'] = group_id
    user_columns = list(user_df.columns)
    user_columns = [user_columns[-1]] + user_columns[:-1]
    user_df = user_df[user_columns]
    if group_name is not None:
        user_df['name'] = group_name
        user_columns = list(user_df.columns)
        user_columns = [user_columns[-1]] + user_columns[:-1]
    user_df = user_df[user_columns]
    

    
    #only need the first 4 columns
    #added if clause so when group name is passed we don't lose uid
    if group_name is not None:
        user_df = user_df.iloc[:, :5]
    else:
        user_df = user_df.iloc[:, :4]
    
    if write:
        filename = 'users_in_group_' + str(group_id) + '.xlsx'
        full_path = os.path.join(file_location, filename)
        user_df.to_excel(full_path)
        return
    else:
        return user_df
    
    
def get_users_in_all_groups(session_id, write=True, file_location=DOWNLOAD_LOCATION, 
                            filename="users_in_all_groups.xlsx", delim=DELIMITER):
    """Gets the people every different group. Will take a while to request every group
    """
    
    group_frame = get_groups(session_id, write=False)
    
    big_df = pd.DataFrame()
    print("Grabbing all of the users in every group. Will take a few minutes...")
    
    for index, rows in group_frame.iterrows():
        gid = rows.gid
        g_name = rows['name']
        if rows.peopleCount == 0:
            #skips groups that don't have anyone in them
            continue
        small_df = get_users_in_group(session_id, gid, write=False, group_name=g_name)
        big_df = big_df.append(small_df, sort=False)
    
    if write:
        full_path = os.path.join(file_location, filename)
        big_df.to_excel(full_path)
        return
    else:
        return big_df

       
    
        
def get_user(session_id, user_id):
    """Gets all of the info on a single person. The family, group, and note data 
    has to be parsed specially
    """
    
    url_suffix = "/people/" + str(user_id)
    parameters = {"session_id":session_id}
    person_data = _request_get_data(url_suffix, parameters)
    
    person_data['fid'] = ""
    if person_data['family'] != []:
        family_list = []
        for person in person_data['family']:
            relative = f"{person['uid']}:{person['relationship']}"
            family_list.append(relative)
            person_data['fid'] = person['fid']
        family_string = " ".join(family_list)
        person_data['family'] = family_string
    
    if person_data['groups'] != []:
        group_list = []
        for group in person_data['groups']:
            group_list.append(str(group['gid']))
        person_data['groups'] = " ".join(group_list)
    if person_data['note']:
        notes = []
        for key, value in person_data['note'].items():
            notes.append(f'{key}:{value}')
        person_data['note'] = " ".join(notes)
    ordered_columns = person_data.keys()
    small_df = pd.DataFrame([person_data], columns=ordered_columns)
    
    return small_df

def get_all_users(session_id, write=True, file_location=DOWNLOAD_LOCATION, 
                  filename='all_users_full.xlsx', delim=DELIMITER):
    """Gets the full data on all of the users, one at a time
    """
    
    people_all = download_all(session_id, write=False)
    big_df = pd.DataFrame()
    print("Grabbing every user one at a time...this will take a few minutes")
    for index, rows in people_all.iterrows():
        small_df = get_user(session_id, rows['uid'])
        big_df = big_df.append(small_df, sort=False)
        
    df_columns = list(big_df.columns)
    meta_fields = _get_metadata(session_id)
    for i in range(len(df_columns)):
        for field, name in meta_fields.items():
            if df_columns[i] == field:
                df_columns[i] = name
    big_df.columns = df_columns
    
    if write:
        full_path = os.path.join(file_location, filename)
        big_df.to_excel(full_path)
        return
    else:
        return big_df


def update_all_users(session_id, input_filepath=None, write=True, 
                     write_file_location=DOWNLOAD_LOCATION, 
                     write_filename="updated_all_users_full.xlsx"):
    """Compares the local users file to the current database online and updates local
    
    input_filepath = full path to local excel file to run through
    
    """
    
    if input_filepath is None:
        input_filepath = os.path.join(DOWNLOAD_LOCATION, "all_users_full.xlsx")
    people_all = download_all(session_id, write=False)
    local_all = pd.read_excel(input_filepath)
    to_append = pd.DataFrame()
    local_list = list(local_all.uid)
    people_list = list(people_all.uid)
    for person in local_list:
        if person not in people_list:
            to_append = to_append.append(get_user(session_id, person), sort=False)
    local_all = local_all.append(to_append)
    if write:
        full_path = os.path.join(write_file_location, write_filename)
        local_all.to_excel(full_path)
        return
    else:
        return local_all


def get_user_attendance(session_id, uid, week_offset=0, number_of_weeks=50, 
                      write=True, file_location=DOWNLOAD_LOCATION, delim=DELIMITER):
    """Gets a single user's attendance. 
    """
    
    url_suffix = "/attendance/for_person/" + str(uid)
    parameters = {"session_id":session_id, 
                  "start": str(week_offset), 
                  "count": str(number_of_weeks)}
    
    
    att_data = _request_get_data(url_suffix, parameters)
    att_items = att_data['items']
    att_df = pd.DataFrame(att_items)
    
    if write:
        filename = "user_" + str(uid) + "_attendance.xlsx"
        full_path = os.path.join(file_location, filename)
        att_df.to_excel(full_path)
        return
    else:
        return att_df

def get_all_attendance(session_id, week_off=0, number_of_weeks=50, write=True, 
                   file_location=DOWNLOAD_LOCATION, filename="all_attendance.xlsx", 
                   delim=DELIMITER):
    """Goes through every user and gets their attendence. 
    
    Parameters
    ----------
    weeks_off = offset back from current week. So 5 would start 5 weeks ago and 
                work backwards from that
    number_of_weeks = the number of events to count. Elexio default is 50. Entering a very 
                large number will ensure that you get everything
    
    """
    
    
    people_all = download_all(session_id, write=False)
    big_df = pd.DataFrame()
    print("Grabbing attendance of every user one at a time...this will take a few minutes")
    for index, rows in people_all.iterrows():
        small_df = get_user_attendance(session_id, uid=rows['uid'],
                                       write=False, week_offset=week_off, 
                                       number_of_weeks=number_of_weeks)
        
        big_df = big_df.append(small_df)
    
    if write:
        full_path = os.path.join(file_location, filename)
        big_df.to_excel(full_path)
        return
    else:
        return big_df


#This code will be executed when this file is run. If this file is imported into
#another python program it will not run

if __name__ == "__main__":
    
    session_id = get_session_id()
    
    
    #download_all(session_id)
    #get_pdf_of_user(session_id, 1149)
    #get_groups(session_id)
    #get_users_in_group(session_id, 19)
    #get_users_in_all_groups(session_id)
    #get_user(session_id, 1149)
    #get_all_users(session_id)
    #get_user_attendance(session_id, 1149)
    #get_all_attendance(session_id)
    #update_all_users(session_id)
    
    


