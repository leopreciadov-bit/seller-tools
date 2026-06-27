@echo off
REM Run from Windows (where gh may already be logged in)
cd /d %~dp0
gh auth status || gh auth login
call scripts\deploy_github_pages.sh
pause