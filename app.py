"""
GLS Bug Bounty Platform

Copyright (C) 2026 Dhiptanshu Malik

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See the LICENSE file for details.
"""
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from models import db, User, Category, Challenge, Solve, HintUnlock, GlobalSetting

from sqlalchemy import event

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Enable Write-Ahead Logging (WAL) for better concurrency
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    with app.app_context():
        @event.listens_for(db.engine, 'connect')
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_setting(key, default=None):
    setting = GlobalSetting.query.filter_by(key=key).first()
    return setting.value if setting else default

def set_setting(key, value):
    setting = GlobalSetting.query.filter_by(key=key).first()
    if not setting:
        setting = GlobalSetting(key=key, value=value)
        db.session.add(setting)
    else:
        setting.value = value
    db.session.commit()

@app.context_processor
def inject_global_settings():
    return dict(leaderboard_visible=get_setting('leaderboard_visible', 'true') == 'true')

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Fetch all categories and challenges
    categories = Category.query.all()
    # Challenges might need to be filtered or processed for visibility based on prerequisites
    # For now, pass them all and let the template or frontend handle logic, or process here.
    # To properly handle chaining, we should probably check what the user has solved.
    
    # Find the welcome challenge to display prominently
    welcome_challenge = Challenge.query.filter_by(flag="flag{w3lc0me_to_c7bersh@de2}").first()
    
    user_solves = [s.challenge_id for s in current_user.solves]
    user_hint_unlocks = [h.challenge_id for h in current_user.hint_unlocks]

    challenges_data = {}
    for cat in categories:
        if cat.name == 'Welcome':
            continue
            
        challenges_data[cat.name] = []
        # Sort by order_index, then ID
        sorted_challenges = sorted(cat.challenges, key=lambda c: (c.order_index, c.id))
        for chal in sorted_challenges:
            is_solved = chal.id in user_solves
            is_locked = False
            if chal.prerequisite_id:
                if chal.prerequisite_id not in user_solves:
                    is_locked = True
            
            # Admins see everything as unlocked
            if current_user.role == 'admin':
                is_locked = False

            challenges_data[cat.name].append({
                'id': chal.id,
                'title': chal.title,
                'description': chal.description,
                'points': chal.points,
                'solved': is_solved,
                'locked': is_locked,
                'prerequisite_id': chal.prerequisite_id,
                'free_hint': chal.free_hint,
                'hint': chal.hint,
                'hint_cost': chal.hint_cost,
                'hint_unlocked': chal.id in user_hint_unlocks
            })

    # specific check for welcome challenge solved status
    welcome_data = None
    if welcome_challenge:
        welcome_data = {
            'id': welcome_challenge.id,
            'title': welcome_challenge.title,
            'description': welcome_challenge.description,
            'points': welcome_challenge.points,
            'solved': welcome_challenge.id in user_solves,
            'flag': welcome_challenge.flag # Passing flag specifically for "sanity check" visual if needed, but safe not to.
        }

    return render_template('index.html', categories=categories, challenges=challenges_data, welcome_challenge=welcome_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password') # This is the EVENT PASSWORD
        
        # Admin Login Bypass or Specific Check
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(username=username, role='admin')
                db.session.add(user)
                db.session.commit()
            login_user(user)
            return redirect(url_for('admin_dashboard'))

        # Regular User Login
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            if user.is_banned:
                flash('This user has been banned.', 'danger')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid Username or Password (Mobile Number)', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/submit_flag', methods=['POST'])
@login_required
def submit_flag():
    if current_user.is_banned:
        return jsonify({'status': 'error', 'message': 'You are banned.'})

    data = request.json
    challenge_id = data.get('challenge_id')
    submitted_flag = data.get('flag')
    
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return jsonify({'status': 'error', 'message': 'Challenge not found'})
        
    # Check if already solved
    if Solve.query.filter_by(user_id=current_user.id, challenge_id=challenge.id).first():
        return jsonify({'status': 'info', 'message': 'Already solved!'})

    # Check prerequisite
    if challenge.prerequisite_id:
        if not Solve.query.filter_by(user_id=current_user.id, challenge_id=challenge.prerequisite_id).first():
             return jsonify({'status': 'error', 'message': 'Prerequisite not met'})

    if submitted_flag.strip() == challenge.flag.strip():
        solve = Solve(user_id=current_user.id, challenge_id=challenge.id)
        db.session.add(solve)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Correct Flag!', 'points': challenge.points})
    else:
        return jsonify({'status': 'error', 'message': 'Incorrect Flag'})

