#!/usr/bin/python
# -*- coding: UTF-8 -*-

# TODO: fix on traylers two play buttons displayed

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
        
        btn_categories_error = gtk.Button("Repeat")
        btn_categories_error.connect("clicked", self.btn_categories_error_clicked)
        btn_categories_error.show()
        self.hb_categories_error = gtk.HBox(False, 1)
        self.hb_categories_error.pack_start(btn_categories_error, True, False, 10)
        
        self.vb_left.pack_start(self.sw_categories, True, True, 1)
        self.vb_left.pack_start(self.sp_categories, True, False, 1)
        self.vb_left.pack_start(self.hb_categories_error, True, False, 1)
        
        # Add widgets to vb_center
        self.tv_playlists = self.create_tree_view()
        self.tv_playlists.connect("row-activated", self.tv_playlists_row_activated)
        # Stores arg: title, flv, mpv
        self.playlists_store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, str)
        self.single_playlist_store = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str)
        self.tv_playlists.show()
        self.sw_playlists = self.create_scrolled_window()
        self.sw_playlists.add(self.tv_playlists)
        
        self.iv_results = gtk.IconView()
        self.iv_results.set_pixbuf_column(COL_PIXBUF)
        self.iv_results.set_text_column(COL_TEXT)
        self.iv_results.set_item_width(ICON_VIEW_ITEM_WIDTH)
        self.sw_results = self.create_scrolled_window()
        self.sw_results.add(self.iv_results)
        self.sw_results.show_all()
        vadj = self.sw_results.get_vadjustment()
        vadj.connect("value-changed", self.on_results_scroll_to_bottom)
        self.iv_results.connect("expose-event", self.on_results_draw)
        self.iv_results.connect("item-activated", self.on_result_activated)
        
        self.cp_center = gtk.Spinner()
        self.cp_center.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btn_center_error = gtk.Button("Repeat")
        btn_center_error.connect("clicked", self.btn_center_error_clicked)
        btn_center_error.show()
        self.hb_center_error = gtk.HBox(False, 1)
        self.hb_center_error.pack_start(btn_center_error, True, False, 10)
        
        self.vb_center.pack_start(self.sw_playlists, True, True, 1)
        self.vb_center.pack_start(self.sw_results, True, True, 1)
        self.vb_center.pack_start(self.cp_center, True, False, 1)
        self.vb_center.pack_start(self.hb_center_error, True, False, 1)
        
        # Add widgets to vb_right
        self.lb_info = gtk.Label("")
        self.lb_info.set_size_request(SIDE_SIZE, -1)
        self.lb_info.set_line_wrap(True)
        self.lb_info.show()
        self.fr_info = gtk.Frame("Info")
        self.fr_info.add(self.lb_info)
        
        self.tv_actors = self.create_tree_view()
        self.tv_actors.connect("row-activated", self.tv_actors_row_activated)
        sw_actors = self.create_scrolled_window()
        sw_actors.add(self.tv_actors)
        sw_actors.show_all()
        self.fr_actors = gtk.Frame("Actors")
        self.fr_actors.add(sw_actors)
        
        self.sp_actors = gtk.Spinner()
        self.sp_actors.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btn_actors_error = gtk.Button("Repeat")
        btn_actors_error.connect("clicked", self.btn_actors_error_clicked)
        btn_actors_error.show()
        
        self.hb_actors_error = gtk.HBox(False, 1)
        self.hb_actors_error.pack_start(btn_actors_error, True, False, 10)

        self.lb_no_actors = gtk.Label("No actors")
        
        sp_links = gtk.Spinner()
        sp_links.set_size_request(SPINNER_SIZE, SPINNER_SIZE)
        
        btn_links_error = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
        btn_links_error.set_image(image)
        btn_links_error.set_tooltip_text("Repeat")
        
        self.btn_open = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_BUTTON)
        self.btn_open.set_image(image)
        self.btn_open.set_label("Open")
        self.btn_open.set_tooltip_text("Get movie links or serial parts list")
        self.btn_open.connect("clicked", self.btn_open_clicked)
        self.btn_open.show()
        self.btn_open.set_sensitive(False)
        
        self.btn_save = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        self.btn_save.set_image(image)
        self.btn_save.set_tooltip_text("Add to bookmarks")
        self.btn_save.connect("clicked", self.btn_save_clicked)
        
        self.btn_delete = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
        self.btn_delete.set_image(image)
        self.btn_delete.set_tooltip_text("Remove from bookmarks")
        self.btn_delete.connect("clicked", self.btn_delete_clicked)
        
        hb_actions = gtk.HBox(True, 1)
        hb_actions.pack_start(sp_links, True, False, 10)
        hb_actions.pack_start(btn_links_error, True, True, 5)
        hb_actions.pack_start(self.btn_open, True, True, 5)
        hb_actions.pack_start(self.btn_save, True, True, 5)
        hb_actions.pack_start(self.btn_delete, True, True, 5)
        hb_actions.show()
        fr_actions = gtk.Frame("Actions")
        fr_actions.add(hb_actions)
        fr_actions.show()
        
        tv_back_actors = self.create_tree_view()
        sw_back_actors = self.create_scrolled_window()
        sw_back_actors.add(tv_back_actors)
        fr_back_actors = gtk.Frame("Actors history")
        fr_back_actors.add(sw_back_actors)
        
        self.vb_right.pack_start(self.fr_info, False, False, 1)
        self.vb_right.pack_start(self.fr_actors, True, True, 1)
        self.vb_right.pack_start(self.sp_actors, True, False, 1)
        self.vb_right.pack_start(self.hb_actors_error, True, False, 1)
        self.vb_right.pack_start(self.lb_no_actors, True, False, 1)
        self.vb_right.pack_start(fr_actions, False, False, 1)
        self.vb_right.pack_start(fr_back_actors, True, True, 1)
        
        hbox.pack_start(self.vb_left, False, False, 1)
        hbox.pack_start(self.vb_center, True, True, 1)
        hbox.pack_start(self.vb_right, False, False, 1)
        
        vbox.pack_start(hbox, True, True, 1)
        
        self.add(vbox)
        vbox.show()
        hbox.show()
        self.vb_center.show()
        self.show()
        
        self.categories_thread = None
        self.results_thread = None
        self.actors_thread = None
        self.player_thread = None
        self.js_thread = None
        self.playlist_thread = None # Not used? Playlists repeat not implemented
        
        self.range_repeat_set = set()
        self.images_cache = {}
        self.image_threads = []
        
        self.next_links = set()
        
        self.is_actors_available = False
        self.actors_link = ""

        self.results_store = None
        self.results_title = None
        self.results_link = None
        self.prev_history = []
        self.next_history = []
        self.update_prev_next_buttons()
        self.results_position = None
        self.saved_items_position = None
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
        self.it_main = self.treestore.append(None, [DIR_PIXBUF, "Главная", DOMAIN])
        
    def add_to_main(self, title, href):
        self.treestore.append(self.it_main, [FILE_PIXBUF, title, href])
        
    def add_drop_to_root(self, title, href):
        self.it_drop = self.treestore.append(None, [DIR_PIXBUF, title, href])
        
    def add_to_drop(self, title, href):
        self.treestore.append(self.it_drop, [FILE_PIXBUF, title, href])
        
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
            elif self.categories_thread == None or not self.categories_thread.is_alive():
                self.categories_thread = CategoriesThread(self)
                self.categories_thread.start()
                
    def btn_categories_error_clicked(self, widget):
        if not self.categories_thread.is_alive():
            self.categories_thread = CategoriesThread(self)
            self.categories_thread.start()
    
    def show_center_spinner(self, is_paging):
        self.btn_refresh.set_sensitive(False)
        self.btn_up.set_sensitive(False)
        self.cp_center.show()
        self.cp_center.start()
        self.sw_playlists.hide()
        self.sw_results.set_visible(is_paging)
        self.vb_center.set_child_packing(self.cp_center, 
                                        not is_paging, 
                                        False, 
                                        1, 
                                        gtk.PACK_START)
        self.hb_center_error.hide()
        
    def show_results_data(self):
        if self.btn_saved_items.get_active():
            self.btn_refresh.set_sensitive(False)
        else:
            self.btn_refresh.set_sensitive(True)
        self.btn_up.set_sensitive(False)
        self.cp_center.hide()
        self.cp_center.stop()
        self.sw_playlists.hide()
        self.sw_results.show()
        self.hb_center_error.hide()
        
    def show_playlists_data(self):
        self.set_title(PROG_NAME + " - " + self.playlists_title)
        self.btn_up.set_sensitive(True)
        self.cp_center.hide()
        self.cp_center.stop()
        self.sw_playlists.show()
        self.sw_results.hide()
        self.hb_center_error.hide()
        
    def show_center_error(self, title):
        is_paging = (title == "")
        if title == "playlists_error":
            self.playlistsError = True
        else:
            self.playlistsError = False
            
        if not is_paging:
            self.set_title(PROG_NAME + " - Error")
        self.cp_center.hide()
        self.cp_center.stop()
        self.sw_playlists.hide()
        self.sw_results.set_visible(is_paging)
        self.vb_center.set_child_packing(self.hb_center_error, not is_paging, False, 1, gtk.PACK_START)
        self.hb_center_error.show()

    # TODO: implement playlists error    
    def btn_center_error_clicked(self, widget):
        if self.playlistsError:
            print "Not yet implemented"
        else:
            if not self.results_thread.is_alive():
                self.results_thread = ResultsThread(self,
                                                   self.results_thread.link,
                                                   self.results_thread.title)
                self.results_thread.start()
        
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
            if(self.results_title != title): # do not save on refresh when prev and current titles are equal
                self.save_to_prev_history() 
                self.next_history = [] # reset next items history on new results
                self.update_prev_next_buttons()
            # Then make changes
            self.results_next_link = ""
            self.results_title = title
            self.set_title(PROG_NAME + " - " + title)
            self.create_and_set_results_model()
            self.range_repeat_set.clear()
            self.next_links.clear()
        self.show_results_data()

    def save_to_prev_history(self):
        if(self.results_store != None):
            history_item = HistoryItem(self.results_title,
                                      self.results_store,
                                      self.prev_link,
                                      self.results_next_link,
                                      self.get_results_position())
            self.prev_history.append(history_item)
            
    def save_to_next_history(self):
        if(self.results_store != None):
            history_item = HistoryItem(self.results_title,
                                      self.results_store,
                                      self.prev_link,
                                      self.results_next_link,
                                      self.get_results_position())
            self.next_history.append(history_item)

    def restore_from_history(self, history_item):
        self.results_title = history_item.title
        self.results_store = history_item.store
        self.results_link = history_item.refreshLink
        self.results_next_link = history_item.next_link
        self.iv_results.set_model(self.results_store)
        # Restore position
        if history_item.results_position != None:
            self.iv_results.scroll_to_path(history_item.results_position,
                                          False, 0, 0)
        self.set_title(PROG_NAME + " - " + self.results_title)
        self.range_repeat_set.clear()
        self.next_links.clear()
        self.show_results_data()
        
    def update_prev_next_buttons(self):
        prev_size = len(self.prev_history)
        next_size = len(self.next_history)
        # Set top item titles as tooltips for buttons
        if(prev_size > 0):
            top_item = self.prev_history[prev_size-1]
            self.btn_prev.set_tooltip_text(top_item.title)
        else:
            self.btn_prev.set_tooltip_text("No previous history items")
        if(next_size > 0):
            top_item = self.next_history[next_size-1]
            self.btn_next.set_tooltip_text(top_item.title)
        else:
            self.btn_next.set_tooltip_text("No next history items")
        # Emable buttons if lists are not empty, disable otherwise    
        self.btn_prev.set_sensitive(prev_size > 0)
        self.btn_next.set_sensitive(next_size > 0)
        
    def create_and_set_results_model(self):
        self.results_store = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str)
        self.iv_results.set_model(self.results_store) 
        
    def add_to_results_model(self, title, href, image):
        if image in self.images_cache:
            self.results_store.append([self.images_cache[image], title, href, image])
        else:
            self.results_store.append([EMPTY_POSTER, title, href, image])
    
    def scroll_to_top_of_list(self, store):
        if store != None:
            first_iter = store.get_iter_first()
            first_path = store.get_path(first_iter)
            self.iv_results.scroll_to_path(first_path, False, 0, 0)
        
    def set_results_next_link(self, link):
        if link != "":
            if link.find("http") == -1:
                self.results_next_link = self.get_search_link(link)
            else:
                self.results_next_link = link
        else:
            self.results_next_link = ""

    def get_results_position(self):
        visible_range = self.iv_results.get_visible_range()
        if visible_range != None:
            return visible_range[1][0] # use index_to as position
        return None

    def preserve_saved_items_position(self):
        visible_range = self.iv_results.get_visible_range()
        if visible_range != None:
            self.saved_items_position = visible_range[0][0] # use index_from
        else:
            self.saved_items_position = None
    
    def on_results_draw(self, widget, event):
        if self.results_store == None or self.btn_saved_items.get_active():
            return
        visible_range = self.iv_results.get_visible_range()
        if visible_range != None:
            index_from = visible_range[0][0]
            index_to = visible_range[1][0] + 1
            
            for index in range(index_from, index_to):
                if index not in self.range_repeat_set:
                    self.range_repeat_set.add(index)
                    # Get image link from model on index
                    row = self.results_store[index]
                    link = row[3] # 3 - image link in model
                    if link != "" and link not in self.images_cache:
                        image_thread = ImageThread(link, row, self.images_cache)
                        self.image_threads.append(image_thread)
                        image_thread.start()
    
    def cancel_image_threads(self):
        for thread in self.image_threads:
            if thread.is_alive():
                print "Cancelling thread..."
                thread.cancel()
        self.image_threads = []
        
    def on_results_scroll_to_bottom(self, adj):
        if self.results_store == None or self.btn_saved_items.get_active():
            return
        value = adj.get_value()
        upper = adj.get_upper()
        page_size = adj.get_page_size()
        max_value = value + page_size + page_size
        if max_value > upper:
            if not self.results_thread.is_alive() and self.results_next_link != "":
                if self.results_next_link not in self.next_links:
                    self.next_links.add(self.results_next_link)
                    self.results_thread = ResultsThread(self, self.results_next_link)
                    self.results_thread.start()
                
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
        if self.js_thread == None or not self.js_thread.is_alive():
            # params to init: link and referer
            self.js_thread = JsThread(self, url, referer)
            self.js_thread.start()
    
    def on_result_activated(self, iconview, path):
        store = iconview.get_model()
        results_iter = store.get_iter(path)
        self.saved_item_image = store.get_value(results_iter, 0)
        self.playlists_title = store.get_value(results_iter, 1)
        self.actors_link = store.get_value(results_iter, 2)
        if self.btn_actors.get_active():
            self.start_actors_thread()
        else:
            # This will get actors for last constant links item if actors button is pressed
            self.is_actors_available  = False
            hrefId = self.get_href_id(self.actors_link)
            url = "http://play.cidwo.com/js.php?id=" + hrefId
            referer = "http://play.cidwo.com/player.php?newsid=" + hrefId
            self.start_js_thread(url, referer)
        
    def show_actors_spinner(self):
        self.btn_open.set_sensitive(False)
        self.vb_right.show()
        self.sp_actors.show()
        self.sp_actors.start()
        self.fr_info.hide()
        self.fr_actors.hide()
        self.hb_actors_error.hide()
        self.lb_no_actors.hide()
        
    def show_actors_data(self):
        self.sp_actors.stop()
        self.sp_actors.hide()
        self.fr_info.show()
        self.fr_actors.show()
        self.hb_actors_error.hide()
        
    def show_actors_error(self):
        self.sp_actors.stop()
        self.sp_actors.hide()
        self.fr_info.hide()
        self.fr_actors.hide()
        self.hb_actors_error.show()

    def show_no_actors(self):
        self.sp_actors.stop()
        self.sp_actors.hide()
        self.lb_no_actors.show()

    def show_save_or_delete_button(self):
        if self.is_link_saved(self.playlists_title):
            self.btn_delete.show()
            self.btn_save.hide()
        else:
            self.btn_save.show()
            self.btn_delete.hide()
        
    def on_actors_pre_execute(self):
        self.show_actors_spinner()
        self.show_save_or_delete_button()
        self.actors_store = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
        self.tv_actors.set_model(self.actors_store)
        
    def on_actors_first_item_received(self, info, name, href):
        self.lb_info.set_text(info)
        self.add_to_actors_model(name, href)
        self.is_actors_available = True
        self.show_actors_data()
        
    def add_to_actors_model(self, name, href):
        self.actors_store.append([FILE_PIXBUF, name, href])

    def tv_actors_row_activated(self, treeview, path, view_column):
        model = treeview.get_model()
        actors_iter = model.get_iter(path)
        values = model.get(actors_iter, 1, 2)
        self.prev_link = self.results_link
        self.results_link = values[1]
        if self.results_thread == None or not self.results_thread.is_alive():
            self.results_thread = ResultsThread(self, self.results_link, values[0])
            self.results_thread.start()
            
    def set_actors_player_url(self, player_url):
        self.player_url = player_url
        self.btn_open.set_sensitive(self.player_url != "")
        
    def btn_open_clicked(self, widget):
        if self.player_url.find("http") != -1:
            if self.player_thread == None or not self.player_thread.is_alive():
                self.player_thread = PlayerThread(self)
                self.player_thread.start()
        else:
            message = "Cannot open external link: http:" + self.player_url
            dialog = gtk.MessageDialog(self, 
                                       gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, 
                                       gtk.MESSAGE_INFO,
                                       gtk.BUTTONS_OK,
                                       message)
            dialog.set_title("External link")
            dialog.run()
            dialog.destroy()
            
    def btn_save_clicked(self, widget):
        self.save_link(self.playlists_title, self.actors_link)
        self.show_save_or_delete_button()
        self.save_image(self.playlists_title)
        self.preserve_saved_items_position()
        self.list_saved_files()
        
    def btn_delete_clicked(self, widget):
        self.remove_link(self.playlists_title)
        self.show_save_or_delete_button()
        self.remove_image(self.playlists_title)
        self.preserve_saved_items_position()
        self.list_saved_files()
        
    def btn_saved_items_clicked(self, widget):
        self.list_saved_files()
        
    def btn_refresh_clicked(self, widget):
        if not self.results_thread.is_alive():
            self.results_thread = ResultsThread(self,
                                               self.results_link,
                                               self.results_title)
            self.results_thread.start()
        
    def btn_up_clicked(self, widget):
        self.set_results_title()
        self.show_results_data()
        self.list_saved_files()
        
    def btn_prev_clicked(self, widget):
        self.save_to_next_history()
        if(len(self.prev_history) > 0):
            history_item = self.prev_history.pop()
            self.restore_from_history(history_item)
        self.update_prev_next_buttons()
        
    def btn_next_clicked(self, widget):
        self.save_to_prev_history()
        if(len(self.next_history) > 0):
            history_item = self.next_history.pop()
            self.restore_from_history(history_item)
        self.update_prev_next_buttons()

    def set_results_title(self):
        if self.results_title == None:
            self.set_title(PROG_NAME)
        else:
            self.set_title(PROG_NAME + " - " + self.results_title)
        
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
            self.prev_link = self.results_link
            self.results_link = self.get_search_link()
            if self.results_thread == None or not self.results_thread.is_alive():
                self.results_thread = ResultsThread(self, self.results_link, query)
                self.results_thread.start()
        
    def btn_actors_clicked(self, widget):
        if self.btn_actors.get_active():
            if self.is_actors_available:
                self.vb_right.show()
            elif self.actors_link != "":
                self.start_actors_thread()
        else:
            self.vb_right.hide()
    
    def start_actors_thread(self):
        if self.actors_thread == None or not self.actors_thread.is_alive():
            self.on_actors_pre_execute()
            self.actors_thread = ActorsThread(self, self.actors_link, self.playlists_title)
            self.actors_thread.start()   
            
    def btn_actors_error_clicked(self, widget):
        self.start_actors_thread()
        
    def btn_quit_clicked(self, widget):
        self.destroy()
        
    def on_destroy(self, widget):
        if self.categories_thread != None and self.categories_thread.is_alive():
            self.categories_thread.cancel()
        if self.results_thread != None and self.results_thread.is_alive():
            self.results_thread.cancel()
        if self.actors_thread != None and self.actors_thread.is_alive():
            self.actors_thread.cancel()
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
        self.prev_link = self.results_link
        self.results_link = link
        self.results_thread = ResultsThread(self, link, title)
        self.results_thread.start()
        
    def on_playlists_pre_execute(self):
        self.btn_saved_items.set_sensitive(False)
        self.playlists_store.clear()
        self.single_playlist_store.clear()
        self.show_center_spinner(False)
        
    def set_playlists_model(self):
        self.tv_playlists.set_model(self.playlists_store)
        
    def set_single_playlist_model(self):
        self.tv_playlists.set_model(self.single_playlist_store)
        
    def append_to_playlists(self, title):
        self.itPlaylist = self.playlists_store.append(None, [DIR_PIXBUF, title, None, None])
        
    def append_to_playlist(self, title, flv, mp4):
        self.playlists_store.append(self.itPlaylist, [FILE_PIXBUF, title, flv, mp4])
        
    def append_to_single_playlist(self, title, flv, mp4):
        self.single_playlist_store.append([FILE_PIXBUF, title, flv, mp4])
        
    def tv_playlists_row_activated(self, treeview, path, view_column):
        model = treeview.get_model()
        pl_iter = model.get_iter(path)
        values = model.get(pl_iter, 1, 2, 3) # 0 column is icon
        if values[1] != None and values[2] != None:
            sizeThread = LinksSizeThread(self, values[0], values[1], values[2])
            sizeThread.start()
            
    def create_tree_view(self):
        tree_view = gtk.TreeView()
        
        renderer_pixbuf = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("Image", renderer_pixbuf, pixbuf=0)
        tree_view.append_column(column)
        
        renderer_text = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Title", renderer_text, text=1)
        tree_view.append_column(column)
        
        tree_view.set_headers_visible(False)
        
        return tree_view
        
    def create_scrolled_window(self):
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        return scrolled_window

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
        if self.saved_item_image != None:
                self.saved_item_image.save(path, "png")

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

    def list_saved_files(self, show_on_start = False):
        try:
            saves = os.listdir(APP_SAVES_DIR)
            if len(saves) > 0:
                if show_on_start:
                    self.btn_saved_items.set_active(True)
                self.btn_saved_items.set_sensitive(True)
            else:
                self.btn_saved_items.set_sensitive(False)
                self.btn_saved_items.set_active(False)
                
            if self.btn_saved_items.get_active(): # Show saved items
                self.results_position = self.get_results_position()
                self.btn_prev.set_sensitive(False)
                self.btn_next.set_sensitive(False)
                self.btn_refresh.set_sensitive(False)
                self.set_title(PROG_NAME + " - " + "Saved items")
                saved_items_store = gtk.ListStore(gtk.gdk.Pixbuf,
                                                str,
                                                str,
                                                str)
                self.iv_results.set_model(saved_items_store)
                for title in saves:
                    link = self.get_saved_link(title)
                    if self.is_image_saved(title):
                        saved_items_store.append([self.get_image(title),
                                                title,
                                                link,
                                                None])
                    else:
                        saved_items_store.append([EMPTY_POSTER,
                                                title,
                                                link,
                                                None])
                        
                if self.saved_items_position == None:
                    self.scroll_to_top_of_list(saved_items_store)
                else:
                    self.iv_results.scroll_to_path(self.saved_items_position,
                                                  False, 0, 0)
            else: # Switch back to results
                self.preserve_saved_items_position()
                
                self.update_prev_next_buttons()
                # FIRST set model
                self.iv_results.set_model(self.results_store)
                # THEN restore position
                if self.results_position != None and self.results_store != None:
                    self.iv_results.scroll_to_path(self.results_position,
                                                  False, 0, 0)
                    self.btn_refresh.set_sensitive(True)
                self.set_results_title()
        except OSError as ex:
            self.btn_saved_items.set_sensitive(False)
            self.btn_saved_items.set_active(False)
            print ex
        
