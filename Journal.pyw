from tkinter import *
from tkinter.font import *
from tkinter.ttk import *
import requests
import webbrowser

from pprint import pprint


SUBJ_IDS = {
    'Фізика': 3,
    'Біологія': 4,
    'Географія': 6,
    'Хімія': 7,
    'Історія України': 8,
    'Українська мова': 9,
    'Українська література': 10,
    'Англійська мова': 11,
    'Зарубіжна література': 12,
    'Інформатика': 17,
    'Всесвітня Історія': 20,
    'Алгебра': 21,
    'Геометрія': 22
    }

MONTHS2UA = {
    "01": "січ",
    "02": "лют",
    "03": "бер",
    "04": "квіт",
    "05": "трав",
    "09": "вер",
    "10": "жовт",
    "11": "лист",
    "12": "груд"
    }

SPECIAL = {
    "isVisited": "[✔]",
    "isControl": "[К.Р.]",
    "isHQ": "[NEW]",
    "isSickLeave": "[н-]",
    "isVerbal": "[У]"    
    }

REQUEST_HEADERS = {
    'Host': 'online-shkola.com.ua',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:68.9) Gecko/20100101 Goanna/4.4 Firefox/68.9 Mypal/28.8.0',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.5',
    'origin': 'https://online-shkola.com.ua',
    'Referer': 'https://online-shkola.com.ua/thematic/',
    'Connection': 'keep-alive'
}

UID = 1269

