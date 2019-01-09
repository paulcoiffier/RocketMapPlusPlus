# Configuration files

Configuration files can be used to organize server/scanner deployments.  Any long-form command-line argument can be specified in a configuration file.

##  Default file

The default configuration file is *config/config.ini* underneath the project home. However, this location can be changed by setting the environment variable POGOMAP_CONFIG or using the -cf or --config flag on the command line. In the event that both the environment variable and the command line argument exists, the command line value will take precedence. Note that all relative pathnames are relative to the current working directory (often, but not necessarily where runserver.py is located).

## Setting configuration key/value pairs

  For command line values that take a single value they can be specified as:

    keyname: value
    e.g.   host: 0.0.0.0

  For parameters that may be repeated:

    keyname: [ value1, value2, ...]
    e.g.   username: [ randomjoe, bonnieclyde ]

	*for usernames and passwords, the first username must correspond to the first password, and so on *

  For command line arguments that take no parameters:

    keyname: True
    e.g.   fixed-location: True


## Example config file

```
  location: seattle, wa
  gmaps-key: MyGmapsKeyGoesHereSomeLongString
```

  Running this config file as:

     python runserver.py -cf myconfig.seattle

  would be the same as running with the following command line:

     python runserver.py -l "seattle, wa" -k MyGmapsKeyGoesHereSomeLongString

## Shared config

If you run multiple instances, you can add settings to a shared configuration file rather than adding it to each unique instance configuration file individually. This is useful for settings that are always the same such as Google Maps API key, etc. It makes managing multiple instances easier: instead of having to change the hashing key in every configuration file every month, you only need to change it in the shared config file. Add the shared settings to your shared-config.ini and call the shared config from the command line using the `-scf` flag when you start your instance.

` python runserver.py -cf myconfig.ini -scf shared-config.ini`

Using `--shared-config` in a configuration file does not work.

Remember to remove old keys and any other settings from your normal configs that may cause conflicts. If you set a value like the Google Maps API key in both configuration files, the value set in the regular `-cf` configuration file takes precedence.

## Running multiple configs

   One common way of running multiple locations is to use two configuration files each with common or default database values, but with different location specs.

