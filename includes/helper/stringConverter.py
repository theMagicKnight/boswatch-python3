#!/usr/bin/python3
# -*- coding: utf-8 -*-
#

"""
little Helper for converting strings

@author: Jens Herrmann
"""

import logging


def decodeString(inputString=""):
    """
    Returns given bytes/string as unicode string

    @type    string: String
    @param   string: String to convert to unicode

    @return:    string in unicode
    @exception: Exception if converting to unicode failed
    """
    decodedString = ""
    logging.debug("call decodeString('%s')", inputString)

    if isinstance(inputString, str):
        logging.debug("-- already unicode/str")
        return inputString

    if not isinstance(inputString, (bytes, bytearray)):
        logging.debug("-- converting non-string type to str")
        return str(inputString)

    encodings = (
        'utf-8',
        'windows-1250',
        'windows-1252',
        'latin_1',
        'cp850',
        'cp852',
        'iso8859_2',
        'iso8859_15',
        'mac_latin2',
        'mac_roman'
    )

    for enc in encodings:
        try:
            decodedString = inputString.decode(enc)
            logging.debug("-- string was encoded in: %s", enc)
            break
        except Exception:
            if enc == encodings[-1]:
                logging.warning("no encoding found")
                logging.debug("no encoding found", exc_info=True)
                raise

    return decodedString


def convertToUnicode(inputString=""):
    """
    Returns given string as unicode string

    @type    string: String
    @param   string: String to convert to unicode

    @return:    string in unicode
    @exception: Exception if converting to unicode failed
    """

    decodedString = ""
    logging.debug("call convertToUnicode('%s')", inputString)

    if inputString is None:
        return ""

    if len(str(inputString)) > 0:
        try:
            if isinstance(inputString, int):
                logging.debug("-- integer")
                return str(inputString)

            if isinstance(inputString, str):
                logging.debug("-- unicode/str")
                return inputString

            decodedString = decodeString(inputString)

        except Exception:
            logging.warning("decoding string failed")
            logging.debug("decoding string failed", exc_info=True)
            raise

    return decodedString


def convertToUTF8(inputString=""):
    """
    Returns given string in UTF-8

    In Python 3 this function returns a UTF-8 string (str),
    not bytes, because the application works with text strings.

    @type    string: String
    @param   string: String to convert to UTF-8

    @return:    string in UTF-8 / unicode text
    @exception: Exception if converting to UTF-8 failed
    """

    utf8String = ""
    logging.debug("call convertToUTF8('%s')", inputString)

    if inputString is None:
        return ""

    if len(str(inputString)) > 0:
        try:
            if isinstance(inputString, int):
                logging.debug("-- integer")
                return str(inputString)

            if isinstance(inputString, str):
                logging.debug("-- unicode/str")
                return inputString

            if isinstance(inputString, (bytes, bytearray)):
                try:
                    utf8String = inputString.decode('utf-8', 'strict')
                    logging.debug("-- UTF-8")
                    return utf8String
                except UnicodeDecodeError:
                    logging.debug("string contains non-UTF-8 characters: %s", inputString)

                    decodedString = decodeString(inputString)
                    utf8String = decodedString
                    logging.debug("string converting succeeded: %s", utf8String)
                    return utf8String

            utf8String = str(inputString)
            return utf8String

        except Exception:
            logging.warning("error checking given string")
            logging.debug("error checking given string", exc_info=True)
            raise

    return utf8String
