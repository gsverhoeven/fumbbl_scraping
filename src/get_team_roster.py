import gzip
import pandas as pd
import numpy as np
import plotnine as p9
import requests
import json
import os
import time

def get_team_roster(team_id, df_skills, df_matches, inducements):

    team_id = int(team_id)

    # Need a combi of Team and Match to get the inducements for the roster: use most recent match
    match_id = df_matches.query('team1_id == @team_id or team2_id == @team_id')['match_id'].max()
    # need tournament id for team (SL)
    tournament_id = df_matches.query('team1_id == @team_id or team2_id == @team_id')['tournament_id'].max()
    tournament_name = df_matches.query('team1_id == @team_id or team2_id == @team_id')['tournament_name'].max()

    dirname = "raw/team_files/" + str(team_id)[0:4]

    fname_string_gz = dirname + "/team_" + str(team_id) + ".json.gz"        

    # PM read compressed json file
    with gzip.open(fname_string_gz, mode = "rb") as f:
        team_obj = json.load(f)

    fname_string_gz = dirname + "/team_" + str(team_id) + "_skills.json.gz"        

    # PM read compressed json file
    with gzip.open(fname_string_gz, mode = "rb") as f:
        team_skill_obj = json.load(f)

    # convert json to pd
    team_obj['team_name'] = team_obj.pop('name')
    df_roster = pd.json_normalize(data = team_obj, record_path = 'players', 
    meta = ['team_name' , 'rerolls', 'assistantCoaches', 'cheerleaders', 'apothecary', ['roster', 'name']])

    df_roster.rename({'id' : 'player_id'}, axis = 1, inplace = True)

    df_roster = df_roster.loc[:, ['player_id', 'number', 'position', 'rerolls', 'assistantCoaches', 'cheerleaders', 'apothecary', 'roster.name', 'team_name']]
  
    df_roster['team_id'] = team_id

    # Next we extract the player skill info into a nice pd dataFrame:
    pd_skills = pd.json_normalize(team_skill_obj, 'tournamentSkills')

    # next we add the skill info to the roster.
    pd_skills = pd.json_normalize(team_skill_obj, 'tournamentSkills')

    if pd_skills.empty is False:    
        pd_skills.columns = ['player_id', 'skill_id']

        pd_skills['player_id'] = pd_skills['player_id'].fillna(0).astype(np.int64)
        pd_skills['skill_id'] = pd_skills['skill_id'].fillna(0).astype(np.int64)

    else:
        pd_skills = pd.DataFrame({'player_id': [-1], 'skill_id': [-1]})

    # Next we add the skill names:
    pd_skills= pd.merge(pd_skills, df_skills, on='skill_id', how='left')

    # next we combine the skills with the roster
    df_roster = pd.merge(df_roster, pd_skills, on='player_id', how='left')

    # Next we add the inducements (Star players, bribes etc)
    if (df_matches.query('match_id == @match_id')['team1_id'].values[0] == team_id):
        inducement_id = 'team1'
    elif (df_matches.query('match_id == @match_id')['team2_id'].values[0] == team_id):
        inducement_id = 'team2'
    else:
        inducement_id = -1

    inducements_to_add = inducements.query('match_id == @match_id and team == @inducement_id')['inducements'].values.tolist()

    for inducement in inducements_to_add:
        if not inducement == ['']:
            new_row = df_roster.iloc[[1]].copy()
            new_row['position'] = inducement
            new_row['player_id'] = 99999999
            new_row['number'] = 99
            new_row['skill_id'] = np.nan
            new_row['name'] = np.nan
            df_roster = pd.concat([df_roster, new_row]) # AttributeError: ‘DataFrame’ object has no attribute ‘append’ is an error that occurs when the append() method is used in Pandas versions 2.0 and beyond

    df_roster = df_roster.infer_objects(copy=False).fillna('')

    # Next we add the coach name
    if (df_matches.query('match_id == @match_id')['team1_id'].values[0] == team_id):
        coach_name = df_matches.query('match_id == @match_id')['coach1_ranking'].values[0]
    elif (df_matches.query('match_id == @match_id')['team2_id'].values[0] == team_id):
        coach_name = df_matches.query('match_id == @match_id')['coach2_ranking'].values[0]
    else:
        coach_name = 'unknown'

    df_roster['coach_name'] = coach_name
    df_roster['tournament_id'] = tournament_id
    df_roster['tournament_name'] = tournament_name
    #df_roster = df_roster.drop(df_roster[df_roster.position == ''].index)
    #df_roster['skill_id'] = df_roster['skill_id'].replace(-1, None)

    return df_roster

