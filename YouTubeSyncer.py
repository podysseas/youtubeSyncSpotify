
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime,timedelta
import logging
import json,os # to remove
log = logging.getLogger(__name__)

class YouTubeSyncer():
    """
        This is the class that manages all of Youtube's interactions
    """
    def setLogLevel(self, level):
        if level == 'DEBUG':
            logging.basicConfig(level = logging.DEBUG)
        else:
            logging.basicConfig(level = logging.INFO)

    def __init__(self):
        """
            This is the constructor for the YoutubeService class
        """
        self.client_secrets_file = "client_secret_desktop.json"
        self.scope = ['https://www.googleapis.com/auth/youtube.force-ssl']
        self.api_service_name = 'youtube'
        self.api_version = 'v3'
        self.credentials  = ""
        self.service = ""
        self.nextPageToken ="test" # dummy workaround to start 
        
    def get_authenticated_service(self):
        ''' 
            Loads and returns an authorized YouTube API service.
        '''
        self.service = build(
            self.api_service_name, self.api_version, credentials=self.credentials,cache_discovery=False)

    def load_credentials(self):
        """
            Loads the credentials in the object
        """
        if os.path.exists("CREDENTIALS_PICKLE_FILE"):
            log.info("Using old files credentials!")
            with open("CREDENTIALS_PICKLE_FILE", 'rb') as f:
                self.credentials = pickle.load(f)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, self.scope)
            self.credentials = flow.run_console()
            with open("CREDENTIALS_PICKLE_FILE", 'wb') as f:
                pickle.dump(self.credentials, f)
        log.info(self.credentials)
        if self.cred_is_valid():
            log.debug("Loaded credentials successfully")
        else:
            exit(1)
        
    # create a method to automatic renew credentials after 6 days 
    def renew_credentials(self):
        '''
        This method should be called to renew credentials
        '''
        if os.path.exists("CREDENTIALS_PICKLE_FILE"):
            print("Using old files credentials!")
            with open("CREDENTIALS_PICKLE_FILE", 'rb') as f:
                self.credentials = pickle.load(f)
        
        self.credentials.refresh(Request())
    
    def get_liked_songs(self):
        """
            This method returns a list of songs that are liked by the user
        """
        if self.nextPageToken !="test": 
            resp = self.service.videos().list(part="snippet,contentDetails,statistics",
                                            myRating = "like",
                                            prettyPrint=True,
                                            maxResults=30,pageToken=self.nextPageToken).execute()
            if "nextPageToken" in resp.keys():
                log.debug("Transferring to next page")
            else:
                log.debug("This is the last page")
                self.nextPageToken =""
            return resp 
        else:
            return self.service.videos().list(part="snippet,contentDetails,statistics",
                                            myRating = "like",
                                            prettyPrint=True,
                                            maxResults=30).execute()

    
    def cred_is_valid(self):
        log.info(f'Expiration date : {self.credentials.expiry}')
        now = datetime.now()
        time_period = now - self.credentials.expiry
        if time_period.days >=7:
            log.info("If app is on Testing status,refresh tokens are expired.Please manually update!")
            return False
        else:
            log.info("Refresh token will be used to refresh the access token")
            self.renew_credentials()
            log.info(f'New expiration date : {self.credentials.expiry}')
            return True
    
    def get_and_format_liked_songs(self):
        songs = self.get_liked_songs()
        # reconstruct the list of songs
        d = []
        for item in songs['items']:
            if item["snippet"]["categoryId"] == "10" : # take only music"
                log.debug(f'Saving track: {item["id"]}')
                log.debug(f'Name: {item["snippet"]["title"]}  & Category : {item["snippet"]["categoryId"]}')
                myDict = dict()
                myDict["id"] = item["id"]
                myDict["categoryId"] = item["snippet"]["categoryId"]
                myDict["title"] = item["snippet"]["title"]
                d.append(myDict)
        return d
    
    def collect_all_tracks(self):
        if self.cred_is_valid():
            collected_data =[]
            while self.nextPageToken != "":
                self.nextPageToken = myYouTube.get_liked_songs()["nextPageToken"]
                collected_data = collected_data + self.get_and_format_liked_songs()
            return collected_data
        else:
            log.info("Something bad happened!")    
            
#================================================================

def write_to_json(data,filename):
  __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

  pathFile = os.path.join(__location__, filename)
  log.debug("Data are set at: %s" % pathFile)
  with open(pathFile, 'w',encoding='utf-8') as j:
    json.dump(data, j,ensure_ascii=False,indent=4)

if __name__ == '__main__':
  
  myYouTube   = YouTubeSyncer()
  myYouTube.setLogLevel('DEBUG')
  myYouTube.load_credentials()
  myYouTube.get_authenticated_service()
  collected_songs = myYouTube.collect_all_tracks()  
  write_to_json(collected_songs,"songs_liked_youtube.json")
  
    