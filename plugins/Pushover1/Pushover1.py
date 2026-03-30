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
        logging.info("send to Pushover1")
        if configHandler.checkConfig("Pushover1"):

            if typ == "FMS":
                message = globalVars.config.get("Pushover1", "fms_message", raw=True)
                title = globalVars.config.get("Pushover1", "fms_title", raw=True)
                priority = str(globalVars.config.get("Pushover", "fms_prio"))

            elif typ == "ZVEI":
                if globalVars.config.get("Pushover1", "zvei_sep_prio") == '1':
                    if data["zvei"] in globalVars.config.get("Pushover1", "zvei_prio2"):
                        priority = '2'
                    elif data["zvei"] in globalVars.config.get("Pushover1", "zvei_prio1"):
                        priority = '1'
                    elif data["zvei"] in globalVars.config.get("Pushover1", "zvei_prio0"):
                        priority = '0'
                    else:
                        priority = '-1'
                else:
                    priority = str(globalVars.config.get("Pushover1", "zvei_std_prio"))

                message = globalVars.config.get("Pushover1", "zvei_message", raw=True)
                title = globalVars.config.get("Pushover1", "zvei_title", raw=True)

            elif typ == "POC":
                logging.debug("send Pushover1 for %s", typ)

                if globalVars.config.get("Pushover1", "poc_spec_ric") == '0':
                    if data["function"] == '1':
                        priority = str(globalVars.config.get("Pushover1", "SubA"))
                    elif data["function"] == '2':
                        priority = str(globalVars.config.get("Pushover1", "SubB"))
                    elif data["function"] == '3':
                        priority = str(globalVars.config.get("Pushover1", "SubC"))
                    elif data["function"] == '4':
                        priority = str(globalVars.config.get("Pushover1", "SubD"))
                    else:
                        priority = '0'
                else:
                    if data["ric"] in globalVars.config.get("Pushover1", "poc_prio2"):
                        priority = '2'
                    elif data["ric"] in globalVars.config.get("Pushover1", "poc_prio1"):
                        priority = '1'
                    elif data["ric"] in globalVars.config.get("Pushover1", "poc_prio0"):
                        priority = '0'
                    else:
                        priority = '-1'

                message = globalVars.config.get("Pushover1", "poc_message", raw=True)
                title = globalVars.config.get("Pushover1", "poc_title", raw=True)

            else:
                logging.warning("Invalid type: %s", typ)
                return

            try:
                message = wildcardHandler.replaceWildcards(message, data)
                title = wildcardHandler.replaceWildcards(title, data)

                logging.debug("Sending Pushover1 title: %s", title)
                logging.debug("Sending Pushover1 message: %s", message)
                logging.debug("Sending Pushover1 priority: %s", priority)

                sound = globalVars.config.get("Pushover1", "sound")
                if not sound:
                    sound = "pushover"

                payload = {
                    "token": globalVars.config.get("Pushover1", "api_key1"),
                    "user": globalVars.config.get("Pushover1", "user_key1"),
                    "message": message,
                    "html": globalVars.config.get("Pushover1", "html"),
                    "title": title,
                    "sound": sound,
                    "priority": priority
                }

                # retry / expire nur für Emergency Priority 2
                if priority == '2':
                    payload["retry"] = globalVars.config.get("Pushover1", "retry")
                    payload["expire"] = globalVars.config.get("Pushover1", "expire")

                conn = httplib.HTTPSConnection("api.pushover.net:443")
                conn.request(
                    "POST",
                    "/1/messages.json",
                    urllib.parse.urlencode(payload),
                    {"Content-type": "application/x-www-form-urlencoded"},
                )

            except Exception:
                logging.error("cannot send Pushover1 request")
                logging.debug("cannot send Pushover1 request", exc_info=True)
                return

            try:
                response = conn.getresponse()
                response_body = response.read().decode("utf-8", errors="replace")

                if str(response.status) == "200":
                    logging.debug("Pushover1 response: %s - %s - %s", str(response.status), str(response.reason), response_body)
                else:
                    logging.warning("Pushover1 response: %s - %s - %s", str(response.status), str(response.reason), response_body)

            except Exception:
                logging.error("cannot get Pushover1 response")
                logging.debug("cannot get Pushover1 response", exc_info=True)
                return

            finally:
                logging.debug("close Pushover1-Connection")
                try:
                    conn.close()
                except Exception:
                    pass

    except Exception:
        logging.error("unknown error")
        logging.debug("unknown error", exc_info=True)
