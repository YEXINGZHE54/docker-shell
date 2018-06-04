# How to clean images

* edit delete.py, set up host, port, user, password and how to filter repos and tags

* python3 delete.py

* copy delete-config.yaml to the host/container where registry serves

* /bin/registry garbage-collect  $path/to/delete-config.yaml 