class CategoriesThread(threading.Thread):
    def __init__(self, gui = None):
        self.gui = gui
        self.is_cancelled = False
        threading.Thread.__init__(self)
            
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        gobject.idle_add(self.gui.on_categories_pre_execute)
        parser = CategoriesHTMLParser(self) 
        try:
            begin_found = False
            drop_found = False
            is_drop_first = False
            
            response = urllib2.urlopen(DOMAIN)
            
            for line in response:
                if self.is_cancelled:
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
        self.is_nav = False
        self.is_drop = False
        self.is_drop_child = False
        self.href = ""
        self.is_no_drop = True
        HTMLParser.__init__(self)
        
    def handle_starttag(self, tag, attrs):
        if tag == "div" and len(attrs) == 1:
            attr = attrs[0]
            if attr[0] == "class" and attr[1] == "nav":
                self.is_nav = True
                gobject.idle_add(self.task.gui.add_main_to_root)
        
        if self.is_nav:
            if tag == "li":
                if len(attrs) != 0:
                    attr = attrs[0]
                    if attr[0] == "class":
                        if attr[1] == "drop":
                            self.is_drop = True
                        elif attr[1].find("nodrop") != -1:
                            self.is_no_drop = True
                else:
                    self.is_drop_child = True
            elif tag == "a":
                for attr in attrs:
                    if attr[0] == "href":
                        if attr[1].find(WDOMAIN) == -1:
                            self.href = WDOMAIN + attr[1]
                        else:
                            self.href = attr[1]
        
    def handle_endtag(self, tag):
        if self.is_nav:
            if tag == "div":
                self.is_nav = False
                gobject.idle_add(self.task.gui.on_categories_post_execute)
                self.task.cancel()
            elif tag == "li":
                if self.is_drop_child:
                    self.is_drop_child = False
                elif self.is_drop:
                    self.is_drop = False
                elif self.is_no_drop:
                    self.is_no_drop = False
        
    def handle_data(self, data):
        if self.is_nav:
            if data.strip() != "":
                if self.is_drop and not self.is_drop_child:
                    gobject.idle_add(self.task.gui.add_drop_to_root, data, self.href)
                elif self.is_drop_child:
                    gobject.idle_add(self.task.gui.add_to_drop, data, self.href)
                elif self.is_no_drop and data != "ТВ":
                    gobject.idle_add(self.task.gui.add_to_main, data, self.href)
                    
