"""Every lesson, in the order the Maths tool lists them (grouped by area
on the Lessons page).

    from mathskit import lessons
    lessons.ALL               # [Lesson, ...]
    lessons.find('linear')
"""
from . import (angles, brackets, completing_square, fdp, fractions, like_terms, linear, parallel_lines, percentages,
               polygons, probability, quadratics, ratio, right_triangles, straight_lines, trees,
               venn)

ALL = [fractions.LESSON, fdp.LESSON, percentages.LESSON, ratio.LESSON, like_terms.LESSON, brackets.LESSON, linear.LESSON,
       quadratics.LESSON, completing_square.LESSON, straight_lines.LESSON, angles.LESSON, parallel_lines.LESSON, polygons.LESSON, right_triangles.LESSON,
       probability.LESSON, venn.LESSON, trees.LESSON]


def find(key):
    for lesson in ALL:
        if lesson.key == key:
            return lesson
    raise KeyError('No lesson %r' % key)
