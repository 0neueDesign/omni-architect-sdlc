#!/bin/bash
# A simple script to automatically stage, commit, and push all changes.
git add .
git commit -m "Auto-commit from push script"
git push -u origin main