@app.route('/buy_hint', methods=['POST'])
@login_required
def buy_hint():
    if current_user.is_banned:
        return jsonify({'status': 'error', 'message': 'You are banned.'})

    data = request.json
    challenge_id = data.get('challenge_id')
    
    challenge = Challenge.query.get(challenge_id)
    if not challenge or not challenge.hint:
        return jsonify({'status': 'error', 'message': 'Hint not available'})
        
    # Check if already unlocked
    if HintUnlock.query.filter_by(user_id=current_user.id, challenge_id=challenge.id).first():
        return jsonify({'status': 'info', 'message': 'Hint already unlocked', 'hint': challenge.hint})

    # Check points (Optional: You can allow negative score or strictly enforce positive)
    # User said "buy with 25 points if available". 
    # Usually in CTFs, you can buy even if it makes your score negative, or you need current_score >= cost.
    # Let's enforce current_score >= cost for safety.
    if current_user.get_score() < challenge.hint_cost:
        return jsonify({'status': 'error', 'message': f'Not enough points! Need {challenge.hint_cost} pts.'})

    unlock = HintUnlock(user_id=current_user.id, challenge_id=challenge.id)
    db.session.add(unlock)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Hint Unlocked!', 'hint': challenge.hint, 'deducted': challenge.hint_cost})

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    categories = Category.query.all()
    categories = Category.query.all()
    # Fetch all users (including admins, so they can reset themselves)
    users = User.query.order_by(User.id).all()
    return render_template('admin.html', categories=categories, users=users)

@app.route('/admin/add_challenge', methods=['POST'])
@login_required
def add_challenge():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    description = request.form.get('description')
    free_hint = request.form.get('free_hint')
    flag = request.form.get('flag')
    points = request.form.get('points')
    prerequisite_id = request.form.get('prerequisite_id')
    hint = request.form.get('hint')
    hint_cost = request.form.get('hint_cost')
    
    if not prerequisite_id:
        prerequisite_id = None
    
    new_chal = Challenge(
        title=title,
        category_id=category_id,
        description=description,
        free_hint=free_hint,
        flag=flag,
        points=points,
        prerequisite_id=prerequisite_id,
        hint=hint,
        hint_cost=hint_cost if hint_cost else 25
    )
    
    db.session.add(new_chal)
    db.session.commit()
    
    flash('Challenge Added Successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_challenge/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def edit_challenge(challenge_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    chal = Challenge.query.get_or_404(challenge_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        chal.title = request.form.get('title')
        chal.category_id = request.form.get('category_id')
        chal.description = request.form.get('description')
        chal.free_hint = request.form.get('free_hint')
        chal.flag = request.form.get('flag')
        chal.points = request.form.get('points')
        chal.hint = request.form.get('hint')
        chal.hint_cost = request.form.get('hint_cost')
        
        prereq = request.form.get('prerequisite_id')
        chal.prerequisite_id = prereq if prereq else None
        
        db.session.commit()
        flash('Challenge Updated Successfully!', 'success')
        return redirect(url_for('index'))
        
    return render_template('edit_challenge.html', challenge=chal, categories=categories)

@app.route('/admin/delete_challenge/<int:challenge_id>', methods=['POST'])
@login_required
def delete_challenge(challenge_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    chal = Challenge.query.get_or_404(challenge_id)
    # Delete dependent records first
    Solve.query.filter_by(challenge_id=chal.id).delete()
    HintUnlock.query.filter_by(challenge_id=chal.id).delete()
    
    db.session.delete(chal)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Challenge Deleted'})

@app.route('/admin/reorder_challenges', methods=['POST'])
@login_required
def reorder_challenges():
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    order_list = data.get('order', [])
    
    try:
        for index, challenge_id in enumerate(order_list):
            chal = Challenge.query.get(int(challenge_id))
            if chal:
                chal.order_index = index
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Error saving order: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/ban_user/<int:user_id>', methods=['POST'])
@login_required
def ban_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_banned = True
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'User {user.username} has been banned.'})

@app.route('/admin/unban_user/<int:user_id>', methods=['POST'])
@login_required
def unban_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'User {user.username} has been unbanned.'})

