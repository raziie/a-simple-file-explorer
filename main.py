import math
from datetime import datetime
from tkinter import *
import os
import ctypes
import pathlib
import shutil
from tkinter import messagebox as mb
from ttkbootstrap import Style
from ttkbootstrap.constants import *


def convertDate(timestamp, event=None):
    date = datetime.utcfromtimestamp(timestamp)
    return date.strftime('%d   %b   %Y')


def convertSize(sizeBytes):
    if sizeBytes == 0:
        return "0B"
    sizeName = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(sizeBytes, 1024)))
    p = math.pow(1024, i)
    s = round(sizeBytes / p, 2)
    return "%s %s" % (s, sizeName[i])


def getSize(path):
    totalSize = 0
    if os.path.isfile(path):
        totalSize = os.path.getsize(path)
    else:
        for dirPath, dirNames, fileNames in os.walk(path):
            for file in fileNames:
                filePath = os.path.join(dirPath, file)
                if not os.path.islink(filePath):
                    totalSize += os.path.getsize(filePath)
    return convertSize(totalSize)


def getType(name):
    if '.' in name:
        theType = name.split('.')[1]
    else:
        theType = 'Folder'
    return theType


class App:
    def __init__(self):
        # make a Tkinter object
        self.root = Tk()
        self.customizeRoot()

        self.style = Style(theme='darkly')

        # new file or folder
        self.newFileName = StringVar(self.root, "NewFile.txt", 'new_name')
        Entry(self.root, textvariable=self.newFileName, width=30)

        self.searchFileName = StringVar(self.root, "search", 'to_search')

        self.currentPath = StringVar(self.root, name='currentPath', value=pathlib.Path.cwd())
        # Bind changes in this variable to the pathChange function
        self.currentPath.trace('w', self.pathChange)
        Entry(self.root, textvariable=self.currentPath).grid(sticky='NSEW', column=1, row=0, ipady=10, ipadx=10)

        self.icon = PhotoImage(file='folder_up.png')
        Button(self.root, text='Folder Up', image=self.icon, command=self.goBack).grid(sticky='NSEW', column=0, row=0)

        self.addShortcuts()

        # List of files and folder
        self.fileList = Listbox(self.root, font=("Arial", 12))
        self.customizeList()

        # List of recent files and folder
        self.recentList = Listbox(self.root, font=("Arial", 12))
        self.customizeRecent()
        self.recentPaths = {}

        # Menu
        self.menubar = Menu(self.root)
        self.themeMenu = Menu(self.menubar, tearoff=0)
        self.customizeMenu()
        self.customizeThemeMenu()

        # right click menu
        self.rightClickMenu = Menu(self.root, tearoff=0)
        self.customizeRightClickMenu()

        self.isCut = False
        self.isSorted = False

    def customizeRoot(self):
        # set a title for our file explorer main window
        self.root.title('File Explorer')
        # expand row and column
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.geometry("1000x800")

    def addShortcuts(self):
        self.root.bind("<Alt-Up>", self.goBack)
        self.root.bind("<Control-x>", self.cut)
        self.root.bind("<Control-c>", self.copy)
        self.root.bind("<Control-v>", self.paste)
        self.root.bind("<Delete>", self.delete)
        self.root.bind("<Control-r>", self.rename)
        self.root.bind("<Control-f>", self.searchPopUp)

    def customizeList(self):
        self.fileList.grid(sticky='NSEW', column=1, row=1, ipady=20, ipadx=20)
        # open by double click and enter
        self.fileList.bind('<Double-1>', self.changePathByClick)
        self.fileList.bind('<Return>', self.changePathByClick)

        self.fileList.bind('<Motion>', lambda e: self.changeBackground(e))

    def changeBackground(self, event):
        widget = event.widget
        index = widget.nearest(event.y)

        if self.style.theme.type == 'dark':
            selectedColor = 'primary'
            othersColor = 'dark'
        else:
            selectedColor = 'primary'
            othersColor = 'light'

        if 0 <= index < self.fileList.size():
            self.fileList.itemconfig(index, bg=self.style.colors.get(selectedColor))
            for itemIndex in range(0, self.fileList.size()):
                if itemIndex is not index:
                    self.fileList.itemconfig(itemIndex, bg=self.style.colors.get(othersColor))

    def customizeRecent(self):
        self.recentList.grid(sticky='NSEW', column=0, row=1)
        # open by double click and enter
        self.recentList.bind('<Double-1>', self.recentChangePathByClick)
        self.recentList.bind('<Return>', self.recentChangePathByClick)

    def customizeMenu(self):
        # Adding a new File button
        self.menubar.add_command(label="New", command=self.newPopup)
        # Adding sort button
        self.menubar.add_command(label="Sort", command=self.sortFilesAndFolders)
        # Adding search button
        self.menubar.add_command(label="Search", command=self.searchPopUp)
        self.menubar.add_cascade(label='Themes', menu=self.themeMenu)
        # Adding a quit button to the Menubar
        self.menubar.add_command(label="Quit", command=self.root.quit)
        self.root.config(menu=self.menubar)

    def customizeRightClickMenu(self):
        self.rightClickMenu.add_command(label="Cut", command=self.cut)
        self.rightClickMenu.add_command(label="Copy", command=self.copy)
        self.rightClickMenu.add_command(label="Paste", command=self.paste)
        self.rightClickMenu.add_command(label="Rename", command=self.rename)
        self.rightClickMenu.add_command(label="Delete", command=self.delete)
        self.rightClickMenu.add_command(label="Properties", command=self.displayProperties)
        self.fileList.bind('<Button-3>', self.rightClickPopup)

    def rightClickPopup(self, event):
        try:
            self.rightClickMenu.tk_popup(event.x_root, event.y_root)
        finally:
            self.rightClickMenu.grab_release()

    def customizeThemeMenu(self):
        self.themeMenu.add_command(label='Cosmo', command=lambda: self.changeTheme('cosmo'))
        self.themeMenu.add_command(label='Flatly', command=lambda: self.changeTheme('flatly'))
        self.themeMenu.add_command(label='Journal', command=lambda: self.changeTheme('journal'))
        self.themeMenu.add_command(label='Litera', command=lambda: self.changeTheme('litera'))
        self.themeMenu.add_command(label='Lumen', command=lambda: self.changeTheme('lumen'))
        self.themeMenu.add_command(label='Minty', command=lambda: self.changeTheme('minty'))
        self.themeMenu.add_command(label='Pulse', command=lambda: self.changeTheme('pulse'))
        self.themeMenu.add_command(label='Sandstone', command=lambda: self.changeTheme('sandstone'))
        self.themeMenu.add_command(label='United', command=lambda: self.changeTheme('united'))
        self.themeMenu.add_command(label='Yeti', command=lambda: self.changeTheme('yeti'))
        self.themeMenu.add_command(label='Morph', command=lambda: self.changeTheme('morph'))
        self.themeMenu.add_command(label='Simplex', command=lambda: self.changeTheme('simplex'))
        self.themeMenu.add_command(label='Cerculean', command=lambda: self.changeTheme('cerculean'))
        self.themeMenu.add_separator()
        self.themeMenu.add_command(label='Solar', command=lambda: self.changeTheme('solar'))
        self.themeMenu.add_command(label='Superhero', command=lambda: self.changeTheme('superhero'))
        self.themeMenu.add_command(label='Darkly', command=lambda: self.changeTheme('darkly'))
        self.themeMenu.add_command(label='Cyborg', command=lambda: self.changeTheme('cyborg'))
        self.themeMenu.add_command(label='Vapor', command=lambda: self.changeTheme('vapor'))

    def changeTheme(self, theme):
        self.style = Style(theme=theme)

    def themePopup(self, event):
        try:
            self.themeMenu.tk_popup(event.x_root, event.y_root)
        finally:
            self.themeMenu.grab_release()

    def pathChange(self, *event):
        # Get all Files and Folders from the given Directory
        directory = os.listdir(self.currentPath.get())

        # Clearing the list
        self.fileList.delete(0, END)

        # Inserting the files and directories into the list
        for file in directory:
            self.fileList.insert(0, file)

        if self.isSorted:
            self.sortFilesAndFolders()

    def changePathByClick(self, event=None):
        # Get clicked item.
        picked = self.fileList.get(self.fileList.curselection()[0])
        # get the complete path by joining the current path with the picked item
        path = os.path.join(self.currentPath.get(), picked)
        # Check if item is file, then open it
        if os.path.isfile(path):
            os.startfile(path)
        # Set new path, will trigger pathChange function.
        else:
            self.currentPath.set(path)

        # update recent list
        self.updateRecent(picked, path)

    def updateRecent(self, picked, path):
        if picked not in self.recentList.get(0, END):
            if self.recentList.size() > 10:
                del self.recentPaths[self.recentList.get(END)]
                self.recentList.delete(END)
            self.recentList.insert(0, picked)
            self.recentPaths[picked] = path

    def recentChangePathByClick(self, event=None):
        # Get clicked item.
        picked = self.recentList.get(self.recentList.curselection()[0])
        # get the complete path by joining the current path with the picked item
        path = self.recentPaths[picked]
        # Check if item is file, then open it
        if os.path.isfile(path):
            os.startfile(path)
        # Set new path, will trigger pathChange function.
        else:
            self.currentPath.set(path)

    def goBack(self, event=None):
        # get the new path
        newPath = pathlib.Path(self.currentPath.get()).parent
        # set it to currentPath
        self.currentPath.set(str(newPath))

    def newPopup(self):
        newWindow = Toplevel(self.root)
        newWindow.geometry("400x150")
        newWindow.resizable(False, False)
        newWindow.title("new file Window")
        newWindow.columnconfigure(0, weight=1)
        Label(newWindow, text='Enter File or Folder name', padx=50).grid()
        Entry(newWindow, textvariable=self.newFileName).grid(column=0, pady=5, sticky='NSEW')
        Button(newWindow, text="Create", command=lambda: self.newFileOrFolder(newWindow)).grid(pady=20, padx=100,
                                                                                               sticky='NSEW')

    def newFileOrFolder(self, newWindow):
        # check if it is a file name or a folder
        if len(self.newFileName.get().split('.')) != 1:
            open(os.path.join(self.currentPath.get(), self.newFileName.get()), 'w').close()
        else:
            os.mkdir(os.path.join(self.currentPath.get(), self.newFileName.get()))
        # destroy the top
        newWindow.destroy()
        self.pathChange()

    def copy(self, event=None):
        # Get clicked item.
        global fileToCopy
        global fileName
        fileName = self.fileList.get(self.fileList.curselection()[0])
        fileToCopy = os.path.join(self.currentPath.get(), fileName)

    def paste(self, event=None):
        directoryToPaste = os.path.join(self.currentPath.get(), fileName)
        # using the try-except method
        try:
            if self.isCut:
                # using the move() method of the shutil module to
                # move the cut file to the desired directory
                shutil.move(fileToCopy, directoryToPaste)
                # showing success message using the messagebox's showinfo() method
                mb.showinfo(title="File moved!", message="The selected file has been moved to the selected location.")
                self.isCut = False
            else:
                if os.path.isfile(fileToCopy):
                    # using the copy() method of the shutil module to
                    # paste the select file to the desired directory
                    shutil.copy(fileToCopy, directoryToPaste)
                else:
                    # using the copytree() method of the shutil module to
                    # paste the select folder to the desired directory
                    shutil.copytree(fileToCopy, directoryToPaste)
                # showing success message using the messagebox's showinfo() method
                mb.showinfo(title="File copied!", message="The selected file has been copied to the selected location.")
            self.pathChange()
        except:
            # using the showerror() method to display error
            mb.showerror(title="Error!", message="Selected file is unable to copy to the selected location. Please "
                                                 "try again!")

    def cut(self, event=None):
        self.copy()
        self.isCut = True

    def delete(self, event=None):
        # Get clicked item.
        toDelete = self.fileList.get(self.fileList.curselection()[0])
        toDeletePath = os.path.join(self.currentPath.get(), toDelete)

        # Check if item is file or folder
        if os.path.isfile(toDeletePath):
            # deleting the file using the remove() method of the os module
            os.remove(toDeletePath)
        else:
            # deleting the file using the rmdir() method of the os module
            shutil.rmtree(toDeletePath)
        # displaying the success message using the messagebox's showinfo() method
        mb.showinfo(title="File deleted!", message="The selected file has been deleted.")
        self.pathChange()

    # function to rename a file
    def rename(self, event=None):
        global enteredFileName
        enteredFileName = StringVar()

        # creating another window
        rename_window = Toplevel(self.root)
        # setting the title
        rename_window.title("Rename File")
        # setting the size and position of the window
        rename_window.geometry("300x150")
        # disabling the resizable option
        rename_window.resizable(False, False)

        # creating a label
        rename_label = Label(rename_window, text="Enter the new file name:", font=("verdana", "8"))
        # placing the label on the window
        rename_label.pack(pady=4)

        # creating an entry field
        rename_field = Entry(rename_window, width=26, textvariable=enteredFileName, relief=GROOVE,
                             font=("verdana", "10"))
        # placing the entry field on the window
        rename_field.pack(pady=4, padx=4)

        # creating a button
        submitButton = Button(rename_window, text="Submit", command=self.submitName, width=12, relief=GROOVE,
                              font=("verdana", "8"))
        # placing the button on the window
        submitButton.pack(pady=5)

    def submitName(self):
        # getting the entered name from the entry field
        renameName = enteredFileName.get()
        # setting the entry field to empty string
        enteredFileName.set("")

        currentName = self.fileList.get(self.fileList.curselection()[0])
        currentFilePath = os.path.join(self.currentPath.get(), currentName)
        newPath = os.path.join(self.currentPath.get(), renameName)

        # using the rename() method to rename the file
        os.rename(currentFilePath, newPath)
        # using the showinfo() method to display a message box to show the success message
        mb.showinfo(title="File Renamed!", message="The selected file has been renamed.")
        self.pathChange()

    def sortFilesAndFolders(self):
        self.isSorted = True
        temp_list = list(self.fileList.get(0, END))
        temp_list.sort(key=str.lower)
        # delete contents of present listbox
        self.fileList.delete(0, END)
        # load listbox with sorted data
        for item in temp_list:
            self.fileList.insert(END, item)

    def searchPopUp(self, event=None):
        global searchWindow
        searchWindow = Toplevel(self.root)
        searchWindow.geometry("400x180")
        searchWindow.resizable(False, False)
        searchWindow.title("Searching Window")
        searchWindow.columnconfigure(0, weight=1)
        Label(searchWindow, text='search box:').grid()
        Entry(searchWindow, textvariable=self.searchFileName).grid(column=0, pady=5, sticky='NSEW')
        Button(searchWindow, text="Search", command=self.search).grid(pady=5, sticky='NSEW')

    def search(self, event=None):
        self.fileList.delete(0, END)
        # This is to get the directory that the program is currently running in
        path = os.walk(os.path.dirname(os.path.realpath(__file__)))
        for root, dirs, files in path:
            for name in files:
                if name.startswith(self.searchFileName.get()):
                    self.fileList.insert(0, name)
        searchWindow.destroy()

    def displayProperties(self):
        name = self.fileList.get(self.fileList.curselection()[0])
        path = os.path.join(self.currentPath.get(), name)
        created = convertDate(os.path.getctime(path))
        lastModified = convertDate(os.path.getmtime(path))
        size = getSize(path)
        fileType = getType(name)

        propWindow = Toplevel(self.root)
        propWindow.geometry("800x250")
        propWindow.resizable(False, False)
        propWindow.title("Properties")
        propWindow.columnconfigure(0, weight=1)

        info = 'Location:\t\t' + str(path) + \
               '\n\nCreated:\t\t\t' + str(created) + \
               '\n\nLast Modified:\t\t' + str(lastModified) + \
               '\n\nSize:\t\t\t' + str(size) + \
               '\n\nType:\t\t\t' + fileType
        Label(propWindow, pady=10, padx=0, text=info, justify="left", font=("Arial", 10)).grid()
        Button(propWindow, text="OK", command=lambda: propWindow.destroy()).grid(pady=10, padx=100, sticky='NSEW')


if __name__ == "__main__":
    # Increase Dots Per inch so it looks sharper
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
    # Create an instance of app
    application = App()
    # Call the function so the list displays
    application.pathChange('')
    # run the main program
    application.root.mainloop()
