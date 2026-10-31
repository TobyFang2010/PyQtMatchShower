# main.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QWidget, QVBoxLayout
)
from PyQt5.QtCore import QTimer, Qt

# pyuic 编译导出的模块
from setupui import Ui_SetupDialog
from base_scoreboard import Ui_BaseScoreboardWindow
from base_controls import Ui_BaseControlsDialog
from basketball_scoreboard import Ui_BasketballScoreboardWindow
from basketball_controls import Ui_BasketballControlsDialog


class SetupDialog(QDialog, Ui_SetupDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.match_data = None
        self.btnStart.clicked.connect(self.on_start)

    def on_start(self):
        data = {
            "team_a": self.lineEditTeamA.text().strip() or "甲队",
            "team_b": self.lineEditTeamB.text().strip() or "乙队",
            "match_name": self.lineEditMatchName.text().strip(),
            "template": "none",
            "total_time": self.timeEditDuration.time(),
            "unknown_duration": self.checkUnknownDuration.isChecked(),
            "use_foul": self.checkFoul.isChecked(),
            "foul_limit": self.spinFoulLimit.value(),
            "use_timeout": self.checkTimeout.isChecked(),
            "timeout_limit": self.spinTimeoutLimit.value(),
            "enable_offense": self.checkOffenseSide.isChecked(),
            "allow_change": self.checkMidGameChange.isChecked(),
            "auto_switch": self.checkAutoSwitch.isChecked(),
            "switch_timing": self.comboSwitchTiming.currentText(),
            "use_big_score": self.checkBigScore.isChecked(),
            "rounds": self.spinTotalRounds.value()
        }
        if self.radioBasketball.isChecked():
            data["template"] = "basketball"
        self.match_data = data
        self.accept()


class BaseControlsDialog(QDialog, Ui_BaseControlsDialog):
    def __init__(self, parent_board):
        super().__init__()
        self.setupUi(self)
        self.board = parent_board
        self.btnAddScoreA.clicked.connect(lambda: self.board.add_score("A", 1))
        self.btnAddScoreB.clicked.connect(lambda: self.board.add_score("B", 1))
        self.btnSubScoreA.clicked.connect(lambda: self.board.add_score("A", -1))
        self.btnSubScoreB.clicked.connect(lambda: self.board.add_score("B", -1))
        self.btnPause.clicked.connect(self.board.toggle_clock)
        self.btnReset.clicked.connect(self.board.reset_all)


class BaseScoreboardWindow(QMainWindow, Ui_BaseScoreboardWindow):
    def __init__(self, match_data):
        super().__init__()
        self.setupUi(self)
        self.data = match_data
        self.score_a = 0
        self.score_b = 0
        self.running = False
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick)

        self.labelTeamAName.setText(self.data["team_a"])
        self.labelTeamBName.setText(self.data["team_b"])
        title = self.data["match_name"] or f"{self.data['team_a']} VS {self.data['team_b']}"
        self.labelTitle.setText(title)

        hh = self.data["total_time"].hour()
        mm = self.data["total_time"].minute()
        ss = self.data["total_time"].second()
        self.remain_sec = hh * 3600 + mm * 60 + ss
        self.refresh_lcd()

        self.overlay_timer = QTimer()
        self.overlay_timer.setSingleShot(True)
        self.overlay_timer.timeout.connect(self.hide_overlay)

        self.ctrl_win = BaseControlsDialog(self)
        self.ctrl_win.show()

    def refresh_lcd(self):
        self.lcdScoreA.display(self.score_a)
        self.lcdScoreB.display(self.score_b)
        h, r = divmod(self.remain_sec, 3600)
        m, s = divmod(r, 60)
        self.lcdTime.display(f"{h:02d}:{m:02d}:{s:02d}")

    def add_score(self, side, delta):
        if side == "A":
            self.score_a = max(0, self.score_a + delta)
            self.labelScoreAOverlay.setText(f"{delta:+d}")
            self.labelScoreAOverlay.setVisible(True)
        else:
            self.score_b = max(0, self.score_b + delta)
            self.labelScoreBOverlay.setText(f"{delta:+d}")
            self.labelScoreBOverlay.setVisible(True)
        self.overlay_timer.start(1200)
        self.refresh_lcd()

    def hide_overlay(self):
        self.labelScoreAOverlay.setVisible(False)
        self.labelScoreBOverlay.setVisible(False)

    def toggle_clock(self):
        if self.running:
            self.timer.stop()
            self.running = False
        else:
            self.timer.start()
            self.running = True

    def tick(self):
        if self.remain_sec > 0:
            self.remain_sec -= 1
            self.refresh_lcd()
        else:
            self.timer.stop()
            self.running = False

    def reset_all(self):
        self.score_a = 0
        self.score_b = 0
        hh = self.data["total_time"].hour()
        mm = self.data["total_time"].minute()
        ss = self.data["total_time"].second()
        self.remain_sec = hh * 3600 + mm * 60 + ss
        self.refresh_lcd()


