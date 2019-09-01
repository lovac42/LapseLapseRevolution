# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/LapseLapseRevolution


import sys
from anki.lang import _
from anki.hooks import wrap, addHook
from anki.utils import fmtTimeSpan, json
from anki.sched import Scheduler
from aqt.reviewer import Reviewer
from aqt import mw

# Fun Facts:
#  Anki 2.0.8 = v1.99
PYTHON2=sys.version_info[0]<3
PYCALLBAK="py.link" if PYTHON2 else "pycmd" #Anki2.0 or below


# TODO: map buttons to dance mat using autohotkey


# TODO: add config options
START = 1 #no hotkey for button 0
END = 5 #exclusive, so add 1


def getMultiplier(i, div=100.0):
    return (0,20,40,60,80,100)[i]/div




class LapseLapseRevolution:
    def __init__(self):
        self.lap_grade=0
        self.lap_btns=LapseButtons()

    def onAnswerCard(self, rev, ease, _old):
        if rev.mw.state != "review": return
        if rev.state != "answer": return
        if rev.card.odid==0 and rev.card.queue==2:
            if self.lap_btns.isShown():
                self.lap_btns.hide()
                self.lap_grade=ease
                ease=1
            elif ease==1:
                self.lap_btns.show()
                return
        return _old(rev, ease)

    def onLapseIvl(self, sched, card, conf, _old):
        if card.odid==0 and card.queue==2:
            return self.lap_btns.getIvl(card,conf,self.lap_grade)
        return _old(sched,card,conf)





class LapseButtons:
    def __init__(self):
        self.toolbar=mw.reviewer.bottom.web
        self.visible=False
        addHook('showAnswer',self.onShowAnswer)

    def onShowAnswer(self):
        self.hide()
        self.card=mw.reviewer.card
        self.conf=mw.col.sched._lapseConf(self.card)

    def isShown(self):
        return self.visible

    def hide(self):
        self.visible=False

    def show(self):
        self.visible=True
        self.toolbar.setFocus()
        middle=self.getButtons()
        self.toolbar.eval("showAnswer(%s);" % json.dumps(middle))

    def getButtons(self):
        def but(i, label):
            if i == 3:
                extra = "id=defease"
            else:
                extra = ""
            due = self.buttonTime(i)
            return '''
<td align=center>%s<button %s title="%s" onclick='%s("ease%d");'>\
%s</button></td>''' % (due, extra, _("Shortcut key: %s") % i, PYCALLBAK, i, label)
        buf = "<center><table cellpading=0 cellspacing=0><tr>"
        for ease, label in self.buttonList():
                buf += but(ease, label)
        buf += "</tr></table>"
        script = """
<script>$(function () { $("#defease").focus(); });</script>"""
        return buf + script

    def buttonTime(self, i):
        if not mw.col.conf['estTimes']:
            return "<div class=spacer></div>"
        ivl=self.getIvl(self.card,self.conf,i)*86400
        txt=fmtTimeSpan(ivl,short=True)
        return '<span class=nobold>%s</span><br>'%txt

    def buttonList(self):
        arr=[]
        for i in range(START,END):
            m=getMultiplier(i,1)
            arr.append((i, _("%d%%"%m)))
        return arr

    def getIvl(self, card, conf, ease):
        ivl=card.ivl*getMultiplier(ease)
        return max(1,conf['minInt'],int(ivl))



llr=LapseLapseRevolution()
Reviewer._answerCard=wrap(Reviewer._answerCard,llr.onAnswerCard,"around")
Scheduler._nextLapseIvl=wrap(Scheduler._nextLapseIvl,llr.onLapseIvl,"around")
if not PYTHON2:
    from anki.schedv2 import Scheduler as SchedulerV2
    SchedulerV2._lapseIvl=wrap(SchedulerV2._lapseIvl,llr.onLapseIvl,"around")

