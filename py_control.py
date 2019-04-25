from app import app, db
from app.models import User, SavedScan


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'SavedScan': SavedScan}


if __name__ == "__main__":
    app.run()
