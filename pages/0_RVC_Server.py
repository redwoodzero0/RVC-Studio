import subprocess
from time import sleep
import psutil

from webui import MENU_ITEMS, SERVERS, ObjectNamespace, get_cwd
import streamlit as st
st.set_page_config(layout="wide",menu_items=MENU_ITEMS)

from webui.utils import pid_is_active, poll_url
from webui.components import active_subprocess_list, st_iframe
from webui.contexts import ProgressBarContext, SessionStateContext

CWD = get_cwd()

def stop_server(pid):
    if pid_is_active(pid):
        process = psutil.Process(pid)
        if process.is_running(): process.kill()

def start_server(host,port):
    pid = SERVERS["RVC"].get("pid")
    if pid_is_active(pid):
        process = psutil.Process(pid)
        if process.is_running(): return SERVERS["RVC"]["url"]
    
    base_url = f"http://{host}:{port}"
    cmd = f"python api.py --port={port} --host={host}"
    p = subprocess.Popen(cmd, cwd=CWD)

    if poll_url(base_url):
        SERVERS["RVC"] = {
            "url": base_url,
            "pid": p.pid
        }
    
    return base_url

def initial_state():
    return ObjectNamespace(
        remote_bind=False,
        host="localhost",
        port=5555
    )

if __name__=="__main__":
    with SessionStateContext("rvc-api",initial_state()) as state:
        pid = SERVERS["RVC"].get("pid")
        is_active = pid_is_active(pid)

        with st.form("rvc-api-form"):
            state.remote_bind = st.checkbox("Bind to 0.0.0.0 (Required for docker or remote connections)", value=state.remote_bind)
            state.host = "0.0.0.0" if state.remote_bind else "localhost"
            state.port = st.number_input("Port", value=state.port or 5555)
            state.url = st.text_input("Server URL", value = f"http://{state.host}:{state.port}")

            if st.form_submit_button("Start Server",disabled=is_active):
                with ProgressBarContext([1]*5,sleep,"Waiting for rvc api to load") as pb:
                    start_server(host=state.host,port=state.port)
                    pb.run()
                    st.experimental_rerun()
                
        active_subprocess_list()
        
        if is_active:
            if st.button("Stop Server",type="primary"):
                stop_server(pid)
                st.experimental_rerun()

            st_iframe(url=f'{SERVERS["RVC"]["url"]}/docs',height=800)