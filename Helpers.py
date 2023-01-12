import datetime
import os 
import logging
import json
import re 
log = logging.getLogger(__name__)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

class Helpers():
    """
        This class  provides helper methods
    """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        
        
    def setLogLevel(self, level):
        if level == 'DEBUG':
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)
    
    def set_file_attribute(self):
        date = datetime.datetime.now()
        return  date.strftime("%m_%d")           

    def write_to_json(self,data,filename):
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        pathFile = os.path.join(__location__, filename)
        log.debug("Data are set at: %s" % pathFile)
        with open(pathFile, 'w',encoding='utf-8') as j:
            json.dump(data, j,ensure_ascii=False,indent=4)

    def load_data(self,filename):
        with open(filename, encoding="utf8") as json_file:
            return  json.load(json_file)

    def remove_old_data(self,source_name):
        pathdir = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        pattern = re.compile("songs_.*"+ source_name + ".*.json")
        for filepath in os.listdir(pathdir):
            if pattern.match(filepath):
                os.remove(os.path.join(__location__, filepath))
                
    def return_old_data(self,source_name):
        pathdir = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        pattern = re.compile("songs_.*"+ source_name + ".*_test.json")
        for filepath in os.listdir(pathdir):
            if pattern.match(filepath):
                log.debug(f"Old data is set to {filepath}")
                return filepath

            
    def compare_songs(self,old_data, new_data):
        if len(old_data) > len(new_data) :
            log.error("Old data is bigger than new data")
            return []
        diff_ids = []
        log.info("Comparing old and new data")
        if len(old_data) != len(new_data):
            log.info("New songs found")
            old_ids = [d['track_id'] for d in old_data]
            new_ids = [d['track_id'] for d in new_data]
            for id in new_ids:
                if id in old_ids:
                    log.debug(f'Already added song with id {id}')
                else:
                    log.debug(f"New song with id {id}')")
                    diff_ids.append(id)
        return diff_ids
