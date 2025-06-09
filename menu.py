import nuke

nuke.pluginAddPath('./helpers')
import get_shotlist

helpers_menu = nuke.menu('Nodes').addMenu('Helpers')
nuke.menu('Nodes').addCommand("Helpers/get_shotlist", "get_shotlist.get_shotlist()")