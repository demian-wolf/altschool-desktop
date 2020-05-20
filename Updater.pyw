import tkinter as tk
import tkinter.ttk as ttk
import tempfile
import hashlib
import zipfile
import os
import io

import requests

PATH_TO_LATEST_ARCHIVE = "https://github.com/demian-wolf/Alternativa-PC-Client/archive/master.zip"
CWD = os.getcwd()
APP_NAME = os.path.basename(os.path.normpath(CWD))


def md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def list_dir(path):
    return filter(lambda p: not p.startswith(".git") and not p.startswith(".idea"),
                  (os.path.relpath(os.path.join(dirpath, file), path)
                   for (dirpath, dirnames, filenames) in os.walk(path)
                   for file in filenames))


class Updater(tk.Tk):
    def __init__(self):
        super().__init__()
        self.update_app()
        self.title("\"Альтернатива\" ПК-Клієнт Автооновлювач")
        self.resizable(False, False)
        self.create_wgts()

    def create_wgts(self):
        self.state_label = tk.Label(self, text="Перевірка оновлень...", relief="raised",
                                    bg="yellow", cursor="watch", width=100, height=10)
        self.state_label.pack(fill="both", expand="yes")
        btn_frame = tk.Frame(self)
        self.update_btn = ttk.Button(btn_frame, text="Оновити!", command=self.update_app,
                                     state="disabled")
        self.update_btn.pack(fill="x")
        ttk.Button(btn_frame, text="Вихід", command=self.destroy).pack(fill="x")
        btn_frame.pack(fill="x")

        self.update()
        is_new_update = self.check_for_updates()
        if is_new_update:
            self.state_label["text"] = "❌ Доступні оновлення. Слід оновити програму!"
            self.state_label["bg"] = "red"
            self.update_btn["state"] = "normal"
        else:
            self.state_label["text"] = "✓ Ви використовуєте останню версію програми"
            self.state_label["bg"] = "lightgreen"
        self.state_label["cursor"] = ""

    def update_app(self):
        pass

    def check_for_updates(self):
        self.cwd_checksums, self.upd_checksums = {}, {}
        with tempfile.TemporaryDirectory() as tmp_path:
            zipfile.ZipFile(io.BytesIO(requests.get(PATH_TO_LATEST_ARCHIVE).content)).extractall(tmp_path)

            for cwd_fname in list_dir(CWD):
                self.cwd_checksums[cwd_fname] = md5(cwd_fname)

            upd_path = os.path.join(tmp_path, APP_NAME + "-master")

            for upd_fname in list_dir(upd_path):
                self.upd_checksums[upd_fname] = md5(os.path.join(upd_path, upd_fname))

            print(CWD, os.path.join(tmp_path, APP_NAME + "-master"))
            print(self.cwd_checksums, self.upd_checksums, sep="\n")
            return self.cwd_checksums != self.upd_checksums


if __name__ == "__main__":
    Updater().mainloop()
