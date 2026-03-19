#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Pushover-Plugin to send FMS-, ZVEI- and POCSAG - messages to Pushover Clients

@author: Ricardo Krippner

@requires: Pushover-Configuration has to be set in the config.ini
"""

import logging
import http.client as httplib
import urllib.parse

from includes import globalVars
from includes.helper import configHandler
from includes.helper import wildcardHandler


def onLoad():
    return


def run(typ, freq, data):
    try:
        if configHandler.checkConfig("Pushover"):

            if typ == "FMS":
                message = globalVars.config.get("Pushover", "fms_message", raw=True)
                title = globalVars.config.get("Pushover", "fms_title", raw=True)
                priority = str(globalVars.config.get("Pushover", "fms_prio"))

            elif typ == "ZVEI":
                if globalVars.config.get("Pushover", "zvei_sep_prio") == '1':
                    if data["zvei"] in globalVars.config.get("Pushover", "zvei_prio2"):
                        priority = '2'
                    elif data["zvei"] in globalVars.config.get("Pushover", "zvei_prio1"):
                        priority = '1'
                    elif data["zvei"] in globalVars.config.get("Pushover", "zvei_prio0"):
                        priority = '0'
                    else:
                        priority = '-1'
                else:
                    priority = str(globalVars.config.get("Pushover", "zvei_std_prio"))

                message = globalVars.config.get("Pushover", "zvei_message", raw=True)
                title = globalVars.config.get("Pushover", "zvei_title", raw=True)

            elif typ == "POC":
                logging.debug("send Pushover for %s", typ)

                if globalVars.config.get("Pushover", "poc_spec_ric") == '0':
                    if data["function"] == '1':
                        priority = str(globalVars.config.get("Pushover", "SubA"))
                    elif data["function"] == '2':
                        priority = str(globalVars.config.get("Pushover", "SubB"))
                    elif data["function"] == '3':
                        priority = str(globalVars.config.get("Pushover", "SubC"))
                    elif data["function"] == '4':
                        priority = str(globalVars.config.get("Pushover", "SubD"))
                    else:
                        priority = '0'
                else:
                    if data["ric"] in globalVars.config.get("Pushover", "poc_prio2"):
                        priority = '2'
                    elif data["ric"] in globalVars.config.get("Pushover", "poc_prio1"):
                        priority = '1'
                    elif data["ric"] in globalVars.config.get("Pushover", "poc_prio0"):
                        priority = '0'
                    else:
                        priority = '-1'

                message = globalVars.config.get("Pushover", "poc_message", raw=True)
                title = globalVars.config.get("Pushover", "poc_title", raw=True)

            else:
                logging.warning("Invalid type: %s", typ)
                return

            try:
                message = wildcardHandler.replaceWildcards(message, data)
                title = wildcardHandler.replaceWildcards(title, data)

                logging.debug("Sending Pushover title: %s", title)
                logging.debug("Sending Pushover message: %s", message)
                logging.debug("Sending Pushover priority: %s", priority)

                sound = globalVars.config.get("Pushover", "sound")
                if not sound:
                    sound = "pushover"

                payload = {
                    "token": globalVars.config.get("Pushover", "api_key"),
                    "user": globalVars.config.get("Pushover", "user_key"),
                    "message": message,
                    "html": globalVars.config.get("Pushover", "html"),
                    "title": title,
                    "sound": sound,
                    "priority": priority
                }

                # retry / expire nur für Emergency Priority 2
                if priority == '2':
                    payload["retry"] = globalVars.config.get("Pushover", "retry")
                    payload["expire"] = globalVars.config.get("Pushover", "expire")

                conn = httplib.HTTPSConnection("api.pushover.net:443")
                conn.request(
                    "POST",
                    "/1/messages.json",
                    urllib.parse.urlencode(payload),
                    {"Content-type": "application/x-www-form-urlencoded"},
                )

            except Exception:
                logging.error("cannot send Pushover request")
                logging.debug("cannot send Pushover request", exc_info=True)
                return

            try:
                response = conn.getresponse()
                response_body = response.read().decode("utf-8", errors="replace")

                if str(response.status) == "200":
                    logging.debug("Pushover response: %s - %s - %s", str(response.status), str(response.reason), response_body)
                else:
                    logging.warning("Pushover response: %s - %s - %s", str(response.status), str(response.reason), response_body)

            except Exception:
                logging.error("cannot get Pushover response")
                logging.debug("cannot get Pushover response", exc_info=True)
                return

            finally:
                logging.debug("close Pushover-Connection")
                try:
                    conn.close()
                except Exception:
                    pass

    except Exception:
        logging.error("unknown error")
        logging.debug("unknown error", exc_info=True)
