from app import app, db
from sqlalchemy import text

def remove_is_notified_column():
    with app.app_context():
        # Drop the is_notified column using text()
        db.session.execute(text('ALTER TABLE chat_message DROP COLUMN is_notified'))
        db.session.commit()
        print("Successfully removed is_notified column from chat_message table")

if __name__ == '__main__':
    remove_is_notified_column()