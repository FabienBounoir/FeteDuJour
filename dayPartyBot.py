import tweepy
import requests
import random

from datetime import datetime, timedelta
from unidecode import unidecode

Month = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

DayOfTheWeek = [
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"
]

def normalize_twitter_username(text):
    # Supprimer les accents
    text = unidecode(text)
    
    # Remplacer les espaces et tirets par des underscores
    text = text.replace(' ', '_').replace('-', '_')
    
    # Mettre tout en minuscules
    text = text.lower()
    
    return text


# Twitter API credentials
API_KEY = "API_KEY"
API_SECRET = "API_SECRET"

ACCESS_TOKEN = "ACCESS_TOKEN"
ACCESS_TOKEN_SECRET = "ACCESS_TOKEN_SECRET"

# Authentification Twitter
api = tweepy.Client(access_token=ACCESS_TOKEN,
                    access_token_secret=ACCESS_TOKEN_SECRET,
                    consumer_key=API_KEY,
                    consumer_secret=API_SECRET)

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
apiOld = tweepy.API(auth)

# add actual year
responseFerie = requests.get("https://calendrier.api.gouv.fr/jours-feries/metropole.json")
responseFerie = responseFerie.json()

responseSaint = requests.get("https://nominis.cef.fr/json/nominis.php")
responseSaint = responseSaint.json()

names = ""
namesDer = "" 

# recupere les key de responseSaint["response"]["prenoms"]
for key in responseSaint["response"]["prenoms"]["majeur"]:
    names += key + ", "

names = names[:-2]


if("derives" in responseSaint["response"]["prenoms"]):
    # dans responseSaint["response"]["prenoms"]["derives"] prendre 5 key random
    key = list(responseSaint["response"]["prenoms"]["derives"].keys())

    # take 5 random key
    random.shuffle(key)
    key = key[:7]

    for k in key:
        namesDer += k + ", "

    namesDer = namesDer[:-2]



date = datetime.now()
dateString = date.strftime("%Y-%m-%d")

tweet = "[" + DayOfTheWeek[date.weekday()] +" " +str(date.day) + " " + Month[date.month - 1] + "]\n"

if dateString in responseFerie:
    tweet += "🎉 Aujourd'hui, est un jour férié en france Métropolitaine 🇫🇷 \n Nous fêtons ➡️ " + responseFerie[dateString] + " !"
    tweet += "\n\n"
    tweet += "Mais c'est aussi la fête de " + names

    nameFerie = responseFerie[dateString]

else:
    tweet += "🌟 Aujourd'hui, nous souhaitons une bonne fête à " + names
    if(namesDer):
        tweet += "\n\n"
        tweet += "Mais aussi à " + namesDer + ", ..."
    


# # Envoi d'un tweet
tweetInfo = tweetSend = api.create_tweet(
    text= tweet,
)

tweet_id = tweetSend.data.get('id')

for key in responseSaint["response"]["saints"]["majeurs"]:
    tweet = "✝️ [" + responseSaint["response"]["saints"]["majeurs"][key]["valeur"] +"]\n"
    tweet += responseSaint["response"]["saints"]["majeurs"][key]["description"]    

    if(len(tweet) > 278):
        tweet = tweet[:278]
        if(tweet.rfind(".") > 0):
            tweet = tweet[:tweet.rfind(".") + 1]
        elif(tweet.rfind("?") > 0):
            tweet = tweet[:tweet.rfind("?") + 1]
        elif(tweet.rfind("!") > 0):
            tweet = tweet[:tweet.rfind("!") + 1]
        elif(tweet.rfind(";") > 0):
            tweet = tweet[:tweet.rfind(";")] + "..."
        elif(tweet.rfind(",") > 0):
            tweet = tweet[:tweet.rfind(",")] + "..."
        else:
            tweet = tweet[:tweet.rfind(" ")] + "..."

    tweetInfo = tweetSend = api.create_tweet(
        text= tweet,
        in_reply_to_tweet_id=tweet_id,
    )

    tweet_id = tweetSend.data.get('id')

pingUsers = ""

for key in responseSaint["response"]["prenoms"]["majeur"]:
    pingUsers += "@" + normalize_twitter_username(key) + " "

tweetSend = api.create_tweet(
    text= "👀 Happy Saint " + pingUsers + " !", 
    in_reply_to_tweet_id=tweet_id,
)
