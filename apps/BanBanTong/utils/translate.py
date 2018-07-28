# coding=utf-8
# translate.py
import pypinyin


def trans2pinyin(original_string):
    first_letter_lst = pypinyin.pinyin(original_string, pypinyin.FIRST_LETTER)
    full_letter = ' '.join(pypinyin.lazy_pinyin(original_string, pypinyin.TONE2))

    return {
        'first_letter_set': ''.join([i[0] for i in first_letter_lst]),
        'full_letter': full_letter
    }


if __name__ == '__main__':
    ori = u'重庆很重要'
    print trans2pinyin(ori)
