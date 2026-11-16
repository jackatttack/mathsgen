"""Every lesson, in the order the Maths tool lists them (grouped by area
on the Lessons page).

    from mathskit import lessons
    lessons.ALL               # [Lesson, ...]
    lessons.find('linear')
"""
from . import brackets, like_terms, linear, percentages, quadratics

ALL = [percentages.LESSON, like_terms.LESSON, brackets.LESSON, linear.LESSON,
       quadratics.LESSON]


def find(key):
    for lesson in ALL:
        if lesson.key == key:
            return lesson
    raise KeyError('No lesson %r' % key)
