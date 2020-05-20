import tkinter as tk
import tkinter.ttk as ttk
import tempfile
import hashlib
import zipfile
import shutil
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

def get_dict_difference(dict1, dict2):
    return set(dict1.items()) ^ set(dict2.items())


class Updater(tk.Tk):
    def __init__(self):
        super().__init__()

        self.cwd_checksums, self.upd_checksums = {}, {}

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

    def check_for_updates(self):
        self.tempdir_descriptor = tempfile.TemporaryDirectory()
        tmp_path = self.tempdir_descriptor.name

        zipfile.ZipFile(io.BytesIO(requests.get(PATH_TO_LATEST_ARCHIVE).content)).extractall(tmp_path)

        for cwd_fname in list_dir(CWD):
            self.cwd_checksums[cwd_fname] = md5(cwd_fname)

        self.upd_path = os.path.join(tmp_path, APP_NAME + "-master")
        for upd_fname in list_dir(self.upd_path):
            self.upd_checksums[upd_fname] = md5(os.path.join(self.upd_path, upd_fname))

        print(CWD, self.upd_path)
        print(self.cwd_checksums, self.upd_checksums, sep="\n")
        return self.cwd_checksums != self.upd_checksums

    def update_app(self):
        self.update_btn["state"] = "disabled"
        self.update()
        seen = []
        for fname, _ in get_dict_difference(self.cwd_checksums, self.upd_checksums):
            if fname in seen:
                continue
            seen.append(fname)

            # TODO: remove not only unnecessary files from previous version but directories, too
            if fname in self.cwd_checksums and fname not in self.upd_checksums:  # if the file doesn't exist in new update
                os.remove(fname)
                continue

            ppath = os.path.dirname(fname)
            if ppath:
                os.makedirs(ppath, exist_ok=True)

            shutil.copy(os.path.join(self.upd_path, fname), CWD)

        self.tempdir_descriptor.cleanup()

        self.update_btn["state"] = "normal"
        self.update()


if __name__ == "__main__":
    Updater().mainloop()
