# -*- coding: utf-8 -*-
"""
比赛计分板 - 主屏展示 + 独立控制台操作
主屏：纯展示，可投影到大屏幕
控制台：快捷按钮，独立弹窗，放在操作人面前
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QWidget, QVBoxLayout
)
from PyQt5.uic import loadUi
from PyQt5.QtCore import QTimer, QTime


# ========== 赛前设置 ==========
class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("setup.ui", self)
        self.setFixedSize(self.size())

        self.btnStart.clicked.connect(self.accept)
        self.checkUnknownDuration.toggled.connect(
            lambda c: self.timeEditDuration.setEnabled(not c))
        self.checkFoul.toggled.connect(
            lambda c: self.spinFoulLimit.setEnabled(c))
        self.checkTimeout.toggled.connect(
            lambda c: self.spinTimeoutLimit.setEnabled(c))
        self.radioPvZ.toggled.connect(self._on_pvz)

    def _on_pvz(self, checked):
        for w in [self.timeEditDuration, self.checkUnknownDuration,
                  self.checkFoul, self.spinFoulLimit,
                  self.checkTimeout, self.spinTimeoutLimit,
                  self.checkOffenseSide, self.checkMidGameChange,
                  self.checkAutoSwitch, self.comboSwitchTiming,
                  self.checkBigScore]:
            w.setEnabled(not checked)

    def get_config(self):
        t = self.timeEditDuration.time()
        return {
            "match_name": self.lineEditMatchName.text() or "友谊赛",
            "team_a": self.lineEditTeamA.text() or "甲队",
            "team_b": self.lineEditTeamB.text() or "乙队",
            "template": "basketball" if self.radioBasketball.isChecked() else
                        "pvz" if self.radioPvZ.isChecked() else "none",
            "duration_sec": t.second() + t.minute() * 60 + t.hour() * 3600,
            "use_foul": self.checkFoul.isChecked(),
            "use_timeout": self.checkTimeout.isChecked(),
            "total_rounds": self.spinTotalRounds.value(),
        }


# ========== 主屏展示（通用） ==========
class BaseScoreboardWindow(QMainWindow):
    OVERLAY_MS = 3500

    def __init__(self, config, parent=None):
        super().__init__(parent)
        loadUi("base_scoreboard.ui", self)
        self.config = config

        self.score_a = 0
        self.score_b = 0
        self.remaining_sec = config.get("duration_sec", 1200)
        self.is_paused = False

        self.labelTitle.setText(
            f"{config['team_a']} VS {config['team_b']} — {config['match_name']}")
        self.labelTeamAName.setText(config["team_a"])
        self.labelTeamBName.setText(config["team_b"])
        self._refresh()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

        self.overlay_timer_a = QTimer(self)
        self.overlay_timer_a.setSingleShot(True)
        self.overlay_timer_a.timeout.connect(lambda: self._hide_overlay("A"))

        self.overlay_timer_b = QTimer(self)
        self.overlay_timer_b.setSingleShot(True)
        self.overlay_timer_b.timeout.connect(lambda: self._hide_overlay("B"))

    def _refresh(self):
        self.lcdScoreA.display(self.score_a)
        self.lcdScoreB.display(self.score_b)
        t = QTime(0, 0).addSecs(self.remaining_sec)
        self.lcdTime.display(t.toString("mm:ss"))

    def _tick(self):
        if not self.is_paused and self.remaining_sec > 0:
            self.remaining_sec -= 1
            self._refresh()

    def add_score(self, team, points):
        if team == "A":
            self.score_a += points
            self._show_overlay("A", points)
        else:
            self.score_b += points
            self._show_overlay("B", points)
        self._refresh()

    def sub_score(self, team, points):
        if team == "A":
            self.score_a = max(0, self.score_a - points)
        else:
            self.score_b = max(0, self.score_b - points)
        self._refresh()

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def reset_score(self):
        self.score_a = 0
        self.score_b = 0
        self._refresh()

    def _show_overlay(self, team, points):
        label = self.labelScoreAOverlay if team == "A" else self.labelScoreBOverlay
        timer = self.overlay_timer_a if team == "A" else self.overlay_timer_b
        label.setText(f"+{points}")
        label.show()
        label.raise_()
        timer.start(self.OVERLAY_MS)

    def _hide_overlay(self, team):
        if team == "A":
            self.labelScoreAOverlay.hide()
        else:
            self.labelScoreBOverlay.hide()


# ========== 控制台（通用） ==========
class BaseControlsDialog(QDialog):
    def __init__(self, scoreboard, parent=None):
        super().__init__(parent)
        loadUi("base_controls.ui", self)
        self.scoreboard = scoreboard
        self.setFixedSize(self.size())

        self.btnAddScoreA.clicked.connect(lambda: self.scoreboard.add_score("A", 1))
        self.btnAddScoreB.clicked.connect(lambda: self.scoreboard.add_score("B", 1))
        self.btnSubScoreA.clicked.connect(lambda: self.scoreboard.sub_score("A", 1))
        self.btnSubScoreB.clicked.connect(lambda: self.scoreboard.sub_score("B", 1))
        self.btnPause.clicked.connect(self._on_pause)
        self.btnReset.clicked.connect(self.scoreboard.reset_score)

    def _on_pause(self):
        self.scoreboard.toggle_pause()
        self.btnPause.setText("继续" if self.scoreboard.is_paused else "暂停 / 继续")


# ========== 主屏展示（篮球） ==========
class BasketballScoreboardWindow(BaseScoreboardWindow):
    OFFENSE_SEC = 24

    def __init__(self, config, parent=None):
        QMainWindow.__init__(self, parent)
        loadUi("basketball_scoreboard.ui", self)
        self.config = config

        self.score_a = 0
        self.score_b = 0
        self.foul_a = 0
        self.foul_b = 0
        self.timeout_a = 0
        self.timeout_b = 0
        self.remaining_sec = config.get("duration_sec", 720)
        self.offense_sec = self.OFFENSE_SEC
        self.is_paused = False
        self.offense_team = "A"

        self.labelTitle.setText(
            f"{config['team_a']} VS {config['team_b']} — {config['match_name']}")
        self.labelTeamAName.setText(config["team_a"])
        self.labelTeamBName.setText(config["team_b"])
        self._refresh()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

        self.overlay_timer_a = QTimer(self)
        self.overlay_timer_a.setSingleShot(True)
        self.overlay_timer_a.timeout.connect(lambda: self._hide_overlay("A"))
        self.overlay_timer_b = QTimer(self)
        self.overlay_timer_b.setSingleShot(True)
        self.overlay_timer_b.timeout.connect(lambda: self._hide_overlay("B"))

    def _refresh(self):
        self.lcdScoreA.display(self.score_a)
        self.lcdScoreB.display(self.score_b)
        self.lcdFoulA.display(self.foul_a)
        self.lcdFoulB.display(self.foul_b)
        self.lcdTimeoutA.display(self.timeout_a)
        self.lcdTimeoutB.display(self.timeout_b)
        t = QTime(0, 0).addSecs(self.remaining_sec)
        self.lcdGameTime.display(t.toString("mm:ss"))
        ot = QTime(0, 0).addSecs(self.offense_sec)
        self.lcdOffenseTime.display(ot.toString("mm:ss.z"))
        side = self.config["team_a"] if self.offense_team == "A" else self.config["team_b"]
        self.labelOffenseSide.setText(f"进攻方: {side}")

    def _tick(self):
        if not self.is_paused and self.remaining_sec > 0:
            self.remaining_sec -= 1
            if self.offense_sec > 0:
                self.offense_sec -= 1
            self._refresh()

    def add_score(self, team, points):
        if team == "A":
            self.score_a += points
            self._show_overlay("A", points)
        else:
            self.score_b += points
            self._show_overlay("B", points)
        self.offense_sec = self.OFFENSE_SEC
        self._refresh()

    def add_foul(self, team):
        if team == "A":
            self.foul_a += 1
        else:
            self.foul_b += 1
        self._refresh()

    def add_team_timeout(self, team):
        if team == "A":
            self.timeout_a += 1
        else:
            self.timeout_b += 1
        self._refresh()

    def switch_offense(self):
        self.offense_team = "B" if self.offense_team == "A" else "A"
        self.offense_sec = self.OFFENSE_SEC
        self._refresh()

    def reset_score(self):
        self.score_a = self.score_b = 0
        self.foul_a = self.foul_b = 0
        self.timeout_a = self.timeout_b = 0
        self.offense_sec = self.OFFENSE_SEC
        self._refresh()

    def _show_overlay(self, team, points):
        label = self.labelScoreAOverlay if team == "A" else self.labelScoreBOverlay
        timer = self.overlay_timer_a if team == "A" else self.overlay_timer_b
        label.setText(f"+{points}")
        label.show()
        label.raise_()
        timer.start(self.OVERLAY_MS)

    def _hide_overlay(self, team):
        if team == "A":
            self.labelScoreAOverlay.hide()
        else:
            self.labelScoreBOverlay.hide()


# ========== 控制台（篮球） ==========
class BasketballControlsDialog(QDialog):
    def __init__(self, scoreboard, parent=None):
        super().__init__(parent)
        loadUi("basketball_controls.ui", self)
        self.scoreboard = scoreboard
        self.setFixedSize(self.size())

        self.btnScoreA1.clicked.connect(lambda: self.scoreboard.add_score("A", 1))
        self.btnScoreA3.clicked.connect(lambda: self.scoreboard.add_score("A", 3))
        self.btnScoreB1.clicked.connect(lambda: self.scoreboard.add_score("B", 1))
        self.btnScoreB3.clicked.connect(lambda: self.scoreboard.add_score("B", 3))
        self.btnSubScoreA.clicked.connect(lambda: self.scoreboard.sub_score("A", 1))
        self.btnSubScoreB.clicked.connect(lambda: self.scoreboard.sub_score("B", 1))
        self.btnFoulA.clicked.connect(lambda: self.scoreboard.add_foul("A"))
        self.btnFoulB.clicked.connect(lambda: self.scoreboard.add_foul("B"))
        self.btnTimeoutA.clicked.connect(lambda: self.scoreboard.add_team_timeout("A"))
        self.btnTimeoutB.clicked.connect(lambda: self.scoreboard.add_team_timeout("B"))
        self.btnSwitchOffense.clicked.connect(self.scoreboard.switch_offense)
        self.btnPause.clicked.connect(self._on_pause)
        self.btnReset.clicked.connect(self.scoreboard.reset_score)

    def _on_pause(self):
        self.scoreboard.toggle_pause()
        self.btnPause.setText("继续" if self.scoreboard.is_paused else "暂停 / 继续")


# ========== 主入口 ==========
def main():
    app = QApplication(sys.argv)

    setup = SetupDialog()
    if setup.exec_() != QDialog.Accepted:
        sys.exit(0)
    config = setup.get_config()

    if config["template"] == "basketball":
        scoreboard = BasketballScoreboardWindow(config)
        controls = BasketballControlsDialog(scoreboard)
    else:
        scoreboard = BaseScoreboardWindow(config)
        controls = BaseControlsDialog(scoreboard)

    scoreboard.show()
    controls.show()

    # 控制台放到主屏旁边
    controls.move(scoreboard.x() + scoreboard.width() + 20, scoreboard.y())

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
