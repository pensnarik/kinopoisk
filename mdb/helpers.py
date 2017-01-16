# -*- encoding: utf-8 -*-

unhtml_map = {
    '&quot;': '"', '&laquo;': '"', '&raquo;': '"', '&#34;': '"', '&#8220;': '"',
    '&#171;': '"', '&#187;': '"', '&#039;': '\'', '&#39;': '\'', '&amp;': '&',
    '&copy;': '(c)', '&bull;': '*', '&#151;': '-', '&#8211;': '-', '&#8212;': '-',
    '&#45;': '-', '&mdash;': '-', '&lt;': '<', '&gt;': '>', '&nbsp;': ' ', '&#160': ' ',
    '\n': '', '\r': '', '&#124;': '|', '&#033;': '!', '&#33;': '!', '&#58;': ':', '&#x3a;': ':',
    '&lsaquo;': '<', '&rsaquo;': '>'
}

headers = {'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
           'Chrome/34.0.1847.132 Safari/537.36', 'Connection': 'close'}


def unhtml(input_string):
    """
    Заменяет HTML последовательности в строке на символы из таблицы ASCII для хранения
    в БД и читаемого отображения в толстом клиенте
    """
    return input_string.replace('&nbsp', '')


def get_date(date_as_russian_text):
    """
    Возвращает дату в формате ISO8601
    """
    month_mapping_d = {u'января': 1, u'февраля': 2, u'марта': 3, u'апреля': 4, u'мая': 5,
                       u'июня': 6, u'июля': 7, u'августа': 8, u'сентября': 9, u'октября': 10,
                       u'ноября': 11, u'декабря': 12}
    month_mapping_m = {u'январь': 1, u'февраль': 2, u'март': 3, u'апрель': 4, u'май': 5, u'июнь': 6,
                       u'июль': 7, u'август': 8, u'сентябрь': 9, u'октябрь': 10, u'ноябрь': 11,
                       u'декабрь': 12}
    if u'до н.э.' in date_as_russian_text:
        era = 'BC'
    else:
        era = 'AD'

    data = date_as_russian_text.replace(u' до н.э.', '').replace(u',', '').split()

    if len(data) == 3:
        # Bug with https://www.kinopoisk.ru/film/224679/dates/
        if data[0] == '0':
            data[0] = '1'
        return {'precision': 'd',
                'date': '%s-%.02d-%.02d %s' % (data[2], month_mapping_d[data[1].lower()],
                                               int(data[0]), era)}
    elif len(data) == 2:
        return {'precision': 'm',
                'date': '%s-%.02d-01 %s' % (data[1], month_mapping_m[data[0].lower()], era)}
    elif len(data) == 1:
        return {'precision': 'y',
                'date': '%s-01-01 %s' % (data[0], era)}
