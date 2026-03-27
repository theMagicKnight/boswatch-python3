#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Functions to load and import the Plugins

@author: Bastian Schroll

@requires: Configuration has to be set in the config.ini
"""

import logging
import os
import importlib.util

from configparser import NoOptionError
from includes import globalVars


def loadPlugins():
    """
    Load all plugins into globalVars.pluginList

    @return: nothing
    @exception: Exception if insert into globalVars.pluginList failed
    """
    try:
        logging.debug("loading plugins")

        for plugin_info in getPlugins():
            try:
                plugin = loadPlugin(plugin_info)
            except Exception:
                logging.error("error loading plugin: %s", plugin_info["name"])
                logging.debug("error loading plugin: %s", plugin_info["name"], exc_info=True)
            else:
                try:
                    logging.debug("call %s.onLoad()", plugin_info["name"])
                    plugin.onLoad()
                    globalVars.pluginList[plugin_info["name"]] = plugin
                except Exception:
                    logging.error("error calling %s.onLoad()", plugin_info["name"])
                    logging.debug("error calling %s.onLoad()", exc_info=True)

    except Exception:
        logging.error("cannot load plugins")
        logging.debug("cannot load plugins", exc_info=True)
        raise


def getPlugins():
    """
    Get a Python list of all activated plugins

    @return: plugins as Python list
    @exception: Exception if plugin search failed
    """
    try:
        logging.debug("Search in plugin folder")
        plugin_folder = os.path.join(globalVars.script_path, "plugins")
        plugins = []

        for entry in os.listdir(plugin_folder):
            location = os.path.join(plugin_folder, entry)
            plugin_file = os.path.join(location, entry + ".py")

            if not os.path.isdir(location) or not os.path.isfile(plugin_file):
                continue

            try:
                if globalVars.config.getint("Plugins", entry):
                    plugins.append({
                        "name": entry,
                        "path": plugin_file,
                    })
                    logging.debug("Plugin [ENABLED ] %s", entry)
                else:
                    logging.debug("Plugin [DISABLED] %s", entry)
            except NoOptionError:
                logging.warning("Plugin [NO CONF ] %s", entry)

    except Exception:
        logging.error("Error during plugin search")
        logging.debug("Error during plugin search", exc_info=True)
        raise

    return plugins


def loadPlugin(plugin):
    """
    Import a single plugin

    @type    plugin: plugin data
    @param   plugin: Contains the information to import a plugin

    @return: imported module
    @exception: Exception if plugin import failed
    """
    try:
        logging.debug("load plugin: %s", plugin["name"])

        spec = importlib.util.spec_from_file_location(plugin["name"], plugin["path"])
        if spec is None or spec.loader is None:
            raise ImportError("cannot create import spec for plugin: %s" % plugin["name"])

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    except Exception:
        logging.error("cannot load plugin: %s", plugin["name"])
        logging.debug("cannot load plugin: %s", plugin["name"], exc_info=True)
        raise
