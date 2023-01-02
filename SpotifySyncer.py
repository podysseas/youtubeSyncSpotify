import base64
import requests
import logging
import os,json # to remove
log = logging.getLogger(__name__)

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
        self.refresh_token = "AQDOboDf8_ge83Yk5aTX7KDIyOsGH2mUSAMDLNhb3VMeHy0xTMPQxvGxl3Dw62DOQubAUWO7pjUNkxxl1z2qAVettEZywOJGEBVbPDb9gcP7bLR6SJzoGsDElFC1bwAFzYM"
        self.current_offset = 0
        self.songs = []
        
    def setLogLevel(self, level):
        if level == 'DEBUG':
            logging.basicConfig(level = logging.DEBUG)
        else:
            logging.basicConfig(level = logging.INFO)

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
  collected_songs = mySpotify.collect_all_tracks()  
  write_to_json(collected_songs,"songs_liked_spotify.json")