class ResultsThread(threading.Thread):
    def __init__(self, gui, link, title = ""):
        self.gui = gui
        self.title = title
        self.link = link
        self.is_cancelled = False
        threading.Thread.__init__(self)
    
    def run(self):
        gobject.idle_add(self.gui.on_results_pre_execute, self.title)  
        parser = ResultsHTMLParser(self)
        try:
            response = urllib2.urlopen(self.link)
            for line in response:
                if self.is_cancelled:
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
        self.is_cancelled = True

class ResultsHTMLParser(HTMLParser):
    def __init__(self, task):
        self.task = task
        self.is_poster_div = False
        self.is_poster_anchor = False
        self.is_nav_div = False
        self.is_nav_anchor = False
        self.count = 0
        self.next_link = ""
        self.data = ""
        HTMLParser.__init__(self)
        
    def handle_starttag(self, tag, attrs):
        if tag == "div":
            if len(attrs) != 0:
                attr = attrs[0]
                if attr[0] == "class":
                    if attr[1] == "custom-poster":
                        self.is_poster_div = True
                    elif attr[1] == "navigation":
                        self.is_nav_div = True
        elif tag == "a":
            if self.is_poster_div:
                self.is_poster_anchor = True
                for attr in attrs:
                    if attr[0] == "href":
                        self.href = attr[1]
                        break
            if self.is_nav_div:
                self.is_nav_anchor = True
                for attr in attrs:
                    if attr[0] == "href":
                        self.nav_href = attr[1]
                        break
                    elif attr[0] == "onclick":
                        self.onclick = attr[1]
        elif tag == "img":
            if self.is_poster_anchor:
                for attr in attrs:
                    if attr[0] == "src":
                        self.image = attr[1]
                        break

        
    def handle_endtag(self, tag):
        if tag == "div":
            if self.is_nav_div:
                self.is_nav_div = False
                gobject.idle_add(self.task.gui.set_results_next_link, 
                                 self.next_link)
                self.task.cancel()
        elif tag == "a":
            if self.is_poster_div:
                self.is_poster_anchor = False
                self.is_poster_div = False
                gobject.idle_add(self.task.gui.add_to_results_model, 
                                 self.data, 
                                 self.href, 
                                 self.image)
                self.data = ""
            if self.is_nav_anchor:
                self.is_nav_anchor = False
        elif tag == "body":
            self.task.cancel()
            gobject.idle_add(self.task.gui.set_results_next_link, "")
        
    def handle_data(self, data):
        if data.strip() != "":
            if self.is_poster_anchor:
                if(self.count == 0):
                    gobject.idle_add(self.task.gui.on_first_item_received, 
                                     self.task.title)
                self.data += data
                
                # self.title != "" on new results list, not paging
                # scrolling to top after first item added to model  
                if(self.count == 1 and self.task.title != ""):
                    gobject.idle_add(self.task.gui.scroll_to_top_of_list,
                                     self.task.gui.results_store)
                self.count += 1
            elif self.is_nav_anchor:
                if data == "Вперед":
                    if self.nav_href == "#":
                        list_submit_begin = self.onclick.find("list_submit(")
                        list_submit_end = self.onclick.find(")", list_submit_begin)
                        if list_submit_begin != -1 and list_submit_end != -1:
                            self.next_link = self.onclick[list_submit_begin+12: list_submit_end]
                    else:
                        self.next_link = self.nav_href
        
