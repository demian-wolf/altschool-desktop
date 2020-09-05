import requests
import warnings
from collections import namedtuple


HEADERS = {
    'Host': 'online-shkola.com.ua',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:68.9) Gecko/20100101 Goanna/4.4 Firefox/68.9 Mypal/28.8.0',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.5',
    'origin': 'https://online-shkola.com.ua',
    'Referer': 'https://online-shkola.com.ua/thematic/',
    'Connection': 'keep-alive',
}

Subject = namedtuple("Subject", ("id", "title"))
Topic = namedtuple("Topic", ("id", "title", "lessons", "thematic_mark"))
Lesson = namedtuple("Lesson", ("id", "title", "date", "marks", "special_signs"))
Mark = namedtuple("Mark", ("state", "value"))
SpecialSign = namedtuple("SpecialSign", ("db_name", "pretty_name"))
SubjectMetadata = namedtuple("SubjectMetadata", ("start_learning_date", "semester_mark", "lessons_visited_pct", "tests_hw_done_pct", "creative_hw_done_pct"))

UNSENT, ABSENT, UNCHECKED = Mark("unsent", None), Mark("absent", None), Mark("unchecked", None)

SPECIAL_SIGNS = ["isHQ",
                 "isControl",
                 "isVerbal",
                 "isSickLeave",
                 "isVisited",
                 ]


class JournalAPI:
    def __init__(self, uid, language, headers=HEADERS):
        
        self.uid = uid
        self.language = language
        
        self.subjects = []
        for subject in requests.get('https://online-shkola.com.ua/api/v2/users/1269/thematic/subjects',
                                    headers=headers,
                                    cookies={"lang": language.lower()},
                                    verify=False).json()["subjects"]:
            self.subjects.append(Subject(subject["id"], subject["name"]))

    def get_subject(self, subject):
        if isinstance(subject, Subject):
            subject = subject.id
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            json_data = requests.get("https://online-shkola.com.ua/api/v2/users/%s/thematic/subject/%s" % (self.uid, subject),
                                        headers=HEADERS, cookies={"lang": self.language.lower()}, verify=False).json()

        topics = []
        for topic in json_data["themes"]:
            lessons = []
            for lesson in topic["lessons"]:
                isHw = lesson["hw"]["isHw"]
                isTest = "testId" in lesson
                isTrainingTest = "trainingTestId" in lesson
                testId = lesson["testId"] if isTest else 0
                trainingTestId = lesson["trainingTestId"] if isTrainingTest else 0
                lessonId = lesson["id"]
                
                if isTrainingTest:
                    training_test_mark = Mark("ready", lesson["trainingTestMark"]) if lesson["trainingTestMark"] else UNSENT  # TODO: how to determine if it is sent and 0, or it is not sent
                else:
                    training_test_mark = ABSENT
                hw_mark = UNSENT
                test_mark = UNSENT
                result_mark = UNSENT
                if isHw:
                    if lesson["hw"]["status"] == 4:
                        result_mark = hw_mark = Mark("ready", lesson["hw"]["mark"])
                    elif lesson["hw"]["status"] == 2:
                        result_mark = hw_mark = UNCHECKED
                else:
                    hw_mark = ABSENT
                if isTest:
                    if lesson["isCompleted"]:
                        result_mark = test_mark = Mark("ready", lesson["testMark"])
                else:
                    test_mark = ABSENT
                if hw_mark == test_mark == ABSENT:
                    result_mark = ABSENT
                if (hw_mark not in [ABSENT, UNSENT]) and (test_mark not in [ABSENT, UNSENT]):
                    result_mark = Mark("ready", hw_mark + test_mark)

                special_signs = [special_sign for special_sign in SPECIAL_SIGNS if lesson[special_sign]]
                
                lessons.append(Lesson(lesson["id"], lesson["title"], lesson["date"], [result_mark, training_test_mark, test_mark, hw_mark], special_signs))

            marks_list = []
            control_mark = None  # for the case if the control work is not done/checked yet
            for lesson in lessons:
                result_mark = lesson.marks[0]
                if (result_mark not in (UNSENT, UNCHECKED, ABSENT)) and ("isSickLeave" not in lesson.special_signs) and ("isVerbal" not in lesson.special_signs):
                    if "isControl" not in lesson.special_signs:
                        marks_list.append(int(result_mark.value))
                    else:
                        control_mark = int(result_mark.value)  # TODO: fix if two control works
            if len(marks_list):
                thematic = sum(marks_list) / len(marks_list)
                if control_mark is not None:  # if the control work is already done
                    thematic = Mark("real", (thematic + control_mark) / 2)
            else:
                thematic = UNSENT if control_mark is None else control_mark
            
            topics.append(Topic(topic["id"], topic["title"], lessons, thematic))
        return topics

    def get_subject_metadata(self, subject):
        if isinstance(subject, Subject):
            subject = subject.id
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            json_data = requests.get("https://online-shkola.com.ua/api/v2/users/%s/thematic/subject/%s" % (self.uid, subject),
                                        headers=HEADERS, cookies={"lang": self.language.lower()}, verify=False).json()

        return SubjectMetadata(json_data["dateStartLearning"], json_data["mark"], json_data["visitedPercentage"], json_data["doneTestsPercentage"], json_data["doneHwPercentage"])

        
if __name__ == "__main__":
    x = JournalAPI(1269, "ru")
    y = JournalAPI(1269, "ua")
