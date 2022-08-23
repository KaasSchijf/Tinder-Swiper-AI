import ctypes
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from termcolor import colored
import random
import time
import requests
import pandas as pd
from geopy.geocoders import Nominatim
import datetime
from Modules.likeliness_classifier import Classifier
import tensorflow.compat.v1 as tf
import Modules.person_detector as person_detector

geolocator = Nominatim(user_agent="auto-tinder")
TINDER_URL = "https://api.gotinder.com"

#change window title
liked = disliked = newmatches = 0
def title(liked, disliked, newmatches):
    ctypes.windll.kernel32.SetConsoleTitleW(f"Tinder Swiper | Likes : {str(liked)} | Disliked : {str(disliked)} | New Matches  {str(newmatches)}")

class tinderAPI():
    def __init__(self, token):
        self._token = token

    def nearby_persons(self):
        data = requests.get(TINDER_URL + "/v2/recs/core", headers={"X-Auth-Token": self._token})
        data = list(map(lambda user: Person(user, self), data.json()["data"]["results"]))
        return data

    def like(self, person):
        data = requests.post(TINDER_URL + f"/like/{person.id}", data={"content_hash": person.content_hash, "s_number": person.s_number}, headers={"X-Auth-Token": self._token}).text
        return data

    def refreshtoken(self, account, index):
        data = 'RR\n' + account['Refreshtoken']
        headers = {
            'content-type': 'application/x-google-protobuf',
            'dnt': '1',
            'is-created-as-guest': 'false',
            'origin': 'https://tinder.com',
            'persistent-device-id': '35bb0250-7981-4258-bead-8cd89bff674d',
            'platform': 'android',
            'tinder-version': '3.41.0',
            'user-session-id': 'null',
            'user-session-time-elapsed': '1',
            'x-auth-token': self._token,
        }

        response = requests.post('https://api.gotinder.com/v3/auth/login?locale=nl', headers=headers, data=data)
        print(response.text)

        token = response.text.split('$')[1].split('"')[0]
        refreshtoken = 'Pey' + response.text.split('Pey')[1].split('')[0]

        df = pd.read_csv("Accounts.csv")
        df.loc[index, "Token"] = token
        df.loc[index, "Refreshtoken"] = refreshtoken
        account['Token'] = token
        account["Refreshtoken"] = refreshtoken
        df.to_csv("Accounts.csv", index=False)
        print(colored(f"[{str(datetime.datetime.now())}] New Login token generated!", 'green'))
        return account

    def dislike(self, person):
        requests.get(TINDER_URL + f"/pass/{person.id}?s_number={person.s_number}&content_hash={person.content_hash}", headers={"X-Auth-Token": self._token}).json()
        return True

    def matches(self, limit=60):
        matches = []
        try:
            data = requests.get(TINDER_URL + f"/v2/matches?count={limit}", headers={"X-Auth-Token": self._token}).json()
            for match in data["data"]["matches"]:
                matches.append(match['_id'])
        except:
            pass
        return matches

    def boost(self):
        requests.post(TINDER_URL +'/boost', headers={"X-Auth-Token": self._token}, json={"amount": 1})
        return True

class Person(object):

    def __init__(self, data, api):
        self._api = api

        self.id = data["user"]["_id"]
        self.name = data["user"].get("name", "Unknown")

        self.bio = data["user"].get("bio", "")
        self.distance = float(data["distance_mi"]) / 0.62137

        self.birth_date = datetime.datetime.strptime(data['user']["birth_date"], '%Y-%m-%dT%H:%M:%S.%fZ') if data.get("birth_date", False) else None
        self.gender = ["Male", "Female", "Unknown"][data["user"].get("gender", 2)]

        self.images = list(map(lambda photo: photo["url"], data["user"].get("photos", [])))
        self.s_number = data['s_number']
        self.content_hash = data['content_hash']

        self.jobs = list(map(lambda job: {"title": job.get("title", {}).get("name"), "company": job.get("company", {}).get("name")}, data["user"].get("jobs", [])))
        self.schools = list(map(lambda school: school["name"], data["user"].get("schools", [])))

        if data["user"].get("pos", False):
            self.location = geolocator.reverse(f'{data["user"]["pos"]["lat"]}, {data["user"]["pos"]["lon"]}')

    def like(self):
        return self._api.like(self)

    def dislike(self):
        return self._api.dislike(self)

    def download_images(self, folder, images):
        index = -1
        for image_url in images:
            index += 1
            req = requests.get(image_url, stream=True)
            if req.status_code == 200:
                with open(f"{folder}/{self.id}_{self.name}_{index}.jpeg", "wb") as f:
                    f.write(req.content)
            time.sleep(0.2)

    def predict_likeliness(self, classifier, sess):
        ratings = []
        for image in self.images:
            req = requests.get(image, stream=True)
            tmp_filename = f"./Modules/images/tmp/run.jpg"
            if req.status_code == 200:
                with open(tmp_filename, "wb") as f:
                    f.write(req.content)
            img = person_detector.get_person(tmp_filename, sess)
            if img:
                img = img.convert('L')
                img.save(tmp_filename, "jpeg")
                certainty = classifier.classify(tmp_filename)
                pos = certainty["positive"]
                ratings.append(pos)
        ratings.sort(reverse=True)
        ratings = ratings[:5]
        if len(ratings) == 0:
            return 0.001
        return ratings[0]*0.6 + sum(ratings[1:])/len(ratings[1:])*0.4

