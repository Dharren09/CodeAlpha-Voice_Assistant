import os
import sys
import dotenv
import logging
import pyttsx3
import vosk
import pyaudio
import spacy
from datetime import datetime
import json
from contextlib import contextmanager
import contextlib
import time
import wolframalpha
import memoize
from twilio.rest import Client
import smtplib
import concurrent.futures
import webbrowser
import requests
import wikipedia
import pyjokes
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random

# an instance to load environment variables
dotenv.load_dotenv()

# load the environment variables as regular python variables
wolfram_app_id = os.getenv('WolframAlpha_API_KEY')
news_api_key = os.getenv("newsapi")
google_search_api_key = os.getenv("googlesearchapi")
open_weather_api_key = os.getenv('openweatherapi')
news_URL = os.getenv('newsURL')
spotify_client_id = os.getenv('spotifyClientID')
spotify_client_secret_key = os.getenv('spotifyClientSecret')
Twilio_Account_SID = os.getenv('TwilioAccountSID')
Twilio_Auth_Token = os.getenv('TwilioAuthToken')
Twilio_Phone_Number = os.getenv('TwilioPhoneNumber')
cx = os.getenv('CustomSearchEngineID')
# load any other variables that you may have here

modelName = os.getenv('modelName') # the model
creatorName = os.getenv('creatorName') # the creator

logging.basicConfig(filename='voice_assistant.log', level=logging.ERROR)

# a custom logger for vosk
vosk_logger = logging.getLogger("vosk")
vosk_logger.setLevel(logging.DEBUG)

# creating a file handler to redirect logs to a file
file_handler = logging.FileHandler('vosk_logs.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
vosk_logger.addHandler(file_handler)

engine = None

def startEngine():
    global engine
    engine = pyttsx3.init('espeak', debug=True)
    voices = engine.getProperty('voices')

    if voices:
        engine.setProperty('voice', voices[0].id)  # You can change the index based on the voice you want to use

def speak(text, rate=140, volume=0.35):
    if engine is None:
        startEngine()
    try:
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Something happened during speech synthesis: {type(e).__name__} - {e}")

@contextmanager
def audio_stream_manager():
    """ Opens and closes a PyAudio stream in a context """
    audio = pyaudio.PyAudio()
    stream = None

    try:
        stream = audio.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=16000,
                            input=True,
                            frames_per_buffer=4096)
        yield stream
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        audio.terminate()

def listen_and_recognize(timeout=60):
    """Continuously captures user speech and recognizes it using Vosk."""

    model = vosk.Model('vosk-model-en-us-aspire-0.2') # wget https://alphacephei.com/vosk/models/vosk-model-en-us-aspire-0.2.zip then unzip
    with audio_stream_manager() as stream:
        recognized_text = ""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Read audio data from the microphone
                data = stream.read(4096, 2)

                # Feed the audio data to the Vosk recognizer
                recognizer = vosk.KaldiRecognizer(model, 16000)
                recognizer.AcceptWaveform(data)

                # Check if a recognition result is available
                result = recognizer.Result()

                # Process the complete recognition result
                if result:
                    user_query = json.loads(result)
                    recognized_text = user_query.get("text", "").lower()

                    if recognized_text:
                         break
                    else:
                        speak("I'm sorry, I couldn't understand your query. Please try again or rephrase it.")
                        time.sleep(1)
        except Exception as e:
            print(f"An error occurred during Vosk recognition: {e}")
        finally:
            pass

    tokenized_text = async_tokenization(recognized_text)
    speak(tokenized_text)
    return tokenized_text

def takeCommand():
    """Prompts the user for speech input and returns the recognized text."""
    with contextlib.ExitStack() as stack:
        # Open and close the PyAudio stream in a context to ensure proper cleanup
        stream = stack.enter_context(audio_stream_manager())

        # Continuously prompt the user until a valid recognition is obtained
        try:
            while True:
                recognized_text = listen_and_recognize()

                # Check if the recognition is valid
                if recognized_text:
                    return recognized_text

                # Provide feedback for timeouts and unsuccessful recognitions
                speak("I'm sorry, I couldn't understand your query. Please try again or rephrase it.")

                # Allow for multiple recognition attempts within a window
                time.sleep(1)
        except Exception as e:
            print(f"An error occurred during command recognition: {e}")

