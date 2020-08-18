import datetime
import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Tuple

import src.docs.create_doc as create_doc
import src.main.common_funcs as comm_funcs
import src.main.constants as consts


# def init_from_xlsx(f_name: Path,
#                    out: Path = 'tmp',
#                    date=None):
#     """ Преобразовать xlsx файл в список объектов класса Word,
#         вывести их в файл с дополнением старого содержимого
#     """
#     # TODO: Редактировать после перехода к db
#     assert f_name.exists(), \
#         f"File: '{f_name}' does not exist, func – init_from_xlsx"
#
#     if not out.exists():
#         with out.open('w'):
#             pass
#
#     if date is None:
#         date = datetime.date.today()
#     else:
#         date = comm_funcs.str_to_date(date).strftime(const.DATEFORMAT)
#
#     assert f"[{date}]\n" not in out.open('r', encoding='utf-8').readlines(), \
#         f"Date '{date}' currently exists in the '{out}' file, func – init_from_xlsx"
#
#     rb = open_workbook(str(f_name))
#     sheet = rb.sheet_by_index(0)
#
#     # удаляется заглавие, введение и прочие некорректные данные
#     content = list(filter(lambda x: len(x[0]) and (len(x[2]) or len(x[3])),
#                           [sheet.row_values(i) for i in range(sheet.nrows)]))
#     content.sort(key=lambda x: x[0])
#
#     # группировка одинаковых слов вместе
#     content = itertools.groupby(
#         map(lambda x: Word(x[0], x[2], x[3]), content),
#         key=lambda x: (x._word, x.properties)
#     )
#
#     # суммирование одинаковых слов в один объект класса Word
#     result = [
#         functools.reduce(lambda res, elem: res + elem, list(group[1]), Word(''))
#         for group in content
#     ]
#
#     with out.open('a', encoding='utf-8') as f:
#         f.write(f"\n\n[{date}]\n")
#         f.write('\n'.join(map(str, result)))
#         f.write(f"\n[/{date}]\n")


