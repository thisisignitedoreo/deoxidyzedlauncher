from PySide6 import (
    QtWidgets,
    QtCore,
    QtGui
)
from form import Ui_Form
import subprocess
import traceback
import requests
import zipfile
import pathlib
import shutil
import json
import sys
import io
import os

if not os.path.isfile("settings.json"):
    with open("settings.json", "w") as f:
        json.dump({"lang": "en", "path": "C:/Program Files/DeoxidyzedGD/", "installed_mods": []}, f)

with open("settings.json", "r") as f:
    settings = json.load(f)

class DeoxidyzedLauncher(QtWidgets.QWidget):
    def __init__(self):
        super(DeoxidyzedLauncher, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.lineEdit.setText(settings["path"])
        self.ui.radioButton.setChecked(settings["lang"] == "en")
        self.ui.radioButton_2.setChecked(settings["lang"] == "ru")

        self.set_names()
        self.fetch_mods()
        self.recheck()
        self.connect()

    def connect(self):
        self.ui.listWidget.itemDoubleClicked.connect(self.fetch_mod)
        self.ui.toolButton_2.clicked.connect(self.browse_path)
        self.ui.toolButton_3.clicked.connect(self.recheck)
        self.ui.toolButton_4.clicked.connect(self.fetch_mods)
        self.ui.pushButton.clicked.connect(self.install)
        self.ui.pushButton_2.clicked.connect(self.install_mod)
        self.ui.pushButton_3.clicked.connect(self.about)
        self.ui.radioButton.clicked.connect(lambda: self.set_lang("en"))
        self.ui.radioButton_2.clicked.connect(lambda: self.set_lang("ru"))
        self.ui.progressBar.setMaximum(100)

# GAME
    def install(self):
        if self.recheck_status():
            # play
            self.set_status(self.get_string("playing", settings["lang"]))
            self.ui.pushButton.setEnabled(False)
            app.processEvents()
            subprocess.call([f"{settings['path']}GeometryDash.exe"], cwd=settings["path"])
            self.recheck()
            self.ui.pushButton.setEnabled(True)
        else:
            # install
            self.set_status(self.get_string("installing", settings["lang"]))
            self.ui.pushButton.setEnabled(False)
            game = self.download_file("https://www.dropbox.com/s/z2mkmv52l7xuyqs/client.zip?dl=1")
            self.create_dir_if_nexist(settings["path"])
            self.unzip(game, settings["path"])
            self.recheck()
            self.ui.pushButton.setEnabled(True)

# MODS
    def install_mod(self):
        bs = "\\"  # sorry
        cur_dir = os.path.abspath(".")
        os.chdir(settings["path"])
        if self.slug in settings["installed_mods"]:
            # deinstall
            self.set_status(self.get_string("deinstalling", settings["lang"]))
            self.set_status(0)
            self.ui.pushButton.setEnabled(False)
            app.processEvents()
            deinstaller = self.download_file(f"https://thisisignitedoreo.github.io/deoxidyzed/mods_repository/{self.slug}/deinstall.bat")
            app.processEvents()
            open(settings["path"] + "deinstall.bat", "wb").write(deinstaller)
            app.processEvents()
            os.system("deinstall.bat")
            os.remove(f"{settings['path']}deinstall.bat")
            self.set_status(100)
            self.recheck()
            settings["installed_mods"].remove(self.slug)
            settings["installed_mods"] = self.delete_duplicates(settings["installed_mods"])
            self.save_settings()
            self.ui.pushButton.setEnabled(True)
        else:
            # fresh install
            self.set_status(self.get_string("downloading", settings["lang"]))
            self.ui.pushButton.setEnabled(False)
            app.processEvents()
            mod = self.download_file(f"https://thisisignitedoreo.github.io/deoxidyzed/mods_repository/{self.slug}/mod.zip")
            app.processEvents()
            open(settings["path"] + "mod.zip", "wb").write(mod)
            self.set_status(self.get_string("unpacking", settings["lang"]))
            shutil.unpack_archive(settings["path"] + "mod.zip", settings["path"])
            self.set_status(self.get_string("finishing", settings["lang"]))
            app.processEvents()
            post_install_script = self.download_file(f"https://thisisignitedoreo.github.io/deoxidyzed/mods_repository/{self.slug}/install.bat")
            app.processEvents()
            open(settings["path"] + "install.bat", "wb").write(post_install_script)
            app.processEvents()
            os.system("install.bat")
            self.set_status(self.get_string("finishing", settings["lang"]))
            os.remove(f"{settings['path']}install.bat")
            os.remove(f"{settings['path']}mod.zip")
            self.recheck()
            settings["installed_mods"].append(self.slug)
            settings["installed_mods"] = self.delete_duplicates(settings["installed_mods"])
            self.save_settings()
            self.ui.pushButton.setEnabled(True)
        os.chdir(cur_dir)

        if self.slug in settings["installed_mods"]:
            self.ui.pushButton_2.setText(self.get_string("deinstall", settings["lang"]))
        else:
            self.ui.pushButton_2.setText(self.get_string("install", settings["lang"]))

    def fetch_mod(self, item):
        self.slug = item.data(QtCore.Qt.UserRole)
        self.mod_index = self.find_mod_by_slug(self.slug)
        name = self.mods[self.mod_index]["name"]
        desc = self.mods[self.mod_index]["description"]
        author = self.mods[self.mod_index]["author"]
        available = self.mods[self.mod_index]["available"]
        icon = self.qpix_from_url(f"https://thisisignitedoreo.github.io/deoxidyzed/mods_repository/{self.slug}/icon.png").scaled(48, 48, mode=QtCore.Qt.SmoothTransformation)

        if self.slug in settings["installed_mods"]:
            self.ui.pushButton_2.setText(self.get_string("deinstall", settings["lang"]))
        else:
            self.ui.pushButton_2.setText(self.get_string("install", settings["lang"]))

        self.ui.pushButton_2.setEnabled(available and self.recheck_status())
        self.ui.label_2.setPixmap(icon)
        self.ui.label_4.setText(name)
        self.ui.label_3.setText(f"by: {author}\n{desc}")

    def fetch_mods(self):
        self.mods = json.loads(requests.get("https://thisisignitedoreo.github.io/deoxidyzed/mods_repository/mods_repository.json").content)
        self.ui.listWidget.clear()
        for i in self.mods:
            item = QtWidgets.QListWidgetItem()
            item.setText(i["name"])
            item.setIcon(self.qicon_from_url(f"https://thisisignitedoreo.github.io/deoxidyzed/mods_repository/{i['slug']}/icon.png"))
            item.setData(QtCore.Qt.UserRole, i["slug"])
            self.ui.listWidget.addItem(item)

    def qicon_from_url(self, url):
        data_str = requests.get(url)
        if not data_str.ok:
            return QtGui.QIcon(":/assets/assets/noicon.png")
        else:
            data_str = data_str.content
        qpix = QtGui.QPixmap()
        qpix.loadFromData(data_str)
        qicon = QtGui.QIcon(qpix)
        return qicon

    def qpix_from_url(self, url):
        data_str = requests.get(url)
        if not data_str.ok:
            data_str = open("assets/noicon.png", "rb").read()
        else:
            data_str = data_str.content
        qpix = QtGui.QPixmap()
        qpix.loadFromData(data_str)
        return qpix

    def find_mod_by_slug(self, slug):
        for k, i in enumerate(self.mods):
            if i["slug"] == slug:
                return k

# LANG
    def set_names(self):
        self.ui.radioButton.setText(self.get_string("en", settings["lang"]))
        self.ui.radioButton_2.setText(self.get_string("ru", settings["lang"]))
        self.ui.pushButton_3.setText(self.get_string("about", settings["lang"]))
        self.ui.toolButton_2.setText(self.get_string("browse", settings["lang"]))
        self.ui.toolButton_3.setText(self.get_string("recheck", settings["lang"]))
        self.ui.toolButton_4.setText(self.get_string("recheck", settings["lang"]))
        self.ui.label.setText(self.get_string("mods", settings["lang"]))
        self.ui.label_2.setText(self.get_string("selectShort", settings["lang"]))
        self.ui.label_3.setText(self.get_string("selectLong", settings["lang"]))

    def set_lang(self, lang):
        settings["lang"] = lang
        self.save_settings()
        self.set_names()
        self.recheck()

    def recheck(self):
        status = self.recheck_status()
        if status:
            self.ui.pushButton.setText(self.get_string("play", settings["lang"]))
        else:
            self.ui.pushButton.setText(self.get_string("install", settings["lang"]))

    def get_string(self, string_id, lang):
        self.strings = {
            "en": {
                "en": "English",
                "ru": "Russian",
                "play": "Play",
                "playing": "Playing",
                "install": "Install",
                "installing": "Installing",
                "deinstall": "Deinstall",
                "deinstalling": "Deinstalling",
                "downloading": "Downloading",
                "unpacking": "Unpacking",
                "finishing": "Finishing",
                "mods": "Mods:",
                "recheck": "Recheck",
                "about": "About",
                "aboutText": "DeoxidyzedLauncher is FOSS program.\nDistributed in GPL-3.0-only license.",
                "browse": "Browse",
                "selectFolder": "Select Folder",
                "selectShort": "Select mod!",
                "selectLong": "Select mod on left pane and it will show here.",
            },
            "ru": {
                "en": "Английский",
                "ru": "Русский",
                "play": "Играть",
                "playing": "Игра запущена",
                "install": "Установить",
                "installing": "Установка",
                "deinstall": "Удалить",
                "deinstalling": "Удаление",
                "downloading": "Скачивание",
                "unpacking": "Разархивирование",
                "finishing": "Завершение",
                "mods": "Моды:",
                "recheck": "Перепроверить",
                "about": "О программе",
                "aboutText": "DeoxidyzedLauncher это опенсорсная программа.\nРаспространяется под GPL-3.0-only лицензией.",
                "browse": "Обзор",
                "selectFolder": "Выбрать папку",
                "selectShort": "Выберете мод!",
                "selectLong": "Выберете мод слева, и он появится тут.",
            },
        }
        if lang in self.strings.keys():
            if string_id in self.strings[lang].keys():
                return self.strings[lang][string_id]

        print(f"Non-existing id {string_id}")
        return string_id

# OTHER
    def about(self):
        QtWidgets.QMessageBox.about(
            self,
            self.get_string("about", settings["lang"]),
            self.get_string("aboutText", settings["lang"])
        )

    def unzip(self, bytes_, path):
        try:
            with zipfile.ZipFile(io.BytesIO(bytes_)) as zf:
                zf.extractall(path)
        except:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText(traceback.format_exc())
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.exec()

    def set_status(self, data):
        if isinstance(data, int):
            self.ui.progressBar.setValue(data)
        elif isinstance(data, str):
            self.ui.pushButton.setText(data)

    def download_file(self, url):
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')
        file = b""

        if total_length is None:
            file += response.content
        else:
            dl = 0
            total_length = int(total_length)
            self.ui.progressBar.setMaximum(total_length)
            for data in response.iter_content(chunk_size=65536):
                app.processEvents()
                dl += len(data)
                file += data
                self.ui.progressBar.setValue(dl)

        self.ui.progressBar.setMaximum(100)
        self.ui.progressBar.setValue(100)

        return file

    def browse_path(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(caption=self.get_string("selectFolder", settings["lang"]))
        if folder:
            settings["path"] = self.end_if_not(folder, "/")
            self.save_settings()
            self.ui.lineEdit.setText(folder)
            self.recheck()

    def end_if_not(self, string, ending):
        return string if string.endswith(ending) else string + ending

    def save_settings(self):
        with open("settings.json", "w") as f:
            f.write(json.dumps(settings))

    def delete_duplicates(self, array):
        res = []
        for i in array:
            if i not in res:
                res.append(i)
        return res

    def recheck_status(self):
        return os.path.isdir(settings["path"]) and os.path.isfile(settings["path"] + "GeometryDash.exe")

    def create_dir_if_nexist(self, path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = DeoxidyzedLauncher()
    window.show()

    sys.exit(app.exec())
