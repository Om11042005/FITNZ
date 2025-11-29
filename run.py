import importlib, os, sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from FITNZ import main as m
# setup database
try:
    m.db.setup_database()
except Exception as e:
    print('DB setup error:', e)
app = m.AppController()
app.mainloop()