class Word:
    __slots__ = (
        '_word', '_id', '_properties',
        '_english_defs', '_russian_defs', '_date')

    def __init__(self,
                 word: str = '',
                 date: datetime.date or str = None,
                 properties: set or str = None,
                 english: List[str] = None,
                 russian: List[str] = None) -> None:
        """
        :param word: str, word to learn.
        :param properties: set or str, language level, formal, ancient etc.
        :param date: datetime.date, in the date word has been learned.
        :param english: list of str, English definitions of the word.
        :param russian: list of str, Russian definitions of the word.
        """
        self._word = comm_funcs.fmt_str(word)
        self._id = comm_funcs.word_id(self._word)

        english = english or []
        russian = russian or []
        self._english_defs = (
            english.split('; ') if isinstance(english, str) else english)
        self._russian_defs = (
            russian.split('; ') if isinstance(russian, str) else russian)

        self._date = (comm_funcs.str_to_date(date) or
                      datetime.datetime.now().date())

        properties = properties or set()
        if isinstance(properties, str):
            # properties here like '[p1, ...]'
            properties = properties[1:-1].split(', ')

        properties = set(
            comm_funcs.fmt_str(prop)
            for prop in properties
            if prop
        )
        self._properties = properties

    @property
    def word(self) -> str:
        """
        :return: str, word.
        """
        return self._word

    @property
    def date(self) -> datetime.date:
        """
        :return: datetime.date, in this date word has been learned.
        """
        return self._date

    @property
    def id(self) -> str:
        """
        :return: str, word's id.
        """
        return self._id

    @property
    def english(self) -> List[str]:
        """
        :return: list of str, English defs.
        """
        return self._english_defs

    @property
    def russian(self) -> List[str]:
        """
        :return: list of str, Russian defs.
        """
        return self._russian_defs

    @property
    def properties(self) -> set:
        """
        :return: set, word's properties.
        """
        return self._properties

    def with_english(self) -> str:
        """
        :return: str, word with its English defs joined with '; '.
        """
        defs = '; '.join(self.english)
        word = self.word.capitalize()
        return f"{word} – {defs}"

    def with_russian(self) -> str:
        """
        :return: str, word with its Russian defs joined with '; '.
        """
        defs = '; '.join(self.russian)
        word = self.word.capitalize()
        return f"{word} – {defs}"

    def is_fit(self,
               *properties: str) -> bool:
        """
        :param properties: list of str, properties to check.
        :return: bool, whether the word fit with the all properties.
        """
        return all(
            prop.lower() in self.properties
            for prop in properties
        )

    def __getitem__(self,
                    index: int or slice) -> str:
        """ Get symbol by the index or create str with slice.

        :param index: int or slice.
        :return: result str.
        """
        return self.word[index]

    def __iter__(self) -> iter:
        """
        :return: iter to the word.
        """
        return iter(self.word)

    def __add__(self,
                other: Any) -> Any:
        """ Join defs, properties of two objects.

        :param other: Word to join with self.
        :return: Word obj, joined items.
        :exception TypeError: if wrong type given.
        :exception ValueError: if the word aren't equal.
        """
        if not isinstance(other, Word):
            raise TypeError(f"Operator + between Word and str isn't supported")

        if self.word != other.word and self.word != other.word != '':
            raise ValueError("Operator + demands for the equal words")

        return Word(
            max(self.word, other.word),
            min(self.date, other.date),
            self.properties.union(other.properties),
            other.english + self.english,
            other.russian + self.russian
        )

    def __eq__(self,
               other: Any) -> bool:
        """ ==
        If other is int, comparing len of the word with it.
        If other is Word, comparing the words.

        :param other: int or Word to compare.
        :return: bool, whether word equals to the item.
        :exception TypeError: if wrong type given.
        """
        if isinstance(other, str):
            return self.word == other.strip()
        if isinstance(other, Word):
            return (self.word == other.word and
                    self.properties == other.properties)

        raise TypeError(f"Demanded str or Word, but '{type(other)}' given")

    def __ne__(self,
               other: Any) -> bool:
        """ != """
        return not (self == other)

    def __gt__(self,
               other: Any) -> bool:
        """ > """
        if isinstance(other, str):
            return self.word > other.strip()
        if isinstance(other, Word):
            return self.word > other.word

        raise TypeError(f"Demanded str or Word, but '{type(other)}' given")

    def __lt__(self,
               other: Any) -> bool:
        """ < """
        return self != other and not (self > other)

    def __ge__(self,
               other: Any) -> bool:
        """ >= """
        return self > other or self == other

    def __le__(self,
               other: Any) -> bool:
        """ <= """
        return self < other or self == other

    def __len__(self) -> int:
        """
        :return: int, length of the word.
        """
        return len(self.word)

    def __bool__(self) -> bool:
        """
        :return: bool, whether the word exists (not empty).
        """
        return bool(self.word)

    def __contains__(self,
                     item: str) -> bool:
        """
        :return: bool, whether the defs or the word contains given item.
        """
        item = comm_funcs.fmt_str(item)
        return any(
            item in definition
            for definition in [self.word] + self.english + self.russian
        )

    def __str__(self) -> str:
        """ Str format:
        `word [properties] – English defs; Russian defs.`

        Or without properties.

        :return: str this format.
        """
        word = self.word.capitalize()
        properties = f" [{', '.join(self.properties)}]" * bool(self.properties)
        eng = f"{'; '.join(self.english)}\t" * bool(self.english)
        rus = f"{'; '.join(self.russian)}" * bool(self.russian)

        return f"{word}{properties} – {eng}{rus}"

    def __hash__(self) -> int:
        """
        :return: int, hash the word and the properties.
        """
        return sum(self.word) + hash(self.properties)

    def __repr__(self) -> str:
        """ Str format:
            Word: ...
            Properties: ...
            English: ...
            Russian: ...

        :return: str this format.
        """
        res = f"Word: {self.word}\n" \
              f"Properties: {self.properties}\n" \
              f"English: {self.english}\n" \
              f"Russian: {self.russian}"
        return res


