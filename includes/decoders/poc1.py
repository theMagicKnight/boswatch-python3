#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
POCSAG Decoder

@author: Bastian Schroll
@author: Jens Herrmann

@requires: Configuration has to be set in the config.ini
"""

import logging
import re
import csv

from includes import globalVars
from includes import doubleFilter


def decode_escape_sequences(value):
    try:
        return value.encode("utf-8").decode("unicode_escape")
    except Exception:
        return value


def get_base_replacements():
    """
    Grundbereinigung direkt im Code.
    Diese Regeln greifen immer.
    """
    return [
        ("\r\n", ""),
        ("\n", ""),
        ("\r", ""),
        ("\\r\\n", ""),
        ("\\n", ""),
        ("\\r", ""),
        ("<NUL><NUL>", ""),
        ("<NUL>", ""),
        ("<NUL", ""),
        ("< NUL>", ""),
        ("<EOT>", ""),
    ]


def load_csv_replacements():
    """
    Lädt optionale Zusatz-Ersetzungen aus CSV,
    wenn in der config aktiviert.
    """
    replacements = []

    try:
        if not globalVars.config.getint("POC", "replace_csv_enable"):
            logging.debug("POC replace.csv disabled by config")
            return replacements
    except Exception:
        logging.debug("POC replace_csv_enable not set, CSV replacements disabled")
        return replacements

    try:
        csv_file = globalVars.config.get("POC", "replace_csv_file")
    except Exception:
        csv_file = "/opt/boswatch/csv/replace.csv"

    try:
        with open(csv_file, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                if row[0].startswith("#"):
                    continue
                if len(row) < 2:
                    continue

                search = decode_escape_sequences(row[0])
                replace = decode_escape_sequences(row[1])

                replacements.append((search, replace))

        logging.debug("Loaded %d CSV replacements from %s", len(replacements), csv_file)

    except Exception:
        logging.error("Could not load replace.csv", exc_info=True)

    return replacements


def apply_replacements(text):
    """
    Erst feste Grundregeln, dann optional CSV-Regeln.
    """
    replacements = get_base_replacements() + load_csv_replacements()

    for search, replace in replacements:
        text = text.replace(search, replace)

    return text.strip()


def isAllowed(poc_id):
    """
    Simple Filter Functions (Allowed, Denied and Range)

    @type    poc_id: string
    @param   poc_id: POCSAG Ric

    @requires:  Configuration has to be set in the config.ini

    @return:    Checks both allow/deny-rule and filter-range (suitable for signal-RIC)
    @exception: none
    """

    allowed = 0

    if globalVars.config.get("POC", "allow_ric"):
        if poc_id in globalVars.config.get("POC", "allow_ric"):
            logging.info("RIC %s is allowed", poc_id)
            return True
        else:
            logging.info("RIC %s is not in the allowed list", poc_id)
            allowed = 0

    if poc_id in globalVars.config.get("POC", "deny_ric"):
        logging.info("RIC %s is denied by config.ini", poc_id)
        return False

    if globalVars.config.getint("POC", "filter_range_start") < int(poc_id) < globalVars.config.getint("POC", "filter_range_end"):
        logging.info("RIC %s in between filter range", poc_id)
        return True
    else:
        logging.info("RIC %s out of filter range", poc_id)
        allowed = 0

    if globalVars.config.get("POC", "netIdent_ric"):
        if poc_id in globalVars.config.get("POC", "netIdent_ric"):
            logging.info("RIC %s as net identifier", poc_id)
            return True
        else:
            allowed = 0

    if globalVars.config.get("multicastAlarm", "multicastAlarm_delimiter_ric"):
        if poc_id in globalVars.config.get("multicastAlarm", "multicastAlarm_delimiter_ric"):
            logging.info("RIC %s as multicastAlarm delimiter", poc_id)
            return True
        else:
            allowed = 0

    if globalVars.config.get("multicastAlarm", "multicastAlarm_ric"):
        if poc_id in globalVars.config.get("multicastAlarm", "multicastAlarm_ric"):
            logging.info("RIC %s as multicastAlarm message", poc_id)
            return True
        else:
            allowed = 0

    if allowed == 0:
        return False
    return True


def decode(freq, decoded):
    """
    Export POCSAG information from Multimon-NG string and call alarmHandler.processAlarmHandler()
    """
    has_geo = False

    try:
        bitrate = 0
        poc_id = ""
        poc_sub = ""

        if "POCSAG512:" in decoded:
            bitrate = 512
        elif "POCSAG1200:" in decoded:
            bitrate = 1200
        elif "POCSAG2400:" in decoded:
            bitrate = 2400

        if bitrate != 0:
            m_addr = re.search(r"Address:\s*([0-9]+)", decoded)
            m_func = re.search(r"Function:\s*([0-3])", decoded)

            if m_addr:
                poc_id = m_addr.group(1).zfill(7)
            else:
                try:
                    if bitrate == 512:
                        poc_id = decoded[20:27].replace(" ", "").zfill(7)
                    else:
                        poc_id = decoded[21:28].replace(" ", "").zfill(7)
                except Exception:
                    poc_id = ""

            if m_func:
                poc_sub = str(int(m_func.group(1)) + 1)
            else:
                try:
                    if bitrate == 512:
                        poc_sub = str(int(decoded[39]) + 1)
                    else:
                        poc_sub = str(int(decoded[40]) + 1)
                except Exception:
                    poc_sub = ""

        if bitrate == 0:
            logging.warning("POCSAG Bitrate not found")
            logging.debug(" - (%s)", decoded)
        else:
            logging.debug("POCSAG Bitrate: %s", bitrate)

            if "Alpha:" in decoded:
                try:
                    poc_text = decoded.split("Alpha:   ", 1)[1]
                except Exception:
                    poc_text = ""

                logging.debug("POC raw text before replace: %r", poc_text)
                poc_text = apply_replacements(poc_text)
                logging.debug("POC text after replace: %r", poc_text)

                if globalVars.config.getint("POC", "geo_enable"):
                    try:
                        logging.debug("Using %s to find geo-tag in %s", globalVars.config.get("POC", "geo_format"), poc_text)
                        m = re.search(globalVars.config.get("POC", "geo_format"), poc_text)
                        if m:
                            logging.debug("Found geo-tag in message, parsing...")
                            has_geo = True
                            geo_order = globalVars.config.get("POC", "geo_order").split(",")

                            if geo_order[0].lower() == "lon":
                                lon = m.group(1) + "." + m.group(2)
                                lat = m.group(3) + "." + m.group(4)
                            else:
                                lat = m.group(1) + "." + m.group(2)
                                lon = m.group(3) + "." + m.group(4)

                            logging.debug("Finished parsing geo; lon: %s, lat: %s", lon, lat)
                        else:
                            logging.debug("No geo-tag found")
                            has_geo = False
                    except Exception:
                        has_geo = False
                        logging.error("Exception parsing geo-information", exc_info=True)
                else:
                    has_geo = False
            else:
                poc_text = ""

            if re.search(r"[0-9]{7}", poc_id) and re.search(r"[1-4]{1}", poc_sub):
                if isAllowed(poc_id):
                    if doubleFilter.checkID("POC", poc_id + poc_sub, poc_text):
                        data = {
                            "ric": poc_id,
                            "function": poc_sub,
                            "msg": poc_text,
                            "bitrate": bitrate,
                            "description": poc_id,
                            "has_geo": has_geo
                        }

                        if has_geo is True:
                            data["lon"] = lon
                            data["lat"] = lat

                        data["functionChar"] = data["function"].replace("1", "a").replace("2", "b").replace("3", "c").replace("4", "d")
                        data["ricFuncChar"] = data["ric"] + data["functionChar"]

                        logging.info("POCSAG%s: %s %s %s ", data["bitrate"], data["ric"], data["function"], data["msg"])

                        if globalVars.config.getint("POC", "idDescribed"):
                            from includes import descriptionList
                            data["description"] = descriptionList.getDescription("POC", data["ric"] + data["functionChar"])

                        if globalVars.config.getint("multicastAlarm", "multicastAlarm") and data["ric"] != globalVars.config.get("POC", "netIdent_ric") and (data["msg"] == "" or data["ric"] in globalVars.config.get("multicastAlarm", "multicastAlarm_delimiter_ric")):
                            logging.debug(" - multicastAlarm without msg")
                            from includes import multicastAlarm
                            multicastAlarm.newEntrymultiList(data)

                        elif globalVars.config.getint("multicastAlarm", "multicastAlarm") and data["msg"] != "" and data["ric"] in globalVars.config.get("multicastAlarm", "multicastAlarm_ric"):
                            logging.debug(" - multicastAlarm with message")
                            from includes import multicastAlarm
                            multicastAlarm.multicastAlarmExec(freq, data)

                        else:
                            try:
                                from includes import alarmHandler
                                alarmHandler.processAlarmHandler("POC", freq, data)
                            except Exception:
                                logging.error("processing alarm failed")
                                logging.debug("processing alarm failed", exc_info=True)

                    doubleFilter.newEntry(poc_id + poc_sub, poc_text)
                else:
                    logging.debug("POCSAG%s: %s is not allowed", bitrate, poc_id)
            else:
                logging.warning("No valid POCSAG%s RIC: %s SUB: %s", bitrate, poc_id, poc_sub)

    except Exception:
        logging.error("error while decoding")
        logging.debug("error while decoding", exc_info=True)
