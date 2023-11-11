# Jey - Voice Assistant

Jey is a Python-based voice assistant that allows users to interact with their computer using voice commands. It provides a range of functionalities, including sending messages, playing music, fetching weather updates, and more.

## Features

- **Voice Recognition:** Jey uses Vosk for voice recognition, allowing for natural language interaction.
- **Text-to-Speech:** The assistant responds with synthesized speech using the pyttsx3 library.
- **API Integration:** Fetch news updates, weather information, and perform searches using various APIs.
- **Spotify Integration:** Play music from Spotify using the Spotipy library.
- **Wolfram Alpha Integration:** Retrieve answers to general knowledge questions using Wolfram Alpha API.
- **GUI Interface:** The project includes a simple Tkinter-based GUI for user interaction.

## Getting Started

### Prerequisites

- Python 3.x
- Required Python packages: vosk, pyttsx3, spacy, wolframalpha, twilio, spotipy, requests, wikipedia, pyjokes

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/voice-assistant.git

2. Install dependencies:

   ```bash
   pip install -r requirements.txt

3. Setup environment variables:
   create `.env` file in the project root with the following;

   ```env
   WolframAlpha_API_KEY=your_wolfram_alpha_api_key
   newsapi=your_newsapi_key
   googlesearchapi=your_google_search_api_key
   openweatherapi=your_open_weather_api_key
   spotifyClientID=your_spotify_client_id
   spotifyClientSecret=your_spotify_client_secret
   TwilioAccountSID=your_twilio_account_sid
   TwilioAuthToken=your_twilio_auth_token
   TwilioPhoneNumber=your_twilio_phone_number
   CustomSearchEngineID=your_custom_search_engine_id
   modelName=your_model_name
   creatorName=your_creator_name

4 . Run the GUI application:

    ```bash
    python3 main.py

## Contributing

Feel free to contribute to the development of Jey. Here are some 
ways you can contribute:

- Report bugs or suggest features by creating issues.
- Submit pull requests to address open issues or enhance existing features.

## Developer

`Dharren Pius Makoha - Python Intern at CodeAlpha`
`Twitter`   - `https://www.twitter.com/iamdevdharrenzug`
`Github`    - `https://github.com/Dharren09`
`Instagram` - `https://instagram/iamdharrenz_ug`
`Linkedin`  - `https://linkedin.com/makohadharrenpius`
