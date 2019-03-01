# Supervisord on Linux

## Assuming:

* You are running on Linux
* You have installed [supervisord](http://supervisord.org/)
* You have seen a shell prompt at least a few times in your life
* You have configured your stuff properly in `config.ini`
* You understand worker separation
* You can tie your own shoelaces

## The good stuff

cd into your root RocketMapPlusPlus folder. Then:

    cd contrib/supervisord/
    ./install-reinstall.sh

When this completes, you will have all the required files. (this copies itself and the required files so that there is no conflict when doing a `git pull`. Now we are going to edit your local copy of gen-workers.sh:

    cd ~/supervisor
    nano gen-workers.sh


In this file, change the variables needed to suit your situation. Below is a snippet of the variables:

    # Webserver Location
    initloc="Dallas, TX"

    # Variables
    directory='/path/to/your/runserver/directory/' # Path to the folder containing runserver.py **NOTICE THE TRAILING /**

You should now have a bunch of .ini files in `~/supervisor/hex1/`

You can now do:

    supervisord -c ~/supervisor/supervisord.conf

You should be able to see from the web as well at `http://localhost:5001` Read up on the supervisord link at the top if you want to understand more about supervisorctl and how to control from the web.
