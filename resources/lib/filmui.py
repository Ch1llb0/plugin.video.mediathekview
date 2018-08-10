# -*- coding: utf-8 -*-
"""
The film model UI module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
Licensed under MIT License
"""

import os

# pylint: disable=import-error
import xbmcgui
import xbmcplugin

from resources.lib.film import Film
from resources.lib.settings import Settings


class FilmUI(Film):
    """
    The film model view class

    Args:
        plugin(MediathekView): the plugin object

        sortmethods(array, optional): an array of sort methods
            for the directory representation. Default is
            ```
            [
                xbmcplugin.SORT_METHOD_TITLE,
                xbmcplugin.SORT_METHOD_DATE`
                xbmcplugin.SORT_METHOD_DURATION,
                xbmcplugin.SORT_METHOD_SIZE
            ]
            ```
    """

    def __init__(self, plugin, sortmethods=None):
        Film.__init__(self)
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.settings = Settings()
        self.sortmethods = sortmethods if sortmethods is not None else [
            xbmcplugin.SORT_METHOD_TITLE,
            xbmcplugin.SORT_METHOD_DATE,
            xbmcplugin.SORT_METHOD_DURATION,
            xbmcplugin.SORT_METHOD_SIZE
        ]
        self.showshows = False
        self.showchannels = False

    def begin(self, showshows, showchannels):
        """
        Begin a directory containing films

        Args:
            showshows(bool): if `True` the showname is prefixed
                to the film name

            showchannels(bool): if `True` the channel name is
                suffixed to the film name
        """
        self.showshows = showshows
        self.showchannels = showchannels
        # xbmcplugin.setContent( self.handle, 'tvshows' )
        for method in self.sortmethods:
            xbmcplugin.addSortMethod(self.handle, method)

    def add(self, alttitle=None, total_items=None):
        """
        Add the current entry to the directory

        Args:
            altname(str, optional): alternative name for the entry

            total_items(int, optional): if specified, the number
                is passed to the kodi routines in order to
                optimize the setup of the directory
        """
        (videourl, listitem, ) = self.get_list_item(alttitle)

        # create context menu
        contextmenu = []
        if self.url_video or self.url_video_sd or self.url_video_hd:
            # play with subtitles
            if not self.settings.autosub and self.url_sub:
                contextmenu.append((
                    self.plugin.language(30921),
                    'RunPlugin({})'.format(
                        self.plugin.build_url({
                            'mode': "playwithsrt",
                            'id': self.filmid,
                            'only_set_resolved_url': False
                        })
                    )
                ))

            # Download movie
            contextmenu.append((
                self.plugin.language(30922),
                'RunPlugin({})'.format(
                    self.plugin.build_url({
                        'mode': "downloadmv",
                        'id': self.filmid,
                        'quality': 1
                    })
                )
            ))
            if self.url_video_hd:
                # Download HD movie
                contextmenu.append((
                    self.plugin.language(30923),
                    'RunPlugin({})'.format(
                        self.plugin.build_url({
                            'mode': "downloadmv",
                            'id': self.filmid,
                            'quality': 2
                        })
                    )
                ))
            # Download TV episode
            contextmenu.append((
                self.plugin.language(30924),
                'RunPlugin({})'.format(
                    self.plugin.build_url({
                        'mode': "downloadep",
                        'id': self.filmid,
                        'quality': 1
                    })
                )
            ))
            if self.url_video_hd:
                # Download HD TV episode
                contextmenu.append((
                    self.plugin.language(30925),
                    'RunPlugin({})'.format(
                        self.plugin.build_url({
                            'mode': "downloadep",
                            'id': self.filmid,
                            'quality': 2
                        })
                    )
                ))
            listitem.addContextMenuItems(contextmenu)

        if self.settings.autosub and self.url_sub:
            videourl = self.plugin.build_url({
                'mode': "playwithsrt",
                'id': self.filmid,
                'only_set_resolved_url': True
            })

        if total_items is not None:
            xbmcplugin.addDirectoryItem(
                handle=self.handle,
                url=videourl,
                listitem=listitem,
                isFolder=False,
                totalItems=total_items
            )
        else:
            xbmcplugin.addDirectoryItem(
                handle=self.handle,
                url=videourl,
                listitem=listitem,
                isFolder=False
            )

    def end(self):
        """ Finish a directory containing films """
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=False)

    def get_list_item(self, alttitle, film=None):
        """ Returns a Kodi `listitem` for a film """
        if film is None:
            film = self
        # get the best url
        # pylint: disable=line-too-long
        videourl = film.url_video_hd if (
            film.url_video_hd != "" and self.plugin.settings.preferhd) else film.url_video if film.url_video != "" else film.url_video_sd
        videohds = " (HD)" if (film.url_video_hd !=
                               "" and self.plugin.settings.preferhd) else ""
        # exit if no url supplied
        if videourl == "":
            return None

        if alttitle is not None:
            resultingtitle = alttitle
        else:
            if self.showshows:
                resultingtitle = film.show + ': ' + film.title
            else:
                resultingtitle = film.title
            if self.showchannels:
                resultingtitle += ' [' + film.channel + ']'

        info_labels = {
            'title': resultingtitle + videohds,
            'sorttitle': resultingtitle.lower(),
            'tvshowtitle': film.show,
            'plot': film.description
        }

        if film.size > 0:
            info_labels['size'] = film.size * 1024 * 1024

        if film.seconds > 0:
            info_labels['duration'] = film.seconds

        if film.aired is not None:
            airedstring = '%s' % film.aired
            if airedstring[:4] != '1970':
                info_labels['date'] = airedstring[8:10] + '-' + \
                    airedstring[5:7] + '-' + airedstring[:4]
                info_labels['aired'] = airedstring
                info_labels['dateadded'] = airedstring

        icon = os.path.join(
            self.plugin.path,
            'resources',
            'icons',
            film.channel.lower() + '-m.png'
        )

        listitem = xbmcgui.ListItem(resultingtitle, path=videourl)
        listitem.setInfo(type='video', infoLabels=info_labels)
        listitem.setProperty('IsPlayable', 'true')
        listitem.setArt({
            'thumb': icon,
            'icon': icon
        })
        return (videourl, listitem)