def tokengen(accounts, index):
    phone = accounts[index]['Phone'].replace('+', '')
    try:
        s = requests.Session()
        headers = {
            'authority': 'api.gotinder.com',
            'app-session-id': 'f45c2040-3b7a-440e-9285-81a0caef9c9f',
            'app-session-time-elapsed': '1',
            'app-version': '1033900',
            'content-type': 'application/x-google-protobuf',
            'is-created-as-guest': 'false',
            'origin': 'https://tinder.com',
            'persistent-device-id': '35bb0250-7981-4258-bead-8cd89bff674d',
            'platform': 'android',
            'tinder-version': '3.39.0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'user-session-id': 'null',
            'user-session-time-elapsed': '1',
        }

        data = '''\n\r\n''' + phone
        print(colored(f"[{str(datetime.datetime.now())}] Logging into [{accounts[index]['Phone']}]...", 'yellow'))
        response = s.post('https://api.gotinder.com/v3/auth/login?locale=nl', headers=headers, data=data)
        if phone in response.text:
            phonecode = input("\n\nVerification Code" + colored(' > ', 'magenta'))
            data = '''\n\r\n''' + phone + '' + str(phonecode)
            response = s.post('https://api.gotinder.com/v3/auth/login?locale=nl', headers=headers, data=data)
            if '@' in response.text:
                key = 'Pey' + response.text.split('Pey')[1].split('')[0]
                emailcode = input("\n\nEmail Code" + colored(' > ', 'magenta'))
                data = '''*\''' + str(emailcode) + '''R\n''' + key
                response = s.post('https://api.gotinder.com/v3/auth/login?locale=nl', headers=headers, data=data)

            token = response.text.split('$')[1].split('"')[0]
            refreshtoken = 'Pey' + response.text.split('Pey')[1].split('')[0]

            df = pd.read_csv("Accounts.csv")
            df.loc[index, "Token"] = token
            df.loc[index, "Refreshtoken"] = refreshtoken
            df.to_csv("Accounts.csv", index=False)
            print(colored(f"[{str(datetime.datetime.now())}] Login token generated!", 'green'))
            return token
        else:
            print('Error logging into [' + accounts[index]['Phone'] + ']...')
    except:
        print('Error logging into [' + accounts[index]['Phone'] + ']...')


def autoliking(account, index):
    global liked, disliked, newmatches
    active = True
    api = tinderAPI(account['Token'])

    #activate tinder boost
    #api.boost()

    matcheslist = api.matches()

    while active:
        detection_graph = person_detector.open_graph()
        with detection_graph.as_default():
            with tf.Session() as sess:

                classifier = Classifier(graph="./Modules/tf/training_output/retrained_graph.pb", labels="./Modules/tf/training_output/retrained_labels.txt")

                end_time = time.time() + 60 * 60 * 2
                while active:
                    try:
                        try:
                            persons = api.nearby_persons()
                        except:
                            print(colored( f"{account['Name']} [{str(datetime.datetime.now())}] Renewing token...",'red'))
                            account = api.refreshtoken(account, index)

                        #check if new match
                        matches = api.matches()
                        for match in matches:
                            if match not in matcheslist:
                                #new match found
                                matcheslist.append(match)
                                newmatches += 1
                                title(liked, disliked, newmatches)

                        for person in persons:
                            #stops after 2 hours then switches accounts
                            if time.time() > end_time:
                                print(colored( f"{account['Name']} [{str(datetime.datetime.now())}] 2 hours passed...",'red'))
                                active = False
                                break

                            #max range of 30 km from your location
                            if person.distance < 30:
                                print(colored(f"{account['Name']} [{str(datetime.datetime.now())}] AI Calculating Score for {person.name}...", 'yellow'))
                                score = person.predict_likeliness(classifier, sess)
                                print(colored(f"{account['Name']} [{str(datetime.datetime.now())}] Calculated Score: {score}", 'magenta'))

                                if score > 0.65:
                                    liked += 1
                                    title(liked, disliked, newmatches)
                                    print(colored(f"{account['Name']} [{str(datetime.datetime.now())}] High Score, Liking...", 'green'))
                                    res = person.like()
                                    if any(message in res for message in ['rate_limited_until', "liked_remaining': 0"]):
                                        # stops then switches accounts
                                        print(colored(f"{account['Name']} [{str(datetime.datetime.now())}] No Likes Left, Switching accs if possible...", 'red'))
                                        active = False
                                        break
                                    if "match': True" in res:
                                        print(colored(f"{account['Name']} [{str(datetime.datetime.now())}] You Matched!!!", 'green'))
                                        time.sleep(5)
                                    #download pictures
                                    #person.download_images(folder="./Modules/images/Liked", images=person.images)
                                else:
                                    disliked += 1
                                    title(liked, disliked, newmatches)
                                    person.dislike()
                                    print(colored(f"{account['Name']} [{str(datetime.datetime.now())}] Low Score, Disliking...", 'red'))
                                    #person.download_images(folder="./Modules/images/Disliked", images=person.images)

                            time.sleep((random.randint(1500, 8000)) / 1000)
                    except Exception:
                        time.sleep((random.randint(1500, 5000)) / 1000)
                        pass

def start(accounts):
    for index in range(len(accounts)):
        if len(accounts[index]['Token']) < 20:
            print('No Login Token Saved in Accounts.csv, Trying to generate...')
            accounts[index]['Token'] = tokengen(accounts, index)

    while True:
        for index in range(len(accounts)):
            autoliking(accounts[index], index)

            sleeptime = random.randint(18010, 18100) / len(accounts)
            print(colored(f"{accounts[index]['Name']} [{str(datetime.datetime.now())}] Sleeping for {str(sleeptime / 60)} Minutes...",'red'))
            time.sleep(sleeptime)
