"""
Created on Tue Jul 16 10:18:22 2019

@author: Ade
"""
import helpers
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import csv
import os
import glob
import datetime
from tempfile import NamedTemporaryFile
import shutil
from ast import literal_eval
from distutils.dir_util import copy_tree


class Root(Tk):
    def __init__(self):

        # Create root window
        super(Root, self).__init__()
        self.title("Search Data")
        self.minsize(640, 500)

        # Declare global variables
        global fileList, export_list, fils, filter_box_frames, open_nodes
        fileList = {}
        export_list = {}
        fils = {}
        filter_box_frames = []
        open_nodes = []

        # Create variables for filter and database csv
        self.fil_csv = helpers.filters()
        self.file_csv = helpers.DB(self.fil_csv)

        self.frame_setup()
        self.resultsList()


    ''' Initial setup, within frame setup '''

    def frame_setup(self):

        ''' Setup Frames in Root Window '''

        # Filter frame (contains filter widgets; top left)
        self.filter_frame = Frame(self)
        self.filter_frame.grid(column=0, row=0)
        # Setup filter widgets
        self.filter_widget_setup(self.filter_frame)

        # Button Frame (contains main buttons (ie. add, edit, etc; top right)
        button_frame = Frame(self)
        button_frame.grid(column=1, row=0)
        # Setup button widgets
        self.button_widget_setup(button_frame)

        # File Treeview Frame (displays files being searched through; bottom left)
        tree_frame = LabelFrame(self, text="Results", padx=5, pady=5)
        tree_frame.grid(column=0, row=1, columnspan=3, padx=10, pady=10, sticky='news')
        # Setup file tree widget
        self.file_tree_setup(tree_frame)

        # Export list frame (displays files to be exported)
        export_frame = LabelFrame(self, text="Export", padx=5, pady=5)
        export_frame.grid(column=3, row=1, padx=10, pady=10, sticky='news')
        # Setup Listbox widget
        self.export_list_setup(export_frame)

        # Top menu (options for filter and database access)
        self.menubar = Menu(self)
        # Setup menubar widget
        self.menubar_setup()

        # Right Click Menu
        self.popup_menu = Menu(self, tearoff=0)
        self.popupcmds()

        # Configure frames to resize
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.filter_frame.columnconfigure(0, weight=1)
        self.filter_frame.rowconfigure(0, weight=1)
        export_frame.columnconfigure(0, weight=1)
        export_frame.rowconfigure(1, weight=1)

        self.minsize(self.winfo_width(), self.winfo_height())
        self.config(menu=self.menubar)

    def filter_widget_setup(self, frame, mode='new'):
        # Add option boxes for each filter type in csv

        # Destroy all widgets if refreshing
        if mode == 'refresh':
            for frame_ in filter_box_frames:
                frame_.destroy()

        # Make all widgets
        grid = 0
        for fil, name in self.fil_csv.get_filters().items():
            cbFrame = LabelFrame(frame, text=fil)
            cbFrame.grid(row=grid // 3, column=grid % 3, padx=10, pady=10, sticky='nw')

            cb = ttk.Combobox(cbFrame, postcommand=lambda: self.update_filterbox())
            cb.set('All')
            cb.pack()

            fils.update({fil: cb})
            filter_box_frames.append(cbFrame)

            cb.bind('<<ComboboxSelected>>', self.selection)
            grid += 1

    def button_widget_setup(self, frame):
        # Add selected file(s) to export list
        add_export = Button(frame, text='Add', command=self.add_export)
        add_export.grid(column=0, row=0, padx=5, pady=5)

        # Remove selected file(s) from export list
        remove_export = Button(frame, text='Remove', command=self.remove_export)
        remove_export.grid(column=1, row=0, padx=5, pady=5)

        # Edit properties of selected file(s)
        self.edit_file = Button(frame, text='Edit tags', command=self.properties)
        self.edit_file.grid(column=0, row=2, columnspan=2, padx=5, pady=5, sticky='ew')

        # Clear export list
        clear_export = Button(frame, text='Clear Export List', command=self.clear_export_list)
        clear_export.grid(column=0, row=3, columnspan=2, padx=5, pady=5, sticky='ew')


    def file_tree_setup(self, frame):
        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")

        self.tree = ttk.Treeview(frame,
                     columns=("fullpath", "type", "date", "tags"),displaycolumns=["date", "tags"],
                     yscrollcommand=lambda f, l: self.autoscroll(vsb, f, l),
                     xscrollcommand=lambda f, l: self.autoscroll(hsb, f, l),
                     selectmode='extended')

        vsb['command'] = self.tree.yview
        hsb['command'] = self.tree.xview
        self.tree.heading("#0", text="Files", anchor='w')
        self.tree.heading("date", text="Date", anchor='w')
        self.tree.heading("tags", text="Tags", anchor='w')
        self.tree.column("date", stretch=0, width=200)

        self.tree.bind('<<TreeviewOpen>>', self.update_tree)
        self.tree.bind('<Button-3>', self.right_click)

        self.tree.grid(column=0, row=0, sticky='nswe')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')

    def autoscroll(self, sbar, first, last):
        """Hide and show scrollbar as needed."""
        first, last = float(first), float(last)
        if first <= 0 and last >= 1:
            sbar.grid_remove()
        else:
            sbar.grid()
        sbar.set(first, last)

    def export_list_setup(self, frame):
        self.export_box = Listbox(frame, selectmode='extended')
        self.export_box.grid(column=0, row=0, stick='news')
        self.export_box.config(width=0, height=0)

        # Export list to .txt file
        self.export = Button(frame, text="Export .txt", command=self.export_as_text)
        self.export.grid(sticky='ews')

        # Export list to temporary folder
        self.exportFolder = Button(frame, text="Export Folder", command=self.export_as_folder)
        self.exportFolder.grid(sticky='ews')

    def menubar_setup(self):
        filtermenu = Menu(self.menubar, tearoff=0)
        filtermenu.add_command(label='Add filter', command=self.add_filter_window)
        filtermenu.add_command(label='Remove filter', command=self.remove_filter_window)
        filtermenu.add_command(label='Autosort Files', command=self.autosort_window)
        self.menubar.add_cascade(label='Filter', menu=filtermenu)

        dbmenu = Menu(self.menubar, tearoff=0)
        dbmenu.add_command(label="Update", command=self.update_database_refresh)
        self.menubar.add_cascade(label="Database", menu=dbmenu)

    def popupcmds(self):
        self.popup_menu.add_command(label="Add to export list", command=self.add_export)
        self.popup_menu.add_command(label="Properties", command=self.properties)


    ''' Update Functions '''

    def update_filterbox(self):
        # Updates filter options when box is expanded
        lstDict = self.fil_csv.get_filters()
        for fil, box in fils.items():
            lst = lstDict[fil]
            lst.insert(0, 'All')
            box['values'] = lst

    def update_database_refresh(self):
        self.file_csv.updateDB()
        self.refresh()

    ''' Button Functions '''

    def clear_export_list(self):
        # clear export listbox
        export_list.clear()
        self.export_box.delete(0, END)

    def add_export(self):
        # add file(s) to export list
        current_items = self.tree.selection()

        for ID in current_items:
            if ID in export_list.keys():
                pass
            else:  # not in list -- add
                export_list.update({ID: self.tree.item(ID, 'text')})
                self.export_box.insert(END, self.tree.item(ID, 'text'))

    def remove_export(self):
        # remove selected file(s) from export list
        current_items = self.export_box.curselection()
        for i in current_items[::-1]:
            del export_list[list(export_list.keys())[list(export_list.values()).index(self.export_box.get(0, END)[i])]]
            self.export_box.delete(i)

    def export_as_folder(self):
        # create temporary folder with copy of files in export list

        # if temporary folder already exists remove it
        path = os.path.dirname(os.path.abspath('.')) + '/temp_folder'
        if os.path.exists(path):
            shutil.rmtree(path)

        #  create new temporary folder
        os.mkdir(path)

        # move files from export list to array
        files = []
        dirs = []
        for node, fn in export_list.items():
            if self.tree.set(node, 'type') == 'directory':
                dirs.append(self.tree.item(node, 'values')[0])
            elif self.tree.set(node, 'type') == 'file':
                files.append(self.tree.item(node, 'values')[0])

        # fill temp folder with files from export list
        for f in files:
            shutil.copy(f, path)
        for d in dirs:
            copy_tree(d, path)

    def export_as_text(self):
        # export list in a .txt file
        file = os.path.dirname(os.path.abspath('.')) + '/file_export.txt'
        with open(file, 'w') as f:
            for node, val in export_list.items():
                if self.tree.set(node, 'type') == 'directory':
                    for root, dirs, files in os.walk(self.tree.item(node, 'values')[0]):
                        for name in files:
                            fn = os.path.join(root, name).replace('\\','/')
                            dt = str(datetime.datetime.fromtimestamp(os.stat(os.path.join(fn)).st_mtime))
                            tgs = str(self.file_csv.get_tags(fn))
                            fn_string = '\"' + fn + ', ' + dt + ', ' + tgs + '\",\n'
                            f.write(fn_string)
                elif self.tree.set(node, 'type') == 'file':
                    fn = self.tree.item(node, 'values')[0]
                    dt = self.tree.item(node, 'values')[2]
                    tgs = self.tree.item(node, 'values')[3]
                    fn_string = '\"' + fn + ', ' + dt + ', ' + tgs + '\",\n'
                    f.write(fn_string)


    ''' Menu Bar Functions '''

    def update_filcb(self, box, val_list):
        val_list.insert(0, 'All')
        box['values'] = val_list

    def fil_select(self, box, box2, fil_dict):
        if box.get() == 'All':
            box2['values'] = ['']
        else:
            box2['values'] = fil_dict[box.get()]

    def remove_filter(self, t, n, win):
        if t.get() == 'All' or n.get() == 'None':
            # error
            messagebox.showwarning('Remove Filter', 'No Filter Selected')
        else:
            tmp = messagebox.askokcancel(title="Delete filter", message="Delete filter and associated tags?")
            if tmp:
                # remove from filter csv
                self.fil_csv.remove(t.get(), n.get())

                # remove tag from associated files
                self.file_csv.remove_all_tag(t.get(), n.get())

                # check whether filter type still exists in filter csv
                exst = False
                for ftype, fname in self.fil_csv.get_filters().items():
                    if t.get() == ftype:
                        exst = True
                if not exst:
                    # remove combobox from global variable
                    del fils[t.get()]

                self.refresh()
                win.destroy()

    def remove_filter_window(self):
        # Remove filter from csv
        window = Toplevel(self)
        window.title("Remove Filters")

        fil_object = self.fil_csv.get_filters()

        cb_type = ttk.Combobox(window, postcommand=lambda: self.update_filcb(cb_type, list(fil_object.keys())))
        cb_type.set('All')
        cb_type.pack(padx=10, pady=10)

        cb_name = ttk.Combobox(window, postcommand=lambda: self.fil_select(cb_type, cb_name, fil_object))
        cb_name.set('None')
        cb_name.pack(padx=10, pady=10)

        remove = Button(window, text="Remove", command=lambda: self.remove_filter(cb_type, cb_name, window))
        remove.pack(padx=10, pady=10)

    def add_filter(self, type_entry, name_entry, window):
        self.fil_csv.add(type_entry, name_entry)
        # Adds new filter to csv, refreshes main window, and deletes add filter window
        self.refresh()
        window.destroy()

    def add_filter_window(self):
        # Add new filter to csv
        window = Toplevel(self)
        window.title("Add Filters")

        typeFil = LabelFrame(window, text="Type (ex. Batch, Processing)")
        typeFil.grid(row=0, column=0, padx=10, pady=10)

        typeEntry = Entry(typeFil)
        typeEntry.pack(padx=10, pady=10)

        typeEntry.delete(0, END)

        nameFil = LabelFrame(window, text="Name ((ex. mf4o4, Processed)")
        nameFil.grid(row=1, column=0, padx=10, pady=10)

        nameEntry = Entry(nameFil)
        nameEntry.pack(padx=10,pady=10)

        nameEntry.delete(0, END)

        add = Button(window, text="Add", command=lambda: self.add_filter(typeEntry.get(), nameEntry.get(), window))
        add.grid(row=2, column=1, padx=10, pady=10)

    def autosort(self, type_entry, name_entry, window):
        tempfile = NamedTemporaryFile(mode='w', delete=False, newline='')

        with open(self.file_csv.file, 'r') as csvfile, tempfile:
            reader = csv.DictReader(csvfile, fieldnames=self.file_csv.key_fieldnames)
            writer = csv.DictWriter(tempfile, fieldnames=self.file_csv.key_fieldnames)

            for row in reader:
                if name_entry in row['fullpath']:
                    new_tags = literal_eval(row['tags'])
                    new_tags.update({type_entry: name_entry})
                    writer.writerow({'fullpath': row['fullpath'], 'parent': row['parent'], 'filename': row['filename'], 'mod_date': row['mod_date'], 'tags': new_tags})
                else:
                    writer.writerow({'fullpath': row['fullpath'], 'parent': row['parent'], 'filename': row['filename'], 'mod_date': row['mod_date'], 'tags': row['tags']})

        # ask if sure
        tmp = messagebox.askokcancel(title="Autosort", message="Autosorting will change tags on files with the selected filter string in the path")
        if tmp:
            shutil.move(tempfile.name, self.file_csv.file)
        window.destroy()

    def autosort_window(self):
        # open window to choose which filter to autosort
        window = Toplevel(self)
        window.title("Autosort Files")

        fil_object = self.fil_csv.get_filters()

        cb_type = ttk.Combobox(window, postcommand=lambda: self.update_filcb(cb_type, list(fil_object.keys())))
        cb_type.set('All')
        cb_type.pack(padx=10, pady=10)

        cb_name = ttk.Combobox(window, postcommand=lambda: self.fil_select(cb_type, cb_name, fil_object))
        cb_name.set('None')
        cb_name.pack(padx=10, pady=10)

        autosort = Button(window, text="Autosort", command=lambda: self.autosort(cb_type.get(), cb_name.get(), window))
        autosort.pack(padx=10, pady=10)

    ''' File Properties '''

    def properties(self):
        # Set up properties window
        window = Toplevel(self)
        window.title("Edit File Properties")

        fn = Label(window, text="Selected file(s) have the following tags: ")
        fn.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        filframe = LabelFrame(window, text="Properties")
        filframe.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nwes')

        # Get highlighted items
        currentItems = self.tree.selection()
        lblctr = 0

        multiple_tags = {}

        for ID in currentItems:
            if self.tree.set(ID, "type") == 'directory':  # fix rn it does nothing with folders
                break

            else:
                tags = self.get_tags_as_dict(ID)

                if len(tags) <= 0:
                    if lblctr == 0:
                        lbl = Label(filframe, text="No tags associated with this file")
                        lbl.pack(padx=10, pady=10)
                        lblctr += 1
                    pass
                else:
                    for tag_type, tag_name in tags.items():
                        if tag_type in multiple_tags:
                            if tag_name not in multiple_tags[tag_type]:
                                multiple_tags[tag_type].append(tag_name)
                        else:
                            multiple_tags[tag_type] = [tag_name]

                for tag_type, tag_name in multiple_tags.items():
                    tg_text = tag_type + ' : ' + ', '.join(tag_name)
                    lbl = Label(filframe, text=tg_text)
                    lbl.pack(padx=10, pady=10)



        newFil = Button(window, text="Add new tag", command=lambda: self.add_tags(currentItems))
        newFil.grid(row=0, column=0, padx=10, pady=10, sticky='nwse')

        editFil = Button(window, text="Remove tag", command=lambda: self.remove_tags(currentItems))
        editFil.grid(row=0, column=1, padx=10, pady=10, stick='nswe')

    def update_combobox(self, box, options):
        # updates combobox with most recent filter options
        options.insert(0, '')
        box['values'] = options

    def add_selected(self, filelist, t, n, win):
        if t.get() == 'All' or n.get() == 'None':
            messagebox.showwarning('Add Filter', 'No Filter Selected')
        else:
            tmp = messagebox.askyesno('Add Filters', 'Add tag to all selected files?')
            if tmp:
                for file in filelist:
                    self.file_csv.change_tags(file, {t.get():n.get()})
                self.refresh()
                win.destroy()

    def remove_selected(self, filelist, box, win):
        tmp = messagebox.askyesno('Remove Filters', 'Remove selected on all selected files?')
        if tmp:
            t = literal_eval(box.get())
            for file in filelist:
                self.file_csv.change_tags(file, t, mode='Remove')
            self.refresh()
            win.destroy()

    def add_tags(self, nodelist):
        window = Toplevel(self)
        window.title("Add tag")

        fil_object = self.fil_csv.get_filters()

        flist = []
        for node in nodelist:
            # if node is a directory add all files below to flist
            if self.tree.set(node, 'type') == 'directory':
                for root, dirs, files in os.walk(self.tree.item(node, 'values')[0]):
                    for name in files:
                        flist.append(os.path.join(root, name).replace('\\','/'))

            # if node is a file add to flist
            elif self.tree.set(node, 'type') == 'file':
                flist.append(self.tree.item(node, 'values')[0])

        # Show combobox widget with filter type options
        cb_type = ttk.Combobox(window, postcommand=lambda: self.update_filcb(cb_type, list(fil_object.keys())))
        cb_type.set('All')
        cb_type.pack(padx=10, pady=10)

        # Show combobox widget with filter name options (with specified filter type)
        cb_name = ttk.Combobox(window, postcommand=lambda: self.fil_select(cb_type, cb_name, fil_object))
        cb_name.set('None')
        cb_name.pack(padx=10, pady=10)

        # Apply selected filter type and name to selected file(s)
        apply = Button(window, text="Apply", command=lambda: self.add_selected(flist, cb_type, cb_name, window))
        apply.pack(padx=10, pady=10)

    def remove_tags(self, nodelist):
        window = Toplevel(self)
        window.title("Remove tag")

        flist = []
        tlist = []

        for node in nodelist:
            tags = {}

            # if node is a directory add all files below to flist, tags
            if self.tree.set(node, 'type') == 'directory':
                for root, dirs, files in os.walk(self.tree.item(node, 'values')[0]):
                    for name in files:
                        fn = os.path.join(root,name).replace('\\', '/')
                        flist.append(fn)
                        tags.update(self.file_csv.get_tags(fn))

            # if node is a file add filename and tags to flist, tags
            elif self.tree.set(node, 'type') == 'file':
                flist.append(self.tree.item(node, 'values')[0])
                tags = self.get_tags_as_dict(node)

            for key, val in tags.items():
                if {key:val} in tlist:
                    break
                else:
                    tlist.append({key:val})

        # Display combobox with current filters on selected items that can be removed
        cb_type = ttk.Combobox(window, postcommand=lambda: self.update_combobox(cb_type, tlist))
        cb_type.set('All')
        cb_type.pack(padx=10, pady=10)


        apply = Button(window, text="Remove", command=lambda: self.remove_selected(flist, cb_type, window))
        apply.pack(padx=10, pady=10)


    ''' Events '''

    def right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            # mouse pointer over item
            self.tree.selection_set(iid)
            try:
                self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
            finally:
                self.popup_menu.grab_release()
        else:
            pass

    def selection(self, event):
        self.resultsList()


    ''' Housekeeping Functions '''
    def clear(self):
        # clear file tree and fileList variable
        fileList.clear()
        self.tree.delete(*self.tree.get_children())

    def refresh(self):
        print('refresh')
        # Refresh current filters
        self.filter_widget_setup(self.filter_frame, mode='refresh')

        self.resultsList()

    def get_tags_as_dict(self, node):
        tags = '{' + self.tree.item(node, 'tags')[0] + '}'
        tags = literal_eval(tags)
        return tags

    ''' Tree Functions '''

    def populate_tree(self, tree, node):
        if tree.set(node, "type") != 'directory':
            return

        path = tree.set(node, "fullpath")
        tree.delete(*tree.get_children(node))

        parent = tree.parent(node)
        special_dirs = [] if parent else glob.glob('.') + glob.glob('..')

        for p in special_dirs + os.listdir(path):
            ptype = None

            p = os.path.join(path, p).replace('\\','/')
            inDict = False

            for key, value in fileList.items():
                if p in value:
                    inDict = True
                    break

            if inDict:
                if os.path.isdir(p): ptype = "directory"
                elif os.path.isfile(p): ptype = "file"

                fname = os.path.split(p)[1]
                id = tree.insert(node, "end", text=fname, values=[p, ptype])

                if ptype == 'directory':
                    if fname not in ('.', '..'):
                        tree.insert(id, 0, text="dummy")
                        tree.item(id, text=fname)
                elif ptype == 'file':
                    dt = datetime.datetime.fromtimestamp(os.stat(p).st_mtime)
                    tgs = self.file_csv.get_tags(p)
                    print(tgs)
                    tag_string = ''
                    ctr = 0
                    for i in list(tgs.values()):
                        tag_string = tag_string + i
                        ctr += 1
                        if ctr < len(list(tgs.values())):
                            tag_string = tag_string + ', '

                    # store tags as string (use self.get_tags_as_dict() to access tags)
                    tree.item(id, tags=str(tgs))
                    tree.set(id, "date", "%s" % dt)
                    tree.set(id, "tags", "%s" % tag_string)


    def populate_roots(self, tree):
        dir = self.file_csv.home_folder

        node = tree.insert('', 'end', text=dir, values=[dir, "directory"])
        self.populate_tree(tree, node)

    def update_tree(self, event):
        print('update tree')
        tree = event.widget
        self.populate_tree(tree, tree.focus())


    ''' Main Functions'''

    def resultsList(self):  # starts with all files in dictionary
        self.clear()

        #  Makes a list of file paths within search results
        dates = {}
        self.file_csv.find_file_filter(fils, fileList, dates)
        self.populate_roots(self.tree)



root = Root()
root.mainloop()
