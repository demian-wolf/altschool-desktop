#!/usr/bin/env python3

import tkinter as tk
import tkinter.ttk as ttk

import time
import datetime
import random
import collections
import base64

import requests
from bs4 import BeautifulSoup
from jinja2 import Template
import htmlmin
import magic

from JournalAPI import JournalAPI


HELP_TEXT = """Ця програма збирає всі конспекти (\"Головне в уроці\") з усіх доступних уроків.
Зверніть увагу, що:
    1) буде відкрито (ще) одне вікно браузера.
    2) цей процес може зайняти досить багато часу в залежності від кількості уроків (чим ближче до кінця навчального року - тим більше) і від вашого Інтернет-з'єднання."""

class OrderedDefaultdict(collections.OrderedDict):
    """ A defaultdict with OrderedDict as its base class.
        Source: https://stackoverflow.com/a/4127426/8661764
    """

    def __init__(self, default_factory=None, *args, **kwargs):
        if not (default_factory is None or callable(default_factory)):
            raise TypeError('first argument must be callable or None')
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory  # called by __missing__()

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key,)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):  # Optional, for pickle support.
        args = (self.default_factory,) if self.default_factory else tuple()
        return self.__class__, args, None, None, iter(self.items())

    def __repr__(self):  # Optional.
        return '%s(%r, %r)' % (self.__class__.__name__, self.default_factory, self.items())


class Main(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Експорт конспектів уроків - "Альтернатива" ПК-Клієнт')
        self.resizable(False, False)

        tk.Label(self, text=HELP_TEXT, anchor="w", justify="left", wraplength=750).pack()

        credentials_frame = tk.Frame(self)
        credentials_frame.pack()

        login_frame = tk.Frame(credentials_frame)

        uid_frame = tk.Frame(credentials_frame)
        tk.Label(uid_frame, text="UID:").pack(side="left")
        self.uid_entry = tk.Entry(uid_frame, bg="white")
        self.uid_entry.insert(0, "1269")
        self.uid_entry.pack(side="left")
        uid_frame.pack(anchor="e")

        lang_frame = tk.Frame(credentials_frame)
        tk.Label(lang_frame, text="Мова:").pack(side="left")
        self.lang_cbox = ttk.Combobox(lang_frame, value=("UA", "RU"), width=3)
        self.lang_cbox.set("UA")
        self.lang_cbox.pack(side="left")
        lang_frame.pack(anchor="e")

        self.save_external_var = tk.BooleanVar(self)
        self.save_external_cbtn = tk.Checkbutton(credentials_frame, text="Експортувати зображення", variable=self.save_external_var)
        self.save_external_cbtn.pack(anchor="e")
        
        self.progressbar = ttk.Progressbar(self, mode="determinate")
        self.progressbar.pack(fill="both")

        self.status_label = tk.Label(self, text="", wraplength=750)
        self.status_label.pack()
        
        self.fetch_button = ttk.Button(self, text="Почати!", command=self.fetch)
        self.fetch_button.pack()

        self.safe_mode = False

    def set_task(self, task):
        self.status_label.configure(text=task)
        self.update()
        if self.safe_mode:
            time.sleep(random.uniform(1, 5))

    def _fix_link(self, link):
        save_external = self.save_external_var.get()
        if link.startswith("/"):
            link = "https://online-shkola.com.ua/{}".format(link)
        if save_external:
            content = requests.get(link, verify=False).content
            mimetype = magic.Magic(mime=True).from_buffer(content)
            return "data:{};base64,{}".format(mimetype, base64.b64encode(content).decode("utf-8"))
        return link
        
    def fetch(self):
        def _change_widgets_state(state):
            for widget in (self.fetch_button, self.uid_entry, self.lang_cbox, self.save_external_cbtn):
                widget.configure(state=state)

        _change_widgets_state("disabled")

        uid, lang = int(self.uid_entry.get()), self.lang_cbox.get().lower()

        self.set_task("Підготовка...")

        queue = OrderedDefaultdict(lambda: [])
        queue_length = 0
        japi = JournalAPI(uid, lang)
        for subject in japi.subjects:
            for topic in japi.get_subject(subject):
                for lesson in topic.lessons:
                    queue[subject].append(lesson)
                    queue_length += 1
        self.progressbar.configure(maximum=queue_length)
        
        self.summaries = OrderedDefaultdict(lambda: [])

        step = 0
        for subject in queue:
            for lesson in queue[subject]:
                self.set_task("Збираються дані з уроку з id={} ({!r}: {!r})...".format(lesson.id, subject.title, lesson.title))
                date = ".".join(lesson.date.split()[0].split("-")[::-1])
                soup = BeautifulSoup(requests.post("https://online-shkola.com.ua/lessons/watch.php?id={}".format(lesson.id), cookies={"lang": lang}, verify=False).history[0].content, features="lxml")
                summary = soup.find("div", class_="lesson-content-text", id="content-1")
                for a in summary.findAll("a", href=True):
                    a["href"] = self._fix_link(a["href"])
                for img in summary.findAll("img"):
                    img["src"] = self._fix_link(img["src"])

                result = str(soup)
                self.summaries[subject].append((date, str(summary)))
                step += 1
                self.progressbar.configure(value=step)

        self.set_task("Фінальна обробка даних...")

        with open("summaries_template.html") as template_fp:
            template = Template(template_fp.read())
            with open("summaries.html", "w") as output_fp:
                output_fp.write(htmlmin.minify(template.render(lang=lang, subjects=japi.subjects, summaries=self.summaries, creation_date=datetime.datetime.today().strftime("%d.%m.%Y %H:%M:%S"))))

        self.set_task("")
        
        _change_widgets_state("normal")

if __name__ == "__main__":
    r = Main()
    r.mainloop()
