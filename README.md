# elexio-api
A few python functions to pull and parse data from [Elexio's](https://www.elexio.com/) api. Documentation for this API can be found at https://wheatlandpca.elexiochms.com/api_documentation (login required)

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


### Build Status
[![Build Status](https://dev.azure.com/boonepeterg/elexio-api/_apis/build/status/boonepeter.elexio-api?branchName=master)](https://dev.azure.com/boonepeterg/elexio-api/_build/latest?definitionId=1&branchName=master)
