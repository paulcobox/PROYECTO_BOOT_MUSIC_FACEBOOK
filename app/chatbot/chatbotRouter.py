import os
from app import app, api
from flask import request, make_response
from random import choice
from requests import post, delete
from json import dumps
from flask_restx import Resource
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


chatbot_nspace = api.namespace('chatbot', description="Modulo de Chatbot")


def spotify_initial():
    auth_manager = SpotifyClientCredentials(client_id=os.getenv('SPOTIFY_CLIENT_ID'), client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'))
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

def spotify_search(music):
    try:
        spotify = spotify_initial()
        results =  spotify.search(q=music)
        tracks_list = results['tracks']['items']
        tracks = []
        for index in range(len(tracks_list)):
            tracks.append(tracks_list[index])

        return tracks

    except Exception as error:
        return False



@app.route('/webhook', methods=['GET'])
def webhook():
    print(request)
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    print("validacion")
    if mode and token:
        if mode == 'subscribe' and token == os.getenv('FB_HOOK_TOKEN'):
            print("Token Exitoso")
            return challenge
    print("Token Errado")
    return 'Token Errado'

@app.route('/webhook', methods=['POST'])
def webhook_handle_message():
    data = request.get_json()
    print(data)
    for event in data['entry']:
        messaging = event['messaging']
        for message in messaging:

            # if message.get('sender'):
            recipient_id = message['sender']['id']

            if message.get('postback'):
                postback = message['postback']
                if postback.get('payload'):
                    print('entro 1')
                    if postback.get('payload') == 'GET_STARTED_PAYLOAD':
                        response_text = messages_random()
                        mensaje_inicial({
                            "recipient_id": recipient_id,
                            "message": 'Hola, Seleccione que desea hacer:'
                        })

            if message.get('message'):
                if message['message'] and message['message'].get('quick_reply'):
                    payload_resp = message['message']['quick_reply'].get('payload')
                    if payload_resp == 'POSTBACK_PAYLOAD_MUSICA':
                        sender_graph({
                            "recipient_id": recipient_id,
                            "message": 'Ingrese la Cancion o el Artista que desea Buscar:'
                        })
                elif message['message'] and not message['message'].get('quick_reply'):
                    mensage_text =  message['message'].get('text')
                    tracks_list = spotify_search(mensage_text)

                    if tracks_list and len(tracks_list):
                        sender_graph_template(
                            {
                            "recipient_id": recipient_id,
                            "tracks": tracks_list
                            }
                        )
                    else:
                        sender_graph({
                            "recipient_id": recipient_id,
                            "message": 'Musica y/o Artista no Encontrado.'
                        })


    return 'Token'

def mensaje_inicial(object_message):
    post('https://graph.facebook.com/v10.0/me/messages', 
        params={
            "access_token": os.getenv('FB_PAGE_TOKEN')
        },
        headers={
            "Content-Type": "application/json"
        },
        data=dumps({
            "messaging_type": "RESPONSE",
            "recipient": {
                "id": object_message['recipient_id']
            },
            "message": {
                "text": object_message['message'],
                "quick_replies":[
                    {
                        "content_type":"text",
                        "title":"Buscar Musica",
                        "payload":"POSTBACK_PAYLOAD_MUSICA",
                        "image_url":"https://www.colorcombos.com/images/colors/990000.png"
                    },
                    {
                        "content_type":"text",
                        "title":"Conversar",
                        "payload":"POSTBACK_PAYLOAD_CONVERSAR",
                        "image_url":"https://www.colorcombos.com/images/colors/5BC236.png"
                    }
                ]
            }
        }))

def sender_graph_template(object_message):
    msn_tracks =   [template_spotify_track(track) for track in object_message['tracks']]
    post('https://graph.facebook.com/v10.0/me/messages', 
        params={
            "access_token": os.getenv('FB_PAGE_TOKEN')
        },
        headers={
            "Content-Type": "application/json"
        },
        data=dumps({
            "messaging_type": "RESPONSE",
            "recipient": {
                "id": object_message['recipient_id']
            },
            "message": {
                "attachment":{
                    "type":"template",
                    "payload":{
                        "template_type":"generic",
                        "sharable": "true",
                        "elements":msn_tracks
                    }
                }
            }
        }))

def template_spotify_track(track):

    album = track['album']
    track_name = track['name']
    artists = track['artists'][0]
    image = album['images'][0]
    web_url = track['external_urls']
    template = {
        "title": f"{str(artists['name'])} - {str(track_name)}",
        "image_url":image['url'],
        "subtitle":str(album['name']),
        "default_action": {
            "type": "web_url",
            "url": str(web_url['spotify']),
            'messenger_extensions': 'false',
            "webview_height_ratio": "tall",
        },
    "buttons":[
            {
                "type":"web_url",
                "url":str(web_url['spotify']),
                "title":"Play Spotify"
            }           
        ]      
    }
    return template

def sender_graph(object_message):
    post('https://graph.facebook.com/v10.0/me/messages', 
        params={
            "access_token": os.getenv('FB_PAGE_TOKEN')
        },
        headers={
            "Content-Type": "application/json"
        },
        data=dumps({
            "messaging_type": "RESPONSE",
            "recipient": {
                "id": object_message['recipient_id']
            },
            "message": {
                "text": object_message['message']
            }
        }))

def messages_random():
    list_messages = ['Hola', 'Que tal?', 'Todo bien', 'Pachaqtec', 'Covid']
    return choice(list_messages)


@chatbot_nspace.route('/setup')
class ChatbotSetupResource(Resource):
    @chatbot_nspace.doc('chatbot_setup')
    def get(self):

        post('https://graph.facebook.com/v10.0/me/messenger_profile', 
            params={
                "access_token": os.getenv('FB_PAGE_TOKEN')
            },
            headers={
                "Content-Type": "application/json"
            },
            data=dumps({
                "get_started":{
                    "payload":"GET_STARTED_PAYLOAD"
                },
                "greeting": [
                    {
                        "locale": "default",
                        "text": "Buenos dias {{user_full_name}}!"
                    }
                ]
            }))
        return "Succes Setup", 200


@chatbot_nspace.route('/setup/remove')
class ChatbotSetupRemoveResource(Resource):
    @chatbot_nspace.doc('chatbot_remove_setup')
    def delete(self):

        delete('https://graph.facebook.com/v10.0/me/messenger_profile', 
            params={
                "access_token": os.getenv('FB_PAGE_TOKEN')
            },
            headers={
                "Content-Type": "application/json"
            },
            data=dumps({
                "fields": ["get_started","greeting"]
            }))
        return "Succes Setup Remove", 200


