
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
import json



def configure():
    with open("config.json", "r") as config_file:
        config_dict = json.load(config_file)
        
    if config_dict["Configured"] == "False":
        print("Configure your base URL...")
        print("An example is: 'https://wheatlandpca.elexiochms.com/api'")
        session_id = ""
        while session_id == "":
            base = input("Enter your base URL: ")
            session_id = get_session_id()
            if session_id == "":
                print("It looks like that base url is not valid. Try again")
        
        config_dict["BASEURL"] = base
        config_dict["Configure"] = "False"
        with open("config.json", "w") as config_file:
            config_file.write(json.dumps(config_dict))
    return

def base_url():
    with open("config.json", "r") as config_file:
        config_dict = json.load(config_file)
    return config_dict["BASEURL"]

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


def download_all(session_id, write=True, path_to_download="people_all.csv"):
    """Requests all of the people and formats it in a csv
    path_to_download: file name or full file path. If just file name, 
                      will save to current working directory
    
    """
    people_url = BASEURL + '/people/all' + '?session_id=' + session_id
    
    people_all_response = requests.get(people_url)
    people_all_response.raise_for_status()
    
    #this response object will have a json of all of the people in the database
    people_json = people_all_response.json()
    people_data = people_json['data']
    
    
    #empty list to store people
    big_list = []
    
    #people_data.items() unpacks the keys and values of a dictonary
    #which we can then loop through
    for last_letter, people_with_last in people_data.items():
        for person in people_with_last:
            big_list.append(person)
    
    
    #This gets us the columns in the correct order
    ordered_columns = list(people_json['data']['A'][0].keys())
    
    #pandas is the python package for dealing with data in columns
    data_frame = pd.DataFrame(big_list, columns=ordered_columns)
    
    #get metadata to label the csv
    meta_fields = get_metadata(session_id)
    
    #rename columns in the dataframe
    for i in range(len(ordered_columns)):
        for field, name in meta_fields.items():
            if ordered_columns[i] == field:
                ordered_columns[i] = name
                
    data_frame.columns = ordered_columns
    
    if write:
        data_frame.to_csv(path_to_download)
        return
    else:
        return data_frame


def _parse_names(last_name_dict):
    
    big_list = []
    
    #people_data.items() unpacks the keys and values of a dictonary
    #which we can then loop through
    for last_letter, people_with_last in last_name_dict.items():
        for person in people_with_last:
            big_list.append(person)
    return big_list
    


def get_metadata(session_id):
    """Returns a dictionary of {'text1': 'Race'} etc
    """
    
    url = BASEURL + '/user/get_meta_data' + '?session_id=' + session_id
    metadata_response = requests.get(url)
    
    metadata_response.raise_for_status()
    meta_json = metadata_response.json()
    meta_date_fields = meta_json['data']['dateFieldLabels']
    meta_text_fields = meta_json['data']['textFieldLabels']

    meta_date_fields.update(meta_text_fields)
    
    return meta_date_fields
    
def get_pdf_of_user(session_id, user_id, filepath_to_save=None):
    url = BASEURL + '/people/' + str(user_id) + '/?session_id=' + session_id + '&format=pdf'
    
    pdf_response = requests.get(url)
    pdf_response.raise_for_status()
    
    filename = str(user_id) + '.pdf'
    
    if filepath_to_save is not None:
        full_path = os.path.join(filepath_to_save, filename)
    else:
        full_path = filename
    with open(full_path, 'wb') as pdf_file:
        pdf_file.write(pdf_response.content)
    return

def get_groups(session_id, write=True):
    """Gets all of the groups and their descriptions, but not who is in them
    """
    url = BASEURL + '/groups/sync?session_id=' + session_id
    groups_response = requests.get(url)
    groups_response.raise_for_status()
    groups_data = groups_response.json()['data']
    ordered_columns = list(groups_data[0].keys())
    groups_frame = pd.DataFrame(groups_data, columns=ordered_columns)
    
    #clean up the HTML in the description column. Not essential so in a try
    try:
        clean = groups_frame['description'].str.replace(r'<p>|</p>', '')
        groups_frame['description'] = clean
    except:
        pass
    if write:
        groups_frame.to_csv('groups.csv')
        return
    else:
        return groups_frame
    
    

