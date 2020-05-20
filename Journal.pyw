from tkinter import *
from tkinter.font import *
from tkinter.ttk import *
from collections import OrderedDict
import datetime
import requests
import webbrowser


SUBJ_IDS = OrderedDict([
    ('Фізика', 3),
    ('Біологія', 4),
    ('Географія', 6),
    ('Хімія', 7),
    ('Історія України', 8),
    ('Українська мова', 9),
    ('Українська література', 10),
    ('Англійська мова', 11),
    ('Зарубіжна література', 12),
    ('Інформатика', 17),
    ('Всесвітня Історія', 20),
    ('Алгебра', 21),
    ('Геометрія', 22)])

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

UNSENT, UNCHECKED, ABSENT = "☒", "⚖", "—"


class Main(Tk):
    def __init__(self):
        super().__init__()

        # withdraw and deiconify are used to make window opening slighter
        self.withdraw()
        self.iconphoto(True, PhotoImage(file="app_icon.png"))
        self.title('Журнал - "Альтернатива" ПК-Клієнт')
        self.state("zoomed")
        self.focus_force()

        self.create_wgts()
        self.create_menus()

        self.update_info(first_time=True)
        self.deiconify()

    def create_wgts(self):
        panel_frame = Frame(self)
        leftpanel_frame = Frame(panel_frame)
        self.subj_var = StringVar(self)
        self.subj_cbox = Combobox(leftpanel_frame, values=list(SUBJ_IDS.keys()), state="readonly",
                                  textvariable=self.subj_var)
        self.subj_cbox.current(0)
        self.subj_cbox.pack(side=LEFT)

        self.lang_var = StringVar(self)
        self.lang_cbox = Combobox(leftpanel_frame, values=["RU", "UA"], state="readonly", textvariable=self.lang_var,
                                  width=3)
        self.lang_cbox.current(0)
        self.lang_cbox.pack(side=LEFT)

        self.update_button = Button(leftpanel_frame, text="Оновити ⭮", command=self.update_info)
        self.update_button.pack(side=LEFT)

        self.show_base_info_var = BooleanVar(self, False)
        Checkbutton(leftpanel_frame, text="Відображати базову інформацію", variable=self.show_base_info_var).pack(
            side=LEFT)
        leftpanel_frame.pack(side=LEFT)

        rightpanel_frame = Frame(panel_frame)
        Button(leftpanel_frame, text="Увійти до аккаунту", command=self.login).pack(side=LEFT)
        Button(rightpanel_frame, text="Інші налаштування ⚙", command=self.advanced_settings).pack(side=LEFT)
        Button(rightpanel_frame, text="Допомога ❓", command=self.help).pack(side=LEFT)
        rightpanel_frame.pack(side=RIGHT)
        panel_frame.pack(fill=X)

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
        self.treeview.tag_configure("todayLesson", font=Font(size=12, underline=True))
        self.treeview.tag_configure("thematic_mark", font=(None, 12, "italic"))
        self.treeview.tag_configure("base_info", font=(None, 12))

        self.treeview.pack(fill=BOTH, expand=YES, side=LEFT)

        self.tscrollbar = Scrollbar(treeview_frame, command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=self.tscrollbar.set)
        self.tscrollbar.pack(fill=Y, side=LEFT)
        treeview_frame.pack(fill=BOTH, expand=YES)

        self.subj_var.trace("w", self.update_info)
        self.lang_var.trace("w", self.update_info)
        self.show_base_info_var.trace("w", self.update_info)

    def create_menus(self):
        def do_rclick_popup(event):
            try:
                selected_item = self.treeview.identify_row(event.y)
                self.treeview.selection_set(selected_item)
                item_values = self.treeview.item(selected_item)["values"]
                item_tags = self.treeview.item(selected_item)["tags"]
                if "lesson" in item_tags or "todayLesson" in item_tags:
                    menu_labels = ["Скласти Тренувальний Тест", "Скласти Тестове ДЗ", "Скласти Творче ДЗ"]
                    for i in range(2, 5):
                        self.rclick_menu.entryconfig(menu_labels[i - 2], state="normal" if item_values[-i] else "disabled")
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
        self.rclick_menu.add_command(label="Скласти Творче ДЗ", command=self.open_hw_in_webbrowser)
        self.rclick_menu.add_separator()
        self.rclick_menu.add_command(label="Властивості", command=self.view_properties)
        self.treeview.bind("<Button-3>", do_rclick_popup)

    def update_info(self, *args, first_time=False):
        # TODO: add catching errors
        # TODO: add archived years
        # TODO: add properties
        # TODO: do something only when something is selected in Treeview, not just double-clicked on the free space

        self.update_button.config(state="disabled")
        if not first_time:
            self.update_idletasks()
        
        subject = self.subj_var.get()
        language = self.lang_var.get()
        journal_data = requests.get("https://online-shkola.com.ua/api/v2/users/%s/thematic/subject/%s" % (UID, SUBJ_IDS[subject]),
                                   headers=REQUEST_HEADERS, cookies={"lang": language.lower()}).json()
        
        self.treeview.delete(*self.treeview.get_children())

        if self.show_base_info_var.get():
            base_info_tv_item = self.treeview.insert("", END, text="Базова Інформація", tag="topic")
            start_learning_date = journal_data["dateStartLearning"].split("-")

            self.treeview.insert(base_info_tv_item, END, text="Дата зарахування до школи:", values=(" ".join((str(int(start_learning_date[2])), MONTHS2UA[start_learning_date[1]], start_learning_date[0])),),
                                 tag="base_info")
            self.treeview.insert(base_info_tv_item, END, text="Семестрова оцінка з даного предмету:", values=(str(journal_data["mark"]) + " балів",), tag="base_info")
            self.treeview.insert(base_info_tv_item, END, text="Відкрито уроків:", values=(str(journal_data["visitedPercentage"]) + " %",), tag="base_info")
            self.treeview.insert(base_info_tv_item, END, text="Виконано Тестових ДЗ:", values=(str(journal_data["doneTestsPercentage"]) + " %",), tag="base_info")
            self.treeview.insert(base_info_tv_item, END, text="Виконано Творчих ДЗ:", values=(str(journal_data["doneHwPercentage"]) + " %",), tag="base_info")

            self.treeview.insert("", END)
            
        for topic in journal_data["themes"]:
            topic_item = self.treeview.insert("", END, text=topic["title"], tag="topic")
            self.treeview.item(topic_item, open=True)
            for lesson in topic["lessons"]:
                tags = ["lesson"]
                
                isHw = int(lesson["hw"]["isHw"])
                isTest = "testId" in lesson
                isTrainingTest = "trainingTestId" in lesson
                testId = lesson["testId"] if isTest else 0
                trainingTestId = lesson["trainingTestId"] if isTrainingTest else 0
                lessonId = lesson["id"]

                # Get and process the marks
                if isTrainingTest:
                    training_test_mark = lesson["trainingTestMark"] if lesson["trainingTestMark"] else UNSENT  # TODO: how to determine if it is sent and 0, or it is not sent
                else:
                    training_test_mark = ABSENT
                hw_mark = UNSENT
                test_mark = UNSENT
                result_mark = UNSENT
                if isHw:
                    if lesson["hw"]["status"] == 4:
                        result_mark = hw_mark = lesson["hw"]["mark"]
                    elif lesson["hw"]["status"] == 2:
                        result_mark = hw_mark = UNCHECKED
                else:
                    hw_mark = ABSENT
                if isTest:
                    if lesson["isCompleted"]:
                        result_mark = test_mark = lesson["testMark"]
                else:
                    test_mark = ABSENT
                if hw_mark == test_mark == ABSENT:
                    result_mark = ABSENT
                if (hw_mark not in [ABSENT, UNSENT]) and (test_mark not in [ABSENT, UNSENT]):
                    result_mark = hw_mark + test_mark
                mark = "%s (%s/%s/%s)" % (result_mark, training_test_mark, test_mark, hw_mark)

                # Get and process the date
                date = lesson["date"].split()[0].split("-")
                if datetime.date(*map(int, date)) == datetime.date.today():
                    tags.remove("lesson")
                    tags.append("todayLesson")
                date = " ".join((date[2], MONTHS2UA[date[1]], date[0]))

                # Get and process the special marks
                special = ""
                for smark in SPECIAL:
                    if lesson[smark]:
                        special += SPECIAL[smark] + " "
                        tags.append(smark)
                
                self.treeview.insert(topic_item, END, text=lesson["title"], values=(date, mark, special, isHw, testId, trainingTestId, lessonId), tags=tags)

            # Count the thematic mark
            marks_list = []
            control_mark = -1  # for the case if the control work is not done/checked yet
            for item in self.treeview.get_children(topic_item):
                result_mark = self.treeview.item(item, "values")[1].split()[0]
                if (result_mark not in (UNSENT, UNCHECKED, ABSENT))\
                        and (SPECIAL["isSickLeave"] not in self.treeview.item(item))\
                        and (SPECIAL["isVerbal"] not in self.treeview.item(item)):
                    if SPECIAL["isControl"] not in self.treeview.item(item)["values"][2]:
                        marks_list.append(int(result_mark))
                    else:
                        control_mark = int(result_mark)
            if len(marks_list):
                thematic = sum(marks_list) / len(marks_list)
                if control_mark != -1:  # if the control work is already done
                    thematic = (thematic + control_mark) / 2
                thematic = "%.f" % thematic
            else:
                thematic = UNSENT if control_mark == -1 else control_mark
            self.treeview.insert(topic_item, END, values=("", "Тематична: %s" % thematic), tag="thematic_mark")
        self.update_button.config(state="normal")

    def open_lesson_in_webbrowser(self, event=None):
        item_info = self.treeview.item(self.treeview.selection()[0])
        if "lesson" in item_info["tags"] or "todayLesson" in item_info["tags"]:
            webbrowser.open("https://online-shkola.com.ua/lessons/watch.php?id=%s" % item_info["values"][-1])

    def open_training_test_in_webbrowser(self, event=None):
        webbrowser.open("https://online-shkola.com.ua/tests/completing.php?id=%s" % self.treeview.item(self.treeview.selection()[0])["values"][-2])

    def open_test_hw_in_webbrowser(self, event=None):
        webbrowser.open("https://online-shkola.com.ua/tests/completing.php?id=%s" % self.treeview.item(self.treeview.selection()[0])["values"][-3])

    def open_hw_in_webbrowser(self, event=None):
        webbrowser.open("https://online-shkola.com.ua/lessons/watch.php?id=%s#lesson-content-homework" % self.treeview.item(self.treeview.selection()[0])["values"][-1])

    def view_properties(self, event=None):
        pass

    def login(self, event=None):
        webbrowser.open("https://online-shkola.com.ua/")

    def advanced_settings(self, event=None):
        pass

    def help(self, event=None):
        pass


class AdvancedSettings(Toplevel):
    def __init__(self):
        super().__init__()


class Help(Toplevel):
    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    Main().mainloop()
