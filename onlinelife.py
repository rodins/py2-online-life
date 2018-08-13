#!/usr/bin/python
# -*- coding: UTF-8 -*-

# TODO: nothing found for results and actors

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
APP_DIR_NAME = ".gtk_online_life"
SAVES_DIR_NAME = "saves"
SAVED_IMAGES_DIR_NAME = "saved_images"

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
HOME = os.path.expanduser("~")
APP_SAVES_DIR = os.path.join(HOME, APP_DIR_NAME, SAVES_DIR_NAME)
APP_SAVED_IMAGES_DIR = os.path.join(HOME,
                                    APP_DIR_NAME,
                                    SAVED_IMAGES_DIR_NAME)
    
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
    
class OnlineLifeGui(gtk.Window):
    def __init__(self):
        super(OnlineLifeGui, self).__init__()
        
        self.connect("destroy", self.on_destroy)
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
        
        btn_categories = gtk.ToggleToolButton(gtk.STOCK_DIRECTORY)
        btn_categories.set_tooltip_text("Show/hide categories")
        btn_categories.connect("clicked", self.btn_categories_clicked)
        toolbar.insert(btn_categories, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        bookmark_icon = gtk.Image()
        bookmark_icon.set_from_file(os.path.join(sys.path[0], 
                                                "images", 
                                                "bookmark_24.png"))
        
        self.btn_saved_items = gtk.ToggleToolButton()
        self.btn_saved_items.set_icon_widget(bookmark_icon)
        self.btn_saved_items.set_tooltip_text("Show/hide bookmarks")
        self.btn_saved_items.connect("clicked", self.btn_saved_items_clicked)
        toolbar.insert(self.btn_saved_items, -1)
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        self.btn_refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
        self.btn_refresh.set_tooltip_text("Update results")
        self.btn_refresh.connect("clicked", self.btn_refresh_clicked)
        self.btn_refresh.set_sensitive(False)
        toolbar.insert(self.btn_refresh, -1)
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        self.btn_up = gtk.ToolButton(gtk.STOCK_GO_UP)
        self.btn_up.set_tooltip_text("Move up")
        self.btn_up.connect("clicked", self.btn_up_clicked)
        self.btn_up.set_sensitive(False)
        toolbar.insert(self.btn_up, -1)
        
        self.btn_prev = gtk.ToolButton(gtk.STOCK_GO_BACK)
        self.btn_prev.connect("clicked", self.btn_prev_clicked)
        self.btn_prev.set_sensitive(False)
        toolbar.insert(self.btn_prev, -1)
        
        self.btn_next = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
        self.btn_next.connect("clicked", self.btn_next_clicked)
        self.btn_next.set_sensitive(False)
        toolbar.insert(self.btn_next, -1)
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        entry_item = gtk.ToolItem()
        entry = gtk.Entry()
        entry.set_tooltip_text("Search online-life")
        entry.connect("activate", self.entry_activated)
        entry_item.add(entry)
        toolbar.insert(entry_item, -1)
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        self.btn_actors = gtk.ToggleToolButton(gtk.STOCK_INFO)
        self.btn_actors.set_tooltip_text("Show/hide info")
        self.btn_actors.connect("clicked", self.btn_actors_clicked)
        toolbar.insert(self.btn_actors, -1)
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        btn_exit = gtk.ToolButton(gtk.STOCK_QUIT)
        btn_exit.set_tooltip_text("Quit program")
        btn_exit.connect("clicked", self.btn_quit_clicked)
        toolbar.insert(btn_exit, -1)
        
        vbox.pack_start(toolbar, False, False, 1)
        toolbar.show_all()
        
        hbox = gtk.HBox(False, 1)
        
        SIDE_SIZE = 220
        SPINNER_SIZE = 32
        self.vb_left = gtk.VBox(False, 1)
        self.vb_center = gtk.VBox(False, 1)
        self.vb_right = gtk.VBox(False, 1)
        self.vb_left.set_size_request(SIDE_SIZE, -1)
        self.vb_right.set_size_request(SIDE_SIZE, -1)
        
        # Add widgets to vb_left
        self.tv_categories = self.create_tree_view()
        self.tv_categories.connect("row-activated", self.tv_categories_row_activated)
        self.tv_categories.show()
        self.sw_categories = self.create_scrolled_window()
        self.sw_categories.add(self.tv_categories)
        
        self.sp_categories = gtk.Spinner()
        self.sp_categories.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btn_categoriesError = gtk.Button("Repeat")
        btn_categoriesError.connect("clicked", self.btn_categories_error_clicked)
        btn_categoriesError.show()
        self.hb_categories_error = gtk.HBox(False, 1)
        self.hb_categories_error.pack_start(btn_categoriesError, True, False, 10)
        
        self.vb_left.pack_start(self.sw_categories, True, True, 1)
        self.vb_left.pack_start(self.sp_categories, True, False, 1)
        self.vb_left.pack_start(self.hb_categories_error, True, False, 1)
        
        # Add widgets to vb_center
        self.tvPlaylists = self.create_tree_view()
        self.tvPlaylists.connect("row-activated", self.tv_playlists_row_activated)
        # Stores arg: title, flv, mpv
        self.playlistsStore = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, str)
        self.singlePlaylistStore = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str)
        self.tvPlaylists.show()
        self.swPlaylists = self.create_scrolled_window()
        self.swPlaylists.add(self.tvPlaylists)
        
        self.ivResults = gtk.IconView()
        self.ivResults.set_pixbuf_column(COL_PIXBUF)
        self.ivResults.set_text_column(COL_TEXT)
        self.ivResults.set_item_width(ICON_VIEW_ITEM_WIDTH)
        self.swResults = self.create_scrolled_window()
        self.swResults.add(self.ivResults)
        self.swResults.show_all()
        vadj = self.swResults.get_vadjustment()
        vadj.connect("value-changed", self.on_results_scroll_to_bottom)
        self.ivResults.connect("expose-event", self.on_results_draw)
        self.ivResults.connect("item-activated", self.on_result_activated)
        
        self.spCenter = gtk.Spinner()
        self.spCenter.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btnCenterError = gtk.Button("Repeat")
        btnCenterError.connect("clicked", self.btn_center_error_clicked)
        btnCenterError.show()
        self.hbCenterError = gtk.HBox(False, 1)
        self.hbCenterError.pack_start(btnCenterError, True, False, 10)
        
        self.vb_center.pack_start(self.swPlaylists, True, True, 1)
        self.vb_center.pack_start(self.swResults, True, True, 1)
        self.vb_center.pack_start(self.spCenter, True, False, 1)
        self.vb_center.pack_start(self.hbCenterError, True, False, 1)
        
        # Add widgets to vb_right
        self.lbInfo = gtk.Label("")
        self.lbInfo.set_size_request(SIDE_SIZE, -1)
        self.lbInfo.set_line_wrap(True)
        self.lbInfo.show()
        self.frInfo = gtk.Frame("Info")
        self.frInfo.add(self.lbInfo)
        
        self.tvActors = self.create_tree_view()
        self.tvActors.connect("row-activated", self.tv_actors_row_activated)
        swActors = self.create_scrolled_window()
        swActors.add(self.tvActors)
        swActors.show_all()
        self.frActors = gtk.Frame("Actors")
        self.frActors.add(swActors)
        
        self.spActors = gtk.Spinner()
        self.spActors.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btn_actorsError = gtk.Button("Repeat")
        btn_actorsError.connect("clicked", self.btn_actors_error_clicked)
        btn_actorsError.show()
        self.hbActorsError = gtk.HBox(False, 1)
        self.hbActorsError.pack_start(btn_actorsError, True, False, 10)
        
        spLinks = gtk.Spinner()
        spLinks.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btnLinksError = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
        btnLinksError.set_image(image)
        btnLinksError.set_tooltip_text("Repeat")
        
        self.btnOpen = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_BUTTON)
        self.btnOpen.set_image(image)
        self.btnOpen.set_label("Open")
        self.btnOpen.set_tooltip_text("Get movie links or serial parts list")
        self.btnOpen.connect("clicked", self.btn_open_clicked)
        self.btnOpen.show()
        self.btnOpen.set_sensitive(False)
        
        self.btnSave = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        self.btnSave.set_image(image)
        self.btnSave.set_tooltip_text("Add to bookmarks")
        self.btnSave.connect("clicked", self.btn_save_clicked)
        
        self.btnDelete = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
        self.btnDelete.set_image(image)
        self.btnDelete.set_tooltip_text("Remove from bookmarks")
        self.btnDelete.connect("clicked", self.btn_delete_clicked)
        
        hbActions = gtk.HBox(True, 1)
        hbActions.pack_start(spLinks, True, False, 10)
        hbActions.pack_start(btnLinksError, True, True, 5)
        hbActions.pack_start(self.btnOpen, True, True, 5)
        hbActions.pack_start(self.btnSave, True, True, 5)
        hbActions.pack_start(self.btnDelete, True, True, 5)
        hbActions.show()
        frActions = gtk.Frame("Actions")
        frActions.add(hbActions)
        frActions.show()
        
        tvBackActors = self.create_tree_view()
        swBackActors = self.create_scrolled_window()
        swBackActors.add(tvBackActors)
        frBackActors = gtk.Frame("Actors history")
        frBackActors.add(swBackActors)
        
        self.vb_right.pack_start(self.frInfo, False, False, 1)
        self.vb_right.pack_start(self.frActors, True, True, 1)
        self.vb_right.pack_start(self.spActors, True, False, 1)
        self.vb_right.pack_start(self.hbActorsError, True, False, 1)
        self.vb_right.pack_start(frActions, False, False, 1)
        self.vb_right.pack_start(frBackActors, True, True, 1)
        
        hbox.pack_start(self.vb_left, False, False, 1)
        hbox.pack_start(self.vb_center, True, True, 1)
        hbox.pack_start(self.vb_right, False, False, 1)
        
        vbox.pack_start(hbox, True, True, 1)
        
        self.add(vbox)
        vbox.show()
        hbox.show()
        self.vb_center.show()
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
        self.resultsTitle = None
        self.resultsLink = None
        self.prevHistory = []
        self.nextHistory = []
        self.update_prev_next_buttons()
        self.resultsPosition = None
        self.savedItemsPosition = None
        self.list_saved_files(True) # Show save results on start
        
    def show_categories_spinner(self):
        self.sp_categories.show()
        self.sp_categories.start()
        self.sw_categories.hide()
        self.hb_categories_error.hide()
    
    def show_categories_data(self):
        self.sp_categories.hide()
        self.sp_categories.stop()
        self.sw_categories.show()
        self.hb_categories_error.hide()
    
    def show_categories_error(self):
        self.sp_categories.hide()
        self.sp_categories.stop()
        self.sw_categories.hide()
        self.hb_categories_error.show()
        
    def on_categories_pre_execute(self):
        self.treestore = gtk.TreeStore(gtk.gdk.Pixbuf, str, str)
        self.show_categories_spinner()
        
    def add_main_to_root(self):
        self.itMain = self.treestore.append(None, [DIR_PIXBUF, "Главная", DOMAIN])
        
    def add_to_main(self, title, href):
        self.treestore.append(self.itMain, [FILE_PIXBUF, title, href])
        
    def add_drop_to_root(self, title, href):
        self.itDrop = self.treestore.append(None, [DIR_PIXBUF, title, href])
        
    def add_to_drop(self, title, href):
        self.treestore.append(self.itDrop, [FILE_PIXBUF, title, href])
        
    #TODO: use on first item reseived not on post execute   
    def on_categories_post_execute(self):
        self.tv_categories.set_model(self.treestore)
        self.show_categories_data()
        
    def on_categories_error(self):
        self.show_categories_error()
        
    def btn_categories_clicked(self, widget):
        if self.vb_left.get_visible():
            self.vb_left.hide()
        else:
            self.vb_left.show()
            if self.tv_categories.get_model() != None:
                self.show_categories_data()
            elif self.categoriesThread == None or not self.categoriesThread.is_alive():
                self.categoriesThread = CategoriesThread(self)
                self.categoriesThread.start()
                
    def btn_categories_error_clicked(self, widget):
        if not self.categoriesThread.is_alive():
            self.categoriesThread = CategoriesThread(self)
            self.categoriesThread.start()
    
    def show_center_spinner(self, isPaging):
        self.btn_refresh.set_sensitive(False)
        self.btn_up.set_sensitive(False)
        self.spCenter.show()
        self.spCenter.start()
        self.swPlaylists.hide()
        self.swResults.set_visible(isPaging)
        self.vb_center.set_child_packing(self.spCenter, 
                                        not isPaging, 
                                        False, 
                                        1, 
                                        gtk.PACK_START)
        self.hbCenterError.hide()
        
    def show_results_data(self):
        if self.btn_saved_items.get_active():
            self.btn_refresh.set_sensitive(False)
        else:
            self.btn_refresh.set_sensitive(True)
        self.btn_up.set_sensitive(False)
        self.spCenter.hide()
        self.spCenter.stop()
        self.swPlaylists.hide()
        self.swResults.show()
        self.hbCenterError.hide()
        
    def show_playlists_data(self):
        self.set_title(PROG_NAME + " - " + self.playlistsTitle)
        self.btn_up.set_sensitive(True)
        self.spCenter.hide()
        self.spCenter.stop()
        self.swPlaylists.show()
        self.swResults.hide()
        self.hbCenterError.hide()
        
    def show_center_error(self, title):
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
        self.vb_center.set_child_packing(self.hbCenterError, not isPaging, False, 1, gtk.PACK_START)
        self.hbCenterError.show()

    # TODO: implement playlists error    
    def btn_center_error_clicked(self, widget):
        if self.playlistsError:
            print "Not yet implemented"
        else:
            if not self.resultsThread.is_alive():
                self.resultsThread = ResultsThread(self,
                                                   self.resultsThread.link,
                                                   self.resultsThread.title)
                self.resultsThread.start()
        
    def on_results_pre_execute(self, title):
        if title != "":
            self.set_title(PROG_NAME + " - Loading...")
            self.cancel_image_threads()
            if self.btn_saved_items.get_active():
                self.btn_saved_items.set_active(False)
                self.list_saved_files()
        self.show_center_spinner(title == "")
        
    def on_first_item_received(self, title = ""):
        if title != "":
            # Saving to history first
            if(self.resultsTitle != title): # do not save on refresh when prev and current titles are equal
                self.save_to_prev_history() 
                self.nextHistory = [] # reset next items history on new results
                self.update_prev_next_buttons()
            # Then make changes
            self.resultsNextLink = ""
            self.resultsTitle = title
            self.set_title(PROG_NAME + " - " + title)
            self.create_and_set_results_model()
            self.rangeRepeatSet.clear()
            self.nextLinks.clear()
        self.show_results_data()

    def save_to_prev_history(self):
        if(self.resultsStore != None):
            historyItem = HistoryItem(self.resultsTitle,
                                      self.resultsStore,
                                      self.prevLink,
                                      self.resultsNextLink,
                                      self.get_results_position())
            self.prevHistory.append(historyItem)
            
    def save_to_next_history(self):
        if(self.resultsStore != None):
            historyItem = HistoryItem(self.resultsTitle,
                                      self.resultsStore,
                                      self.prevLink,
                                      self.resultsNextLink,
                                      self.get_results_position())
            self.nextHistory.append(historyItem)

    def restore_from_history(self, historyItem):
        self.resultsTitle = historyItem.title
        self.resultsStore = historyItem.store
        self.resultsLink = historyItem.refreshLink
        self.resultsNextLink = historyItem.nextLink
        self.ivResults.set_model(self.resultsStore)
        # Restore position
        if historyItem.resultsPosition != None:
            self.ivResults.scroll_to_path(historyItem.resultsPosition,
                                          False, 0, 0)
        self.set_title(PROG_NAME + " - " + self.resultsTitle)
        self.rangeRepeatSet.clear()
        self.nextLinks.clear()
        self.show_results_data()
        
    def update_prev_next_buttons(self):
        prevSize = len(self.prevHistory)
        nextSize = len(self.nextHistory)
        # Set top item titles as tooltips for buttons
        if(prevSize > 0):
            topItem = self.prevHistory[prevSize-1]
            self.btn_prev.set_tooltip_text(topItem.title)
        else:
            self.btn_prev.set_tooltip_text("No previous history items")
        if(nextSize > 0):
            topItem = self.nextHistory[nextSize-1]
            self.btn_next.set_tooltip_text(topItem.title)
        else:
            self.btn_next.set_tooltip_text("No next history items")
        # Emable buttons if lists are not empty, disable otherwise    
        self.btn_prev.set_sensitive(prevSize > 0)
        self.btn_next.set_sensitive(nextSize > 0)
        
    def create_and_set_results_model(self):
        self.resultsStore = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str)
        self.ivResults.set_model(self.resultsStore) 
        
    def add_to_results_model(self, title, href, image):
        if image in self.imagesCache:
            self.resultsStore.append([self.imagesCache[image], title, href, image])
        else:
            self.resultsStore.append([EMPTY_POSTER, title, href, image])
    
    def scroll_to_top_of_list(self, store):
        firstIter = store.get_iter_first()
        firstPath = store.get_path(firstIter)
        self.ivResults.scroll_to_path(firstPath, False, 0, 0)
        
    def set_results_next_link(self, link):
        if link != "":
            if link.find("http") == -1:
                self.resultsNextLink = self.get_search_link(link)
            else:
                self.resultsNextLink = link
        else:
            self.resultsNextLink = ""

    def get_results_position(self):
        visible_range = self.ivResults.get_visible_range()
        if visible_range != None:
            return visible_range[1][0] # use indexTo as position
        return None

    def preserve_saved_items_position(self):
        visible_range = self.ivResults.get_visible_range()
        if visible_range != None:
            self.savedItemsPosition = visible_range[0][0] # use indexFrom
        else:
            self.savedItemsPosition = None
    
    def on_results_draw(self, widget, event):
        if self.resultsStore == None or self.btn_saved_items.get_active():
            return
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
    
    def cancel_image_threads(self):
        for thread in self.imageThreads:
            if thread.is_alive():
                print "Cancelling thread..."
                thread.cancel()
        self.imageThreads = []
        
    def on_results_scroll_to_bottom(self, adj):
        if self.resultsStore == None or self.btn_saved_items.get_active():
            return
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
                
    def get_href_id(self, href):
        id_begin = href.find(DOMAIN_NO_SUFFIX)
        # id_begin detection make suffix independent
        if id_begin != -1:
            id_begin = href.find("/", id_begin+1)
            
        id_end = href.find("-", id_begin)
        if id_begin != -1 and id_end != -1:
            id_str = href[id_begin+1: id_end]
            return id_str
        
    def start_js_thread(self, url, referer):
        if self.jsThread == None or not self.jsThread.is_alive():
            # params to init: link and referer
            self.jsThread = JsThread(self, url, referer)
            self.jsThread.start()
    
    def on_result_activated(self, iconview, path):
        store = iconview.get_model()
        resultsIter = store.get_iter(path)
        self.savedItemImage = store.get_value(resultsIter, 0)
        self.playlistsTitle = store.get_value(resultsIter, 1)
        self.actorsLink = store.get_value(resultsIter, 2)
        if self.btn_actors.get_active():
            self.start_actors_thread()
        else:
            # This will get actors for last constant links item if actors button is pressed
            self.isActorsAvailable  = False
            hrefId = self.get_href_id(self.actorsLink)
            url = "http://play.cidwo.com/js.php?id=" + hrefId
            referer = "http://play.cidwo.com/player.php?newsid=" + hrefId
            self.start_js_thread(url, referer)
        
    def show_actors_spinner(self):
        self.btnOpen.set_sensitive(False)
        self.vb_right.show()
        self.spActors.show()
        self.spActors.start()
        self.frInfo.hide()
        self.frActors.hide()
        self.hbActorsError.hide()
        
    def show_actors_data(self):
        self.spActors.stop()
        self.spActors.hide()
        self.frInfo.show()
        self.frActors.show()
        self.hbActorsError.hide()
        
    def show_actors_error(self):
        self.spActors.stop()
        self.spActors.hide()
        self.frInfo.hide()
        self.frActors.hide()
        self.hbActorsError.show()    

    def show_save_or_delete_button(self):
        if self.is_link_saved(self.playlistsTitle):
            self.btnDelete.show()
            self.btnSave.hide()
        else:
            self.btnSave.show()
            self.btnDelete.hide()
        
    def on_actors_pre_execute(self):
        self.show_actors_spinner()
        self.show_save_or_delete_button()
        
    def on_actors_first_item_received(self, info, name, href):
        self.actorsStore = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
        self.tvActors.set_model(self.actorsStore)
        self.lbInfo.set_text(info)
        self.add_to_actors_model(name, href)
        self.isActorsAvailable = True
        self.show_actors_data()
        
    def add_to_actors_model(self, name, href):
        self.actorsStore.append([FILE_PIXBUF, name, href])

    def tv_actors_row_activated(self, treeview, path, view_column):
        model = treeview.get_model()
        actors_iter = model.get_iter(path)
        values = model.get(actors_iter, 1, 2)
        self.prevLink = self.resultsLink
        self.resultsLink = values[1]
        if self.resultsThread == None or not self.resultsThread.is_alive():
            self.resultsThread = ResultsThread(self, self.resultsLink, values[0])
            self.resultsThread.start()
            
    def set_actors_player_url(self, playerUrl):
        self.playerUrl = playerUrl
        self.btnOpen.set_sensitive(self.playerUrl != "")
        
    def btn_open_clicked(self, widget):
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
            
    def btn_save_clicked(self, widget):
        self.save_link(self.playlistsTitle, self.actorsLink)
        self.show_save_or_delete_button()
        self.save_image(self.playlistsTitle)
        self.preserve_saved_items_position()
        self.list_saved_files()
        
    def btn_delete_clicked(self, widget):
        self.remove_link(self.playlistsTitle)
        self.show_save_or_delete_button()
        self.remove_image(self.playlistsTitle)
        self.preserve_saved_items_position()
        self.list_saved_files()
        
    def btn_saved_items_clicked(self, widget):
        self.list_saved_files()
        
    def btn_refresh_clicked(self, widget):
        if not self.resultsThread.is_alive():
            self.resultsThread = ResultsThread(self,
                                               self.resultsLink,
                                               self.resultsTitle)
            self.resultsThread.start()
        
    def btn_up_clicked(self, widget):
        self.set_results_title()
        self.show_results_data()
        self.list_saved_files()
        
    def btn_prev_clicked(self, widget):
        self.save_to_next_history()
        if(len(self.prevHistory) > 0):
            historyItem = self.prevHistory.pop()
            self.restore_from_history(historyItem)
        self.update_prev_next_buttons()
        
    def btn_next_clicked(self, widget):
        self.save_to_prev_history()
        if(len(self.nextHistory) > 0):
            historyItem = self.nextHistory.pop()
            self.restore_from_history(historyItem)
        self.update_prev_next_buttons()

    def set_results_title(self):
        if self.resultsTitle == None:
            self.set_title(PROG_NAME)
        else:
            self.set_title(PROG_NAME + " - " + self.resultsTitle)
        
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
        
    def entry_activated(self, widget):
        query = widget.get_text().strip()
        if query != "":
            self.query = query
            self.prevLink = self.resultsLink
            self.resultsLink = self.get_search_link()
            if self.resultsThread == None or not self.resultsThread.is_alive():
                self.resultsThread = ResultsThread(self, self.resultsLink, query)
                self.resultsThread.start()
        
    def btn_actors_clicked(self, widget):
        if self.btn_actors.get_active():
            if self.isActorsAvailable:
                self.vb_right.show()
            elif self.actorsLink != "":
                self.start_actors_thread()
        else:
            self.vb_right.hide()
    
    def start_actors_thread(self):
        if self.actorsThread == None or not self.actorsThread.is_alive():
            self.on_actors_pre_execute()
            self.actorsThread = ActorsThread(self, self.actorsLink, self.playlistsTitle)
            self.actorsThread.start()   
            
    def btn_actors_error_clicked(self, widget):
        self.start_actors_thread()
        
    def btn_quit_clicked(self, widget):
        self.destroy()
        
    def on_destroy(self, widget):
        if self.categoriesThread != None and self.categoriesThread.is_alive():
            self.categoriesThread.cancel()
        if self.resultsThread != None and self.resultsThread.is_alive():
            self.resultsThread.cancel()
        if self.actorsThread != None and self.actorsThread.is_alive():
            self.actorsThread.cancel()
        self.cancel_image_threads()
        gtk.main_quit()
        
    def tv_categories_row_activated(self, treeview, path, view_column):
        model = treeview.get_model()
        iter_child = model.get_iter(path)
        values = model.get(iter_child, 1, 2) # 0 column is icon
        iter_parent = model.iter_parent(iter_child)
        title = values[0]
        link = values[1]
        if(iter_parent != None):
            values_parent = model.get(iter_parent, 1)
            title = values_parent[0] + " - " + title
        self.prevLink = self.resultsLink
        self.resultsLink = link
        self.resultsThread = ResultsThread(self, link, title)
        self.resultsThread.start()
        
    def on_playlists_pre_execute(self):
        self.btn_saved_items.set_sensitive(False)
        self.playlistsStore.clear()
        self.singlePlaylistStore.clear()
        self.show_center_spinner(False)
        
    def set_playlists_model(self):
        self.tvPlaylists.set_model(self.playlistsStore)
        
    def set_single_playlist_model(self):
        self.tvPlaylists.set_model(self.singlePlaylistStore)
        
    def append_to_playlists(self, title):
        self.itPlaylist = self.playlistsStore.append(None, [DIR_PIXBUF, title, None, None])
        
    def append_to_playlist(self, title, flv, mp4):
        self.playlistsStore.append(self.itPlaylist, [FILE_PIXBUF, title, flv, mp4])
        
    def append_to_single_playlist(self, title, flv, mp4):
        self.singlePlaylistStore.append([FILE_PIXBUF, title, flv, mp4])
        
    def tv_playlists_row_activated(self, treeview, path, view_column):
        model = treeview.get_model()
        pl_iter = model.get_iter(path)
        values = model.get(pl_iter, 1, 2, 3) # 0 column is icon
        if values[1] != None and values[2] != None:
            sizeThread = LinksSizeThread(self, values[0], values[1], values[2])
            sizeThread.start()
            
    def create_tree_view(self):
        treeView = gtk.TreeView()
        
        rendererPixbuf = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("Image", rendererPixbuf, pixbuf=0)
        treeView.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Title", rendererText, text=1)
        treeView.append_column(column)
        
        treeView.set_headers_visible(False)
        
        return treeView
        
    def create_scrolled_window(self):
        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledWindow.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        return scrolledWindow

    def is_image_saved(self, title):
        path = os.path.join(APP_SAVED_IMAGES_DIR, title)
        return os.path.exists(path)

    def get_image(self, title):
        path = os.path.join(APP_SAVED_IMAGES_DIR, title)
        return gtk.gdk.pixbuf_new_from_file(path)

    def save_image(self, title):
        if not os.path.exists(APP_SAVED_IMAGES_DIR):
            os.makedirs(APP_SAVED_IMAGES_DIR)
        path = os.path.join(APP_SAVED_IMAGES_DIR, title)
        if self.savedItemImage != None:
                self.savedItemImage.save(path, "png")

    def remove_image(self, title):
        path = os.path.join(APP_SAVED_IMAGES_DIR, title)
        if os.path.exists(path):
            os.remove(path)

    def is_link_saved(self, title):
         path = os.path.join(APP_SAVES_DIR, title)
         return os.path.exists(path)

    def save_link(self, title, link):
        if not os.path.exists(APP_SAVES_DIR):
            os.makedirs(APP_SAVES_DIR)
        path = os.path.join(APP_SAVES_DIR, title)
        with open(path, "w") as f:
            f.write(link)

    def remove_link(self, title):
        path = os.path.join(APP_SAVES_DIR, title)
        if os.path.exists(path):
            os.remove(path)

    def get_saved_link(self, title):
        filename = os.path.join(APP_SAVES_DIR, title)
        with open(filename, "r") as f:
            link = f.read()
            return link

    def list_saved_files(self, showOnStart = False):
        try:
            saves = os.listdir(APP_SAVES_DIR)
            if len(saves) > 0:
                if showOnStart:
                    self.btn_saved_items.set_active(True)
                self.btn_saved_items.set_sensitive(True)
            else:
                self.btn_saved_items.set_sensitive(False)
                self.btn_saved_items.set_active(False)
                
            if self.btn_saved_items.get_active(): # Show saved items
                self.resultsPosition = self.get_results_position()
                self.btn_prev.set_sensitive(False)
                self.btn_next.set_sensitive(False)
                self.btn_refresh.set_sensitive(False)
                self.set_title(PROG_NAME + " - " + "Saved items")
                savedItemsStore = gtk.ListStore(gtk.gdk.Pixbuf,
                                                str,
                                                str,
                                                str)
                self.ivResults.set_model(savedItemsStore)
                for title in saves:
                    link = self.get_saved_link(title)
                    if self.is_image_saved(title):
                        savedItemsStore.append([self.get_image(title),
                                                title,
                                                link,
                                                None])
                    else:
                        savedItemsStore.append([EMPTY_POSTER,
                                                title,
                                                link,
                                                None])
                        
                if self.savedItemsPosition == None:
                    self.scroll_to_top_of_list(savedItemsStore)
                else:
                    self.ivResults.scroll_to_path(self.savedItemsPosition,
                                                  False, 0, 0)
            else: # Switch back to results
                self.preserve_saved_items_position()
                
                self.update_prev_next_buttons()
                # FIRST set model
                self.ivResults.set_model(self.resultsStore)
                # THEN restore position
                if self.resultsPosition != None and self.resultsStore != None:
                    self.ivResults.scroll_to_path(self.resultsPosition,
                                                  False, 0, 0)
                    self.btn_refresh.set_sensitive(True)
                self.set_results_title()
            if not self.swResults.get_visible():
                self.show_results_data()
        except OSError as ex:
            self.btn_saved_items.set_sensitive(False)
            self.btn_saved_items.set_active(False)
            print ex
        