def get_users_in_group(session_id, group_id, write=True, group_name=None, filepath=None):
    
    url = BASEURL + '/groups/' + str(group_id) + '/people?session_id=' + session_id
    
    users_in_request = requests.get(url)
    users_in_request.raise_for_status()
    users_data = users_in_request.json()['data']
    user_list = _parse_names(users_data)
    ordered_columns = user_list[0].keys()
    user_df = pd.DataFrame(user_list, columns=ordered_columns)
    user_df['gid'] = group_id
    user_columns = list(user_df.columns)
    user_columns = [user_columns[-1]] + user_columns[:-1]
    user_df = user_df[user_columns]    
    if group_name is not None:
        user_df['name'] = group_name
        user_columns = list(user_df.columns)
        user_columns = [user_columns[-1]] + user_columns[:-1]
    user_df = user_df[user_columns]
    
    
    #rename columns in the dataframe
    meta_fields = get_metadata(session_id)
    for i in range(len(user_columns)):
        for field, name in meta_fields.items():
            if user_columns[i] == field:
                user_columns[i] = name
    user_df.columns = user_columns
    
    #only need the first 4 columns
    #added if clause so when group name is passed we don't lose uid
    if group_name is not None:
        user_df = user_df.iloc[:, :5]
    else:
        user_df = user_df.iloc[:, :4]
    
    if write:
        filename = 'users_in_group_' + str(group_id) + '.csv'
        if filepath is not None:
            filename = os.path.join(filepath, filename)
        user_df.to_csv(filename)
        return
    else:
        return user_df
    
    
def big_df_of_users(session_id, filepath=None):
    """Gets the people in different groups. Will take a while to request every group
    """
    filename = "users_in_all_groups.csv"
    group_frame = get_groups(session_id, write=False)
    
    big_df = pd.DataFrame()
    for index, rows in group_frame.iterrows():
        print(f'adding group {rows.gid}')
        gid = rows.gid
        g_name = rows['name']
        if rows.peopleCount == 0:
            print(f'skipping {gid}')
            continue
        small_df = get_users_in_group(session_id, gid, write=False, group_name=g_name)
        big_df = big_df.append(small_df)
        
    if filepath is not None:
        filename = os.path.join(filepath, filename)
    big_df.to_csv(filename)
    
    return

       
    
        
def get_user(session_id, user_id):
    url = BASEURL + '/people/' + str(user_id) + '/?session_id=' + session_id
    person_response = requests.get(url)
    person_response.raise_for_status()
    
    person_data = person_response.json()['data']
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

def get_all_users(session_id, filename='all_users_big.csv'):
    
    people_all = download_all(session_id, write=False)
    big_df = pd.DataFrame()
    print("Grabbing every user one at a time...this will take a few minutes")
    for index, rows in people_all.iterrows():
        small_df = get_user(session_id, rows['uid'])
        big_df = big_df.append(small_df)
        
    df_columns = list(big_df.columns)
    meta_fields = get_metadata(session_id)
    for i in range(len(df_columns)):
        for field, name in meta_fields.items():
            if df_columns[i] == field:
                df_columns[i] = name
    big_df.columns = df_columns
    
    big_df.to_csv(filename)
    return


def person_attendance(session_id, uid, week_offset=0, number_of_weeks=50):
    
    url = BASEURL + '/attendance/for_person/' + str(uid) + '?session_id=' \
               + session_id + '&start=' + str(week_offset) + '&count=' \
               + str(number_of_weeks)

    att_request = requests.get(url)
    att_request.raise_for_status()
    
    att_items = att_request.json()['data']['items']
    att_df = pd.DataFrame(att_items)

    return att_df

def all_attendance(session_id, filename='all_attendance.csv', week_off=0, count=50):
    """Goes through every user and gets their attendence. 
    
    Parameters
    ----------
    weeks_off = offset back from current week. So 5 would start 5 weeks ago and 
                work backwards from that
    count = the number of events to count. Elexio default is 50. Entering a very 
                large number will ensure that you get everything
    
    """
    
    people_all = download_all(session_id, write=False)
    big_df = pd.DataFrame()
    print("Grabbing attendance of every user one at a time...this will take a few minutes")
    for index, rows in people_all.iterrows():
        small_df = person_attendance(session_id, uid=rows['uid'], 
                                     week_offset=week_off, 
                                     number_of_weeks=count)
        
        big_df = big_df.append(small_df)
    big_df.to_csv(filename)
    return

if __name__ == "__main__":
    configure()
    BASEURL = base_url()
    
    
    
    
    
    
    
    
    
    