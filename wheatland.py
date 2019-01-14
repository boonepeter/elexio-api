
"""
Created on Sat Jan 12 11:12:26 2019

@author: Peter Boone
email: boonepeterg@gmail.com
"""

#import the requests library to use to get and post HTTP requests
import requests
import pandas as pd
import os
import getpass

BASEURL = "https://wheatlandpca.elexiochms.com/api"





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

    for i in range(5):
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
    
    if filepath_to_save:
        full_path = os.path.join(filepath_to_save, filename)
    else:
        full_path = filename
    with open(full_path, 'wb') as pdf_file:
        pdf_file.write(pdf_response.content)
        
    return

def get_groups(session_id, write=True):
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
    
    

def get_users_in_group(session_id, group_id, write=True, group_name=None):
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
    
    if write:
        filename = 'users_in_group_' + str(group_id) + '.csv'
        user_df.to_csv(filename)
        return
    else:
        return user_df
    
def big_df_of_users(session_id):
    """Gets the people in different groups. Will take a while to request every group
    """
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
    big_df.to_csv('users_in_all_groups.csv')
    return

       
    
        
def get_user(session_id, user_id):
    url = BASEURL + '/people/' + str(user_id) + '/?session_id=' + session_id
    person_response = requests.get(url)
    person_response.raise_for_status()
    
    return
    
    

if __name__ == "__main__":
    
    session_id = get_session_id()
    
    #download_all(session_id)
    #get_pdf_of_user(session_id, 1149)
    #download_all(get_session_id())
    #get_metadata(get_session_id())
    #get_groups(session_id)
    #get_users_in_group(session_id, 19)
    #big_df_of_users(session_id)

    pass



