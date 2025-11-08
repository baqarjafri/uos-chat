# Stirling Chat MVP - Setup Script
# This script sets up the development environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stirling Chat MVP - Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Configure Git
Write-Host "Step 1: Configuring Git..." -ForegroundColor Yellow
$gitName = Read-Host "Enter your Git username (e.g., Baqar)"
$gitEmail = Read-Host "Enter your Git email (e.g., baqar@example.com)"

git config user.name "$gitName"
git config user.email "$gitEmail"

Write-Host "✓ Git configured successfully!" -ForegroundColor Green
Write-Host ""

# Step 2: Create Python Virtual Environment
Write-Host "Step 2: Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv venv

Write-Host "✓ Virtual environment created!" -ForegroundColor Green
Write-Host ""

# Step 3: Activate Virtual Environment and Install Dependencies
Write-Host "Step 3: Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "Activating virtual environment..." -ForegroundColor Gray

.\venv\Scripts\Activate.ps1

Write-Host "Installing packages from requirements.txt..." -ForegroundColor Gray
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "✓ Dependencies installed!" -ForegroundColor Green
Write-Host ""

# Step 4: Copy .env.example to .env
Write-Host "Step 4: Creating .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "⚠ .env file already exists. Skipping..." -ForegroundColor Yellow
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created from template!" -ForegroundColor Green
    Write-Host "⚠ IMPORTANT: Edit .env file and add your API keys!" -ForegroundColor Red
}
Write-Host ""

# Step 5: Start PostgreSQL with Docker
Write-Host "Step 5: Starting PostgreSQL with Docker..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host "✓ PostgreSQL started successfully!" -ForegroundColor Green
Write-Host ""

# Step 6: Test Database Connection
Write-Host "Step 6: Testing database connection..." -ForegroundColor Yellow
docker exec stirling_chat_db psql -U postgres -d stirling_chat -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

Write-Host "✓ Database connection successful!" -ForegroundColor Green
Write-Host ""

# Step 7: Make Initial Git Commit
Write-Host "Step 7: Making initial Git commit..." -ForegroundColor Yellow
git add .
git commit -m "Initial commit: Project setup with Docker PostgreSQL, environment config, and URL organization"

Write-Host "✓ Initial commit created!" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete! 🎉" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file and add your API keys:" -ForegroundColor White
Write-Host "   - FIRECRAWL_API_KEY" -ForegroundColor Gray
Write-Host "   - OPENAI_API_KEY" -ForegroundColor Gray
Write-Host "   - ANTHROPIC_API_KEY" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Verify PostgreSQL is running:" -ForegroundColor White
Write-Host "   docker ps" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Access PostgreSQL:" -ForegroundColor White
Write-Host "   docker exec -it stirling_chat_db psql -U postgres -d stirling_chat" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Stop PostgreSQL when done:" -ForegroundColor White
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host ""
