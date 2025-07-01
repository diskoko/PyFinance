from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

def init_db():
    """Initialize the SQLite database with financial goals and journal tables"""
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        # Keep existing journal table
        cursor.execute('''CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Add financial goals table
        cursor.execute('''CREATE TABLE IF NOT EXISTS financial_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            deadline TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Add transactions table for tracking progress
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,  -- 'deposit' or 'withdrawal'
            date TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY(goal_id) REFERENCES financial_goals(id)
        )''')
        
        # Add budget table for tracking monthly budgets
        cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            planned_amount REAL NOT NULL,
            spent_amount REAL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Add expenses table for detailed spending tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            budget_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(budget_id) REFERENCES budgets(id)
        )''')
        conn.commit()

@app.route('/')
def home():
    """Home page showing financial dashboard and journal"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        # Get financial goals (include transaction count and progress percent for consistency with goals page)
        cursor.execute("""
            SELECT g.*, 
                   (SELECT COUNT(*) FROM transactions WHERE goal_id = g.id) as transaction_count,
                   (g.current_amount / g.target_amount * 100) as progress_percent
            FROM financial_goals g
            ORDER BY deadline ASC
        """)
        goals = cursor.fetchall()
        # Calculate total balance from goals
        total_balance = sum(goal[3] for goal in goals)  # goal[3] is current_amount
        
        # Calculate goals completed and total for sidebar
        goals_total = len(goals)
        goals_completed = sum(1 for goal in goals if goal[3] >= goal[2])  # current >= target
        
        # Get recent transactions (show the 5 most recent, newest at the top)
        cursor.execute("""
            SELECT t.date, t.amount, t.type, g.name 
            FROM transactions t 
            JOIN financial_goals g ON t.goal_id = g.id 
            ORDER BY t.date DESC, t.id DESC LIMIT 5
        """)
        recent_transactions = cursor.fetchall()
        
        # Count recent activity (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE date >= date('now', '-7 days')
        """)
        recent_activity_count = cursor.fetchone()[0]
        
        # Get journal entries for calendar
        current_month = today[:7]
        cursor.execute("""
            SELECT DISTINCT strftime('%d', date) 
            FROM journal 
            WHERE strftime('%Y-%m', date) = ?
        """, (current_month,))
        days_with_entries = [int(day[0]) for day in cursor.fetchall()]
        
        # Get budget overview for dashboard
        cursor.execute("""
            SELECT b.category, b.planned_amount, 
                   COALESCE(SUM(e.amount), 0) as spent_amount,
                   (COALESCE(SUM(e.amount), 0) / b.planned_amount * 100) as spent_percent
            FROM budgets b
            LEFT JOIN expenses e ON b.id = e.budget_id 
            WHERE b.month = ?
            GROUP BY b.id, b.category, b.planned_amount
        """, (current_month,))
        budget_overview = cursor.fetchall()
        
        # Calculate budget status (average spending percentage across all categories)
        if budget_overview:
            budget_status = sum(budget[3] for budget in budget_overview) / len(budget_overview)
        else:
            budget_status = 0
        
        # Calculate total financial health score
        goal_score = (goals_completed / goals_total * 100) if goals_total > 0 else 0
        
        # Determine financial status for sidebar
        if goal_score >= 80 and budget_status <= 90:
            status_icon = "🔥"
            status_text = "On Fire!"
        elif goal_score >= 60 and budget_status <= 100:
            status_icon = "✨"
            status_text = "Looking Good"
        elif goal_score >= 40 or budget_status <= 120:
            status_icon = "👀"
            status_text = "Stay Focused"
        else:
            status_icon = "💀"
            status_text = "Need Help"
    
    return render_template('index.html',
                          goals=goals,
                          transactions=recent_transactions,
                          budget_overview=budget_overview,
                          goal_score=goal_score,
                          entry_days=days_with_entries,  # <-- pass to template
                          current_date=today,
                          total_balance=total_balance,
                          # New dynamic data for sidebar
                          goals_completed=goals_completed,
                          goals_total=goals_total,
                          budget_status=round(budget_status, 1),
                          recent_activity_count=recent_activity_count,
                          status_icon=status_icon,
                          status_text=status_text)

