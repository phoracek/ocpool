# ocpool

Manage multiple instances of
[dev-scripts](https://github.com/openshift-metal3/dev-scripts) cluster on a
single machine. dev-scripts have to be configured with a pull-secret and
available in `~/dev-scripts`.

Run ocpool server:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```
