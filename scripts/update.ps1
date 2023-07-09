# update the current branch and setup then start the bot

function Write-Error {
    param([String]$Message)
    Write-Host "`e[31;1mError:`e[0m $Message"
}

# save the branch names
$current_branch = git rev-parse --abbrev-ref HEAD
# set the working directory to the root of the repo
$script_dir = Split-Path $MyInvocation.MyCommand.Path -Parent
Set-Location "$script_dir/.."

# stash any changes
if (!(git diff --quiet)) {
    Write-Host "`e[1mStashing changes...`e[0m"
    git stash save "Auto stash before update $current_branch"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to stash changes, aborting update"
        exit 1
    }
    $changes_stashed = $true  # set a flag to pop the stash later
    Write-Host
}

# merge the current branch into deployment
Write-Host "`e[1mUpdating $current_branch...`e[0m"
git fetch origin
if ($LASTEXITCODE -ne 0) {
    Write-Error "Fetch failed, try again"
} else  { # pull changes after fetch
    git pull origin $current_branch
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Merge failed, resolve conflicts and restore changes manually"
        exit 1
    }
}
Write-Host

# if changes were stashed, pop the stash
if ($changes_stashed) {
    Write-Host "`e[1mRestoring stashed changes`e[0m"
    git stash pop
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to apply stashed changes"
        exit 1
    }
    Write-Host
}
Write-Host "`e[32;1mUpdate completed successfully`e[0m"

# setup the virtual environment
python .\scripts\setup.py --clean
& .\.venv\Scripts\Activate.ps1
# start the bot
python .\scripts\start.py --setup
python .\scripts\start.py --log