@app.route('/admin/penalize_user/<int:user_id>', methods=['POST'])
@login_required
def penalize_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.penalty_points += 5
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'Applied 5 penalty points to {user.username}.'})

@app.route('/admin/reset_score/<int:user_id>', methods=['POST'])
@login_required
def reset_score(user_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Delete all solves
    Solve.query.filter_by(user_id=user.id).delete()
    # Delete all hint unlocks
    HintUnlock.query.filter_by(user_id=user.id).delete()
    # Reset penalty points
    user.penalty_points = 0
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'Score and progress cleared for {user.username}.'})

@app.route('/admin/add_category', methods=['POST'])
@login_required
def add_category():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    name = request.form.get('name')
    if name:
        if Category.query.filter_by(name=name).first():
            flash('Category already exists!', 'error')
        else:
            new_cat = Category(name=name)
            db.session.add(new_cat)
            db.session.commit()
            flash(f'Category {name} created!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_category', methods=['POST'])
@login_required
def update_category():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    category_id = request.form.get('category_id')
    name = request.form.get('name')
    url = request.form.get('url')
    
    category = Category.query.get(category_id)
    if category:
        if name:
            category.name = name
        if url is not None: # interactions with form can send empty string
            category.url = url
            
        db.session.commit()
        flash(f'Category updated!', 'success')
    else:
        flash('Category not found', 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    category = Category.query.get_or_404(category_id)
    
    # Check if category has challenges
    if category.challenges:
        flash(f'Cannot delete category "{category.name}" because it contains challenges. Delete challenges first.', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category.name}" deleted.', 'success')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_category_url/<int:category_id>', methods=['POST'])
@login_required
def update_category_url(category_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    url = data.get('url')
    
    cat = Category.query.get_or_404(category_id)
    cat.url = url
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'URL updated'})

@app.route('/admin/toggle_category_visibility/<int:category_id>', methods=['POST'])
@login_required
def toggle_category_visibility(category_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    cat = Category.query.get_or_404(category_id)
    # Toggle
    cat.is_public = not cat.is_public
    db.session.commit()
    
    status = "Public" if cat.is_public else "Private"
    return jsonify({'status': 'success', 'message': f'Category is now {status}', 'is_public': cat.is_public})

@app.route('/admin/set_all_categories_visibility', methods=['POST'])
@login_required
def set_all_categories_visibility():
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    visible = data.get('visible', False)
    
    try:
        categories = Category.query.all()
        for cat in categories:
            cat.is_public = visible
        db.session.commit()
        status = "Public" if visible else "Private"
        return jsonify({'status': 'success', 'message': f'All categories are now {status}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Leaderboard
@app.route('/leaderboard')
@login_required
def leaderboard():
    is_visible = get_setting('leaderboard_visible', 'false') == 'true'
    
    # Hide from non-admins if toggle is off
    if not is_visible and current_user.role != 'admin':
        flash('The leaderboard is currently hidden by the administrators.', 'info')
        return redirect(url_for('index'))

    users = User.query.filter_by(role='user', is_banned=False).all()
    # Sort by score descending, then by last solve time ascending (earlier is better)
    users.sort(key=lambda u: (-u.get_score(), u.get_last_solve_time()))
    return render_template('leaderboard.html', users=users, is_visible=is_visible)

@app.route('/admin/toggle_leaderboard', methods=['POST'])
@login_required
def toggle_leaderboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    current_state = get_setting('leaderboard_visible', 'false')
    new_state = 'false' if current_state == 'true' else 'true'
    set_setting('leaderboard_visible', new_state)
    
    return redirect(url_for('leaderboard'))

@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user_admin():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    username = request.form.get('username')
    password = request.form.get('password') # Mobile Number
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists!', 'error')
    else:
        new_user = User(username=username, password=password, role='user') # Default role user
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {username} registered successfully!', 'success')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete an admin user.', 'error')
        return redirect(url_for('admin_dashboard'))
        
    # Manual cascade delete
    Solve.query.filter_by(user_id=user.id).delete()
    HintUnlock.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create initial data if empty
        if not Category.query.first():
            # Create Categories
            # 'Welcome' is a hidden category for the welcome flag
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
                flag="flag{html_1nsp3ct0r}",
                points=20
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

    app.run(debug=True, port=5002)
