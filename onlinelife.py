#!/usr/bin/python
# -*- coding: UTF-8 -*-

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import urllib
import urllib2
import requests
import sys
import os
from subprocess import Popen
import threading
from HTMLParser import HTMLParser

DOMAIN = "http://online-life.club"
WDOMAIN = "http://www.online-life.club"
DOMAIN_NO_SUFFIX = "www.online-life."
PROG_NAME = "Online life"

COL_PIXBUF = 0
COL_TEXT = 1
ICON_VIEW_ITEM_WIDTH = 180

FILE_PIXBUF = gtk.gdk.pixbuf_new_from_file(os.path.join(sys.path[0], 
                                                        "images",
                                                        "link_16.png"))
DIR_PIXBUF = gtk.gdk.pixbuf_new_from_file(os.path.join(sys.path[0],
                                                       "images",
                                                       "folder_16.png"))
EMPTY_POSTER = gtk.gdk.pixbuf_new_from_file(os.path.join(sys.path[0],
                                                         "images",
                                                         "blank.png"))
    
class PlayItem:
    def __init__(self, js = ""):
        self.comment = ""
        self.file = ""
        self.download = ""
        
        if (js != ""):
            # Search for file
            file_begin = js.find("\"file\"")
            file_end = js.find("\"", file_begin+10)
            if file_begin != -1 and file_end != -1:
                self.file = js[file_begin+8: file_end]
            
            # Search for download
            download_begin = js.find("\"download\"")
            download_end = js.find("\"", download_begin+12)
            if download_begin != -1 and download_end != -1:
                self.download = js[download_begin+12: download_end]
                
            # Search for comment
            comment_begin = js.find("\"comment\"")
            comment_end = js.find("\"", comment_begin+11)
            if comment_begin != -1 and comment_end != -1:
                self.comment = js[comment_begin+11: comment_end]
    
def stringToFile(page):
    print("Saving...")
    with open("Home.html", "w") as f:
        f.write(page)

def fileToString():
    with open("Home.html", "r") as f:
        page = f.read()
        return page

