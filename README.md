pip install -r requirements.txt

python backen\app.py

project/
├── app.py
├── templates/
│   ├── layout.html
│   └── auth/
│       ├── login.html
│       └── register.html
├── blueprints/
│   ├── __init__.py
│   ├── plans/
│   └── auth/           
│       ├── __init__.py
│       └── routes.py