import sys
from PyQt5.QtWidgets import QApplication
from ftv.data.datastore import DataStore
from ftv.ui.main_window import FTApp

def main():
    app = QApplication(sys.argv)
    ds = DataStore()
    w = FTApp(ds)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
