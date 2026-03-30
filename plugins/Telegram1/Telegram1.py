#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Plugin to send FMS-, ZVEI- and POCSAG-messages via Telegram
@author: Peter Laemmle
@requires: Telegram BOT token, Telegram chat ID, library python-telegram-bot and optional requests and json
"""

import logging
import re
import telegram

from telegram.error import (TelegramError, Unauthorized, BadRequest, NetworkError)
from includes import globalVars

if globalVars.config.get("Telegram1", "RICforLocationAPIKey1"):
    import requests
    import json

from includes.helper import wildcardHandler
from includes.helper import configHandler


# local variables
BOTTokenAPIKey = None
BOTChatIDAPIKey = None
RICforLocationAPIKey = None
GoogleAPIKey = None
RoutingOrigin = None


def escape_text(text, parse_mode):
    if not text:
        return ""

    if parse_mode == "HTML":
        protected_tags = {}
        tag_pattern = r'<(/?)(\w+)>'
        allowed = ["b", "strong", "i", "em", "code", "pre", "u", "s"]

        def protect_tag(match):
            tag_full = match.group(0)
            tag_name = match.group(2)
            if tag_name in allowed:
                placeholder = "__TAG_{0}__".format(len(protected_tags))
                protected_tags[placeholder] = tag_full
                return placeholder
            return tag_full

        text = re.sub(tag_pattern, protect_tag, text)
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        for placeholder, original_tag in protected_tags.items():
            text = text.replace(placeholder, original_tag)

    return text[:4090] + "[...]" if len(text) > 4096 else text


def onLoad():
    """
    While loading the plugins by pluginLoader.loadPlugins()
    this onLoad() routine is called one time for initialize the plugin
    """
    global BOTTokenAPIKey
    global BOTChatIDAPIKey
    global RICforLocationAPIKey
    global GoogleAPIKey
    global RoutingOrigin

    configHandler.checkConfig("Telegram1")
    BOTTokenAPIKey = globalVars.config.get("Telegram1", "BOTTokenAPIKey1")
    BOTChatIDAPIKey = globalVars.config.get("Telegram1", "BOTChatIDAPIKey1")
    RICforLocationAPIKey = globalVars.config.get("Telegram1", "RICforLocationAPIKey1")
    GoogleAPIKey = globalVars.config.get("Telegram1", "GoogleAPIKey1")
    RoutingOrigin = globalVars.config.get("Telegram1", "RoutingOrigin1")

    return


def run(typ, freq, data):
    """
    This function is the implementation of the Plugin.

    @type    typ:  string (FMS|ZVEI|POC)
    @param   typ:  Typ of the dataset
    @type    data: map of data
    @param   data: Contains the parameter for dispatch
    @type    freq: string
    @keyword freq: frequency of the SDR Stick
    """

    try:
        try:
            if typ in ("POC", "FMS", "ZVEI"):
                logging.info("send to Telegram1")
                logging.debug("Read format and compose output for %s-message", typ)

                text = globalVars.config.get("Telegram1", "%s_message" % typ, raw=True)
                text = wildcardHandler.replaceWildcards(text, data)

                logging.debug("Initiate Telegram1 BOT")
                bot = telegram.Bot(token='%s' % BOTTokenAPIKey)

                logging.debug("Send message to chat via Telegram1 BOT API")
                safe_text = escape_text(text, "HTML")
                logging.debug("Telegram final text: %r", safe_text)
                bot.sendMessage('%s' % BOTChatIDAPIKey, safe_text, parse_mode=telegram.ParseMode.HTML)

                # Generate location information only for specific RIC
                if typ == "POC" and data["ric"] == RICforLocationAPIKey:
                    logging.debug("Extract address from POCSAG message")
                    address = "+".join(data["msg"].split(')')[0].split('/', 1)[1].replace('(', ' ').split())

                    logging.debug("Retrieve polylines from Directions API")
                    url = "".join([
                        "https://maps.googleapis.com/maps/api/directions/json?origin=",
                        RoutingOrigin,
                        "&destination=",
                        address,
                        "&mode=driving&key=",
                        GoogleAPIKey
                    ])
                    response = json.loads(requests.get(url).content.decode('utf-8'))
                    logging.debug("Directions API return status: %s", response['status'])

                    logging.debug("Retrieve maps from Google")
                    url = "".join([
                        "https://maps.googleapis.com/maps/api/staticmap?&size=480x640&maptype=roadmap&path=enc:",
                        response['routes'][0]['overview_polyline']['points'],
                        "&language=de&key=",
                        GoogleAPIKey
                    ])
                    with open("overview_map.png", "wb") as img:
                        img.write(requests.get(url).content)

                    url = "".join([
                        "https://maps.googleapis.com/maps/api/staticmap?markers=",
                        address,
                        "&size=240x320&scale=2&maptype=hybrid&zoom=17&language=de&key=",
                        GoogleAPIKey
                    ])
                    with open("detail_map.png", "wb") as img:
                        img.write(requests.get(url).content)

                    logging.debug("Send message and maps via Telegram1 BOT")
                    bot.sendPhoto('%s' % BOTChatIDAPIKey, open('overview_map.png', 'rb'), disable_notification='true')
                    bot.sendPhoto('%s' % BOTChatIDAPIKey, open('detail_map.png', 'rb'), disable_notification='true')

                    logging.debug("Geocode address")
                    url = "".join([
                        "https://maps.googleapis.com/maps/api/geocode/json?address=",
                        address,
                        "&language=de&key=",
                        GoogleAPIKey
                    ])
                    gcode_result = json.loads(requests.get(url).content.decode('utf-8'))
                    logging.debug("Geocoding API return status: %s", gcode_result['status'])

                    logging.debug("Send location via Telegram1 BOT API")
                    bot.sendLocation(
                        '%s' % BOTChatIDAPIKey,
                        gcode_result['results'][0]['geometry']['location']['lat'],
                        gcode_result['results'][0]['geometry']['location']['lng'],
                        disable_notification='true'
                    )

            else:
                logging.warning("Invalid Typ: %s", typ)

        except Unauthorized:
            logging.error("Telegram1 Error: Unauthorized")
            logging.debug("Telegram1 Error: Unauthorized", exc_info=True)

        except BadRequest:
            logging.error("Telegram1 Error: BadRequest")
            logging.debug("Telegram1 Error: BadRequest", exc_info=True)

        except NetworkError:
            logging.error("Telegram1 Error: NetworkError")
            logging.debug("Telegram1 Error: NetworkError", exc_info=True)

        except TelegramError:
            logging.error("Telegram1 Error: TelegramError")
            logging.debug("Telegram1 Error: TelegramError", exc_info=True)

    except Exception:
        logging.error("unknown error")
        logging.debug("unknown error", exc_info=True)
