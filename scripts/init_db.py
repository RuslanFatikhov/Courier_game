#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize database tables for local development.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")


if __name__ == "__main__":
    main()
