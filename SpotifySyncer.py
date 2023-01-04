import base64
import requests
import logging
import editdistance
import os,json # to remove
from unidecode import unidecode
log = logging.getLogger(__name__)
filename = "log1.txt"
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
pathFile = os.path.join(__location__, filename)
log.debug("Data are set at: %s" % pathFile)
# logging.basicConfig(filename=pathFile,
#                     format="%(asctime)s  %(message)s", filemode="w")
logging.basicConfig()


class SpotifySyncer():
    """
        This is the class that manages all of Spotify's interactions
    """

    def __init__(self):
        """
            This is the constructor for the SpotifyService class
        """
        self.token = ""
        self.client_id = "aab6762d5c88439a88e7d1a990deb6bd"
        self.client_secret = "6b16b06247794089807f865d9e0ff09b"
        self.refresh_token = "AQD1W9ME6QIN1vInbd9ZLSf3uo0YU85Navr3gKUbamH-OUJEGvRdjq_wrHZuhi_WH4yLP64GfGxJOOaozkTbneQsvWBVs3sBOFODV-mYJK5QLOocPjOlkBCFUJXSh1yz8B8"
        self.current_offset = 0
        self.songs = []
        
    def setLogLevel(self, level):
        if level == 'DEBUG':
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)
        
    def renew_token(self):
        """
            Renew the refresh token
        """
        
        token_url = "https://accounts.spotify.com/api/token"
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        client_base64 = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode())

        token_headers = { 
            "Authorization":  f"Basic {client_base64.decode()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(url=token_url, headers=token_headers, data = token_data)
        
        log.debug(f'Request details : {response.request.url} ,body : {response.request.body},headers : {response.request.headers}')
        if response.status_code == 200:
            self.token =  response.json()['access_token']
        else:
            log.info("Something went wrong")
        return 
    
    def get_liked_songs(self):
        """
            Returns a list of the songs liked by the user as JSON object
        """
        tracks_url = "https://api.spotify.com/v1/me/tracks"
        
        headers = {
            "Authorization": "Bearer " + self.token,
        } 
        params = {
            "offset": str(self.current_offset)
        }
        response = requests.get(url=tracks_url, headers=headers,params =params)
        log.debug(f'Request details : {response.request.url} ,body : {response.request.body},headers : {response.request.headers}')
        if response.status_code == 200:
            write_to_json(response.json(),"data.json")

            return response.json()
        else:
            log.info("Something went wrong")
        return

    def get_and_format_liked_songs(self):
        songs = self.get_liked_songs()
        log.info(f"Received {len(songs['items'])} songs")
        # following which items/keys to remove
        # for i in range(0,len(songs)):
        #     del songs['items'][i]['track']['album']['available_markets']
        #     del songs['items'][i]['track']['available_markets']
        #     del songs['items'][i]['track']['album']['images']
        #     del songs['items'][i]['track']['artists']
        return self.format_tracks(songs)
    
    def format_tracks(self,songs):
        """
            Takes the <normal> response  and formats is as a list 
        """
        # reconstruct the list of songs
        d = []
        for item in songs['items']:
            myDict = dict()
            track_id = item['track']['id']
            name_song = item['track']['name']
            artist    = item['track']['album']['artists'][0]['name']
            log.debug(f'Saving track: {track_id}')
            log.debug(f'Name: {name_song}  & Artist: {artist}')
            myDict['name'] = name_song
            myDict['artist'] = artist
            myDict["track_id"] = track_id
            d.append(myDict)
        return d
    
    def format_tracks_search_endpoint(self,songs):
        """
            Takes the <normal> response from SEARCH endpoint and formats is as a list
        """
        # reconstruct the list of songs
        d = []
        for item in songs['items']:
            myDict = dict()
            track_id = item['id']
            name_song = item['name']
            artist    = item['artists'][0]['name']
            log.debug(f'Saving track: {track_id}')
            log.debug(f'Name: {name_song}  & Artist: {artist}')
            myDict['name'] = name_song
            myDict['artist'] = artist
            myDict["track_id"] = track_id
            d.append(myDict)
        return d

    def collect_all_tracks(self):
        total_songs = self.get_liked_songs()['total']
        # limit is 20 -> this is the default limit
        offset_div = total_songs//20
        offset_mod = total_songs % 20
        collected_data = []
        for curr_offset in range(0,offset_div):
            self.current_offset = curr_offset*20
            collected_data = collected_data + self.get_and_format_liked_songs()
        if offset_mod > 0 : 
            self.current_offset = offset_div*20
            collected_data = collected_data + self.get_and_format_liked_songs()
        return collected_data
    
    def search_track(self,query,limit=0):
        search_url = "https://api.spotify.com/v1/search"
        
        headers = {
            "Authorization": "Bearer " + self.token,
        } 
        params = {
            "q": query,
            "type": "track",
            "limit": limit
        }

        response = requests.get(url=search_url,params=params,headers=headers)
        log.debug(f'Request details  : {response.request.url} ,body : {response.request.body},headers : {response.request.headers}')
        log.debug(response.json())
        
        if response.status_code == 200:
            return self.format_tracks_search_endpoint(response.json()['tracks'])
        else:
            log.info("Something went wrong")
        return

    def like_a_song(self,track_id):
        """
            Returns a list of the songs liked by the user as JSON object
        """
        tracks_url = "https://api.spotify.com/v1/me/tracks"
        
        headers = {
            "Authorization": "Bearer " + self.token
        } 
        params = {
            "ids": track_id 
        }
        

        response = requests.put(url=tracks_url,params=params,headers=headers)
        
        # response = requests.put(url=tracks_url, headers=headers,data =data)
        log.debug(f'Request details : {response.request.url} ,body : {response.request.body},headers : {response.request.headers} ')
        log.debug(response.status_code)
        if response.status_code == 200:
            log.info(f'Song with id : {track_id} successfully liked!')
        else:
            log.info("Something went wrong")
#================================================================


def write_to_json(data,filename):
  __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

  pathFile = os.path.join(__location__, filename)
  log.debug("Data are set at: %s" % pathFile)
  with open(pathFile, 'w',encoding='utf-8') as j:
    json.dump(data, j,ensure_ascii=False,indent=4)

if __name__ == '__main__':
  
    mySpotify   = SpotifySyncer()
    mySpotify.setLogLevel('INFO')
    mySpotify.renew_token()
#   collected_songs = mySpotify.collect_all_tracks()  
#   write_to_json(collected_songs,"songs_liked_spotify.json")
    
    #TODO : Fetch first tracks that are liked by Spotify 
    #       save them by id in json format
    #       and then try to like the 'new' ones 
    #
    with open('songs_liked_youtube.json', encoding="utf8") as json_file:
        songs_from_youtube = json.load(json_file)
    
    # mySpotify.like_a_song("0CMYUXTTTmI6Lwc0opH2XG")
    for song in songs_from_youtube:
        title_song = song['title']
        log.info(f'Song from youtube is {song["title"]}')
        title_song_unicode = unidecode(song['title'])
        log.info(f'Song from youtube is in unicode format {title_song_unicode}')
        result = mySpotify.search_track(title_song_unicode,limit = 1)
        log.info(f'Result from SPOTIFY api is {result}')
        mySpotify.like_a_song(result[0]['track_id'])
        
        
        
        
        
            
