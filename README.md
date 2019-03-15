# elexio-api
A few python functions to pull and parse data from [Elexio's](https://www.elexio.com/) api.

### Install
```consol
pip install elexio-api
```

### Usage
```python
import elexio_api

id = elexio_api.get_session_id()

elexio_api.download_all(id)
elexio_api.get_pdf_of_user(id, user_id=1149)
```