@app.route('/add_goal', methods=['GET', 'POST'])
def add_goal():
    """Add a new financial goal"""
    if request.method == 'POST':
        name = request.form['name']
        target_amount = float(request.form['target_amount'])
        deadline = request.form['deadline']
        category = request.form['category']
        description = request.form['description']
        
        with sqlite3.connect('finance.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO financial_goals 
                (name, target_amount, deadline, category, description)
                VALUES (?, ?, ?, ?, ?)
            """, (name, target_amount, deadline, category, description))
            conn.commit()
        
        return redirect(url_for('home'))
    
    return render_template('add_goal.html')

@app.route('/update_goal/<int:goal_id>', methods=['POST'])
def update_goal(goal_id):
    """Update progress on a financial goal"""
    amount = float(request.form['amount'])
    transaction_type = request.form['type']
    note = request.form.get('note', '')
    date = datetime.now().strftime('%Y-%m-%d')
    
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        # Add transaction
        cursor.execute("""
            INSERT INTO transactions (goal_id, amount, type, date, note)
            VALUES (?, ?, ?, ?, ?)
        """, (goal_id, amount, transaction_type, date, note))
        
        # Update goal progress
        if transaction_type == 'deposit':
            cursor.execute("""
                UPDATE financial_goals 
                SET current_amount = current_amount + ?
                WHERE id = ?
            """, (amount, goal_id))
        else:
            cursor.execute("""
                UPDATE financial_goals 
                SET current_amount = current_amount - ?
                WHERE id = ?
            """, (amount, goal_id))
        
        conn.commit()
    
    return jsonify({'success': True, 'message': 'Progress updated successfully'})

@app.route('/view_entries')
def view_entries():
    """Show all journal entries in a modern card layout"""
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, date, content, strftime('%d %b %Y', date) as formatted_date
            FROM journal 
            ORDER BY date DESC
        """)
        entries = cursor.fetchall()
    return render_template('view_entries.html', entries=entries)

@app.route('/add_entry', methods=['POST'])
def add_entry():
    """Add a new journal entry (AJAX/JSON response)"""
    try:
        title = request.form['title']
        content = request.form['content']
        date = request.form['date']
        with sqlite3.connect('finance.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO journal (title, content, date)
                VALUES (?, ?, ?)
            """, (title, content, date))
            conn.commit()
            entry_id = cursor.lastrowid
        # Format the date for display
        from datetime import datetime
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d %b %Y')
        # Always return JSON for AJAX requests
        return jsonify({
            'success': True,
            'id': entry_id,
            'title': title,
            'content': content,
            'date': date,
            'formatted_date': formatted_date
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/goals')
def view_goals():
    """View all financial goals and their progress, with sidebar stats"""
    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.*, 
                   (SELECT COUNT(*) FROM transactions WHERE goal_id = g.id) as transaction_count,
                   (g.current_amount / g.target_amount * 100) as progress_percent
            FROM financial_goals g
            ORDER BY deadline ASC
        """)
        goals = cursor.fetchall()
        total_balance = sum(goal[3] for goal in goals)
        goals_total = len(goals)
        goals_completed = sum(1 for goal in goals if goal[3] >= goal[2])
        # Get budget status for sidebar
        current_month = today[:7]
        cursor.execute("""
            SELECT b.category, b.planned_amount, 
                   COALESCE(SUM(e.amount), 0) as spent_amount,
                   (COALESCE(SUM(e.amount), 0) / b.planned_amount * 100) as spent_percent
            FROM budgets b
            LEFT JOIN expenses e ON b.id = e.budget_id 
            WHERE b.month = ?
            GROUP BY b.id, b.category, b.planned_amount
        """, (current_month,))
        budget_overview = cursor.fetchall()
        if budget_overview:
            budget_status = sum(budget[3] for budget in budget_overview) / len(budget_overview)
        else:
            budget_status = 0
        # Recent activity count for sidebar
        cursor.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE date >= date('now', '-7 days')
        """)
        recent_activity_count = cursor.fetchone()[0]
        # Sidebar status icon/text logic (reuse from home)
        goal_score = (goals_completed / goals_total * 100) if goals_total > 0 else 0
        if goal_score >= 80 and budget_status <= 90:
            status_icon = "🔥"
            status_text = "On Fire!"
        elif goal_score >= 60 and budget_status <= 100:
            status_icon = "✨"
            status_text = "Looking Good"
        elif goal_score >= 40 or budget_status <= 120:
            status_icon = "👀"
            status_text = "Stay Focused"
        else:
            status_icon = "💀"
            status_text = "Need Help"
    return render_template('goals.html', goals=goals, total_balance=total_balance,
                          goals_completed=goals_completed, goals_total=goals_total,
                          budget_status=round(budget_status, 1), recent_activity_count=recent_activity_count,
                          status_icon=status_icon, status_text=status_text)

@app.route('/journal')
def view_journal():
    """Show journal entries and calendar"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        # Get journal entries
        cursor.execute("""
            SELECT id, title, content, date, strftime('%d %b %Y', date) as formatted_date
            FROM journal 
            ORDER BY date DESC
        """)
        entries = cursor.fetchall()
        
        # Get days with entries for current month
        current_month = today[:7]
        cursor.execute("""
            SELECT DISTINCT strftime('%d', date) 
            FROM journal 
            WHERE strftime('%Y-%m', date) = ?
        """, (current_month,))
        days_with_entries = [int(day[0]) for day in cursor.fetchall()]
    
    return render_template('journal.html', 
                          entries=entries,
                          entry_days=days_with_entries,
                          days=range(1, 32),
                          current_date=today)

