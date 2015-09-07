# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.core.paginator import Paginator as BasePaginator
from django.core.paginator import Page as BasePage


class Paginator(BasePaginator):
    def __init__(self, page=1, expander=None, *args, **kwargs):
        super(Paginator, self).__init__(*args, **kwargs)
        self.expander = expander
        self.current_page = self.page(page)

    def page_range_slice(self):
        left = self.current_page.number - 2
        right = self.current_page.number + 2
        overflow_left = max(0, (-1 * left) + 1)
        overflow_right = max(0, right - self.num_pages)
        left = max(left - overflow_right, 1)
        right = min(right + overflow_left, self.num_pages)
        return range(left, right + 1)

    def _get_page(self, *args, **kwargs):
        return Page(*args, **kwargs)


class Page(BasePage):
    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        if self.paginator.expander:
            self.object_list = [
                self.paginator.expander(item) for item in self.object_list
            ]
