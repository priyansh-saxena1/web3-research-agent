#!/bin/bash
# Development syntax checker script

echo "🔍 Running development syntax check..."

# Check Python syntax using built-in compile
echo "1️⃣ Python syntax validation..."
find . -name "*.py" -not -path "./__pycache__/*" -not -path "./.*" | while read file; do
    python -m py_compile "$file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - SYNTAX ERROR"
        python -m py_compile "$file"
        exit 1
    fi
done

echo ""
echo "2️⃣ Running comprehensive validation..."
python validate_startup.py

echo ""
echo "3️⃣ Quick import test..."
python -c "
try:
    import app
    print('  ✅ app.py imports successfully')
except Exception as e:
    print(f'  ❌ app.py import failed: {e}')
    exit(1)

try:
    from src.agent.research_agent import Web3ResearchAgent
    print('  ✅ research_agent.py imports successfully')
except Exception as e:
    print(f'  ❌ research_agent.py import failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All syntax checks passed! Ready for deployment."
else
    echo ""
    echo "❌ Syntax check failed. Please fix errors before deploying."
    exit 1
fi
