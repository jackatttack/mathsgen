"""Every lesson, in the order the Maths tool lists them (grouped by area
on the Lessons page).

    from mathskit import lessons
    lessons.ALL               # [Lesson, ...]
    lessons.find('linear')
"""
from . import (angles, brackets, like_terms, linear, percentages, quadratics, ratio,
               right_triangles, straight_lines)

ALL = [percentages.LESSON, ratio.LESSON, like_terms.LESSON, brackets.LESSON, linear.LESSON,
       quadratics.LESSON, straight_lines.LESSON, angles.LESSON, right_triangles.LESSON]


def find(key):
    for lesson in ALL:
        if lesson.key == key:
            return lesson
    raise KeyError('No lesson %r' % key)