def get_user_preference():
    # Prompt the user for their preference on how to be addressed
    speak("Would you like to be addressed by your title and name or simply your name? Say 'yes' or 'no'")
    response = takeCommand()

    # Handle affirmative response
    if response and "yes" in response.get("text", "").lower():
        # Prompt the user for their gender
        speak("What is your gender? Please specify male, female, or non-binary.")
        gender = takeCommand()

        if gender:
            # Determine the appropriate title based on the specified gender
            gender = gender.get("text", "").lower()
            if "male" in gender:
                title = "Mr."
            elif "female" in gender:
                title = "Ms."
            elif "non-binary" in gender:
                title = "Mx."
            else:
                title = ""  # Default to no title if gender is not specified

            # Prompt the user for their name
            speak("Please provide your name.")
            user_name = takeCommand()

            # Greet the user using the determined title and name
            speak(f"Great to meet you, {title} {user_name}!")
            return title, user_name
        else:
            # If the user does not provide their gender, proceed without title
            speak("Thank you for sharing your preference. Please provide your name.")
            user_name = takeCommand()
            speak(f"Great to meet you, {user_name}!")
            return "", user_name

    # Handle negative or unclear response
    else:
        speak("Please provide your name.")
        user_name = takeCommand()
        speak(f"Great to meet you, {user_name}!")
        return "", user_name

def greet_user(title, user_name):
    hour = datetime.now().hour
    if hour >= 0 and hour < 12:
        speak("Good Morning, {} {}!".format(title, user_name))
    elif hour >= 12 and hour < 18:
        speak("Good Afternoon, {} {}!".format(title, user_name))
    else:
        speak("Good Evening, {} {}!".format(title, user_name))

def tokenization(user_query):
    # loading the english model from spacy
    nlp = spacy.load('en_core_web_sm')

    try:
        recognized_text = user_query.get("text", "").lower() # get text extracted from user query then lowcase it for easy interpretation
        doc = nlp(recognized_text) # process the users query

        # initialize variables to stores the objs of subject, verb and object
        subject = []
        verb = []
        object = []

        # iterate through the parsed tokens
        for token in doc:
            if "subj" in token.dep_:
                 subject = token.text
            elif "obj" in token.dep_:
                 object = token.text
            elif "ROOT" in token.dep_:
                 verb = token.text

        if subject and verb and object:
            # handle complex queries using extracted information
            response = f"Subject: {subject}, Verb: {verb}, Object: {object}"
        else:
            logging.error("Sorry, I can only handle simple queries.")
            response = "Sorry, I can only handle simple queries."

        return response

    except Exception as e:
        logging.error(f"An error occured during tokenization: {e}")

def async_tokenization(user_query):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(tokenization, user_query)
        return future.result()

def wolfram_knowledge(user_query):
    """ request to the wolframalpha API """

    @memoize
    def _get_wolfram_response(query):
        try:
            client = wolframalpha.Client(wolfram_app_id)
            res = client.user_query(query)
            for pod in res.pods:
                for sub in pod.subpods:
                    if hasattr(sub, 'plaintext'):
                        print(sub.plaintext)

        except wolframalpha.WolframAlphaError as e:
            print(f"Wolfram Alpha API error: {e}")
            speak("Sorry, I couldn't find an answer for your query.")

    return _get_wolfram_response(user_query)

# def sendEmail(to, content):
#     server = smtplib.SMTP('smtp.gmail.com', 587)
#     server.ehlo()
#     server.starttls()
#     server.login("google OAuth2")
#     server.sendmail('your_email', to, content)
#     server.close()

