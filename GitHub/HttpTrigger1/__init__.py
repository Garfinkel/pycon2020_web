import logging
import requests
import azure.functions as func
import pandas as pd
import json


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Repo Name - ie: Microsoft/vscode-python
    L1 = req.params.get('L1')
    L2 = req.params.get('L2')
    repo_name = f'{L1}/{L2}'

    logging.info(f'Repo Name = {repo_name}')

    # Call GitHub and get all open issues for Repo
    api_root = "https://api.github.com"
    request = f'{api_root}/repos/{repo_name}/issues?state=open&sort=created'
    request_header = {'Accept':'application/vnd.github.v3+json'}
    response = requests.get(request, headers = request_header)

    # Turn results into Pandas Dataframe
    dic = json.loads(response.text)
    df_base = pd.DataFrame.from_dict(dic)

    # Grab max page number, and set max # of loops
    maxloop_int = 3
    if response.links != {}:  # if multiple pages exist
        lastpage = response.links['last']['url']
        
        # split URL to extract max page
        lastpage_split = lastpage.split('page=')
        rootpage_string = lastpage_split[0]
        maxpage_int = int(lastpage_split[1])

        if maxpage_int >= maxloop_int:
            maxpage_int = maxloop_int

        # Paginate through first 10 pages
        for i in range(maxpage_int):
            try:   
                # Call Github API
                pag_url = rootpage_string + str(i)
                print(f'Loop#: {i} | {pag_url}')
                pag_response = requests.get(pag_url, headers = request_header)
                
                # Turn results into Pandas Dataframe
                pag_dic = json.loads(pag_response.text)
                pag_df = pd.DataFrame.from_dict(pag_dic)

                # Append to base DF
                df_base = df_base.append(pag_df)
                
                # Set pagination URL for next loop
                pag_url = pag_response.links['next']['url']
            except:
                pass

    # if no pages exist do nothing
    else:
        pass

    # Filter down DB, sort and return DF 
    df_base = df_base.set_index('number')
    df_base = df_base.sort_index(axis = 1) 
    df_base = df_base[['created_at','title','html_url']]   
    logging.info(df_base.shape)
    return func.HttpResponse(df_base.to_string())

    # Repo to test: http://localhost:7071/api/HttpTrigger1?L1=microsoft&L2=vscode-python