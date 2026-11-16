from app.database.connection import SessionLocal
from app.models.role import Role


DEFAULT_ROLES = [
    {
        "name": "Super Admin",
        "description": "Global administrator with full platform management permissions"
    },
    {
        "name": "Admin",
        "description": "Administrator with user management permissions"
    },
    {
        "name": "Security Analyst",
        "description": "Monitors security events and alerts"
    }
]


def seed_roles():
    db = SessionLocal()

    try:
        created_count = 0
        existing_count = 0

        for role_data in DEFAULT_ROLES:
            existing_role = db.query(Role).filter(
                Role.name == role_data["name"]
            ).first()

            if existing_role:
                print(f"Already exists: {existing_role.name} (ID: {existing_role.id})")
                existing_count += 1
                continue

            new_role = Role(
                name=role_data["name"],
                description=role_data["description"]
            )

            db.add(new_role)
            db.flush()

            print(f"Created: {new_role.name} (ID: {new_role.id})")
            created_count += 1

        db.commit()

        print("\n========== ROLE INITIALIZATION SUMMARY ==========")
        print(f"Created roles: {created_count}")
        print(f"Already existing: {existing_count}")
        print("Role initialization completed successfully!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()
