# main.py
# -*- coding: utf-8 -*-
import logging
logging.basicConfig(filename='app.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', encoding='utf-8')
import customtkinter as ctk
from ui import NovelGeneratorGUI

def main():
    app = ctk.CTk()
    gui = NovelGeneratorGUI(app)
    app.mainloop()

if __name__ == "__main__":
    main()
