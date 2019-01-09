# Common Questions and Answers

### Should I use this as a way to make money?

No, it is gross to charge people for maps when the information should be provided by Niantic! We do not endorse paid maps, which is why this platform is opensource.

### All Pokemon are set as ultra rare, what is going on?
We now use a dynamic rarity system to determine the rarity of pokemon, the rarity is calculated by what you scan so it unique to your area. The rarity is updated every hour so when you start an initial scan everything will probably say it is ultra rare for the first hour and then will adjust itself.

### Does dynamic rarity mean that all future pokemon will get a rarity automatically?
Yes.

### What do the spawn point colors mean?

* A **grey** dot represents a spawn point that is more than 5 minutes from spawning.
* A **light blue** dot represents a spawn point that will spawn in 5 minutes. **Light blue** changes to **dark blue** and finally into **purple** just before spawn time.
* A **green dot** represents a fresh spawn. This will transition to **yellow**, through **orange** and finally **red** (like a stop light) as it is about to despawn.

### Lures are 6 hours right now! Why is it saying they have already expired?

You need to add `-ldur 360` to change the lure assumption to 6 hours (360 minutes.)

### All pokemon disappear after only 1 minute, the map is broken!

One of Niantic's updates removed spawn timers from Pokémon (until there's little time left until they despawn).
Seeing 1-minute timers during initial scan is perfectly normal.

### What's the simplest command to start the map scanning?

./runserver.py -l LOCATION -k GOOGLEKEY
You must replace the values for LOCATION/GOOGLEKEY with your information.

### Nice, what other stuff can I use in the command line?

There is a list [here](http://rocketmap.readthedocs.io/en/develop/first-run/commandline.html) or a more up to date list can be found by running ./runserver.py -h

### Woah I added a ton of cool stuff and now my command line is massive, any way to shorten it?

It is a lot simplier to use a [config file](http://rocketmap.readthedocs.io/en/develop/first-run/configuration-files.html)

### How do I setup port forwarding?

[See this helpful guide](http://rocketmap.readthedocs.io/en/develop/extras/external.html)

### I edited my files/installed unfinished code and messed up, will you help me fix it?

No, the best course of action is to delete it all and start again, this time don't edit files unless you know what you are doing.

### I used a PR and now everything is messed up! HELP ME!

No, remove everything and start from scratch. A Pull Request is merged when it meets the standards of the project.

### “It’s acting like the location flag is missing.”

-l, never forget.

### I'm getting this error...

#### Python version

```
pip or python is not recognized as an internal or external command
```

[Python/pip has not been added to the environment](http://rocketmap.readthedocs.io/en/develop/extras/environment-variables-fix.html)

```.md
Exception, e <- Invalid syntax.
```

This error is caused by Python 3. The project requires python 2.7

#### Gcc missing

```
error: command 'gcc' failed with exit status 1

# - or -

[...]failed with error code 1 in /tmp/pip-build-k3oWzv/pycryptodomex/
```

Your OS is missing the `gcc` compiler library. For Debian, run `apt-get install build-essentials`. For Red Hat, run `yum groupinstall 'Development Tools'`

#### Database error

```
InternalError(1054, u"unknown column 'cp' in 'field list'") or similar
```

Only one instance can run when the database is being modified or upgraded. Run ***ONE*** instance of RM with `-cd` to wipe your database, then run ***ONE*** instance of RM (without `-cd`) to setup your database.

#### Certificate errors

```
Unable to retrieve altitude from Google APIs: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:579).
```

RedHat based distros (Fedora, CentOS) could have an old OpenSSL version that is not compatible to the latest `certifi` package, to fix it you need to:

```bash
pip uninstall certifi
pip install certifi==2015.4.28
```

Use `sudo` or `--user` if you are not using an account with root permission.

And remember that you should do this every time after updating the requirements of the project.

## I have more questions!

Please read all wiki pages relating to the specific function you are questioning. If it does not answer your question, join us on the [RocketMapPlusPlus Discord](https://discord.gg/ZZwzc4h). Before asking questions in #rm on Discord.
