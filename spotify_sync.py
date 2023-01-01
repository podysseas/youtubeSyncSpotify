import requests
import base64
import logging
import json
import os
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver


log = logging.getLogger(__name__)
logging.basicConfig(level = logging.DEBUG)

CLIENT_ID = "aab6762d5c88439a88e7d1a990deb6bd"
CLIENT_SECRET = "6b16b06247794089807f865d9e0ff09b"

# endpoint that I'm connecting to on Spotify's servers
TOKEN_URL = "https://accounts.spotify.com/api/token"


class SpotifyService():
    """
        This is the class that manages all of Spotify's interactions
    """

def write_credentials():
  credentials={
              "client_id" : CLIENT_ID, 
              "client_secret" : CLIENT_SECRET,
              "token" : create_token()
  }
  __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
  pathFile = os.path.join(__location__, "credentials.json")
  log.debug("Data are set at: %s" % pathFile)
  with open(pathFile, 'w',encoding='utf-8') as j:
    json.dump(credentials, j,ensure_ascii=False,indent=4)
  return credentials["token"]

def write_to_json(data,filename):
  __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

  pathFile = os.path.join(__location__, filename)
  log.debug("Data are set at: %s" % pathFile)
  with open(pathFile, 'w',encoding='utf-8') as j:
    json.dump(data, j,ensure_ascii=False,indent=4)

def create_test_token(auth_code):
  
  token_url = TOKEN_URL
  token_data = {
    "grant_type": "authorization_code",
    "code" : auth_code,
    "redirect_uri" : "http://127.0.0.1:8000/spotify/callback/"
  }
  client_base64 = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode())
  
  token_headers = { 
    "Authorization":  f"Basic {client_base64.decode()}",
    "Content-Type": "application/x-www-form-urlencoded"
  }
  
  print("Token url : " , token_url)
  print("Code :" , auth_code)
  
  r = requests.post(url=token_url, headers=token_headers, data = token_data)
  print(r.json())
  return r.json()

def refresh_test_token(token_to_refresh):
  
  token_url = TOKEN_URL
  token_data = {
    "grant_type": "refresh_token",
    "refresh_token": token_to_refresh,
  }
  client_base64 = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode())
  
  token_headers = { 
    "Authorization":  f"Basic {client_base64.decode()}",
    "Content-Type": "application/x-www-form-urlencoded"
  }
  
  print("Token url : " , token_url)
  print("Code :" , token_to_refresh)
  
  r = requests.post(url=token_url, headers=token_headers, data = token_data)
  print(r.json())
  return r.json()

def authorize_application():
  CLIENT_ID = "aab6762d5c88439a88e7d1a990deb6bd"

  AUTH_URL = "https://accounts.spotify.com/authorize"
  uri = 'http://127.0.0.1:8000/spotify/callback/'
  scope =  "user-library-read&user-library-modify&user-read-private&user-read-mail&playlist-modify-private&playlist-modify-public&user-follow-public&user-follow-read"
  client_id = "aab6762d5c88439a88e7d1a990deb6bd"
  auth_headers = {
    "client": CLIENT_ID,
    "response_type": "code",
    "redirect_uri":  "http://127.0.0.1:8000/spotify/callback/",
    "scope": scope,
    
  }
  auth_url = f'https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={uri}&scope={scope}'
  # r = requests.get(url=AUTH_URL, headers=auth_headers)
  print(auth_url)
  return auth_url
  
  


def init_driver():
   
  chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
  chrome_options = Options()
  options = [
      "--no-sandbox",
      # comment the next line for local use 
      # "--headless", 
      "--disable-gpu",
      "--window-size=1920,1200",
      "--ignore-certificate-errors",
      "--disable-extensions",
      "--disable-dev-shm-usage",
      "excludeSwitches", "enable-logging"
  ]

  for option in options:
      chrome_options.add_argument(option)

  chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
  # print("enabling perfomance")
  driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

  driver.implicitly_wait(1)

  return driver

def get_liked_songs(token,offset):
  tracks_url = "https://api.spotify.com/v1/me/tracks"
  
  headers = {
      "Authorization": "Bearer " + token,
      
  } 
  params = {
    "offset": str(offset)
  }
  response = requests.get(url=tracks_url, headers=headers,params =params)
  print(response.status_code)
  print(response.request.url)
  print(response.request.body)
  print(response.request.headers)


  response_json = response.json()
  write_to_json(response_json, "saved_songs_spotify.json")
  return response_json

def filter_saved_songs(token,offset):
  # remove available markets 
  d = get_liked_songs(token , offset )
  print("Received ",len(d), " songs")
  for i in range(0,len(d)):
    del d['items'][i]['track']['album']['available_markets']
    del d['items'][i]['track']['available_markets']
    del d['items'][i]['track']['album']['images']
    del d['items'][i]['track']['artists']

  return d["items"]
  
def create_new_data(data):
  d = []
  for item in data:
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


  
     
        
#================================================================
if __name__ == '__main__':
  
  # auth_url = authorize_application()
  # driver = init_driver()
  # driver.get(auth_url)
  # auth_code = "AQAk0mcO0vGC4a7A2Ynwq3juWlykuJuj8vUO4vvqv-gcRzc6pZ7IUsY6SkWK1-UiLOlupVtETZDroYyqFOTUNby8Ixy7Os6n8a3CZLMCxGlTU1bXwMSoGiGH0nV03s8IBXbC3l1E1g9DG8htTZd04kD3rO44J4VDWacrGr8Zv85th-qkmrWNxyMnWQlP7czO6vJ1IAY41NiEhdZLoxc"
  refresh_token = "AQDOboDf8_ge83Yk5aTX7KDIyOsGH2mUSAMDLNhb3VMeHy0xTMPQxvGxl3Dw62DOQubAUWO7pjUNkxxl1z2qAVettEZywOJGEBVbPDb9gcP7bLR6SJzoGsDElFC1bwAFzYM"
  response_token_json = refresh_test_token(refresh_token)
  token = response_token_json['access_token']

  total_songs  = get_liked_songs(token,offset=0)['total']
  log.debug(f"Total songs found : {total_songs}")
  
  
  
  # limit is 20 -> this is the default limit
  offset_div = total_songs//20
  offset_mod = total_songs % 20
  collected_data = []
  for i in range(0,offset_div):
    print("Offset is : " , i*20)
    data = filter_saved_songs(token,i*20)  
    formatted_data = create_new_data(data)
    # print(formatted_data)
    collected_data = collected_data + formatted_data
  if offset_mod > 0 : 
    data = filter_saved_songs(token,offset_div*20)  
    formatted_data = create_new_data(data)
    collected_data = collected_data + formatted_data
  print(len(collected_data))
  write_to_json(collected_data, "formatted_data_spotify.json")
  
  
  
    
  
  