class ImageThread(threading.Thread):
    def __init__(self, link, row, images_cache):
        self.images_cache = images_cache
        self.link = link
        self.row = row
        self.pixbuf_loader = gtk.gdk.PixbufLoader()
        self.pixbuf_loader.connect("area-prepared", self.pixbuf_loader_prepared)
        self.is_cancelled = False
        threading.Thread.__init__(self)
        
    def pixbuf_loader_prepared(self, pixbufloader):
        self.row[0] = pixbufloader.get_pixbuf()
        
    def write_to_loader(self, buf):
        self.pixbuf_loader.write(buf)
        
    def on_post_execute(self):
        if self.pixbuf_loader.close():
            pixbuf = self.pixbuf_loader.get_pixbuf()
            self.images_cache[self.link] = pixbuf
            self.row[0] = pixbuf
        else:
            print "pixbuf error"
        
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        try:
            response = urllib2.urlopen(self.link)
            for buf in response:
                if self.is_cancelled:
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
        self.is_cancelled = False
        threading.Thread.__init__(self)
        
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        parser = ActorsHTMLParser(self)
        try:
            response = urllib2.urlopen(self.link)
            for line in response:
                if not self.is_cancelled:
                    parser.feed(line.decode('cp1251'))
                else:
                    break
            if parser.count == 0:
                gobject.idle_add(self.gui.show_no_actors)
            parser.close()
        except Exception as ex:
            self.gui.show_actors_error()
            print ex
            