class CategoriesThread(threading.Thread):
    def __init__(self, gui = None):
        self.gui = gui
        self.isCancelled = False
        threading.Thread.__init__(self)
            
    def cancel(self):
        self.isCancelled = True
        
    def run(self):
        gobject.idle_add(self.gui.on_categories_pre_execute)
        parser = CategoriesHTMLParser(self) 
        try:
            begin_found = False
            drop_found = False
            is_drop_first = False
            
            response = urllib2.urlopen(DOMAIN)
            
            for line in response:
                if self.isCancelled:
                    gobject.idle_add(self.gui.show_categories_data)
                    parser.close()
                    response.close()
                    break
                else:
                    parser.feed(line.decode('cp1251'))
                    
        except Exception as ex:
            print ex
            gobject.idle_add(self.gui.on_categories_error)
            
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
                gobject.idle_add(self.task.gui.add_main_to_root)
        
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
                gobject.idle_add(self.task.gui.on_categories_post_execute)
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
                    gobject.idle_add(self.task.gui.add_drop_to_root, data, self.href)
                elif self.isDropChild:
                    gobject.idle_add(self.task.gui.add_to_drop, data, self.href)
                elif self.isNoDrop and data != "ТВ":
                    gobject.idle_add(self.task.gui.add_to_main, data, self.href)
                    
