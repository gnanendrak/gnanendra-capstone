import sqlite3

con = sqlite3.connect('results.db')
print('runs:')
for r in con.execute('SELECT id, n_questions, n_retries_total, total_cost_usd, fail_rate, use_fake FROM runs'): 
    print(' ', r)
    print('answers per run:')
    for r in con.execute('SELECT run_id, COUNT(*) FROM answers GROUP BY run_id'):
        print(' ', r)