@app.route('/budget')
def view_budget():
    """View budget overview and spending tracking"""
    today = datetime.now().strftime('%Y-%m-%d')
    current_month = today[:7]
    
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        # Get budget categories with spending
        cursor.execute("""
            SELECT b.id, b.category, b.planned_amount, 
                   COALESCE(SUM(e.amount), 0) as spent_amount,
                   (COALESCE(SUM(e.amount), 0) / b.planned_amount * 100) as spent_percent
            FROM budgets b
            LEFT JOIN expenses e ON b.id = e.budget_id 
            WHERE b.month = ?
            GROUP BY b.id, b.category, b.planned_amount
        """, (current_month,))
        budget_data = cursor.fetchall()
        
        # Get recent expenses
        cursor.execute("""
            SELECT e.description, e.amount, e.category, e.date, b.category as budget_category
            FROM expenses e
            LEFT JOIN budgets b ON e.budget_id = b.id
            WHERE strftime('%Y-%m', e.date) = ?
            ORDER BY e.date DESC LIMIT 10
        """, (current_month,))
        recent_expenses = cursor.fetchall()

        # Get all expenses for the current month (not just 10 recent)
        cursor.execute("""
            SELECT e.description, e.amount, e.category, e.date, b.category as budget_category
            FROM expenses e
            LEFT JOIN budgets b ON e.budget_id = b.id
            WHERE strftime('%Y-%m', e.date) = ?
            ORDER BY e.date DESC
        """, (current_month,))
        all_expenses = cursor.fetchall()
    
    return render_template('budget.html', 
                          budget_data=budget_data,
                          recent_expenses=recent_expenses,
                          all_expenses=all_expenses,
                          current_month=current_month)

@app.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    """Add a new budget category"""
    if request.method == 'POST':
        category = request.form['category']
        planned_amount = float(request.form['planned_amount'])
        month = request.form['month']
        
        with sqlite3.connect('finance.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO budgets (category, planned_amount, month)
                VALUES (?, ?, ?)
            """, (category, planned_amount, month))
            conn.commit()
        
        return redirect(url_for('view_budget'))
    
    # Get current month for default value
    today = datetime.now().strftime('%Y-%m-%d')
    current_month = today[:7]
    return render_template('add_budget.html', current_month=current_month)

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    """Add a new expense"""
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']
        budget_id = request.form.get('budget_id')
        
        with sqlite3.connect('finance.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (description, amount, category, date, budget_id)
                VALUES (?, ?, ?, ?, ?)
            """, (description, amount, category, date, budget_id if budget_id else None))
            conn.commit()
        
        return redirect(url_for('view_budget'))
    
    # Get available budgets for current month
    today = datetime.now().strftime('%Y-%m-%d')
    current_month = today[:7]
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category FROM budgets WHERE month = ?
        """, (current_month,))
        budgets = cursor.fetchall()
    
    return render_template('add_expense.html', budgets=budgets, current_date=today)

@app.route('/api/financial_status')
def financial_status():
    """API endpoint for financial status overview"""
    today = datetime.now().strftime('%Y-%m-%d')
    current_month = today[:7]
    
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        
        # Total goals and completed goals
        cursor.execute("SELECT COUNT(*) FROM financial_goals")
        total_goals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM financial_goals WHERE current_amount >= target_amount")
        completed_goals = cursor.fetchone()[0]
        
        # Current month budget vs spending
        cursor.execute("""
            SELECT 
                COALESCE(SUM(b.planned_amount), 0) as total_budget,
                COALESCE(SUM(e.amount), 0) as total_spent
            FROM budgets b
            LEFT JOIN expenses e ON b.id = e.budget_id AND strftime('%Y-%m', e.date) = ?
            WHERE b.month = ?
        """, (current_month, current_month))
        budget_data = cursor.fetchone()
        
        # Recent transaction count
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE date >= date('now', '-7 days')")
        recent_activity = cursor.fetchone()[0]
        
    # Calculate financial health indicators
    goal_completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
    budget_utilization = (budget_data[1] / budget_data[0] * 100) if budget_data[0] > 0 else 0
    
    return jsonify({
        'success': True,
        'goal_completion_rate': goal_completion_rate,
        'budget_utilization': budget_utilization,
        'recent_activity': recent_activity
    })

@app.route('/delete_goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM financial_goals WHERE id = ?", (goal_id,))
        cursor.execute("DELETE FROM transactions WHERE goal_id = ?", (goal_id,))
        
        conn.commit()
    return redirect(url_for('view_goals'))

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    """Delete a journal entry by ID"""
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM journal WHERE id = ?", (entry_id,))
        conn.commit()
    return redirect(url_for('view_journal'))

@app.route('/edit_entry/<int:entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    """Edit a journal entry by ID"""
    with sqlite3.connect('finance.db') as conn:
        cursor = conn.cursor()
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            date = request.form['date']
            cursor.execute("""
                UPDATE journal SET title = ?, content = ?, date = ?
                WHERE id = ?
            """, (title, content, date, entry_id))
            conn.commit()
            return redirect(url_for('view_journal'))
        else:
            cursor.execute("SELECT id, title, content, date FROM journal WHERE id = ?", (entry_id,))
            entry = cursor.fetchone()
    return render_template('edit_entry.html', entry=entry)

if __name__ == '__main__':
    # Initialize the database
    init_db()
    # Only for development: enable debug mode and hot reloading
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))