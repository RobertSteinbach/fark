###!/usr/bin/python

# https://www.youtube.com/watch?v=IEEhzQoKtQU&t=373s   (check out threading for enhancement)



# pip install beautifulsoup4
# pip install requests
# pip install pyodbc

from datetime import datetime, timedelta
import time
import requests
# import sys
from bs4 import BeautifulSoup                    # to parse HTML
# import pyodbc                                    # for SQL Server
import sqlite3                                   # for SQLite3
import shutil                                    # to download pictures

##########################
# Initialize
##########################
get_url = ""                                                     #load this variable prior to each GET
fark_url = "https://www.fark.com"
fark_archive_url = "https://www.fark.com/archives/"
comments_url_prefix = "https://www.fark.com/comments/"
new_forum_count = 0  # keep track of how many new ones created
new_image_count = 0
days_back = 1           # how many days to go back

# SQL Server connection
#cnSQL = pyodbc.connect(
#    "Driver={ODBC Driver 17 for SQL Server};Server=ipaddress;Database=dbname;uid=userid;pwd=password")
#cursorSQL = cnSQL.cursor()

# Test SQLServer connection
#strSQL = "SELECT @@version;"
#cursorSQL.execute(strSQL)
#row = cursorSQL.fetchone()
#while row:
#    print(row[0])
#    row = cursorSQL.fetchone()

# Connect to SQLite3 database
dbcon = sqlite3.connect('./db/fark.db')
cursorSQL = dbcon.cursor()
print("SQLite3 database connected")




#####################################
# Sub Routines Go Here
#####################################
def persist_forums(url):                   # build a list of forums from the passed ULR (main page or an archive page)
    global new_forum_count

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    alist = soup.find_all("a")
    links = []
    for a in alist:
        try:
            if a['href'][:4] == "http":
                # print(a)
                if comments_url_prefix in a['href']:
                    links.append(a['href'])
        except:
            foo = "No href found in anchor tag."
            #print(foo, a)

    # get a list of urls that we want to ignore
    omit_urls = []
    sql = "select [value] from KeyValue where [key]='omit_url'; "
    cursorSQL.execute(sql)
    row = cursorSQL.fetchone()
    while row:
        # print(row[0])
        omit_urls.append(row[0])
        row = cursorSQL.fetchone()

    for link in omit_urls:
        #print(link)
        try:
            links.remove(link)
        except:
            foo = "link NOT found to remove"
            #print(foo, link)

    for link in links:
        # see if it exists
        sql = "select count('ForumId') from Forums where ForumURL='" + str(link) + "';"
        cursorSQL.execute(sql)
        if cursorSQL.fetchone()[0] == 0:   #if the count is zero, then add it to the database
            # print("Adding link to DB", link)
            sql = "insert into Forums (ForumURL) VALUES ('" + link + "');"
            cursorSQL.execute(sql)
            dbcon.commit()
            new_forum_count += 1
        else:
            foo = "Link already exists in DB"
            # print(foo, link)

    print("forums added to DB")

    return


def persist_images():
    global new_image_count

    # Make a list of forums to scan through, where scan_date less than a week or so
    from_date = str(datetime.now() - timedelta(days=days_back))
    sql = "select ForumID, ForumURL FROM Forums WHERE ForumDate >='" + from_date + "';"
    cursorSQL.execute(sql)
    forums = cursorSQL.fetchall()

    # Make a list of images that have already been logged.  Will skip through these.
    sql = "select I.ImageURL from Forums F, Images I, ForumImages X "\
          + "where F.ForumId = X.ForumId and X.ImageId = I.ImageId and F.ForumDate > '" + from_date + "';"
    cursorSQL.execute(sql)
    images_existing = cursorSQL.fetchall()

    # for each forum....
    for forum in forums:
        forum_id = forum[0]
        forum_url = forum[1]
        forum_name = forum_url[forum_url.rfind("/")+1:]
        print("...", forum_name)
        response = requests.get(forum_url)
        soup = BeautifulSoup(response.text, "html.parser")

        for img in soup.find_all("img"):
            # print(img)

            try:
                # image_url = (img['data-origsrc'])
                image_url = (img['data-src'])    # this one seems to work better
                # print("!!!!!", image_url)
            except:
                continue            # not an image with the data-src tag

            # see if the image url has already been logged; saves a trip to the database
            if image_url in images_existing:
                continue

            # if here, then we need to log it into the images and/or forumImages table(s)

            # double-check if in Images
            sql = "select count(ImageId) from Images where ImageURL='" + image_url + "';"
            cursorSQL.execute(sql)
            if cursorSQL.fetchone()[0] == 0:  # if the count is zero, then add it to the database
                sql = "insert into Images (ImageURL) VALUES ('" + image_url + "');"
                cursorSQL.execute(sql)
                dbcon.commit()
                new_image_count += 1

            # Get the image_id from the database (may or may not have just inserted it)
            sql = "select ImageID from Images where ImageURL='" + image_url + "';"
            cursorSQL.execute(sql)
            image_id = cursorSQL.fetchone()[0]
            # print('image_id=', image_id)

            # see if the image/forum combination has been logged
            sql = "select count(ImageId) from ForumImages where ForumId=" + str(forum_id) \
                  + " AND ImageId=" + str(image_id) + ";"
            cursorSQL.execute(sql)
            if cursorSQL.fetchone()[0] == 0:  # if the count is zero, then add it to the database
                sql = "insert into ForumImages (ForumId, ImageId) VALUES (" + str(forum_id) + "," + str(image_id) + ");"
                cursorSQL.execute(sql)
                dbcon.commit()

    # quit()
    return


def download_images():

    # sql = "select top 1000 ImageURL from Images where ImagePath is NULL"          # SQL Server
    sql = "select ImageURL from Images where ImagePath is NULL LIMIT 1000"          # SQLite3

    cursorSQL.execute(sql)
    images = cursorSQL.fetchall()
    for image in images:
        image_url = image[0]
        #print(image_url)
        name = image_url[image_url.rfind("/")+1:]       # take everything right of the last slash
        name = name[0: name.find("?")]      # take everything left of the ?
        print("saving picture:", name)
        r = requests.get(image_url, stream=True)
        if r.status_code == 200:
            r.raw.decode_content = True
            f = open("./pics/" + name, "wb")
            shutil.copyfileobj(r.raw, f)
            f.close()
            sql = "update images set ImagePath='" + name + "' where ImageURL='" + image_url + "';"
        else:
            sql = "update images set ImagePath='" + name + "' where ImageURL='Error rc=" + str(r.status_code) + "';"
        cursorSQL.execute(sql)
        dbcon.commit()



    return


def looper():

    while True:

        download_images()    # Go download up to 1000 images (from a previous run)

        persist_forums(fark_url)    # build the list of forums off the main page

        persist_images()    # scan through recent forums and persist pictures to later download

        download_images()    # Go download up to 1000 images


        #break   # just one time

        # sleep for a while
        print('sleeping....')
        time.sleep(3600)

    return

##############################
# Main
###############################


looper()            #go into the infite loop
