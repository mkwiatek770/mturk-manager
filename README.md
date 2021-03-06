# MTurk Manager
This repository houses a web server which is able to completely replace the requester site web page of Mechanical Turk.

The user is able to manage projects, upload batches, create different templates for better reviewing the results and many more.

The instructions of how to write that file can be found in the 'Documentation' page inside of the tool.  

The whole tool is built on top of the [Django-Framework](https://www.djangoproject.com/).  

## Requirements
* Python 3.5+

## Installation
**Note:** If you want to use a virtual environment like `virtualenv` switch to the virtual environment before executing the following step(s)!

1. run `setup.sh`

## Quickstart
1. run `cd mturk`
2. run `python manage.py runserver` to start the server _([more](https://docs.djangoproject.com/en/2.0/ref/django-admin/#django-admin-runserver) on how to start a django server)_
3. visit [localhost:8000](http://localhost:8000)

## Supported Features
* create and manage mechanical turk projects
* define **multiple** worker templates per project
* customize the layout of the worker results
* extensive approve/reject facility

## Upcoming Features
* filter and download the hit results as json or csv

## Contributors
* Kristof Komlossy
* Martin Potthast
* Matthias Hagen

## Contact
Did you find a bug or do you have questions/requests?  
Write me a mail: kristof.komlossy@uni-weimar.de