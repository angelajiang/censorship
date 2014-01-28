import csv
import sqlite3
import helpers

def populate_db(dbpath, csvfilename, tablename):
    """Inserts subset of data from urllist csv file to db"""
    conn = sqlite3.connect(dbpath)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    with open(csvfilename, 'rb') as csvfile:
        urls = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in urls:
            #row[0], row[1], row[3]: area, url, category
            try:
                row[1] = helpers.remove_header(row[1], 'http://')
                row[1] = helpers.remove_header(row[1], 'https://')
                QUERY = 'insert into '+tablename+' values (?,?,?)'
                c.execute(QUERY, (row[0], row[1], row[3]))
                print row[0], row[1], row[3]
            except:
                print 'Error: Row was not ented into db!'
                print row
                pass

    conn.commit()
    conn.close()

def get_urls_by_area(dbpath, tablename, area):
    """Returns list of censored urls corresponding to a given area code"""
    conn = sqlite3.connect(dbpath)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    QUERY = 'select url from '+tablename+' where area=\''+area+'\';'
    urllist = [str(row[0]) for row in c.execute(QUERY)]

    conn.commit()
    conn.close()
    
    return urllist

if __name__ == '__main__':
    populate_db('urls.db', 'URLLists.csv', 'urllist')
    #get_urls_by_area('urls.db', 'urllist', 'glo')

