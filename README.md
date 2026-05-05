# ultrasound-image-converter

## How to execute Python server:
1. Go to server-python directory
```
cd server-python
```
1. Create the environment
```
python3 -m venv -venv
```
2. init the environment
```
. .venv/bin/activate
```
3. Install Python requirements
```
pip install -r requirements.txt
```
4. Init server
```
flask --app controller.controller run
```