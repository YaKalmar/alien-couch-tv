# -*- coding: utf-8 -*-

import calendar
import os
import re
import time

import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_console()
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def print_response(response):
    print(response)


# Build a resource based on a list of properties given as key-value pairs.
# Leave properties with empty values out of the inserted resource.
def build_resource(properties):
    resource = {}
    for p in properties:
        # Given a key like "snippet.title", split into "snippet" and "title", where
        # "snippet" will be an object and "title" will be a property in that object.
        prop_array = p.split('.')
        ref = resource
        for pa in range(0, len(prop_array)):
            is_array = False
            key = prop_array[pa]

            # For properties that have array values, convert a name like
            # "snippet.tags[]" to snippet.tags, and set a flag to handle
            # the value as an array.
            if key[-2:] == '[]':
                key = key[0:len(key) - 2:]
                is_array = True

            if pa == (len(prop_array) - 1):
                # Leave properties without values out of inserted resource.
                if properties[p]:
                    if is_array:
                        ref[key] = properties[p].split(',')
                    else:
                        ref[key] = properties[p]
            elif key not in ref:
                # For example, the property is "snippet.title", but the resource does
                # not yet have a "snippet" object. Create the snippet object here.
                # Setting "ref = ref[key]" means that in the next time through the
                # "for pa in range ..." loop, we will be setting a property in the
                # resource's "snippet" object.
                ref[key] = {}
                ref = ref[key]
            else:
                # For example, the property is "snippet.description", and the resource
                # already has a "snippet" object.
                ref = ref[key]
    return resource


# Remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
    good_kwargs = {}
    if kwargs is not None:
        for key, value in kwargs.iteritems():
            if value:
                good_kwargs[key] = value
    return good_kwargs


def playlists_insert(client, properties, **kwargs):
    # See full sample for function
    resource = build_resource(properties)

    # See full sample for function
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.playlists().insert(
        body=resource,
        **kwargs
    ).execute()

    return response


def playlist_items_insert(client, properties, **kwargs):
    # See full sample for function
    resource = build_resource(properties)

    # See full sample for function
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.playlistItems().insert(
        body=resource,
        **kwargs
    ).execute()

    return print_response(response)


def parse_video_id(url):
    p = re.compile(".*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*")
    matches = p.match(url)
    if matches:
        return matches.groups()[0]
    else:
        return None


def getting_list_of_videos_ids():
    headers = {
        'authority': 'www.reddit.com',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
    }

    params = (
        ('t', 'week'),
        ('limit', 50),
    )

    response = requests.get('https://www.reddit.com/r/videos/top.json', headers=headers, params=params)
    response_json = response.json()

    videos_ids = []
    for i in response_json['data']['children']:
        video_id = parse_video_id(i['data']['url'])
        if video_id:
            videos_ids.append(video_id)
    return videos_ids


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    client = get_authenticated_service()

    playlist_name = calendar.timegm(time.gmtime())

    playlist = playlists_insert(client,
                                {'snippet.title': playlist_name,
                                 'snippet.description': 'From Reddit with ❤️',
                                 'snippet.tags[]': '',
                                 'snippet.defaultLanguage': 'en',
                                 'status.privacyStatus': 'private'},
                                part='snippet,status',
                                onBehalfOfContentOwner='')

    videos_to_add = getting_list_of_videos_ids()

    for video_id in videos_to_add:
        playlist_items_insert(client,
                              {'snippet.playlistId': playlist['id'],
                               'snippet.resourceId.kind': 'youtube#video',
                               'snippet.resourceId.videoId': video_id,
                               'snippet.position': ''},
                              part='snippet',
                              onBehalfOfContentOwner='')
