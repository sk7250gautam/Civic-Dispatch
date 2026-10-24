import os
from app import create_app
from app.seeds.demo_data import seed_database
from app.extensions import db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # Ensure database tables exist and are seeded for instant evaluation
        db.create_all()
        seed_database(reset=False)

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
