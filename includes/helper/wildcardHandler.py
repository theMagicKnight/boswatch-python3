#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import logging
from includes import globalVars
from includes.helper import timeHandler


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def replaceWildcards(text, data):
    try:
        values = {}

        # ---------------------------
        # DATE / TIME
        # ---------------------------
        try:
            values["TIME"] = timeHandler.getTime(data.get("timestamp", 0))
            values["DATE"] = timeHandler.getDate(data.get("timestamp", 0))
        except Exception:
            values["TIME"] = ""
            values["DATE"] = ""

        # ---------------------------
        # SPECIAL
        # ---------------------------
        values["BR"] = "\n"
        values["LPAR"] = "("
        values["RPAR"] = ")"

        # ---------------------------
        # GENERIC DATA (auto upper)
        # ---------------------------
        for key, value in data.items():
            values[key.upper()] = value

        # ---------------------------
        # FMS
        # ---------------------------
        values.setdefault("FMS", data.get("fms", ""))
        values.setdefault("STATUS", data.get("status", ""))
        values.setdefault("DIR", data.get("direction", ""))
        values.setdefault("DIRT", data.get("directionText", ""))
        values.setdefault("TSI", data.get("tsi", ""))

        # ---------------------------
        # ZVEI
        # ---------------------------
        values.setdefault("ZVEI", data.get("zvei", ""))

        # ---------------------------
        # POC
        # ---------------------------
        values.setdefault("RIC", data.get("ric", ""))
        values.setdefault("FUNC", data.get("function", ""))
        values.setdefault("FUNCCHAR", data.get("functionChar", ""))
        values.setdefault("MSG", data.get("msg", ""))
        values.setdefault("BITRATE", str(data.get("bitrate", "")))

        # Function Text
        if "function" in data:
            try:
                if data["function"] == "1":
                    values["FUNCTEXT"] = globalVars.config.get("POC", "rica")
                elif data["function"] == "2":
                    values["FUNCTEXT"] = globalVars.config.get("POC", "ricb")
                elif data["function"] == "3":
                    values["FUNCTEXT"] = globalVars.config.get("POC", "ricc")
                elif data["function"] == "4":
                    values["FUNCTEXT"] = globalVars.config.get("POC", "ricd")
            except Exception:
                values["FUNCTEXT"] = ""

        # ---------------------------
        # DESCRIPTION
        # ---------------------------
        values.setdefault("DESCR", data.get("description", ""))
        values.setdefault("DESCRIPTION", data.get("description", ""))

        # ---------------------------
        # FORMAT
        # ---------------------------
        text = text.format_map(SafeDict(values))

        logging.debug("wildcards replaced (new format {})")

        return text

    except Exception:
        logging.warning("error in wildcard replacement")
        logging.debug("error in wildcard replacement", exc_info=True)
        return text