class OnlineLifeGui(gtk.Window):
    def __init__(self):
        super(OnlineLifeGui, self).__init__()
        
        self.set_title(PROG_NAME)
        self.connect("destroy", self.onDestroy)
        self.set_border_width(5)
        self.set_size_request(700, 400)
        try:
            self.set_icon_from_file(os.path.join(sys.path[0],
                                                 "images", 
                                                 "online_life.png"))
        except Exception, e:
            print e.message
            sys.exit(1)
            
        vbox = gtk.VBox(False, 1)
        
        # Toolbar and it's items
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        
        btnCategories = gtk.ToggleToolButton(gtk.STOCK_DIRECTORY)
        btnCategories.set_tooltip_text("Show/hide categories")
        btnCategories.connect("clicked", self.btnCategoriesClicked)
        toolbar.insert(btnCategories, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        bookmarkIcon = gtk.Image()
        bookmarkIcon.set_from_file(os.path.join(sys.path[0], 
                                                "images", 
                                                "bookmark_24.png"))
        
        btnSavedItems = gtk.ToolButton(bookmarkIcon)
        btnSavedItems.set_tooltip_text("Show/hide bookmarks")
        btnSavedItems.connect("clicked", self.btnSavedItemsClicked)
        btnSavedItems.set_sensitive(False)
        toolbar.insert(btnSavedItems, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        self.btnRefresh = gtk.ToolButton(gtk.STOCK_REFRESH)
        self.btnRefresh.set_tooltip_text("Update results")
        self.btnRefresh.connect("clicked", self.btnRefreshClicked)
        self.btnRefresh.set_sensitive(False)
        toolbar.insert(self.btnRefresh, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        self.btnUp = gtk.ToolButton(gtk.STOCK_GO_UP)
        self.btnUp.set_tooltip_text("Move up")
        self.btnUp.connect("clicked", self.btnUpClicked)
        self.btnUp.set_sensitive(False)
        toolbar.insert(self.btnUp, -1)
        
        self.btnPrev = gtk.ToolButton(gtk.STOCK_GO_BACK)
        self.btnPrev.set_tooltip_text("Go back in history")
        self.btnPrev.connect("clicked", self.btnPrevClicked)
        self.btnPrev.set_sensitive(False)
        toolbar.insert(self.btnPrev, -1)
        
        self.btnNext = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
        self.btnNext.set_tooltip_text("Go forward in history")
        self.btnNext.connect("clicked", self.btnNextClicked)
        self.btnNext.set_sensitive(False)
        toolbar.insert(self.btnNext, -1)
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        entryItem = gtk.ToolItem()
        entry = gtk.Entry()
        entry.set_tooltip_text("Search online-life")
        entry.connect("activate", self.entryActivated)
        entryItem.add(entry)
        toolbar.insert(entryItem, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        self.btnActors = gtk.ToggleToolButton(gtk.STOCK_INFO)
        self.btnActors.set_tooltip_text("Show/hide info")
        self.btnActors.connect("clicked", self.btnActorsClicked)
        toolbar.insert(self.btnActors, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        btnExit = gtk.ToolButton(gtk.STOCK_QUIT)
        btnExit.set_tooltip_text("Quit program")
        btnExit.connect("clicked", self.btnQuitClicked)
        toolbar.insert(btnExit, -1)
        
        vbox.pack_start(toolbar, False, False, 1)
        toolbar.show_all()
        
        hbox = gtk.HBox(False, 1)
        
        SIDE_SIZE = 220
        SPINNER_SIZE = 32
        self.vbLeft = gtk.VBox(False, 1)
        self.vbCenter = gtk.VBox(False, 1)
        self.vbRight = gtk.VBox(False, 1)
        self.vbLeft.set_size_request(SIDE_SIZE, -1)
        self.vbRight.set_size_request(SIDE_SIZE, -1)
        
        # Add widgets to vbLeft
        self.tvCategories = self.createTreeView()
        self.tvCategories.connect("row-activated", self.tvCategoriesRowActivated)
        self.tvCategories.show()
        self.swCategories = self.createScrolledWindow()
        self.swCategories.add(self.tvCategories)
        
        self.spCategories = gtk.Spinner()
        self.spCategories.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btnCategoriesError = gtk.Button("Repeat")
        btnCategoriesError.connect("clicked", self.btnCategoriesErrorClicked)
        btnCategoriesError.show()
        self.hbCategoriesError = gtk.HBox(False, 1)
        self.hbCategoriesError.pack_start(btnCategoriesError, True, False, 10)
        
        tvSavedItems = self.createTreeView()
        swSavedItems = self.createScrolledWindow()
        swSavedItems.add(tvSavedItems)
        frSavedItems = gtk.Frame("Saved items")
        frSavedItems.add(swSavedItems)
        
        self.vbLeft.pack_start(self.swCategories, True, True, 1)
        self.vbLeft.pack_start(self.spCategories, True, False, 1)
        self.vbLeft.pack_start(self.hbCategoriesError, True, False, 1)
        self.vbLeft.pack_start(frSavedItems, True, True, 1)
        
        # Add widgets to vbCenter
        self.tvPlaylists = self.createTreeView()
        self.tvPlaylists.connect("row-activated", self.tvPlaylistsRowActivated)
        # Stores arg: title, flv, mpv
        self.playlistsStore = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, str)
        self.singlePlaylistStore = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str)
        self.tvPlaylists.show()
        self.swPlaylists = self.createScrolledWindow()
        self.swPlaylists.add(self.tvPlaylists)
        
        self.ivResults = gtk.IconView()
        self.ivResults.set_pixbuf_column(COL_PIXBUF)
        self.ivResults.set_text_column(COL_TEXT)
        self.ivResults.set_item_width(ICON_VIEW_ITEM_WIDTH)
        self.swResults = self.createScrolledWindow()
        self.swResults.add(self.ivResults)
        self.swResults.show_all()
        vadj = self.swResults.get_vadjustment()
        vadj.connect("value-changed", self.onResultsScrollToBottom)
        self.ivResults.connect("expose-event", self.onResultsDraw)
        self.ivResults.connect("item-activated", self.onResultActivated)
        
        self.spCenter = gtk.Spinner()
        self.spCenter.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btnCenterError = gtk.Button("Repeat")
        btnCenterError.connect("clicked", self.btnCenterErrorClicked)
        btnCenterError.show()
        self.hbCenterError = gtk.HBox(False, 1)
        self.hbCenterError.pack_start(btnCenterError, True, False, 10)
        
        self.vbCenter.pack_start(self.swPlaylists, True, True, 1)
        self.vbCenter.pack_start(self.swResults, True, True, 1)
        self.vbCenter.pack_start(self.spCenter, True, False, 1)
        self.vbCenter.pack_start(self.hbCenterError, True, False, 1)
        
        # Add widgets to vbRight
        self.lbInfo = gtk.Label("")
        self.lbInfo.set_size_request(SIDE_SIZE, -1)
        self.lbInfo.set_line_wrap(True)
        self.lbInfo.show()
        self.frInfo = gtk.Frame("Info")
        self.frInfo.add(self.lbInfo)
        
        self.tvActors = self.createTreeView()
        self.tvActors.connect("row-activated", self.tvActorsRowActivated)
        swActors = self.createScrolledWindow()
        swActors.add(self.tvActors)
        swActors.show_all()
        self.frActors = gtk.Frame("Actors")
        self.frActors.add(swActors)
        
        self.spActors = gtk.Spinner()
        self.spActors.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btnActorsError = gtk.Button("Repeat")
        btnActorsError.connect("clicked", self.btnActorsErrorClicked)
        btnActorsError.show()
        self.hbActorsError = gtk.HBox(False, 1)
        self.hbActorsError.pack_start(btnActorsError, True, False, 10)
        
        spLinks = gtk.Spinner()
        spLinks.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btnLinksError = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
        btnLinksError.set_image(image)
        btnLinksError.set_tooltip_text("Repeat")
        
        #btnGetLinks = gtk.Button()
        #image = gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_BUTTON)
        #btnGetLinks.set_image(image)
        #btnGetLinks.set_tooltip_text("Get links")
        
        self.btnOpen = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_BUTTON)
        self.btnOpen.set_image(image)
        self.btnOpen.set_label("Open")
        self.btnOpen.set_tooltip_text("Get movie links or serial parts list")
        self.btnOpen.connect("clicked", self.btnOpenClicked)
        self.btnOpen.show()
        self.btnOpen.set_sensitive(False)
        
        btnSave = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        btnSave.set_image(image)
        btnSave.set_tooltip_text("Add to bookmarks")
        
        btnDelete = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
        btnDelete.set_image(image)
        btnDelete.set_tooltip_text("Remove from bookmarks")
        
        hbActions = gtk.HBox(True, 1)
        hbActions.pack_start(spLinks, True, False, 10)
        hbActions.pack_start(btnLinksError, True, True, 5)
        #hbActions.pack_start(btnGetLinks, True, True, 5)
        hbActions.pack_start(self.btnOpen, True, True, 5)
        hbActions.pack_start(btnSave, True, True, 5)
        hbActions.pack_start(btnDelete, True, True, 5)
        hbActions.show()
        frActions = gtk.Frame("Actions")
        frActions.add(hbActions)
        frActions.show()
        
        tvBackActors = self.createTreeView()
        swBackActors = self.createScrolledWindow()
        swBackActors.add(tvBackActors)
        frBackActors = gtk.Frame("Actors history")
        frBackActors.add(swBackActors)
        
        self.vbRight.pack_start(self.frInfo, False, False, 1)
        self.vbRight.pack_start(self.frActors, True, True, 1)
        self.vbRight.pack_start(self.spActors, True, False, 1)
        self.vbRight.pack_start(self.hbActorsError, True, False, 1)
        self.vbRight.pack_start(frActions, False, False, 1)
        self.vbRight.pack_start(frBackActors, True, True, 1)
        
        hbox.pack_start(self.vbLeft, False, False, 1)
        hbox.pack_start(self.vbCenter, True, True, 1)
        hbox.pack_start(self.vbRight, False, False, 1)
        
        vbox.pack_start(hbox, True, True, 1)
        
        self.add(vbox)
        vbox.show()
        hbox.show()
        self.vbCenter.show()
        self.show()
        
        self.categoriesThread = None
        self.resultsThread = None
        self.actorsThread = None
        self.playerThread = None
        self.jsThread = None
        self.playlistThread = None
        
        self.rangeRepeatSet = set()
        self.imagesCache = {}
        self.imageThreads = []
        
        self.nextLinks = set()
        
        self.isActorsAvailable = False
        self.actorsLink = ""

        self.resultsStore = None
        self.prevHistory = []
        self.nextHistory = []
        
    def showCategoriesSpinner(self):
        self.spCategories.show()
        self.spCategories.start()
        self.swCategories.hide()
        self.hbCategoriesError.hide()
    
    def showCategoriesData(self):
        self.spCategories.hide()
        self.spCategories.stop()
        self.swCategories.show()
        self.hbCategoriesError.hide()
    
    def showCategoriesError(self):
        self.spCategories.hide()
        self.spCategories.stop()
        self.swCategories.hide()
        self.hbCategoriesError.show()
        
    def onCategoriesPreExecute(self):
        self.treestore = gtk.TreeStore(gtk.gdk.Pixbuf, str, str)
        self.showCategoriesSpinner()
        
    def addMainToRoot(self):
        self.itMain = self.treestore.append(None, [DIR_PIXBUF, "Главная", DOMAIN])
        
    def addToMain(self, title, href):
        self.treestore.append(self.itMain, [FILE_PIXBUF, title, href])
        
    def addDropToRoot(self, title, href):
        self.itDrop = self.treestore.append(None, [DIR_PIXBUF, title, href])
        
    def addToDrop(self, title, href):
        self.treestore.append(self.itDrop, [FILE_PIXBUF, title, href])
        
    #TODO: use on first item reseived not on post execute   
    def onCategoriesPostExecute(self):
        self.tvCategories.set_model(self.treestore)
        self.showCategoriesData()
        
    def onCategoriesError(self):
        self.showCategoriesError()
        
    def btnCategoriesClicked(self, widget):
        if self.vbLeft.get_visible():
            self.vbLeft.hide()
        else:
            self.vbLeft.show()
            if self.tvCategories.get_model() != None:
                self.showCategoriesData()
            elif self.categoriesThread == None or not self.categoriesThread.is_alive():
                self.categoriesThread = CategoriesThread(self)
                self.categoriesThread.start()
                
    def btnCategoriesErrorClicked(self, widget):
        if not self.categoriesThread.is_alive():
            self.categoriesThread = CategoriesThread(self)
            self.categoriesThread.start()
    
    def showCenterSpinner(self, isPaging):
        self.btnRefresh.set_sensitive(False)
        self.btnUp.set_sensitive(False)
        self.spCenter.show()
        self.spCenter.start()
        self.swPlaylists.hide()
        self.swResults.set_visible(isPaging)
        self.vbCenter.set_child_packing(self.spCenter, 
                                        not isPaging, 
                                        False, 
                                        1, 
                                        gtk.PACK_START)
        self.hbCenterError.hide()
        
    def showResultsData(self):
        self.btnRefresh.set_sensitive(True)
        self.btnUp.set_sensitive(False)
        self.spCenter.hide()
        self.spCenter.stop()
        self.swPlaylists.hide()
        self.swResults.show()
        self.hbCenterError.hide()
        
    def showPlaylsitsData(self):
        self.set_title(PROG_NAME + " - " + self.playlistsTitle)
        self.btnUp.set_sensitive(True)
        self.spCenter.hide()
        self.spCenter.stop()
        self.swPlaylists.show()
        self.swResults.hide()
        self.hbCenterError.hide()
        
    def showCenterError(self, title):
        isPaging = (title == "")
        if title == "playlists_error":
            self.playlistsError = True
        else:
            self.playlistsError = False
            
        if not isPaging:
            self.set_title(PROG_NAME + " - Error")
        self.spCenter.hide()
        self.spCenter.stop()
        self.swPlaylists.hide()
        self.swResults.set_visible(isPaging)
        self.vbCenter.set_child_packing(self.hbCenterError, not isPaging, False, 1, gtk.PACK_START)
        self.hbCenterError.show()
        
    def btnCenterErrorClicked(self, widget):
        if self.playlistsError:
            print "Not yet implemented"
        else:
            if not self.resultsThread.is_alive():
                self.resultsThread = ResultsThread(self,
                                                   self.resultsThread.link,
                                                   self.resultsThread.title)
                self.resultsThread.start()
        
    def onResultsPreExecute(self, title):
        if title != "":
            self.set_title(PROG_NAME + " - Loading...")
            self.cancelImageThreads()
            self.resultsNextLink = ""
        self.showCenterSpinner(title == "")
        
    def onFirstItemReceived(self, title = ""):
        if title != "":
            self.resultsTitle = title
            self.set_title(PROG_NAME + " - " + title)
            self.saveToHistory()
            self.createAndSetResultsModel()
            self.rangeRepeatSet.clear()
            self.nextLinks.clear()
        self.showResultsData()

    def saveToHistory(self):
        if(self.resultsStore != None):
            historyItem = HistoryItem(self.resultsTitle, self.resultsStore, self.resultsNextLink)
            self.prevHistory.append(historyItem)
            self.nextHistory = []
            self.updatePrevNextButtons()

    def updatePrevNextButtons(self):
        self.btnPrev.set_sensitive(len(self.prevHistory) != 0)
        self.btnNext.set_sensitive(len(self.nextHistory) != 0)
        
    def createAndSetResultsModel(self):
        self.resultsStore = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str)
        self.ivResults.set_model(self.resultsStore) 
        
    def addToResultsModel(self, title, href, image):
        if image in self.imagesCache:
            self.resultsStore.append([self.imagesCache[image], title, href, image])
        else:
            self.resultsStore.append([EMPTY_POSTER, title, href, image])
    
    def scrollToTopOfList(self):
        firstIter = self.resultsStore.get_iter_first()
        firstPath = self.resultsStore.get_path(firstIter)
        self.ivResults.scroll_to_path(firstPath, False, 0, 0)
        
    def setResultsNextLink(self, link):
        if link != "":
            if link.find("http") == -1:
                self.resultsNextLink = self.get_search_link(link)
            else:
                self.resultsNextLink = link
        else:
            self.resultsNextLink = ""
    
    def onResultsDraw(self, widget, event):
        visible_range = self.ivResults.get_visible_range()
        if visible_range != None:
            indexFrom = visible_range[0][0]
            indexTo = visible_range[1][0] + 1
            
            for index in range(indexFrom, indexTo):
                if index not in self.rangeRepeatSet:
                    self.rangeRepeatSet.add(index)
                    # Get image link from model on index
                    row = self.resultsStore[index]
                    link = row[3] # 3 - image link in model
                    if link != "" and link not in self.imagesCache:
                        imageThread = ImageThread(link, row, self.imagesCache)
                        self.imageThreads.append(imageThread)
                        imageThread.start()
    
    def cancelImageThreads(self):
        for thread in self.imageThreads:
            if thread.is_alive():
                print "Cancelling thread..."
                thread.cancel()
        self.imageThreads = []
        
    def onResultsScrollToBottom(self, adj):
        value = adj.get_value()
        upper = adj.get_upper()
        page_size = adj.get_page_size()
        max_value = value + page_size + page_size
        if max_value > upper:
            if not self.resultsThread.is_alive() and self.resultsNextLink != "":
                if self.resultsNextLink not in self.nextLinks:
                    self.nextLinks.add(self.resultsNextLink)
                    self.resultsThread = ResultsThread(self, self.resultsNextLink)
                    self.resultsThread.start()
                
    def getHrefId(self, href):
        id_begin = href.find(DOMAIN_NO_SUFFIX)
        # id_begin detection make suffix independent
        if id_begin != -1:
            id_begin = href.find("/", id_begin+1)
            
        id_end = href.find("-", id_begin)
        if id_begin != -1 and id_end != -1:
            id_str = href[id_begin+1: id_end]
            return id_str
        
    def startJsThread(self, url, referer):
        if self.jsThread == None or not self.jsThread.is_alive():
            # params to init: link and referer
            self.jsThread = JsThread(self, url, referer)
            self.jsThread.start()
    
    def onResultActivated(self, iconview, path):
        resultsIter = self.resultsStore.get_iter(path)
        self.playlistsTitle = self.resultsStore.get_value(resultsIter, 1)
        self.actorsLink = self.resultsStore.get_value(resultsIter, 2)
        if self.btnActors.get_active():
            self.startActorsThread()
        else:
            hrefId = self.getHrefId(self.actorsLink)
            url = "http://play.cidwo.com/js.php?id=" + hrefId
            referer = "http://play.cidwo.com/player.php?newsid=" + hrefId
            self.startJsThread(url, referer)
        
            
    def showActorsSpinner(self):
        self.btnOpen.set_sensitive(False)
        self.vbRight.show()
        self.spActors.show()
        self.spActors.start()
        self.frInfo.hide()
        self.frActors.hide()
        self.hbActorsError.hide()
        
    def showActorsData(self):
        self.spActors.stop()
        self.spActors.hide()
        self.frInfo.show()
        self.frActors.show()
        self.hbActorsError.hide()
        
    def showActorsError(self):
        self.spActors.stop()
        self.spActors.hide()
        self.frInfo.hide()
        self.frActors.hide()
        self.hbActorsError.show()
        
    def onActorsPreExecute(self):
        self.showActorsSpinner()
        
    def onActorsFirstItemReceived(self, info, name, href):
        self.actorsStore = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
        self.tvActors.set_model(self.actorsStore)
        self.lbInfo.set_text(info)
        self.addToActorsModel(name, href)
        self.isActorsAvailable = True
        self.actorsLink = ""
        self.showActorsData()
        
    def addToActorsModel(self, name, href):
        self.actorsStore.append([FILE_PIXBUF, name, href])
        
    def tvActorsRowActivated(self, treeview, path, view_column):
        model = treeview.get_model()
        actors_iter = model.get_iter(path)
        values = model.get(actors_iter, 1, 2)
        if self.resultsThread == None or not self.resultsThread.is_alive():
            self.resultsThread = ResultsThread(self, values[1], values[0])
            self.resultsThread.start()
            
    def setActorsPlayerUrl(self, playerUrl):
        self.playerUrl = playerUrl
        self.btnOpen.set_sensitive(self.playerUrl != "")
        
    def btnOpenClicked(self, widget):
        if self.playerUrl.find("http") != -1:
            if self.playerThread == None or not self.playerThread.is_alive():
                self.playerThread = PlayerThread(self)
                self.playerThread.start()
        else:
            message = "Cannot open external link: http:" + self.playerUrl
            dialog = gtk.MessageDialog(self, 
                                       gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, 
                                       gtk.MESSAGE_INFO,
                                       gtk.BUTTONS_OK,
                                       message)
            dialog.set_title("External link")
            dialog.run()
            dialog.destroy()
        
        
    def btnSavedItemsClicked(self, widget):
        print("btnSavedItems clicked")
        
    def btnRefreshClicked(self, widget):
        if not self.resultsThread.is_alive():
            self.resultsThread = ResultsThread(self,
                                               self.resultsLink,
                                               self.resultsTitle)
            self.resultsThread.start()
        
    def btnUpClicked(self, widget):
        self.set_title(PROG_NAME + " - " + self.resultsTitle)
        self.showResultsData()
        
    def btnPrevClicked(self, widget):
        print("btnPrev clicked")
        
    def btnNextClicked(self, widget):
        print("btnNext clicked")
        
    def get_search_link(self, page = ""):
        data = {}
        data['do'] = 'search'
        data['subaction'] = 'search'
        data['mode'] = 'simple'
        data['story'] = self.query.encode('cp1251')
        if page != "":
            data['search_start'] = page
        url_values = urllib.urlencode(data)
        return DOMAIN + "?" + url_values
        
    def entryActivated(self, widget):
        query = widget.get_text().strip()
        if query != "":
            self.query = query
            self.resultsTitle = query
            self.resultsLink = self.get_search_link()
            if self.resultsThread == None or not self.resultsThread.is_alive():
                self.resultsThread = ResultsThread(self, self.resultsLink, query)
                self.resultsThread.start()
        
    def btnActorsClicked(self, widget):
        if self.isActorsAvailable:
            if self.vbRight.get_visible():
                self.vbRight.hide()
            elif self.actorsLink == "":
                self.vbRight.show()
            else:
                self.startActorsThread()
        elif self.actorsLink != "":
            self.startActorsThread()
    
    def startActorsThread(self):
        if self.actorsThread == None or not self.actorsThread.is_alive():
            self.onActorsPreExecute()
            self.actorsThread = ActorsThread(self, self.actorsLink, self.playlistsTitle)
            self.actorsThread.start()   
            
    def btnActorsErrorClicked(self, widget):
        self.startActorsThread()
        
    def btnQuitClicked(self, widget):
        self.destroy()
        
    def onDestroy(self, widget):
        if self.categoriesThread != None and self.categoriesThread.is_alive():
            self.categoriesThread.cancel()
        if self.resultsThread != None and self.resultsThread.is_alive():
            self.resultsThread.cancel()
        if self.actorsThread != None and self.actorsThread.is_alive():
            self.actorsThread.cancel()
        self.cancelImageThreads()
        gtk.main_quit()
        
    def tvCategoriesRowActivated(self, treeview, path, view_column):
        model = treeview.get_model()
        iter_child = model.get_iter(path)
        values = model.get(iter_child, 1, 2) # 0 column is icon
        iter_parent = model.iter_parent(iter_child)
        title = values[0]
        link = values[1]
        if(iter_parent != None):
            values_parent = model.get(iter_parent, 1)
            title = values_parent[0] + " - " + title
        self.resultsTitle = title
        self.resultsLink = link
        self.resultsThread = ResultsThread(self, link, title)
        self.resultsThread.start()
        
    def onPlaylistsPreExecute(self):
        self.playlistsStore.clear()
        self.singlePlaylistStore.clear()
        self.showCenterSpinner(False)
        
    def setPlaylistsModel(self):
        self.tvPlaylists.set_model(self.playlistsStore)
        
    def setSinglePlaylistModel(self):
        self.tvPlaylists.set_model(self.singlePlaylistStore)
        
    def appendToPlaylists(self, title):
        self.itPlaylist = self.playlistsStore.append(None, [DIR_PIXBUF, title, None, None])
        
    def appendToPlaylist(self, title, flv, mp4):
        self.playlistsStore.append(self.itPlaylist, [FILE_PIXBUF, title, flv, mp4])
        
    def appendToSinglePlaylist(self, title, flv, mp4):
        self.singlePlaylistStore.append([FILE_PIXBUF, title, flv, mp4])
        
    def tvPlaylistsRowActivated(self, treeview, path, view_column):
        model = treeview.get_model()
        pl_iter = model.get_iter(path)
        values = model.get(pl_iter, 1, 2, 3) # 0 column is icon
        if values[1] != None and values[2] != None:
            sizeThread = LinksSizeThread(self, values[0], values[1], values[2])
            sizeThread.start()
            
        
    def createTreeView(self):
        treeView = gtk.TreeView()
        
        rendererPixbuf = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("Image", rendererPixbuf, pixbuf=0)
        treeView.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Title", rendererText, text=1)
        treeView.append_column(column)
        
        treeView.set_headers_visible(False)
        
        return treeView
        
    def createScrolledWindow(self):
        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledWindow.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        return scrolledWindow
        
class CategoriesThread(threading.Thread):
    def __init__(self, gui = None):
        self.gui = gui
        self.isCancelled = False
        threading.Thread.__init__(self)
        
    def parseAnchor(self, line):
        anchor_begin = line.find("<a href=")
        anchor_end = line.find("</a>")
        if anchor_begin != -1 and anchor_end != -1:
            anchor = line[anchor_begin:anchor_end]
            href_begin = anchor.find("\"")
            href_end = anchor.find("\"", href_begin+1)
            title_begin = anchor.find(">")
            href = anchor[href_begin+1: href_end]
            title = anchor[title_begin+1:].decode('cp1251')
            if href.find(WDOMAIN) == -1:
                href = WDOMAIN + href
            return (title, href)
            
    def cancel(self):
        self.isCancelled = True
        
    def run(self):
        gobject.idle_add(self.gui.onCategoriesPreExecute)
        parser = CategoriesHTMLParser(self) 
        try:
            begin_found = False
            drop_found = False
            is_drop_first = False
            
            response = urllib2.urlopen(DOMAIN)
            
            for line in response:
                if self.isCancelled:
                    gobject.idle_add(self.gui.showCategoriesData)
                    parser.close()
                    response.close()
                    break
                else:
                    parser.feed(line.decode('cp1251'))
                    
        except Exception as ex:
            print ex
            gobject.idle_add(self.gui.onCategoriesError)
            
class CategoriesHTMLParser(HTMLParser):
    def __init__(self, task):
        self.task = task
        self.isNav = False
        self.isDrop = False
        self.isDropChild = False
        self.href = ""
        self.isNoDrop = True
        HTMLParser.__init__(self)
        
    def handle_starttag(self, tag, attrs):
        if tag == "div" and len(attrs) == 1:
            attr = attrs[0]
            if attr[0] == "class" and attr[1] == "nav":
                self.isNav = True
                gobject.idle_add(self.task.gui.addMainToRoot)
        
        if self.isNav:
            if tag == "li":
                if len(attrs) != 0:
                    attr = attrs[0]
                    if attr[0] == "class":
                        if attr[1] == "drop":
                            self.isDrop = True
                        elif attr[1].find("nodrop") != -1:
                            self.isNoDrop = True
                else:
                    self.isDropChild = True
            elif tag == "a":
                for attr in attrs:
                    if attr[0] == "href":
                        if attr[1].find(WDOMAIN) == -1:
                            self.href = WDOMAIN + attr[1]
                        else:
                            self.href = attr[1]
        
    def handle_endtag(self, tag):
        if self.isNav:
            if tag == "div":
                self.isNav = False
                gobject.idle_add(self.task.gui.onCategoriesPostExecute)
                self.task.cancel()
            elif tag == "li":
                if self.isDropChild:
                    self.isDropChild = False
                elif self.isDrop:
                    self.isDrop = False
                elif self.isNoDrop:
                    self.isNoDrop = False
        
    def handle_data(self, data):
        if self.isNav:
            if data.strip() != "":
                if self.isDrop and not self.isDropChild:
                    gobject.idle_add(self.task.gui.addDropToRoot, data, self.href)
                elif self.isDropChild:
                    gobject.idle_add(self.task.gui.addToDrop, data, self.href)
                elif self.isNoDrop and data != "ТВ":
                    gobject.idle_add(self.task.gui.addToMain, data, self.href)
                    
class ResultsThread(threading.Thread):
    def __init__(self, gui, link, title = ""):
        self.gui = gui
        self.title = title
        self.link = link
        self.isCancelled = False
        threading.Thread.__init__(self)
    
    def run(self):
        gobject.idle_add(self.gui.onResultsPreExecute, self.title)  
        parser = ResultsHTMLParser(self)
        try:
            response = urllib2.urlopen(self.link)
            for line in response:
                if self.isCancelled:
                    parser.close()
                    response.close()
                    gobject.idle_add(self.gui.showResultsData)
                    break
                else:
                    parser.feed(line.decode('cp1251'))      
        except Exception as ex:
            print(ex)
            gobject.idle_add(self.gui.showCenterError, self.title)
            
    def cancel(self):
        self.isCancelled = True

class ResultsHTMLParser(HTMLParser):
    def __init__(self, task):
        self.task = task
        self.isPosterDiv = False
        self.isPosterAnchor = False
        self.isNavDiv = False
        self.isNavAnchor = False
        self.count = 0
        self.nextLink = ""
        HTMLParser.__init__(self)
        
    def handle_starttag(self, tag, attrs):
        if tag == "div":
            if len(attrs) != 0:
                attr = attrs[0]
                if attr[0] == "class":
                    if attr[1] == "custom-poster":
                        self.isPosterDiv = True
                    elif attr[1] == "navigation":
                        self.isNavDiv = True
        elif tag == "a":
            if self.isPosterDiv:
                self.isPosterAnchor = True
                for attr in attrs:
                    if attr[0] == "href":
                        self.href = attr[1]
                        break
            if self.isNavDiv:
                self.isNavAnchor = True
                for attr in attrs:
                    if attr[0] == "href":
                        self.nav_href = attr[1]
                        break
                    elif attr[0] == "onclick":
                        self.onclick = attr[1]
        elif tag == "img":
            if self.isPosterAnchor:
                for attr in attrs:
                    if attr[0] == "src":
                        self.image = attr[1]
                        break

        
    def handle_endtag(self, tag):
        if tag == "div":
            if self.isNavDiv:
                self.isNavDiv = False
                gobject.idle_add(self.task.gui.setResultsNextLink, 
                                 self.nextLink)
                self.task.cancel()
        elif tag == "a":
            if self.isPosterDiv:
                self.isPosterAnchor = False
                self.isPosterDiv = False
            if self.isNavAnchor:
                self.isNavAnchor = False
        elif tag == "body":
            self.task.cancel()
            gobject.idle_add(self.task.gui.setResultsNextLink, "")
        
    def handle_data(self, data):
        if data.strip() != "":
            if self.isPosterAnchor:
                if(self.count == 0):
                    gobject.idle_add(self.task.gui.onFirstItemReceived, 
                                     self.task.title)
                gobject.idle_add(self.task.gui.addToResultsModel, 
                                 data, 
                                 self.href, 
                                 self.image)
                # self.title != "" on new results list, not paging
                # scrolling to top after first item added to model  
                if(self.count == 1 and self.task.title != ""):
                    gobject.idle_add(self.task.gui.scrollToTopOfList)
                self.count += 1
            elif self.isNavAnchor:
                if data == "Вперед":
                    if self.nav_href == "#":
                        list_submit_begin = self.onclick.find("list_submit(")
                        list_submit_end = self.onclick.find(")", list_submit_begin)
                        if list_submit_begin != -1 and list_submit_end != -1:
                            self.nextLink = self.onclick[list_submit_begin+12: list_submit_end]
                    else:
                        self.nextLink = self.nav_href
        
class ImageThread(threading.Thread):
    def __init__(self, link, row, imagesCache):
        self.imagesCache = imagesCache
        self.link = link
        self.row = row
        self.pixbufLoader = gtk.gdk.PixbufLoader()
        self.pixbufLoader.connect("area-prepared", self.pixbufLoaderPrepared)
        self.isCancelled = False
        threading.Thread.__init__(self)
        
    def pixbufLoaderPrepared(self, pixbufloader):
        self.row[0] = pixbufloader.get_pixbuf()
        
    def writeToLoader(self, buf):
        self.pixbufLoader.write(buf)
        
    def onPostExecute(self):
        if self.pixbufLoader.close():
            pixbuf = self.pixbufLoader.get_pixbuf()
            self.imagesCache[self.link] = pixbuf
            self.row[0] = pixbuf
        else:
            print "pixbuf error"
        
    def cancel(self):
        self.isCancelled = True
        
    def run(self):
        try:
            response = urllib2.urlopen(self.link)
            for buf in response:
                if self.isCancelled:
                    break 
                gobject.idle_add(self.writeToLoader, buf)
        except Exception as ex:
            print ex
        gobject.idle_add(self.onPostExecute)
        
class ActorsThread(threading.Thread):
    def __init__(self, gui, link, title):
        self.gui = gui
        self.link = link
        self.title = title
        self.isCancelled = False
        threading.Thread.__init__(self)
        
    def cancel(self):
        self.isCancelled = True
        
    def run(self):
        parser = ActorsHTMLParser(self)
        try:
            response = urllib2.urlopen(self.link)
            for line in response:
                if not self.isCancelled:
                    parser.feed(line.decode('cp1251'))
                else:
                    parser.close()
                    break
        except Exception as ex:
            self.gui.showActorsError()
            print ex
            
class ActorsHTMLParser(HTMLParser):
    def __init__(self, task):
        self.task = task
        self.isDirector = False
        self.isActors = False
        self.count = 0
        HTMLParser.__init__(self)
    
    def handle_starttag(self, tag, attrs):
        self.tag = tag
        if tag == "a":
            for attr in attrs:
                if attr[0] == "href":
                    self.href = attr[1]
                    break
        elif tag == 'iframe':
            for attr in attrs:
                if attr[0] == "src":
                    gobject.idle_add(self.task.gui.setActorsPlayerUrl,
                                     attr[1])
                    self.task.cancel()
                    break
                    
    def handle_endtag(self, tag):
        if tag == 'p':
            if self.isDirector:
                self.isDirector = False
            elif self.isActors:
                self.isActors = False
                    
    def getInfo(self):
        return self.task.title + " - " + self.year + " - " + self.country
        
    def handle_data(self, utf_data):
        utf_data = utf_data.strip()
        if utf_data != "" and utf_data != ",":
            if self.tag == 'a':
                if self.isDirector:
                    name = utf_data + u" (режиссер)"
                    if self.count == 0:
                        gobject.idle_add(
                            self.task.gui.onActorsFirstItemReceived,
                            self.getInfo(),
                            name,
                            self.href)
                    else:
                        gobject.idle_add(self.task.gui.addToActorsModel, 
                                     name, 
                                     self.href)
                    self.count += 1
                elif self.isActors:
                    gobject.idle_add(self.task.gui.addToActorsModel, 
                                     utf_data, 
                                     self.href)
                    self.count += 1
            elif self.tag == 'p':
                if utf_data.find(u"Год:") != -1:
                    self.year = utf_data.split(":")[1].strip()
                elif utf_data.find(u"Страна:") != -1:
                    self.country = utf_data.split(":")[1].strip()
                elif utf_data.find(u"Режиссер:") != -1:
                    self.isDirector = True
                elif utf_data.find(u"В ролях:") != -1:
                    self.isActors = True
                    
def showErrorDialog(window):
    message = "Network problem"
    dialog = gtk.MessageDialog(window, 
                               gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, 
                               gtk.MESSAGE_ERROR,
                               gtk.BUTTONS_OK,
                               message)
    dialog.set_title("Error")
    dialog.run()
    dialog.destroy()

class PlayerThread(threading.Thread):
    def __init__(self, gui):
        self.gui = gui
        self.isCancelled = False
        threading.Thread.__init__(self)
        
    def cancel(self):
        self.isCancelled = True
        
    def startJsThread(self, jsLink):
        if self.gui.jsThread == None or not self.gui.jsThread.is_alive():
            # params to init: link and referer
            self.gui.jsThread = JsThread(self.gui, jsLink, self.gui.playerUrl)
            self.gui.jsThread.start()
        
    def run(self):
        try:
            # Go to player link find js link
            parser = PlayerHTMLParser(self)
            response = urllib2.urlopen(self.gui.playerUrl)
            for line in response:
                if not self.isCancelled:
                    parser.feed(line)
                else:
                    parser.close()
                
        except Exception as ex:
            print ex
            gobject.idle_add(showErrorDialog, self.gui)
                
class PlayerHTMLParser(HTMLParser):
    def __init__(self, task):
        self.task = task
        HTMLParser.__init__(self)
    
    def handle_starttag(self, tag, attrs):
        if tag == "script":
            for attr in attrs:
                if attr[0] == "src" and attr[1].find("js.php") != -1:
                    self.task.isCancelled = True
                    gobject.idle_add(self.task.startJsThread, "http:" + attr[1])
                    break

def getLinkSize(link):
    MBFACTOR = float(1 << 20)
    try:
        response = requests.head(link)
        size = response.headers.get('content-length', 0)
        if size == 0:
            return ""
        return ' ({:.2f} Mb)'.format(int(size)/MBFACTOR)
    except Exception as ex:
        print ex
        return ""
        
class LinksSizeThread(threading.Thread):
    def __init__(self, gui, title, flv, mp4):
        self.gui = gui
        self.title = title
        self.flv = flv
        self.mp4 = mp4
        threading.Thread.__init__(self)
        
    def runPlayItemDialog(self, flv_size, mp4_size):
        play_item = PlayItem()
        play_item.comment = self.title
        play_item.file = self.flv
        play_item.download = self.mp4
        PlayItemDialog(self.gui, play_item, flv_size, mp4_size)
        
    def run(self):
        flv_size = getLinkSize(self.flv)
        mp4_size = getLinkSize(self.mp4)
        gobject.idle_add(self.runPlayItemDialog, 
                         flv_size, 
                         mp4_size)
                    
class JsThread(threading.Thread):
    def __init__(self, gui, url, referer):
        self.gui = gui
        self.jsUrl = url
        self.referer = referer
        self.isCancelled = False
        threading.Thread.__init__(self)
        
    def cancel(self):
        self.isCancelled = True
        
    def playlistLinkParser(self, js):
        link_begin = js.find("pl:")
        link_end = js.find("\"", link_begin+4)
        if link_begin != -1 and link_end != -1:
            link = js[link_begin+4: link_end]
            return link
        return ""
        
    def runPlayItemDialog(self, play_item, flv_size, mp4_size):
        PlayItemDialog(self.gui, play_item, flv_size, mp4_size)
            
    def playItemParser(self, js):
        play_item = PlayItem(js)
            
        return play_item
            
    def playlistParser(self, comment, json):
        if comment != "":
            self.gui.appendToPlaylists(comment)
        
        item_start = json.find("{")
        item_end = json.find("}", item_start+1)
        while item_start != -1 and item_end != -1:
            item = json[item_start: item_end]
            play_item = PlayItem(item)
            if comment != "":
                self.gui.appendToPlaylist(play_item.comment, play_item.file, play_item.download)
            else:
                self.gui.appendToSinglePlaylist(play_item.comment, play_item.file, play_item.download)
            item_start = json.find("{", item_end)
            item_end = json.find("}", item_start)
            
    def playlistsParser(self, json):
        begin = "\"comment\""
        end = "]"
        playlist_begin = json.find(begin)
        playlist_end = json.find(end, playlist_begin)
        while playlist_begin != -1 and playlist_end != -1:
            playlist = json[playlist_begin-1: playlist_end]
            comment_begin = playlist.find(":\"")
            comment_end = playlist.find("\"", comment_begin+2)
            if comment_begin != -1 and comment_end != -1:
                comment = playlist[comment_begin+2: comment_end]
                if playlist.find("\"playlist\"") == -1:
                    comment = ""
                    comment_end = -1
                items = playlist[comment_end+1:]        
                self.playlistParser(comment, items)
                # In case of single playlist
                if(comment == ""):
                    self.gui.setSinglePlaylistModel()
                    self.gui.showPlaylsitsData()
                    return
            
            playlist_begin = json.find(begin, playlist_end+2)
            playlist_end = json.find(end, playlist_begin+1)
        #In case of multiple playlists
        self.gui.setPlaylistsModel()
        self.gui.showPlaylsitsData()
            
    def getPlaylist(self, link):
        gobject.idle_add(self.gui.onPlaylistsPreExecute)
        try:
            response = urllib2.urlopen(link)
            json = response.read()
            gobject.idle_add(self.playlistsParser, json)
        except Exception as ex:
            print ex
            gobject.idle_add(self.gui.showCenterError, "playlists_error")
                
    def run(self):
        headers = {'Referer': self.referer}
        try:
            req = urllib2.Request(self.jsUrl, None, headers)
            response = urllib2.urlopen(req)
            js = response.read()
                
            play_item = PlayItem(js.decode('cp1251'))
            if play_item.comment != "":
                if len(play_item.comment) == 1:
                    play_item.comment = "Fix trailer title"
                flv_size = getLinkSize(play_item.file)
                mp4_size = getLinkSize(play_item.download)
                gobject.idle_add(self.runPlayItemDialog, 
                                 play_item, 
                                 flv_size, 
                                 mp4_size)
            else:
                playlist_link = self.playlistLinkParser(js)
                self.getPlaylist(playlist_link)
            
        except Exception as ex:
            print ex
            gobject.idle_add(showErrorDialog, self.gui)
            
class PlayItemDialog:
    def __init__(self, gui, play_item, flv_size, mp4_size):
        self.gui = gui
        self.play_item = play_item
        self.RESPONSE_FLV = 1
        self.RESPONSE_MP4 = 2
        self.flv_size = flv_size
        self.mp4_size = mp4_size
        self.flv_title = "FLV" + flv_size
        self.mp4_title = "MP4" + mp4_size 
        self.createDialog()
        
    def createDialog(self):
        label = gtk.Label(self.play_item.comment)
        dialog = gtk.Dialog("Process links",
                            self.gui,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (self.flv_title, self.RESPONSE_FLV,
                             self.mp4_title, self.RESPONSE_MP4,
                             gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,))
        if self.flv_size == "":
            dialog.set_response_sensitive(self.RESPONSE_FLV, False)
        if self.mp4_size == "":
            dialog.set_response_sensitive(self.RESPONSE_MP4, False)
            
        dialog.vbox.pack_start(label)
        label.show()
        response = dialog.run()
        if response == self.RESPONSE_FLV:
            Popen(["mpv", self.play_item.file])
        elif response == self.RESPONSE_MP4:
            Popen(["mpv", self.play_item.download])
        dialog.destroy()

class HistoryItem:
    def __init__(self, title, store, nextLink):
        self.title = title
        self.store = store
        self.nextLink = nextLink
                    
def main():
    gobject.threads_init()
    gtk.main()

if __name__ == "__main__":
    gui = OnlineLifeGui()
    main()
