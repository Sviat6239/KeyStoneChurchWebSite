from main import Session, Admin

def CreateDefaultAdmin():
    session = Session()
    admin = session.query(Admin).filter_by(login="superadmin").first()
    if admin:
        print("superadmin already exist!")
        session.close()
        return

    admin = Admin(login="superadmin")
    admin.set_password("123123")
    session.add(admin)
    session.commit()
    print("Default admin created!")
    session.close()    



CreateDefaultAdmin()
