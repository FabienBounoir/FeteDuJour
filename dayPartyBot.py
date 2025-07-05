import os
import requests
import tweepy

from datetime import datetime
from unidecode import unidecode
from dotenv import load_dotenv

# Constantes
MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

DAYS_FR = [
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

# Chargement des variables d'environnement
load_dotenv()


def normalize_twitter_username(text: str) -> str:
    """Nettoie un nom pour l'utiliser en pseudo Twitter."""
    return unidecode(text).replace(' ', '_').replace('-', '_').lower()


def get_api_clients():
    """Initialise les clients Tweepy."""
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

    client = tweepy.Client(
        access_token=access_token,
        access_token_secret=access_token_secret,
        consumer_key=api_key,
        consumer_secret=api_secret
    )

    legacy_auth = tweepy.OAuthHandler(api_key, api_secret)
    legacy_auth.set_access_token(access_token, access_token_secret)
    legacy_api = tweepy.API(legacy_auth)

    return client, legacy_api


def fetch_json(url: str) -> dict:
    """Récupère et retourne une réponse JSON."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erreur lors de la récupération de {url} : {e}")
        return {}


def build_tweet_intro(today: datetime, name: str, holiday: str = None) -> str:
    """Construit le tweet principal."""
    date_str = f"[{DAYS_FR[today.weekday()]} {today.day} {MONTHS_FR[today.month - 1]}]"
    if holiday:
        return (
            f"{date_str}\n🎉 Aujourd'hui, est un jour férié en France Métropolitaine 🇫🇷\n"
            f"Nous fêtons ➡️ {holiday} !\n\n"
            f"Mais c'est aussi la fête de {name}"
        )
    return f"{date_str}\n🌟 Aujourd'hui, nous souhaitons une bonne fête à {name}"


def build_saints_tweet(saints: list) -> str:
    """Construit le tweet de la liste des saints, tronqué à 278 caractères si nécessaire."""
    tweet = "✝️ Nous fêtons également les "
    tweet += ", ".join(f"Saint {saint['name']}" for saint in saints)
    tweet += " !"

    if len(tweet) > 278:
        cut_pos = tweet.rfind(",", 0, 278)
        tweet = tweet[:cut_pos] + "..."
    return tweet


def main():
    # Initialisation
    client, _ = get_api_clients()
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    api_key_fete = os.getenv("API_KEY_FETE_DU_JOUR")

    # Données
    jours_feries = fetch_json("https://calendrier.api.gouv.fr/jours-feries/metropole.json")
    fete_du_jour = fetch_json(f"https://fetedujour.fr/api/v2/{api_key_fete}/json")
    saints_du_jour = fetch_json(f"https://fetedujour.fr/api/v2/{api_key_fete}/json-saints")

    # Construction du tweet principal
    holiday_name = jours_feries.get(today_str)
    main_tweet_text = build_tweet_intro(today, fete_du_jour.get("name", "quelqu’un"), holiday_name)

    # Envoi du tweet principal
    try:
        main_tweet = client.create_tweet(text=main_tweet_text)
        tweet_id = main_tweet.data.get("id")
    except Exception as e:
        print(f"Erreur lors de l'envoi du tweet principal : {e}")
        return

    # Tweet de réponse avec les saints
    try:
        saints_tweet = build_saints_tweet(saints_du_jour.get("saints", []))
        reply = client.create_tweet(text=saints_tweet, in_reply_to_tweet_id=tweet_id)
        tweet_id = reply.data.get("id")
    except Exception as e:
        print(f"Erreur lors de l'envoi du tweet des saints : {e}")

    # Mention personnalisée
    try:
        username = normalize_twitter_username(fete_du_jour.get("name", ""))
        client.create_tweet(text=f"👀 Bonne Fête @{username} !", in_reply_to_tweet_id=tweet_id)
    except Exception as e:
        print(f"Erreur lors de l'envoi du ping utilisateur : {e}")


if __name__ == "__main__":
    main()