class Main(Tk):
    def __init__(self):
        super().__init__()

        self.iconphoto(True, PhotoImage(file="icon.png"))
        self.title('Журнал - "Альтернатива" Клиент для ПК')
        self.state("zoomed")
        self.focus_force()
        
        settings_frame = Frame(self)
        self.subj_var = StringVar(self)
        self.subj_cbox = Combobox(settings_frame, values=list(SUBJ_IDS.keys()), state="readonly", textvariable=self.subj_var)
        self.subj_cbox.current(0)
        self.subj_cbox.pack(side=LEFT)

        self.lang_var = StringVar(self)
        self.lang_cbox = Combobox(settings_frame, values=["RU", "UA"], state="readonly", textvariable=self.lang_var, width=3)
        self.lang_cbox.current(0)
        self.lang_cbox.pack(side=RIGHT)

        self.year_var = StringVar(self)
        self.year_cbox = Combobox(settings_frame, values=["--"], state="readonly", textvariable=self.year_var)
        self.year_cbox.current(0)
        self.year_cbox.pack()
        settings_frame.pack(fill=Y)

        treeview_frame = Frame(self)
        self.treeview = Treeview(treeview_frame, selectmode="browse", columns=["date", "marks", "special"])
        self.treeview.bind("<Double-1>", self.open_lesson_in_webbrowser)
        self.treeview.heading("date", text="Дата")
        self.treeview.heading("marks", text="Оцінки (ТРЕН.ТЕСТ/ТЕСТ.ДЗ/ТВ.ДЗ)")
        self.treeview.heading("special", text="Спец. позначення")
        self.treeview.column("date", width=110, stretch=False, anchor="center")
        self.treeview.column("marks", width=220, stretch=False, anchor="center")
        self.treeview.column("special", width=150, stretch=False, anchor="center")

        self.treeview.tag_configure("topic", font=(None, 12, "bold"))
        self.treeview.tag_configure("lesson", font=(None, 12))
        self.treeview.tag_configure("isControl", background="#dcffd3")
        self.treeview.tag_configure("isVerbal", background="#c0b6fa")
        
        self.treeview.pack(fill=BOTH, expand=YES, side=LEFT)

        self.tscrollbar = Scrollbar(treeview_frame, command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=self.tscrollbar.set)
        self.tscrollbar.pack(fill=Y, side=LEFT)
        treeview_frame.pack(fill=BOTH, expand=YES)

        self.subj_var.trace("w", self.update_info)
        self.lang_var.trace("w", self.update_info)
        self.year_var.trace("w", self.update_info)

        self.create_menus()
        self.update_info()

    def create_menus(self):
        def do_rclick_popup(event):
            try:
                selected_item = self.treeview.identify_row(event.y)
                self.treeview.selection_set(selected_item)
                item_values = self.treeview.item(selected_item)["values"]
                menu_labels = ["Скласти Тренувальний Тест", "Скласти Тестове ДЗ", "Скласти Творче ДЗ"]
                for i in range(2, 5):
                    self.rclick_menu.entryconfig(menu_labels[i - 2], state="normal" if item_values[-i] else "disabled")
                if "lesson" in self.treeview.item(selected_item)["tags"]:
                    self.rclick_menu.post(event.x_root, event.y_root)
            finally:
                self.rclick_menu.grab_release()
                
        self.rclick_menu = Menu(self, tearoff=False)
        self.bold_font = Font(self, self.rclick_menu["font"])
        self.bold_font["weight"] = "bold"
        self.rclick_menu.add_command(label="Відкрити урок у браузері", command=self.open_lesson_in_webbrowser, font=self.bold_font)
        self.rclick_menu.add_separator()
        self.rclick_menu.add_command(label="Скласти Тренувальний Тест", command=self.open_training_test_in_webbrowser)
        self.rclick_menu.add_command(label="Скласти Тестове ДЗ", command=self.open_test_hw_in_webbrowser)
        self.rclick_menu.add_command(label="Скласти Творче ДЗ")
        self.rclick_menu.add_separator()
        self.rclick_menu.add_command(label="Властивості", command=self.view_properties)
        self.treeview.bind("<Button-3>", do_rclick_popup)
        
        
    def update_info(self, *args):
        # TODO: sort the dict keys (it's necessary for older Python versions)
        # TODO: Н/А или 0 - what's the difference
        # TODO: add other functions to look like full journal
        # TODO: show what: tv.dz or test.dz left
        # TODO: add catching errors
        # TODO: add archive years
        
        subject = self.subj_var.get()
        language = self.lang_var.get()
        journal_data = requests.get("https://online-shkola.com.ua/api/v2/users/%s/thematic/subject/%s" % (UID, SUBJ_IDS[subject]), headers=REQUEST_HEADERS, cookies={"lang": language.lower()}).json()["themes"]
        #journal_data = requests.get("https://online-shkola.com.ua/api/v2/users/%s/thematic/archive/2/subject/%s" % (UID, SUBJ_IDS[subject]), headers=REQUEST_HEADERS, cookies={"lang": language.lower()}).json()["themes"]
    
        """for topic in sorted(journal_data):
            topic_data = journal_data[topic]
            for subtopic in sorted(topic_data.keys()):
                print(topic, subtopic)"""
        
        #pprint(journal_data)
        self.treeview.delete(*self.treeview.get_children())
        
        for topic in journal_data:
            topic_tw_item = self.treeview.insert("", END, text=topic["title"], tag="topic")
            self.treeview.item(topic_tw_item, open=True)
            for subtopic in topic["lessons"]:
                tags = ["lesson"]
                if subtopic["testMark"] and subtopic["hw"]["mark"]:
                    result_mark = (subtopic["testMark"] + subtopic["hw"]["mark"]) / 2  # is this the real mark??? or there's another alghoritm of calculating of it?
                elif subtopic["testMark"]:
                    result_mark = subtopic["testMark"]
                elif subtopic["hw"]["mark"]:
                    result_mark = subtopic["hw"]["mark"]
                else:
                    result_mark = "Н/А"
                mark = "%s (%s/%s/%s)" % (result_mark, subtopic["trainingTestMark"], subtopic["testMark"], subtopic["hw"]["mark"])
                date = subtopic["date"].split()[0].split("-")
                date = " ".join((str(int(date[2])), MONTHS2UA[date[1]], date[0]))
                special = ""
                for smark in SPECIAL:
                    if subtopic[smark]:
                        special += SPECIAL[smark] + " "
                        tags.append(smark)
                isHw = int(subtopic["hw"]["isHw"])
                testId = 0 if "testId" not in subtopic else subtopic["testId"]
                trainingTestId = 0 if "trainingTestId" not in subtopic else subtopic["trainingTestId"]
                lessonId = subtopic["id"]
                x = self.treeview.insert(topic_tw_item, END, text=subtopic["title"], values=(date, mark, special, isHw, testId, trainingTestId, lessonId), tags=tags)

    def open_lesson_in_webbrowser(self, event=None):
        item_info = self.treeview.item(self.treeview.selection()[0])
        if "lesson" in item_info["tags"]:
            webbrowser.open("https://online-shkola.com.ua/lessons/watch.php?id=%s" % item_info["values"][-1])

    def open_training_test_in_webbrowser(self, event=None):
        webbrowser.open("https://online-shkola.com.ua/tests/completing.php?id=%s" % self.treeview.item(self.treeview.selection()[0])["values"][-2])

    def open_test_hw_in_webbrowser(self, event=None):
        webbrowser.open("https://online-shkola.com.ua/tests/completing.php?id=%s" % self.treeview.item(self.treeview.selection()[0])["values"][-3])

    def view_properties(self, event=None):
        pass
    
if __name__ == "__main__":
    Main().mainloop()