class ActorsHTMLParser(HTMLParser):
    def __init__(self, task):
        self.task = task
        self.is_director = False
        self.is_actors = False
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
            if self.is_director:
                self.is_director = False
            elif self.is_actors:
                self.is_actors = False
                    
    def get_info(self):
        return self.task.title + " - " + self.year + " - " + self.country
        
    def handle_data(self, utf_data):
        utf_data = utf_data.strip()
        if utf_data != "" and utf_data != ",":
            if self.tag == 'a':
                if self.is_director or self.is_actors:
                    if self.is_director:
                        name = utf_data + u" (режиссер)"
                    else:
                        name = utf_data
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
            elif self.tag == 'p':
                if utf_data.find(u"Год:") != -1:
                    self.year = utf_data.split(":")[1].strip()
                elif utf_data.find(u"Страна:") != -1:
                    self.country = utf_data.split(":")[1].strip()
                elif utf_data.find(u"Режиссер:") != -1:
                    self.is_director = True
                elif utf_data.find(u"В ролях:") != -1:
                    self.is_actors = True
                    
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
        self.is_cancelled = False
        threading.Thread.__init__(self)
        
    def cancel(self):
        self.is_cancelled = True
        
    def start_js_thread(self, js_link):
        if self.gui.js_thread == None or not self.gui.js_thread.is_alive():
            # params to init: link and referer
            self.gui.js_thread = JsThread(self.gui, js_link, self.gui.player_url)
            self.gui.js_thread.start()
        
    def run(self):
        try:
            # Go to player link find js link
            parser = PlayerHTMLParser(self)
            response = urllib2.urlopen(self.gui.player_url)
            for line in response:
                if not self.is_cancelled:
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
                    self.task.is_cancelled = True
                    gobject.idle_add(self.task.start_js_thread, "http:" + attr[1])
                    break

