
import pickle
from unidecode import unidecode

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime,timedelta
import logging
import json,os # to remove
log = logging.getLogger(__name__)
from Helpers import Helpers

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
                                            maxResults=50,pageToken=self.nextPageToken).execute()
            if "nextPageToken" in resp.keys():
                log.debug("Transferring to next page")
            else:
                log.debug("This is the last page")
                self.nextPageToken =""
            # write_to_json(resp,"data.json")
            return resp 
        else:
            return self.service.videos().list(part="snippet,contentDetails,statistics",
                                            myRating = "like",
                                            prettyPrint=True,
                                            maxResults=50).execute()

    
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
        return self.format_tracks(songs)
    
    def format_tracks(self,songs):
        d = []
        for item in songs['items']:
            if item["snippet"]["categoryId"] == "10" : # take only music"
                log.debug(f'Saving track: {item["id"]}')
                log.debug(f'Name: {item["snippet"]["title"]}  & Category : {item["snippet"]["categoryId"]}')
                myDict = dict()
                myDict["track_id"] = item["id"]
                myDict["categoryId"] = item["snippet"]["categoryId"]
                myDict["title"] = item["snippet"]["title"]
                d.append(myDict)
        return d
      
    def collect_all_tracks(self):
        if self.cred_is_valid():
            collected_data =[]
            while self.nextPageToken != "":
                self.nextPageToken = self.get_liked_songs()["nextPageToken"]
                collected_data = collected_data + self.get_and_format_liked_songs()
            return collected_data
        else:
            log.info("Something bad happened!")    
            
    def search_track(self,keyword):
        return self.service.search().list(
                part="snippet",
                maxResults=50,
                q=keyword
            ).execute()["items"][0]
    
    def like_track(self,video_id): # needs format
        return self.service.videos().rate(
                id=video_id,
                rating="like"
            ).execute() 
    
    def is_new(self, track_id):
        with open('songs_from_youtube.json', encoding="utf8") as json_file:
            songs_from_youtube = json.load(json_file)
        log.debug(f'Checking if track with {track_id} is already liked.')
        new = len([song['track_id'] for song in songs_from_youtube if song['track_id']] ) == 0
        return new

#================================================================



if __name__ == '__main__':
  
    myYouTube   = YouTubeSyncer()
    myYouTube.setLogLevel('INFO')
    myYouTube.load_credentials()
    myYouTube.get_authenticated_service()
    collected_songs = myYouTube.collect_all_tracks()
    helpers = Helpers()
    new_filename = "songs_liked_youtube_"  + helpers.set_file_attribute() + ".json"
    helpers.write_to_json(collected_songs,new_filename)


    # Extract diff data from Youtube
    old_data = helpers.load_data(filename=helpers.return_old_data("youtube"))
    new_data = helpers.load_data(filename=new_filename)
    diff = helpers.compare_songs(old_data, new_data)
    if len(diff) != 0:
        d = []
        for track_id in diff:
            info_id = [ item for item in new_data if item['track_id'] == track_id] 
            log.info(f'Info of new song is {info_id}')
            d.append(info_id)
        helpers.write_to_json(d,"new_songs_from_youtube.json")            

    # Like the new ones from Spotify
    new_songs_from_spotify = helpers.load_data('new_songs_from_spotify.json')
    
    for song in new_songs_from_spotify:
        title_song = str(song[0]['title']) + "-" + str(song[0]['artist']) # different format from Spotify
    
        log.info(f'Song from spotify is preformated way   {title_song}')
        title_song_unicode = unidecode( title_song)
        log.info(f'Song from spotify is in unicode format {title_song_unicode}')
        result = myYouTube.search_track(title_song_unicode)
        log.info(f"Result from YOUTUBE api is {result['snippet']['title']}")
        if myYouTube.is_new(result['id']['videoId']):
            log.debug("We will like the song")
            myYouTube.like_track(result['id']["videoId"])
        else:
            log.debug(f'Song from spotify is already liked')
       
        
    
        
       
        
         
        