class ResultsThread(threading.Thread):
    def __init__(self, gui, link, title = ""):
        self.gui = gui
        self.title = title
        self.link = link
        self.isCancelled = False
        threading.Thread.__init__(self)
    
    def run(self):
        gobject.idle_add(self.gui.on_results_pre_execute, self.title)  
        parser = ResultsHTMLParser(self)
        try:
            response = urllib2.urlopen(self.link)
            for line in response:
                if self.isCancelled:
                    parser.close()
                    response.close()
                    gobject.idle_add(self.gui.show_results_data)
                    break
                else:
                    parser.feed(line.decode('cp1251'))      
        except Exception as ex:
            print(ex)
            gobject.idle_add(self.gui.show_center_error, self.title)
            
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
        self.data = ""
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
                gobject.idle_add(self.task.gui.set_results_next_link, 
                                 self.nextLink)
                self.task.cancel()
        elif tag == "a":
            if self.isPosterDiv:
                self.isPosterAnchor = False
                self.isPosterDiv = False
                gobject.idle_add(self.task.gui.add_to_results_model, 
                                 self.data, 
                                 self.href, 
                                 self.image)
                self.data = ""
            if self.isNavAnchor:
                self.isNavAnchor = False
        elif tag == "body":
            self.task.cancel()
            gobject.idle_add(self.task.gui.set_results_next_link, "")
        
    def handle_data(self, data):
        if data.strip() != "":
            if self.isPosterAnchor:
                if(self.count == 0):
                    gobject.idle_add(self.task.gui.on_first_item_received, 
                                     self.task.title)
                self.data += data
                
                # self.title != "" on new results list, not paging
                # scrolling to top after first item added to model  
                if(self.count == 1 and self.task.title != ""):
                    gobject.idle_add(self.task.gui.scroll_to_top_of_list,
                                     self.task.gui.resultsStore)
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
        self.pixbufLoader.connect("area-prepared", self.pixbuf_loader_prepared)
        self.isCancelled = False
        threading.Thread.__init__(self)
        
    def pixbuf_loader_prepared(self, pixbufloader):
        self.row[0] = pixbufloader.get_pixbuf()
        
    def write_to_loader(self, buf):
        self.pixbufLoader.write(buf)
        
    def on_post_execute(self):
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
                gobject.idle_add(self.write_to_loader, buf)
        except Exception as ex:
            print ex
        gobject.idle_add(self.on_post_execute)
        
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
            self.gui.show_actors_error()
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
                    gobject.idle_add(self.task.gui.set_actors_player_url,
                                     attr[1])
                    self.task.cancel()
                    break
                    
    def handle_endtag(self, tag):
        if tag == 'p':
            if self.isDirector:
                self.isDirector = False
            elif self.isActors:
                self.isActors = False
                    
    def get_info(self):
        return self.task.title + " - " + self.year + " - " + self.country
        
    def handle_data(self, utf_data):
        utf_data = utf_data.strip()
        if utf_data != "" and utf_data != ",":
            if self.tag == 'a':
                if self.isDirector:
                    name = utf_data + u" (режиссер)"
                    if self.count == 0:
                        gobject.idle_add(
                            self.task.gui.on_actors_first_item_received,
                            self.get_info(),
                            name,
                            self.href)
                    else:
                        gobject.idle_add(self.task.gui.add_to_actors_model, 
                                     name, 
                                     self.href)
                    self.count += 1
                elif self.isActors:
                    gobject.idle_add(self.task.gui.add_to_actors_model, 
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
                    
def show_error_dialog(window):
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
        
    def start_js_thread(self, jsLink):
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
            gobject.idle_add(show_error_dialog, self.gui)
                
class PlayerHTMLParser(HTMLParser):
    def __init__(self, task):
        self.task = task
        HTMLParser.__init__(self)
    
    def handle_starttag(self, tag, attrs):
        if tag == "script":
            for attr in attrs:
                if attr[0] == "src" and attr[1].find("js.php") != -1:
                    self.task.isCancelled = True
                    gobject.idle_add(self.task.start_js_thread, "http:" + attr[1])
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
        # Some optimization
        if self.flv == self.mp4:
            mp4_size = getLinkSize(self.mp4)
            flv_size = mp4_size
        elif self.mp4.rfind("?download") != -1:
            mp4_size = getLinkSize(self.mp4)
            flv_size = ""
        else:
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
        self.trailersTitle = self.gui.playlistsTitle
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
            self.gui.append_to_playlists(comment)
        
        item_start = json.find("{")
        item_end = json.find("}", item_start+1)
        while item_start != -1 and item_end != -1:
            item = json[item_start: item_end]
            play_item = PlayItem(item)
            if comment != "":
                self.gui.append_to_playlist(play_item.comment, play_item.file, play_item.download)
            else:
                self.gui.append_to_single_playlist(play_item.comment, play_item.file, play_item.download)
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
                    self.gui.set_single_playlist_model()
                    self.gui.show_playlists_data()
                    return
            
            playlist_begin = json.find(begin, playlist_end+2)
            playlist_end = json.find(end, playlist_begin+1)
        #In case of multiple playlists
        self.gui.set_playlists_model()
        self.gui.show_playlists_data()
            
    def getPlaylist(self, link):
        gobject.idle_add(self.gui.on_playlists_pre_execute)
        try:
            response = urllib2.urlopen(link)
            json = response.read()
            gobject.idle_add(self.playlistsParser, json)
        except Exception as ex:
            print ex
            gobject.idle_add(self.gui.show_center_error, "playlists_error")
                
    def run(self):
        headers = {'Referer': self.referer}
        try:
            req = urllib2.Request(self.jsUrl, None, headers)
            response = urllib2.urlopen(req)
            js = response.read()
                
            play_item = PlayItem(js.decode('cp1251'))
            if play_item.comment != "":
                if len(play_item.comment) == 1:
                    play_item.comment = self.trailersTitle
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
            gobject.idle_add(show_error_dialog, self.gui)
            
class PlayItemDialog:
    def __init__(self, gui, play_item, flv_size, mp4_size):
        self.gui = gui
        self.play_item = play_item
        self.RESPONSE_FLV = 1
        self.RESPONSE_MP4 = 2
        self.RESPONSE_INFO = 3
        self.flv_size = flv_size
        self.mp4_size = mp4_size
        self.flv_title = "FLV" + flv_size
        self.mp4_title = "MP4" + mp4_size
        self.play_title = "Play" + mp4_size
        self.create_dialog()
        
    def create_dialog(self):
        label_width = 290
        label = gtk.Label(self.play_item.comment.strip())

        dialog = gtk.Dialog("Process links",
                                        self.gui,
                                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        # Add info button to dialog
        if not self.gui.btn_actors.get_active():
            dialog.add_button(gtk.STOCK_INFO, self.RESPONSE_INFO)
        
        # If we have one link use dialog with one play button and cancel
        if self.flv_size == ""  or self.play_item.file == self.play_item.download:
            # If title too long make label width smaller to activate line wrap
            if len(self.play_item.comment.strip()) > 45:
                label.set_line_wrap(True)
                label.set_justify(gtk.JUSTIFY_CENTER)
                label.set_size_request(label_width, -1)
            
            dialog.add_button(self.play_title, self.RESPONSE_MP4)
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        else:
            dialog.add_button(self.play_title, self.RESPONSE_FLV)
            dialog.add_button(self.play_title, self.RESPONSE_MP4)
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
            
        if self.mp4_size == "":
            dialog.set_response_sensitive(self.RESPONSE_MP4, False)
            
        dialog.vbox.pack_start(label)
        label.show()
        response = dialog.run()
        if response == self.RESPONSE_FLV:
            Popen(["mpv", self.play_item.file])
        elif response == self.RESPONSE_MP4:
            Popen(["mpv", self.play_item.download])
        elif response == self.RESPONSE_INFO:
            self.gui.btn_actors.set_active(True)
            self.gui.start_actors_thread()
        dialog.destroy()

class HistoryItem:
    def __init__(self, title, store, refreshLink, nextLink, resultsPosition):
        self.title = title
        self.store = store
        self.refreshLink = refreshLink
        self.nextLink = nextLink
        self.resultsPosition = resultsPosition
                    
def main():
    gobject.threads_init()
    gtk.main()

if __name__ == "__main__":
    gui = OnlineLifeGui()
    main()