if __name__ == '__main__':
    # clear the terminal before a new operation
    clear = lambda: os.system('clear') # lambda are anonymous or short form functions
    clear()

    startEngine()
    speak("Hi, I am {modelName} your personal assistant. How can I help you?")
    title, user_name = get_user_preference()
    greet_user(title, user_name)
    wolfram_knowledge("")


    while True:
        user_query = listen_and_recognize().lower()

        if "send message" in user_query:
            speak("What is your message")
            message_body = takeCommand()

            speak("What is the receivers phone number?, Kindly start with the country code")
            receiver_number = takeCommand()

            if not receiver_number:
               speak("Receivers Phone number is required, Kindly start with the country code")
               continue

            # Using Twilio to send messages
            client = Client(Twilio_Account_SID, Twilio_Auth_Token)

            message = Client.messages.create(
                body = message_body,
                from_ = Twilio_Phone_Number,
                to = receiver_number
            )

            speak("Messsage has been sent successfully!")

        elif "open youtube" in user_query:
            speak("opening youtube\n")
            webbrowser.open("https://www.youtube.com")

        elif "open stackoverflow" in user_query:
            speak("Opening Stackoverflow\n")
            webbrowser.open("https://www.stackoverflow.com")

        elif "search on google" in user_query:
            speak("What do you want to search about {title}?")
            query = takeCommand()

            base_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "q" : query,
                "key" : "google_search_api_key",
                "cx" : "cx"
            }

            response = requests.get(base_url, params=params)

            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    title = item.get("title", "")
                    link = item.get("link", "")
                    description = item.get("snippet", "")
                    speak(f"Title: {title}\nLink: {link}\nDescription: {description}\n")
                    print(f"Title: {title}\nLink: {link}\nDescription: {description}\n")
                    print("----------------------------")
            else:
                logging.error(f"Unable to fetch search results from Google")
                speak("Sorry, I couldn't find any results for your query.")

        elif "search wikipedia for" in user_query:
            speak("Search wikipedia....")
            query = user_query.replace("search wikipedia for", "")
            try:
                results = wikipedia.summary(query, sentences=3)
                speak("According to Wikipedia")
                speak(results)
            except wikipedia.exceptions.DisambiguationError as e:
                options = e.options
                speak("There are multiple search results. Please specify your query from the following options:")
                for i, option in enumerate(options, 1):
                    speak(f"{i}. {option}")
                choice = takeCommand().lower()
                if choice.isdigit() and 1 <= int(choice) <= len(options):
                    selected_option = options[int(choice) - 1]
                    results = wikipedia.summary(selected_option, sentences=3)
                    speak(f"According to Wikipedia, {selected_option}")
                    speak(results)
                    print(results)
                else:
                    speak("Sorry, I couldn't understand your choice.")
            except wikipedia.exceptions.PageError:
                speak("Sorry, I couldn't find any results for {query} on wikipedia.")
            except wikipedia.exceptions.HTTPTimeoutError:
                speak("Sorry, Wikipedia is not responding. Please try again later.")

        elif "what is the time" in user_query:
            strTime = datetime.now().strftime("%H:%M:%S")
            speak(f"{user_name}, the time is {strTime}")

        elif "the date" in user_query:
            strDate = datetime.today().strftime("%d:%m:%Y")
            speak(f"{user_name}, the date today is {strDate}")

        elif "How are you" in user_query:
            speak(f"I am fine by God's grace, Thank you")
            speak(f"How are you?, {user_name}")

        elif "my name" in user_query:
            speak(f"Your name is {user_name}")

        elif "your name" in user_query:
            speak(f"My name is {modelName}")

        elif "I am fine" in user_query or "I am good" in user_query:
            speak(f"It's good to know that you are doing fine")

        elif "who made you" in user_query or "who created you" in user_query:
            speak("Thanks to {}, I am here talking to you".format(creatorName))

        elif "change your name" in user_query:
            speak("What would you like to call me")
            new_modelName = takeCommand().lower()
            modelName = new_modelName
            speak("Thank you for changing my name to {}".format(new_modelName))

        elif "Tell a joke" in user_query:
            speak(pyjokes.get_joke())

        elif "news today" in user_query:
            speak("which country are we talking about here?")
            print("use country code e.g us, ug or don't specify if global news")
            country_code = takeCommand()
            speak(country_code)

            num_articles = 5

            endpoint = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey" : news_api_key,
                "country" : country_code,
                "category" : "general",
                "pageSize" : num_articles
            }

            # make request to api
            response =  requests.get(endpoint, params=params)

            try:
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articles")

                    if articles:
                         # extract and read the headlines
                         headlines = [article.get("title") for article in articles]
                         for headline in headlines:
                             speak(headline)
                    else:
                         speak(f"I couldn't fint any news for {country_code}")
            except Exception as e:
                print(f"something happened while requesting the api: {e}")
                speak("Could not process your request")

        elif "weather updates" in user_query:
            speak(f"if i a may ask, which location do you want it's weather updates")
            location = takeCommand()

            params = {
                "q" : location,
                "appid" : open_weather_api_key,
                "units" : "metric"
            }

            response = requests.get(base_url, params=params)

            if response.status_code == 200:
                weather_data = response.json()
                temperature = weather_data['main']['temp']
                weather_description = weather_data['weather'][0]['description']
                location_name = weather_data['name'] if 'name' in weather_data else f"Coordinates: {weather_data['coord']['lat']}, {weather_data['coord']['lon']}"
                speak(f"Current weather in {location_name}: {temperature}°C and {weather_description}.")
            else:
                speak("Sorry, I couldn't fetch weather updates for the specified location")

        elif "play music" in user_query:
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=spotify_client_id, client_secret=spotify_client_secret_key, scope='user-library-read user-read-playback-state user-modify-playback-state'))

            speak('which song would you like me to play')
            song_query = takeCommand()

            if song_query:
                results = sp.search(q=song_query, limit=5, type='track')
                if results['tracks']['items']:
                    track_uri = results['tracks']['items'][0]['uri']
                    sp.start_playback(uris=[track_uri])
                    speak(f"Playing {song_query} on spotify.")
                else:
                    speak(f"Sorry, I coudn't find {song_query} on spotify.")
            else:
                # play random song if no no specific song is requested
                random_track_index = random.randint(0, 4) # choosing from a ramdom index between 0 and 4
                track_uri = results['tracks']['items'][random_track_index]['uri']
                sp.start_playback(uris=[track_uri])
                speak("Playing random song from spotify")

        elif "stop" in user_query:
            speak("Bye")
            break

        else:
            wolfram_knowledge(user_query)%
