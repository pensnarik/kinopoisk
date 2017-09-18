#!/usr/bin/env python2

import os
import sys


class App():

    def run(self):
        print("Executing install script on database '%s'" % sys.argv[1])
        os.system('psql -f install.sql "%s" -v database=mdb' % sys.argv[1])


if __name__ == '__main__':
    app = App()
    app.run()
