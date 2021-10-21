#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import argparse
import sys,os
import curses
import time
import redis
import pickle

def draw_menu(stdscr,streamName):
    r = redis.Redis(host='localhost', port=6379)
    k = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    w = []
    height, width = stdscr.getmaxyx()
    for i in range(height - 1):
        w.append(stdscr.subwin(1, width, i, 0))
    statusbar = stdscr.subwin(1,width,height-1,0)

    k = 0
    while (True):
        height, width = stdscr.getmaxyx()

        statusbarstr = "{} | STATUS BAR | REDIS | H:{} | W:{} | {}".format(streamName, height, width, k)

        # Render status bar
        statusbar.attron(curses.color_pair(3))
        statusbar.addstr(0, 0, statusbarstr)
        statusbar.addstr(0, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        statusbar.attroff(curses.color_pair(3))
        statusbar.refresh()
        
        #render help message
        stdscr.addstr(height-2,0,"usage: d_z4 - which will send pdata with support for subwindows")
        if "read_samples" in locals():
            out = read_samples[0]
            msgbody = out[1]
            timestamp = out[1][0][0]
            msgfields = out[1][0][1]
            pdata = msgfields['pdata'.encode()]
            pdata = pickle.loads(pdata)
            for field in pdata:
                i = field['row']
                i = i % 4
                w[field['row']].clear()
                s = field['text']
                w[field['row']].addstr(0,0,field['text'],curses.color_pair(i+1)) 
                w[field['row']].addstr(0,len(s)," " * (width - len(s) - 1),curses.color_pair(i+1))
                w[field['row']].refresh()
        
        # Wait for next input
        if k == 0:
            read_samples = r.xread({streamName:'$'},None,0)
        else:
            read_samples = r.xread({streamName:timestamp},None,0)
            
        k = (k + 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--streamName", help="name of the stream associated with this UX (default=stmxZeta)", default="stmxZeta")
    args, unknown = parser.parse_known_args()
    curses.wrapper(draw_menu, args.streamName)
    
if __name__ == "__main__":
    main()