class BasketballControlsDialog(QDialog, Ui_BasketballControlsDialog):
    def __init__(self, parent_board):
        super().__init__()
        self.setupUi(self)
        self.board = parent_board
        self.btnSwitchOffense.clicked.connect(self.board.switch_offense)
        self.btnPause.clicked.connect(self.board.toggle_clock)

        self.btnScoreA1.clicked.connect(lambda: self.board.add_score("A", 1))
        self.btnScoreA3.clicked.connect(lambda: self.board.add_score("A", 3))
        self.btnScoreB1.clicked.connect(lambda: self.board.add_score("B", 1))
        self.btnScoreB3.clicked.connect(lambda: self.board.add_score("B", 3))

        self.btnSubScoreA.clicked.connect(lambda: self.board.add_score("A", -1))
        self.btnSubScoreB.clicked.connect(lambda: self.board.add_score("B", -1))

        self.btnFoulA.clicked.connect(lambda: self.board.add_foul("A"))
        self.btnFoulB.clicked.connect(lambda: self.board.add_foul("B"))

        self.btnTimeoutA.clicked.connect(lambda: self.board.use_timeout("A"))
        self.btnTimeoutB.clicked.connect(lambda: self.board.use_timeout("B"))

        self.btnReset.clicked.connect(self.board.reset_all)


class BasketballScoreboardWindow(QMainWindow, Ui_BasketballScoreboardWindow):
    def __init__(self, match_data):
        super().__init__()
        self.setupUi(self)
        self.data = match_data
        self.score_a = 0
        self.score_b = 0
        self.foul_a = 0
        self.foul_b = 0
        self.timeout_a = self.data["timeout_limit"]
        self.timeout_b = self.data["timeout_limit"]
        self.offense_side = "A"
        self.running = False

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick)

        self.labelTeamAName.setText(self.data["team_a"])
        self.labelTeamBName.setText(self.data["team_b"])
        title = self.data["match_name"] or f"{self.data['team_a']} VS {self.data['team_b']}"
        self.labelTitle.setText(title)
        self.labelOffenseSide.setText(f"进攻方: {self.data['team_a']}")

        hh = self.data["total_time"].hour()
        mm = self.data["total_time"].minute()
        ss = self.data["total_time"].second()
        self.remain_sec = hh * 3600 + mm * 60 + ss

        self.overlay_timer = QTimer()
        self.overlay_timer.setSingleShot(True)
        self.overlay_timer.timeout.connect(self.hide_overlay)

        self.refresh_lcd()
        self.ctrl_win = BasketballControlsDialog(self)
        self.ctrl_win.show()

    def refresh_lcd(self):
        self.lcdScoreA.display(self.score_a)
        self.lcdScoreB.display(self.score_b)
        self.lcdFoulA.display(self.foul_a)
        self.lcdFoulB.display(self.foul_b)
        self.lcdTimeoutA.display(self.timeout_a)
        self.lcdTimeoutB.display(self.timeout_b)

        h, r = divmod(self.remain_sec, 3600)
        m, s = divmod(r, 60)
        self.lcdGameTime.display(f"{h:02d}:{m:02d}:{s:02d}")

        name = self.data["team_a"] if self.offense_side == "A" else self.data["team_b"]
        self.labelOffenseSide.setText(f"进攻方: {name}")

    def add_score(self, side, delta):
        if side == "A":
            self.score_a = max(0, self.score_a + delta)
            self.labelScoreAOverlay.setText(f"{delta:+d}")
            self.labelScoreAOverlay.setVisible(True)
        else:
            self.score_b = max(0, self.score_b + delta)
            self.labelScoreBOverlay.setText(f"{delta:+d}")
            self.labelScoreBOverlay.setVisible(True)
        self.overlay_timer.start(1200)
        self.refresh_lcd()

    def hide_overlay(self):
        self.labelScoreAOverlay.setVisible(False)
        self.labelScoreBOverlay.setVisible(False)

    def switch_offense(self):
        self.offense_side = "B" if self.offense_side == "A" else "A"
        self.refresh_lcd()

    def add_foul(self, side):
        if side == "A":
            self.foul_a += 1
        else:
            self.foul_b += 1
        self.refresh_lcd()

    def use_timeout(self, side):
        if side == "A" and self.timeout_a > 0:
            self.timeout_a -= 1
        elif side == "B" and self.timeout_b > 0:
            self.timeout_b -= 1
        self.refresh_lcd()

    def toggle_clock(self):
        if self.running:
            self.timer.stop()
            self.running = False
        else:
            self.timer.start()
            self.running = True

    def tick(self):
        if self.remain_sec > 0:
            self.remain_sec -= 1
            self.refresh_lcd()
        else:
            self.timer.stop()
            self.running = False

    def reset_all(self):
        self.score_a = 0
        self.score_b = 0
        self.foul_a = 0
        self.foul_b = 0
        self.timeout_a = self.data["timeout_limit"]
        self.timeout_b = self.data["timeout_limit"]
        self.offense_side = "A"

        hh = self.data["total_time"].hour()
        mm = self.data["total_time"].minute()
        ss = self.data["total_time"].second()
        self.remain_sec = hh * 3600 + mm * 60 + ss
        self.refresh_lcd()


def main():
    app = QApplication(sys.argv)
    setup = SetupDialog()
    if setup.exec_() != QDialog.Accepted or setup.match_data is None:
        return
    md = setup.match_data
    if md["template"] == "basketball":
        win = BasketballScoreboardWindow(md)
    else:
        win = BaseScoreboardWindow(md)
    win.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
