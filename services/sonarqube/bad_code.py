# bad_code.py
# This file intentionally contains many problems to trigger SonarQube rules
# performance issues, code smells, security smells, and bad practices.

import os
import sys
import time
import math
import json
import sqlite3
import threading
from collections import defaultdict

# Hardcoded credentials (security issue)
DB_USER = "admin"
DB_PASS = "password123"

# Global mutable default
CACHE = {}

# Mutable default argument
def append_items(target=[]):
    for i in range(5):
        target.append(i)
    return target

# Inefficient string concatenation in loop
def build_big_string(n):
    s = ""
    for i in range(n):
        s += str(i) + ","
    return s

# Unused variable and shadowing builtins
list = [1, 2, 3]
_unused = 42

# Repeated code / copy-paste
def compute_squares_bad(nums):
    out = []
    for i in nums:
        out.append(i * i)
    return out

def compute_cubes_bad(nums):
    out = []
    for i in nums:
        out.append(i * i * i)
    return out

# File not closed properly
def read_config(path):
    f = open(path, 'r')
    data = f.read()
    # forgot to close f
    return data

# Broad exception catching and ignoring
def divide(a, b):
    try:
        return a / b
    except Exception:
        return None

# Busy-wait (CPU waste)
def busy_wait(seconds):
    start = time.time()
    while time.time() - start < seconds:
        pass

# Inefficient large list usage
def make_large_list(n):
    return [i for i in range(n)]

# SQL with string formatting (SQL injection risk)
def unsafe_query(conn, user):
    cur = conn.cursor()
    query = f"SELECT * FROM users WHERE name = '{user}'"
    cur.execute(query)
    return cur.fetchall()

# Wrong comparison for float
def is_zero(x):
    return x == 0.0

# Using recursion without base case
def infinite_recursion(x):
    return infinite_recursion(x)

# Using threads unsafely with a shared global
def threaded_increment():
    def worker():
        for _ in range(100000):
            CACHE['count'] = CACHE.get('count', 0) + 1
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return CACHE.get('count')

# Blocking I/O inside an async function
import asyncio
async def blocking_sleep():
    time.sleep(1)  # should use await asyncio.sleep(1)

# Duplicate code paths and long functions
def long_function(a, b, c):
    # many unrelated steps
    x = 0
    for i in range(100000):
        x += (i * a) % (b + 1)
    y = []
    for j in range(10000):
        y.append(j * c)
    z = sum(y)
    if z > 0:
        return x / z
    else:
        return None

# Mixing concerns: IO + logic
def save_and_compute(path, data):
    open(path, 'w').write(json.dumps(data))
    # then compute something
    return sum(data)

# Dead code
if False:
    print('this will never run')

# Magic numbers and unclear names
def f(x):
    return x * 42 / 3.14159

# Main entry to exercise functions (so sonar-scanner will analyze them)
if __name__ == '__main__':
    append_items()
    s = build_big_string(1000)
    compute_squares_bad(range(10))
    compute_cubes_bad(range(10))
    try:
        read_config('/nonexistent/path')
    except Exception:
        pass
    divide(1, 0)
    # busy wait for 0.01s to waste CPU
    busy_wait(0.01)
    big = make_large_list(100000)
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE users(name TEXT)')
    unsafe_query(conn, "alice")
    is_zero(1e-12)
    # Do not actually call infinite_recursion()
    threaded_increment()
    # blocking_sleep is defined but not awaited here
    long_function(3, 5, 7)
    save_and_compute('/tmp/out.json', [1,2,3,4])