def get_tourplay_roster(roster_id):
    dirname = "tourplay/roster_files"

    fname_string_gz = dirname + "/roster_" + str(roster_id) + ".json.gz"     

    # check if file already exists, else scrape it
    try:
        f = open(fname_string_gz, mode = "rb")
    except OSError as e:
        # file not present, scrape it  
        fetch_tourplay_roster(roster_id)
        with gzip.open(fname_string_gz, mode = "rb") as f:
            roster = json.load(f)            
    else:
    # read compressed json file
        with gzip.open(fname_string_gz, mode = "rb") as f:
            roster = json.load(f)    
    df_roster = pd.json_normalize(data = roster, record_path = 'lineUps')
    df_roster = df_roster.loc[:, ['number', 'position', 'skills']]

    skills = []
    for i in range(len(df_roster)):
        obj = df_roster.iloc[i]['skills']
        sc = ""
        for s in range(len(obj)):
            if s == 0:
                sc = sc + obj[s]['skillMaster']['name']
            else:
                sc = sc+ ', ' + obj[s]['skillMaster']['name']
        skills.append(sc)

    df_roster['skills'] = skills
    df_roster['cnt'] = 1

    non_player = {
    'rerolls': roster['reRolls'],
    'assistant_coaches': roster['assistantCoaches'],
    'cheerleaders': roster['cheerLeaders'],
    'dedicated_fans': roster['fanFactor'],
}

    for roster_element in non_player:
        if not roster_element == ['']:
            new_row = df_roster.iloc[[1]].copy()
            new_row['number'] = 99
            new_row['position'] = roster_element        
            new_row['skills'] = ""
            new_row['cnt'] = non_player[roster_element]
            df_roster = pd.concat([df_roster, new_row]) 

    for i in range(len(roster['inducements'])):
        if not roster_element == ['']:
            new_row = df_roster.iloc[[1]].copy()
            new_row['number'] = 99
            new_row['position'] = roster['inducements'][i]['inducementMaster']['name']      
            new_row['skills'] = ""
            new_row['cnt'] = roster['inducements'][i]['quantity']
            df_roster = pd.concat([df_roster, new_row])         

    roster_name = roster['rosterMaster']['name'] 
    team_id = roster_id
    coach_name = roster['player']['userNameToShow']
    group_name = roster['inscriptions'][0]['tournament']['name']

    df_roster['team_id'] = roster_id
    df_roster['coach_name'] = coach_name
    df_roster['tournament_name'] = group_name
    df_roster['roster.name'] = roster_name

    # drop StarPlayer row
    df_roster = df_roster.query("position != 'StarPlayers'")
    df_roster = df_roster.query("cnt != 0")
    return df_roster, roster

def fetch_tourplay_roster(roster_id):
    print(roster_id)
    dirname = "tourplay/roster_files"
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    fname_string = dirname + "/roster_" + str(roster_id) + ".json.gz"

    # check if file already exists, else scrape it
    try:
        f = open(fname_string, mode = "rb")

    except OSError as e:
        # file not present, scrape it         
        api_string = "https://tourplay.net/api/rosters/" + str(roster_id)

        referer = 'https://tourplay.net/en/blood-bowl/roster/' + str(roster_id)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': 'application/json, text/plain, */*', 
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip',
            'Referer': referer,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive'
        }

        response = requests.get(api_string, headers = headers)
        response = response.json()

        with gzip.open(fname_string, mode = "w") as f:
            f.write(json.dumps(response).encode('utf-8'))  
            print('x', end = '')
            f.close()
        time.sleep(0.3)
    else:
        # file already present
        print("o", end = '')

    return 0