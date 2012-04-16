Running Tests
=============

./manage.py test generator --settings=settings_dev

Running Locally
===============

./manage.py runserver --settings=settings_dev

Running on VM
=============

Should run unmodified on MAS VM with Python >= 2.4.

TODOs
=====

* Figure out where gadget.xml should be hosted, as well as gadget application
  code (JS, CSS, etc.)

* Endpoints for Contextual Gadget read message callbacks

* Centralized place for MAS apps to specify which Google features they require,
  otherwise their API dependencies will have to be hardcoded.

* Secure (AES?) centralized storage for API keys/secrets. Should work with NPM
  standalone, and MAS.
  
