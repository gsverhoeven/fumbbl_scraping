
import time
import gzip
import json
import pandas as pd


def process_team_jsons(team_ids, fullrun, target = None):

    n_teams = len(team_ids)
    if target is None:
        target = 'raw/df_teams_' + time.strftime("%Y%m%d_%H%M%S") + '.h5'

    if fullrun:
        team_id = []
        division_id = []
        division_name = []
        league = []
        ruleset_id = []
        roster_id = []
        race_name = []
        games_played = []

        print('processing team data for ', n_teams, ' teams')

        for t in range(n_teams):    
            team_id_tmp = int(team_ids[t])
            dirname = "raw/team_files/" + str(team_id_tmp)[0:4]

            fname_string = dirname + "/team_" + str(team_id_tmp) + ".json"                
            fname_string_gz = dirname + "/team_" + str(team_id_tmp) + ".json.gz"        
            
            # read compressed json file
            try:
                f = gzip.open(fname_string_gz, mode = "rb")
                
            except OSError as e:
                try:
                    f = open(fname_string, mode = "rb")
                except OSError as e:
                    print(" missing team")
                else:
                    pass
            else:
                pass
            try:
                team = json.load(f)

            except json.JSONDecodeError as e:
                print(fname_string_gz)
                print("Error: Unable to decode JSON, Error: {}. ".format(e))
                continue

            if str(team) != 'No such team.':
                # grab fields
                team_id.append(team['id'])
                division_id.append(team['divisionId'])
                division_name.append(team['division'])
                league.append(team['league'])
                ruleset_id.append(team['ruleset'])
                roster_id.append(team['roster']['id'])
                race_name.append(team['roster']['name'])
                games_played.append(team['record']['games']) 

            if t % 10000 == 0: 
                print(t, end='')
                print(".", end='')

        data = zip(team_id, division_id, division_name, league, ruleset_id, roster_id, race_name,  games_played)
                
        df_teams = pd.DataFrame(data, columns=['team_id', 'division_id', 'division_name',  'league' ,
        'ruleset_id', 'roster_id', 'race_name',  'games_played'])
        df_teams.to_hdf(target, key='df_teams', mode='w')


    else:
        # read from hdf5 file
        if target is None:
            print("error choose target file")
        df_teams = pd.read_hdf(target)

    df_teams['roster_name'] = df_teams['roster_id'].astype(str) + '_' + df_teams['race_name']

    df_teams['division_id'] = pd.to_numeric(df_teams.division_id) 
    df_teams['roster_id'] = pd.to_numeric(df_teams.roster_id) 
    df_teams['team_id'] = pd.to_numeric(df_teams.team_id) 
    df_teams['games_played'] = pd.to_numeric(df_teams.games_played) 

    df_teams['league'] = pd.to_numeric(df_teams.league) 
    df_teams['ruleset_id'] = pd.to_numeric(df_teams.ruleset_id) 
    
    return df_teams

    