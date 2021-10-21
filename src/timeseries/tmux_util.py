
from os import system
import libtmux

def tmux(command):
    system('tmux %s' % command)

def tmux_shell(command):
    tmux('send-keys %s C-b' % command)

# Start up the terminal 
def open_pane(window_name,env,command):
    server=libtmux.Server()
    session=server.find_where({"session_name":"timeseries"})
    session.new_window(attach=False,window_name=window_name)
    window=session.attached_window
    pane=window.split_window()
    pane.select_pane()
    pane.send_keys('conda activate ' + env)
    pane.send_keys(command)
    

def kill(window_name):
    session.kill_window(window_name)