def get_link_size(link):
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
        
    def run_play_item_dialog(self, flv_size, mp4_size):
        play_item = PlayItem()
        play_item.comment = self.title
        play_item.file = self.flv
        play_item.download = self.mp4
        PlayItemDialog(self.gui, play_item, flv_size, mp4_size)
        
    def run(self):
        # Some optimization
        if self.flv == self.mp4:
            mp4_size = get_link_size(self.mp4)
            flv_size = mp4_size
        elif self.mp4.rfind("?download") != -1:
            mp4_size = get_link_size(self.mp4)
            flv_size = ""
        else:
            flv_size = get_link_size(self.flv)
            mp4_size = get_link_size(self.mp4)
        gobject.idle_add(self.run_play_item_dialog, 
                         flv_size, 
                         mp4_size)
                    
class JsThread(threading.Thread):
    def __init__(self, gui, url, referer):
        self.gui = gui
        self.jsUrl = url
        self.referer = referer
        self.is_cancelled = False
        self.trailersTitle = self.gui.playlists_title
        threading.Thread.__init__(self)
        
    def cancel(self):
        self.is_cancelled = True
        
    def playlist_link_parser(self, js):
        link_begin = js.find("pl:")
        link_end = js.find("\"", link_begin+4)
        if link_begin != -1 and link_end != -1:
            link = js[link_begin+4: link_end]
            return link
        return ""
        
    def run_play_item_dialog(self, play_item, flv_size, mp4_size):
        PlayItemDialog(self.gui, play_item, flv_size, mp4_size)
            
    def play_item_parser(self, js):
        play_item = PlayItem(js)
            
        return play_item
            
    def playlist_parser(self, comment, json):
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
            
    def playlists_parser(self, json):
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
                self.playlist_parser(comment, items)
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
            
    def get_playlist(self, link):
        gobject.idle_add(self.gui.on_playlists_pre_execute)
        try:
            response = urllib2.urlopen(link)
            json = response.read()
            gobject.idle_add(self.playlists_parser, json)
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
                flv_size = get_link_size(play_item.file)
                mp4_size = get_link_size(play_item.download)
                gobject.idle_add(self.run_play_item_dialog, 
                                 play_item, 
                                 flv_size, 
                                 mp4_size)
            else:
                playlist_link = self.playlist_link_parser(js)
                self.get_playlist(playlist_link)
            
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
            self.detect_player(self.play_item.file)
        elif response == self.RESPONSE_MP4:
            self.detect_player(self.play_item.download)
        elif response == self.RESPONSE_INFO:
            self.gui.btn_actors.set_active(True)
            self.gui.start_actors_thread()
        dialog.destroy()

    def detect_player(self, link):
        if os.system("which mpv") == 0:
            self.open_mpv(link)
        elif os.system("which omxplayer") == 0: # Papberry Pi default player
            self.open_omxplayer(link)
        else:
            print("TODO: display dialog that player is not found")

    def open_omxplayer(self, link):
        Popen(["lxterminal", "-e",
	       "omxplayer", "-b", "--live",
		link])

    def open_mpv(self, link):
        Popen(["mpv", link])

class HistoryItem:
    def __init__(self, title, store, refreshLink, next_link, results_position):
        self.title = title
        self.store = store
        self.refreshLink = refreshLink
        self.next_link = next_link
        self.results_position = results_position
                    
def main():
    gobject.threads_init()
    gtk.main()

if __name__ == "__main__":
    gui = OnlineLifeGui()
    main()
