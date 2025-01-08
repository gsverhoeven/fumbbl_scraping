import gzip
import json
import os
import requests
import time

def update_team_skill_jsons(full_run, teamslist, verbose = False):

    n_teams = len(teamslist)

    print("teams to grab:")
    print(n_teams)

    if(full_run):
        for i in range(n_teams):
            if i % 100 == 0: 
                if verbose:
                    # write progress report
                    print(i, end='')
                    print(".")

            team_id = teamslist[i]

            dirname = "raw/team_files/" + str(team_id)[0:4]
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            fname_string = dirname + "/team_" + str(team_id) + "_skills.json" + ".gz"
            # check if file already exists, else scrape it
            try:
                f = open(fname_string, mode = "rb")
                
            except OSError as e:
            # scrape it
                api_string = "https://fumbbl.com/api/team/getOptions/" + str(team_id)

                team_options = requests.get(api_string)
                team_options = team_options.json()
                team_options['tournamentSkills'] = json.loads(team_options['tournamentSkills'])

                with gzip.open(fname_string, mode = "wb") as f:
                    f.write(json.dumps(team_options).encode('utf-8'))
                    f.close()
                if verbose:
                    print("x", end = '')
                time.sleep(0.3)
            else:
                # file already present
                if verbose:
                    print("O", end = '')
                continue 



        # https://github.com/gsverhoeven/fumbbl_datasets/blob/91d9fdfbef3250705a36c5cfba688cf6b858420f/fumbbl_dataset.ipynb            