class Vocabulary:
    __slots__ = '_data', 'graphic_name', '_cursor', '_db'
    _TABLE_NAME = 'Vocabulary'
    _RESTRICT_SHOW = 50
    _TEMPLATE_TO_WORD = "SELECT word, date, properties, " \
                        "English, Russian from {table} "

    def __init__(self,
                 db_path: Path) -> None:
        """" Create a connection to database, cursor,
        load Words from there.

        :param db_path: Path to the database.
        :return: None.
        :exception FileNotFoundError: if the database file doesn't exist.
        :exception sqlite3.Error: if something went wrong while connecting to db.
        """
        if not db_path.exists():
            raise FileNotFoundError("DB file doesn't exist")
        
        try:
            self._db = sqlite3.connect(db_path)
        except sqlite3.Error:
            print("Something went while connecting to the database")
            raise
        
        self._cursor = self._db.cursor()
        self._data = self._load()

        # filename with dynamics of learning
        self.graphic_name = (consts.TABLE_FOLDER /
                             f"info_{self.get_date_span()}.xlsx")

    @classmethod
    def set_restrict_show(cls,
                          new_value: int or bool) -> None:
        """ Change the amount of shown in print words.
        If this value is False, all words will be shown.

        :param new_value: int or bool, amount of words shown in print.
        :return: None.
        """
        cls._RESTRICT_SHOW = new_value

    def _load(self) -> List[Word]:
        """
        :return: list of Words loaded from the database.
        """
        data = self._cursor.execute(
            self._TEMPLATE_TO_WORD.format(table=self._TABLE_NAME)
        )
        words = map(
            lambda fields: Word(*fields),
            data.fetchall()
        )
        return list(words)

    @property
    def data(self) -> List[Word]:
        """
        :return: list of Words, data.
        """
        return self._data

    @property
    def begin(self) -> datetime.date:
        """ Get the date of the first day.

        :return: datetime.date, first date.
        """
        first_date = self._cursor.execute(
            f""" SELECT date FROM {self._TABLE_NAME} ORDER BY date """
        ).fetchone()
        return comm_funcs.str_to_date(first_date[0])

    @property
    def end(self) -> datetime.date:
        """ Get the date of the last day.

        :return: datetime.date, last date.
        """
        last_date = self._cursor.execute(
            f""" SELECT date FROM {self._TABLE_NAME} ORDER BY date DESC """
        ).fetchone()
        return comm_funcs.str_to_date(last_date[0])

    @property
    def duration(self) -> int:
        """
        :return: int, duration of the Vocabulary using.
        """
        return (self.end - self.begin).days + 1

    def dynamic(self) -> Dict[datetime.date, int]:
        """
        :return: dict of datetime.date and int, pairs:
        date – amount of learned words in this date.
        """
        dates = self.get_date_list()
        return dict(Counter(dates))

    def max_day_info(self) -> Tuple[datetime.date, int]:
        """ Get info about the day with max words count.

        :return: tuple of datetime.date and int.
        """
        date, amount = max(self.dynamic().items(), key=lambda x: x[1])
        return date.strftime(consts.DATEFORMAT), amount

    def min_day_info(self) -> Tuple[datetime.date, int]:
        """ Get info about the day with max words count.

        :return: tuple of datetime.date and int.
        """
        min_day = min(self.dynamic().items(), key=lambda x: x[1])
        return tuple(min_day)

    def avg_count_of_words(self) -> float:
        """
        :return: float, average amount of words learned per one day.
        """
        count_of_words = self.dynamic().values()
        print(sum(count_of_words))
        print(len(count_of_words))
        return sum(count_of_words) / len(count_of_words)

    def empty_days_count(self) -> int:
        """
        :return: int, amount of days, the user doing nothing.
        """
        return (self.end - self.begin).days + 1 - len(self.get_date_list())

    def statistics(self) -> str:
        """ Statistics about Vocabulary, str format:
            Duration: ...
            Average amount of learned words: ...
            Empty days: ...
            Total: ...
            Would be total: ...
            Max day: ...
            Min day: ...

        Would be total = amount of empty days *
            average amount of words learned per one day

        :return: this str.
        """
        avg_per_day = self.avg_count_of_words()
        empty_days = self.empty_days_count()
        total = len(self)
        would_be_total = total + avg_per_day * empty_days

        return f"Duration: {self.duration} days\n" \
               f"Average amount of learned words: {avg_per_day}\n" \
               f"Empty days: {empty_days}\n" \
               f"Total: {total}\n" \
               f"Would be total: {would_be_total}\n" \
               f"Max day: {self.max_day_info()}\n" \
               f"Min day: {self.max_day_info()}"

    def get_date_list(self) -> List[datetime.date]:
        """ Get all dates from the database.

        :return: list of datetime.date, all dates.
        """
        dates = self._cursor.execute(
            f""" SELECT DISTINCT date FROM {self._TABLE_NAME} """
        )
        # print(*dates.fetchall(), sep='\n')
        dates = map(
            comm_funcs.str_to_date,
            dates.fetchall()
        )
        return list(dates)

    def get_date_span(self,
                      datefmt: str = consts.DATEFORMAT) -> str:
        """
        :param datefmt: str, date format.
        :return: str, date of the first day - date of the last day.
        """
        begin = self.begin.strftime(datefmt)
        end = self.end.strftime(datefmt)
        return f"{begin}-{end}"

    def get_item_before_now(self,
                            days_count: int) -> List[Word]:
        """ Get words which have been learned
        before the last date for days_count days.

        :param days_count: int, index of day before the last.
        :return: list of Words.
        :exception ValueError: if the index < 0.
        """
        dates = self.get_date_list()
        date_index = len(dates) - days_count - 1
        if date_index < 0:
            raise ValueError("Expected day doesn't exist")

        expected_date = dates[date_index]
        return self[expected_date]

    def all_words(self,
                  reverse: bool = False) -> List[Word]:
        """
        :param reverse: bool, whether the sort will be in reversed order.
        :return: sorted by alphabet list of all words.
        """
        all_words = self.data[:]
        all_words.sort(reverse=reverse)

        return all_words

    def visual_info(self) -> None:
        """ Create a xlsx file with dynamic of learning words.

        :return: None.
        """
        kwargs = {
            'x_axis_name': 'Days',
            'y_axis_name': 'Amount of words',
            'chart_title': 'Words learning dynamic'
        }
        date_to_count = self.dynamic()
        create_doc.visual_info(self.graphic_name, date_to_count, **kwargs)

    def create_docx(self) -> None:
        """ Create docx-file with all words, sorted by alphabet.

        Filename – date_span().

        :return: None.
        """
        filename = header = self.get_date_span()
        create_doc.create_docx(filename, self.all_words(), header)

    def create_pdf(self) -> None:
        """ Create pdf-file with all words, sorted by alphabet.

        Filename – date_span().

        :return: None.
        """
        create_doc.create_pdf(self.get_date_span(), self.all_words())

    def search(self,
               item: str or Word) -> List[Word]:
        """ Get all similar words, means the item is
        in the word or the word is in the item.

        :param item: str or Word, word to find.
        :return: list of words similar to the item.
        :exception TypeError: if wrong type given.
        """
        # TODO: check id's similarity
        if not isinstance(item, (str, Word)):
            raise TypeError(f"Wrong item: '{item}'")

        if isinstance(item, Word):
            item = item.word
        item = comm_funcs.fmt_str(item)

        similar_words = filter(
            lambda word: item in word.word or word.word in item,
            self.data
        )
        return list(similar_words)

    def show_graphic(self) -> None:
        """ Show the graphic.

        :return: None.
        :exception FileExistsError: if the graphic doesn't exist.
        """
        if not self.graphic_name.exists():
            raise FileExistsError(f"{self.graphic_name} doesn't exist")

        os.system(self.graphic_name)

    def search_by_properties(self,
                             *properties: str) -> List[Word]:
        """ Find all words which fit with the given properties.

        :param properties: list of str, properties.
        :return: list of word, words which are fit with the given properties.
        """
        fit_words = filter(
            lambda word: word.is_fit(*properties),
            self.data
        )
        return list(fit_words)

    def search_by_id(self,
                     *ids: str) -> List[Word]:
        """ Find words by their ids.

        :param ids: list of str.
        :return: list of words, words which ids are in the list.
        """
        words_by_id = filter(
            lambda word: word.id in ids,
            self.data
        )
        return list(words_by_id)

    def how_to_say_in_russian(self) -> List[str]:
        """
        :return: list of str, only words.
        """
        words = map(Word.word, self.data)
        return list(words)

    def how_to_say_in_english(self) -> List[str]:
        """
        :return: list of str, only English definitions of the words.
        """
        english_definitions = map(
            lambda word: '; '.join(word.english),
            self.data
        )
        return list(english_definitions)

    def backup(self) -> None:
        """ Backup the database to Google Drive.

        :return: None.
        """
        pass

    def append(self,
               item: Word) -> None:
        """ Add a Word obj to the data list.

        :param item: Word to add.
        :return: None.
        :exception TypeError: if wrong type given.
        """
        if not isinstance(item, Word):
            raise TypeError(f"Word expected, but '{type(item)}' given")
        self._data.append(item)

    def extend(self,
               items: List[Word]) -> None:
        """ Extend the data list by another list of them.

        :param items: list of Words to add.
        :return: None.
        :exception TypeError: if wrong type give.
        """
        if (isinstance(items, list) and
                all(isinstance(item, Word) for item in items)):
            self._data.extend(items)
        else:
            raise TypeError(f"List of Words expected, but "
                            f"'{type(items)}' of '{type(items)}' given")

    def __add__(self,
                other: Word or List[Word]) -> List[Word]:
        """ Concatenate the data list with the
        given Word or list of Words.

        :param other: Word or list of them.
        :return: list of words, concatenated lists.
        :exception TypeError: if wrong type give.
        """
        if isinstance(other, Word):
            return self.data + [other]
        elif (isinstance(other, list) and
              all(isinstance(item, Word) for item in other)):
            return self.data + other
        else:
            raise TypeError("Wrong type, Word or list of Words expected")

    def __iadd__(self,
                 other: Word or List[Word]) -> Any:
        """ Extend the data list by one word on list of them.

        :param other: Word or list of them, word(s) to add.
        :return: self.
        :exception TypeError: if wrong type give.
        """
        if isinstance(other, Word):
            self._data += [other]
            return self
        elif (isinstance(other, list) and
              all(isinstance(item, Word) for item in other)):
            self._data += other
            return self
        else:
            raise TypeError("Wrong type, Word or list of Words expected")

    def __contains__(self,
                     item: str or Word) -> bool:
        """
        :param item: str or Word, word to check.
        :return: bool, whether the word is in the Vocabulary.
        """
        if isinstance(item, Word):
            item = item.word

        item = comm_funcs.fmt_str(item)
        words = self._cursor.execute(
            f""" SELECT word FROM {self._TABLE_NAME} 
                  WHERE word LIKE '%{item}%' """
        )
        return bool(words.fetchone())

    def __len__(self) -> int:
        """
        :return: int, amount of learned words.
        """
        return len(self.data)

    def __getitem__(self,
                    item: datetime.date) -> List[Word]:
        """ Get the list of the words learned
        on the date or between the dates: [start; stop].

        :param item: date or slice of dates.
        :return: list of Words.
        :exception TypeError: if the wrong type given.
        :exception ValueError: if the start index > stop.
        """
        if not isinstance(item, (datetime.date, slice)):
            raise TypeError(f"Wrong type: '{type(item)}', "
                            f"datetime.date or slice expected")

        if isinstance(item, datetime.date):
            items_at_date = filter(
                lambda word: word.date == item,
                self.data
            )
        elif isinstance(item, slice):
            start = item.start or self.begin
            stop = item.stop or self.end

            if not isinstance((start, stop), datetime.date):
                raise TypeError(
                    f"Slice for '{type(start)}', '{type(stop)}'"
                    f" not defined, datetime.date expected")
            if start > stop:
                raise ValueError("Start must be <= than stop")

            items_at_date = filter(
                lambda word: start <= word.date <= stop,
                self.data
            )
        return list(items_at_date)

    def __call__(self,
                 item: str or Word) -> List[Word]:
        """ Find all found that are similar to the given one.

        All the same to search().

        :param item: str ot Word, word to find.
        :return: list of found words.
        """
        return self.search(item)

    def __str__(self) -> str:
        """
        :return: str, info about the Vocabulary and some words.
        """
        info = self.statistics()

        some_words = self.data
        is_shorted = False
        if self._RESTRICT_SHOW is not False:
            some_words = some_words[:self._RESTRICT_SHOW]
            is_shorted = True

        if is_shorted is True:
            some_words += ['...']
        some_words = '\n'.join(str(word) for word in some_words)

        return f"{info}\n\n{some_words}"

    def __bool__(self) -> bool:
        """
        :return: bool, whether the data list isn't empty.
        """
        return bool(self.data)

    def __iter__(self) -> iter:
        """
        :return: iter to data list.
        """
        return iter(self.data)

    def __hash__(self) -> int:
        """
        :return: int, hash from data list.
        """
        return hash(self.data)


if __name__ == '__main__':
    db_path = Path("C:\\Users\\Пользователь\\Desktop\\Temporary mediator\\Vocabulary\\Vocabulary\\data\\user_data\\eng_vocabulary.db")
    vocab = Vocabulary(db_path)
    print(vocab)
    # vocab.visual_info()
# TODO: как сказать по-английски?
#  как сказать по-русски?
#  ряд синонимов,
#  ряд антонимов,
#  полные предложения без перевода,
#  предложения без запоминаемой лексемы с переводом,
#  ассоциации с русскими лексемами, картинкми, образами,
#  переписывать предложения, заменив русские
#  слова английскими (русские ↔ английскимми)
