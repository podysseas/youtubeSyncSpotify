

# Sample Python code for user authorization

import os
import pickle
import google.oauth2.credentials
import json 
from googleapiclient.discovery import build,Resource
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging
# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret_desktop.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
log = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)
def get_authenticated_service():
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        print("Using old files credentials!")
        with open("CREDENTIALS_PICKLE_FILE", 'rb') as f:
            credentials = pickle.load(f)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_console()
        with open("CREDENTIALS_PICKLE_FILE", 'wb') as f:
            pickle.dump(credentials, f)
    return build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials,cache_discovery=False)

# create a method to automatic renew credentials after 6 days 
def existing_credentials():
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        print("Using old files credentials!")
        with open("CREDENTIALS_PICKLE_FILE", 'rb') as f:
            credentials = pickle.load(f)
    # credentials.refresh(Request())
    return credentials

def extract_next_token(response):
  if "nextPageToken" in response:
    print("Next token =>: ",response["nextPageToken"])
    return response["nextPageToken"]
  else:
    print("No next token provided.")
    write_to_json(response,"data_response.json")
    return ""

def extract_next_page_liked_videos(service,nextPage):
  return service.videos().list(part="snippet,contentDetails,statistics",
                                       myRating = "like",
                                       prettyPrint=True,
                                       maxResults=10,
                                       pageToken=nextPage).execute()

def update_list_videos(videos_list,response):
    d = []
    log.debug("Updating videos list...")
    for it in response["items"]:
      
      if it["snippet"]["categoryId"] == "10":
        log.debug("This is a music video!")
        log.debug("Saving video with id %s",it["id"], " with category %s",it["snippet"]["categoryId"],
                  " and title %s",it["snippet"]["title"])
        myDict = dict()
        myDict["id"] = it["id"]
        myDict["catageryId"] = it["snippet"]["categoryId"]
        myDict["title"] = it["snippet"]["title"]
        videos_list.append(myDict)
    return videos_list

def write_to_json(data,filename):
  __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

  pathFile = os.path.join(__location__, filename)
  log.debug("Data are set at: %s" % pathFile)
  with open(pathFile, 'w',encoding='utf-8') as j:
    json.dump(data, j,ensure_ascii=False,indent=4)

if __name__ == '__main__':
  # When running locally, disable OAuthlib's HTTPs verification. When
  # running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
  service = get_authenticated_service()
  
  # cred = existing_credentials()
  # print(cred.expiry)
 
  response = service.videos().list(part="snippet,contentDetails,statistics",
                                        myRating = "like",
                                        prettyPrint=True,
                                        maxResults=30).execute()
  
  videos_list=[]
  next_token="test"
  while next_token != "":
    next_token  = extract_next_token(response)
    response = extract_next_page_liked_videos(service,next_token)
    videos_list = update_list_videos(videos_list,response)

  unique = { each['id'] : each for each in videos_list }
  
  write_to_json(videos_list,"data.json")
  write_to_json(unique,"data_unique.json")
  write_to_json(response,"response.json")

  

