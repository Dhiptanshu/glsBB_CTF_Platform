from app import app, db
import os

with app.app_context():
    db.drop_all()
    print("Dropped all tables.")
    db.create_all()
    print("Created new tables.")
    
    # Trigger the seed logic which is in the `if __name__ == '__main__':` block of app.py
    # Since we can't easily trigger that block from outside without running the server,
    # I'll just copy the seed logic here to be absolutely sure.
    
    from models import Category, Challenge
    
    # Create Categories
    cats = ['Welcome', 'Website', 'Cryptography', 'Steganography', 'Forensics', 'OSINT']
    category_objs = {}
    for c_name in cats:
        cat = Category(name=c_name)
        db.session.add(cat)
        category_objs[c_name] = cat
    db.session.commit()
    
    # Re-fetch ids
    for c_name in cats:
         category_objs[c_name] = Category.query.filter_by(name=c_name).first()

    # 1. Welcome Flag (Separate Category, 50 pts)
    welcome_chal = Challenge(
        category_id=category_objs['Welcome'].id,
        title="Welcome Challenge",
        description="Welcome to GLS BB! Read the rules and submit the flag.",
        flag="flag{w3lc0me_to_c7bersh@de2}", 
        points=50
    )
    db.session.add(welcome_chal)

    # 2. Website Category Chain
    # Challenge A (Start)
    web1 = Challenge(
        category_id=category_objs['Website'].id,
        title="HTML Inspector",
        description="Inspect the element to find the hidden comment.",
        free_hint="There is a hidden clue in the HTML source code.",
        flag="flag{html_1nsp3ct0r}",
        points=20,
        hint="Try right-clicking and viewing source, or use F12 developer tools.",
        hint_cost=5
    )
    db.session.add(web1)
    db.session.commit() # Commit to get ID for chaining

    # Challenge B (Locked by A)
    web2 = Challenge(
        category_id=category_objs['Website'].id,
        title="The Next Step",
        description="Good job on the first one. This one is locked until you solve the first.",
        flag="flag{ch@1n3d_succ3ss}",
        points=30,
        prerequisite_id=web1.id
    )
    db.session.add(web2)

    # Other Categories
    crypto1 = Challenge(
        category_id=category_objs['Cryptography'].id,
        title="Caesar's Salad",
        description="Decrypt this: Veni Vidi Vici",
        flag="flag{julius_caesar}",
        points=15
    )
    db.session.add(crypto1)

    steg1 = Challenge(
        category_id=category_objs['Steganography'].id,
        title="Hidden in Plain Sight",
        description="Look deeper into the image.",
        flag="flag{p1xel_p33per}",
        points=30
    )
    db.session.add(steg1)

    foren1 = Challenge(
        category_id=category_objs['Forensics'].id,
        title="Network Shark",
        description="Analyze the PCAP.",
        flag="flag{w1resh@rk_m@ster}",
        points=25
    )
    db.session.add(foren1)

    osint1 = Challenge(
        category_id=category_objs['OSINT'].id,
        title="Social Butterfly",
        description="Find the location from the photo.",
        flag="flag{g30gu3ss3r}",
        points=10
    )
    db.session.add(osint1)

    db.session.commit()
    print("Database seeded successfully.")
