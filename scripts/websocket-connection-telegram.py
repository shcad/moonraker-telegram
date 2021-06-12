import websocket
import json
import os
import sys
try:
    import thread
except ImportError:
    import _thread as thread
import time

port1 = sys.argv[1]
DIR1 = sys.argv[2]
prog_message1 = sys.argv[3]
prog_message1 = float(prog_message1)
z_message1 = sys.argv[4]
z_message1 = float(z_message1)

prog_message = 0
printer = 0
z_message = 0
progress_z = 0
data = ""


def subscribe():
    global data
    data = {
        "jsonrpc": "2.0",
        "method": "printer.objects.subscribe",
        "params": {
            "objects": {
                "print_stats": ["state"],
                "display_status": ["progress"],
                "gcode_move": ["gcode_position"],
            }
        },
        "id": "5434"
    }


def on_message(ws, message):
    global prog_message
    global printer
    global z_message
    global progress_z
    if "telegram:" in message:
        print(message)
        a, telegram = message.split("telegram: ")
        telegram_msg, b = telegram.split('"')
        os.system(f'sh {DIR1}/scripts/telegram.sh "{telegram_msg}" "0"')
    elif "telegram_picture:" in message:
        print(message)
        a, telegram = message.split("telegram_picture: ")
        telegram_msg, b = telegram.split('"')
        os.system(f'sh {DIR1}/scripts/telegram.sh "{telegram_msg}" "1"')
    elif "Klipper state: Ready" in message:
        subscribe()
        ws.send(json.dumps(data))
    elif "print_stats" in message:
        if "state" in message:
            print(message)
            f = open(f'{DIR1}/websocket_state.txt', 'w')
            f.write(message)
            f.close()
            os.system(f'sh {DIR1}/scripts/read_state.sh "0"')
        if "printing" in message:
            if printer == 0:
                prog_message = prog_message1
                z_message = z_message1
                printer = 1
                progress_z = 0
        if "complete" in message or "standby" in message or "error" in message:
            printer = 0
            prog_message = 0
            z_message = 0
            progress_z = 0
    elif "Klipper state: Shutdown" in message:
        os.system(f'sh {DIR1}/scripts/read_state.sh "1"')
    elif "params" in message:
        if "progress" in message and printer == 1:
            python_json_obj = json.loads(message)
            json_prog1 = python_json_obj["params"][0]["display_status"]["progress"]
            json_prog = json_prog1*100
            progress_z = json_prog
            if json_prog >= float(prog_message) and int(prog_message1) != 0:
                prog_message = prog_message + prog_message1
                os.system(f'sh {DIR}/scripts/telegram.sh 5')
        if "gcode_position" in message and printer == 1 and progress_z > float(0):
            python_json_obj = json.loads(message)
            json_gcode = float(
                python_json_obj["params"][0]["gcode_move"]["gcode_position"][2])
            if json_gcode >= float(z_message) and int(z_message1) != 0:
                z_message = z_message + z_message1
                os.system(f'sh {DIR}/scripts/telegram.sh 5')


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")
    print("Retry : %s" % time.ctime())
    time.sleep(10)
    connect_websocket()  # retry per 10 seconds


def on_open(ws):
    def run(*args):
        for i in range(1):
            start = 1
            time.sleep(1)
            subscribe()
            ws.send(json.dumps(data))
        time.sleep(5)
        start = 0
    thread.start_new_thread(run, ())


def connect_websocket():
    #    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(f'ws://127.0.0.1:{port1}/websocket',
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()


if __name__ == "__main__":
    connect_websocket()
