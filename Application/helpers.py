"""
Created on Fri Aug  9 10:46:05 2019

@author: Ade
"""
import csv
from tkinter import messagebox
import shutil
from tempfile import NamedTemporaryFile
import os
import datetime
from ast import literal_eval


# access to filter csv (get_filters, add, remove)
class filters:
    def __init__(self, file='filters.csv'):
        self.file = file
        self.fieldnames = ['type', 'name']

        # test if the file exists
        try:
            with open(file, 'r') as csvfile:
                print("file exists")
        #  if it doesn't exist make one with correct headers
        except IOError:
            with open(file, 'w', newline='') as csvfile:
                csvwriter = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                csvwriter.writeheader()

    '''  Returns dict with filter types as keys and names as an array of values '''

    def get_filters(self):
        filterDict = {}
        with open(self.file, 'r', encoding='UTF-8', newline='') as csvfile:
            csvreader = csv.DictReader(csvfile, fieldnames=self.fieldnames, delimiter=',')
            next(csvreader, None)
            for row in csvreader:
                if row['type'] in filterDict:
                    filterDict[row['type']].append(row['name'])
                else:
                    filterDict[row['type']] = [row['name']]
        return(filterDict)

    ''' Add new filter to csv (return True if successfully added)'''

    def add(self, filter_type, filter_name):
        # check if entries are valid
        if len(filter_type) == 0 or len(filter_name) == 0:
            messagebox.showwarning("Title", "One or both entries is empty")

        # check if filter already exists within csv
        else:
            exst = False
            for key, val in self.get_filters().items():
                if filter_type == key and filter_name in val:
                    exst = True
                    messagebox.showinfo("Title", "Filter already exists")
                    break
            if not exst:
                with open(self.file, 'a+', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                    writer.writerow({'type': filter_type, 'name': filter_name})
#                 for key, val in self.get_filters().items():
#                     if filter_type == key and filter_name in val:
#                         return True


    ''' Remove selected filter and tags from files '''

    def remove(self, filter_type, filter_name):
        # check for valid entry
        if len(filter_type) == 0 or len(filter_name) == 0:
            messagebox.showwarning("Title", "One or both entries is empty")
        #  if valid entry
        else:
            tmp = messagebox.askokcancel(title="Remove Filter", message="The filter will be removed from all tagged files")
            if tmp:
                tempfile = NamedTemporaryFile(mode='w', delete=False)
                with open(self.file, 'r', newline='') as csvfile, tempfile:
                    reader = csv.DictReader(csvfile, fieldnames=self.fieldnames)
                    writer = csv.DictWriter(tempfile, fieldnames=self.fieldnames)
                    for row in reader:
                        if row['type'] == filter_type and row['name'] == filter_name:
                            pass
                        else:
                            writer.writerow({'type': row['type'], 'name': row['name']})
                shutil.move(tempfile.name, self.file)

#access to database csv (updateDB, get_tags, change_tags)
class DB:
    def __init__(self, filter_class, file='input.csv'):
        self.file = file
        self.key_fieldnames = ['fullpath', 'parent', 'filename', 'mod_date', 'tags']
        self.filter_fieldnames = filter_class.get_filters().keys()
        self.home_folder = os.path.dirname(os.path.abspath('..'))

        # test if the file exists
        try:
            with open(file, 'r') as csvfile:
                print("file exists")

        #  if it doesn't exist make one with correct headers
        except IOError:
            with open(file, 'w') as csvfile:
                csvwriter = csv.DictWriter(csvfile, fieldnames=self.key_fieldnames)
                csvwriter.writeheader()
                print("input created")

    ''' Add new files and delete old files that don't exist anymore '''


    def updateDB(self):
        dir =  self.home_folder # get current directory

        tmp = messagebox.askokcancel(title="Update Database", message="Update database, will remove files and tags that no longer exist")

        if tmp:
            #  create temporary write file
            temp_dict = {}

            # loop through files in system and add to temp dictionary
            for dirName, subdirList, fileList in os.walk(dir):
                for fname in fileList:
                    with open(self.file, 'r', newline='') as csvfile:
                        reader = csv.DictReader(csvfile, fieldnames=self.key_fieldnames)
                        #  check whether file in database
                        exst = False

                        #  if file exists in database already, keep the row
                        for row in reader:
                            if dirName == row['parent'] and fname == row['filename']:
                                exst = True
                                temp_dict.update({row['fullpath']:[row['parent'],row['filename'],row['mod_date'],row['tags']]})
                                break

                        # if file is not in database, add it
                        if not exst:
                            fullpth = dirName + "\\" + fname
                            fullpth = fullpth.replace("\\", "/")
                            mdate = datetime.datetime.fromtimestamp(os.stat(os.path.join(dirName, fname)).st_mtime)

                            temp_dict.update({fullpth: [dirName, fname, mdate, {}] })

        #  write temp dictionary to csv file
        with open(self.file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.key_fieldnames)
            writer.writeheader()

            for key, val in temp_dict.items():
                parent = val[0]
                filename = val[1]
                mod_date = val[2]
                tags = val[3]

                writer.writerow({'fullpath': fullpth,
                                     'parent': parent,
                                     'filename': filename,
                                     'mod_date': mod_date,
                                     'tags': tags})
        print("update success")

    def get_tags(self, filename):
        with open(self.file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, self.key_fieldnames)
            for row in reader:
                tags = {}
                if row['fullpath'].replace("\\", "/") == filename:
                    if not literal_eval(row['tags']):
                        return literal_eval(row['tags'])
                    else:
                        return tags

    def change_tags(self, filename, tag, mode='Add'):
        if mode == 'Add':
            tempfile = NamedTemporaryFile(mode='w', delete=False, newline='')
            with open(self.file, 'r', newline='') as csvfile, tempfile:
                reader = csv.DictReader(csvfile, fieldnames=self.key_fieldnames)
                writer = csv.DictWriter(tempfile, fieldnames=self.key_fieldnames)
                for row in reader:
                    if row['fullpath'].replace("\\", "/") == filename:
                        rowdict = literal_eval(row['tags'])
                        tag_type, tag_name = list(tag.items())[0]
                        r = rowdict
                        r.update({tag_type: tag_name})
                        writer.writerow({'fullpath': row['fullpath'], 'parent': row['parent'], 'filename': row['filename'], 'mod_date': row['mod_date'], 'tags': r})
                    else:
                        writer.writerow({'fullpath': row['fullpath'], 'parent': row['parent'], 'filename': row['filename'], 'mod_date': row['mod_date'], 'tags': row['tags']})
            shutil.move(tempfile.name, self.file)
        elif mode == 'Remove':
            tempfile = NamedTemporaryFile(mode='w', delete=False, newline='')
            with open(self.file, 'r', newline='') as csvfile, tempfile:
                reader = csv.DictReader(csvfile, fieldnames=self.key_fieldnames)
                writer = csv.DictWriter(tempfile, fieldnames=self.key_fieldnames)
                for row in reader:
                    if row['fullpath'].replace("\\", "/") == filename:
                        rowdict = literal_eval(row['tags'])
                        tag_type, tag_name = list(tag.items())[0]
                        if tag_type in rowdict and rowdict[tag_type] == tag_name:
                            r = rowdict
                            del r[tag_type]
                        else:
                            r = rowdict
                        writer.writerow({'fullpath': row['fullpath'], 'parent': row['parent'], 'filename': row['filename'], 'mod_date': row['mod_date'], 'tags': r})
                    else:
                        writer.writerow({'fullpath': row['fullpath'], 'parent': row['parent'], 'filename': row['filename'], 'mod_date': row['mod_date'], 'tags': row['tags']})
            shutil.move(tempfile.name, self.file)

    def find_file_filter(self, active_filters, file_dictionary, metadata_dictionary):
        with open(self.file, 'r') as csvfile:
            ctr = 0
            reader = csv.DictReader(csvfile, fieldnames=self.key_fieldnames, delimiter=',')
            reader.__next__()
            for row in reader:
                add = True
                # check each file for active tags
                for key, val in active_filters.items():
                    if val.get() != 'All':

                        # if file has no tags
                        if len(literal_eval(row['tags'])) == 0:
                            add = False
                            pass

                        # if file tags do not match active filters
                        elif key not in literal_eval(row['tags']).keys():
                            add = False
                            pass
                        elif val.get() != literal_eval(row['tags'])[key]:
                            add = False
                            pass


                if add:
                    fp = row['parent'] + "\\" + row['filename']
                    fp = fp.replace("\\", "/")
                    file_dictionary.update({ctr: fp})
                    metadata_dictionary.update({ctr: row['mod_date']})
                ctr += 1

    def remove_all_tag(self, tag_type, tag_name):
        tempfile = NamedTemporaryFile(mode='w', delete=False, newline='')
        with open(self.file, 'r') as csvfile, tempfile:
            reader = csv.DictReader(csvfile, fieldnames=self.key_fieldnames, delimiter=',')
            reader.__next__()
            writer = csv.DictWriter(tempfile, fieldnames=self.key_fieldnames)
            writer.writeheader()
            for row in reader:
                tags = literal_eval(row['tags'])
                if tag_type in tags.keys():
                    if tags[tag_type] == tag_name:
                        del tags[tag_type]
                        writer.writerow({'fullpath': row['fullpath'], 'parent': row['parent'], 'filename': row['filename'], 'mod_date': row['mod_date'], 'tags': tags})
                else:
                    writer.writerow({'fullpath': row['fullpath'], 'parent': row['parent'], 'filename': row['filename'], 'mod_date': row['mod_date'], 'tags': row['tags']})
        shutil.move(tempfile.name, self.file)


